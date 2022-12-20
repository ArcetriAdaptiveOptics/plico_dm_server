from plico_dm_server.controller.abstract_deformable_mirror import \
    AbstractDeformableMirror
from plico.utils.decorator import override
import os
from ctypes import cdll, CDLL, c_uint, c_double, c_bool, c_float, byref, c_ubyte, POINTER, c_ulong, c_char_p
from plico.utils.logger import Logger
import numpy as np
from numpy import dtype
from PIL import Image
 

class MeadowlarkError(Exception):
    """Exception raised for Meadowlark Optics SDK error.

    Attributes:
        errorCode -- Meadowlark error code
        message -- explanation of the error
    """

    def __init__(self, message, errorCode=None):
        self.message = message
        self.errorCode = errorCode


def initialize_meadowlark_sdk():
    
    blink_c_wrapper_fname = "C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\Blink_C_wrapper"
    image_gen_fname = "C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\ImageGen"
    
    logger = Logger.of('Meadowlark SLM 1920')
    os.add_dll_directory("C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus")
    cdll.LoadLibrary(blink_c_wrapper_fname)
    slm_lib = CDLL("Blink_C_wrapper")
    logger.notice('slm_lib loaded %s' % (blink_c_wrapper_fname))
    
    # Open the image generation library
    cdll.LoadLibrary(image_gen_fname)
    image_lib = CDLL("ImageGen")
    logger.notice('slm_lib loaded %s' % (image_gen_fname))

    
    # Basic parameters for calling Create_SDK
    bit_depth = c_uint(12)
    num_boards_found = c_uint(0)
    constructed_okay = c_uint(-1)
    is_nematic_type = c_bool(1)
    RAM_write_enable = c_bool(1)
    use_GPU = c_bool(1)
    max_transients = c_uint(20)
    
    # Call the Create_SDK constructor
    # Returns a handle that's passed to subsequent SDK calls
    slm_lib.Create_SDK(bit_depth, byref(num_boards_found), byref(constructed_okay), is_nematic_type, RAM_write_enable, use_GPU, max_transients, 0)
    logger.notice('slm sdk created')
    
    if constructed_okay.value == 0:
        raise MeadowlarkError("Blink SDK did not construct successfully");
    
    if num_boards_found.value != 1:
        slm_lib.Delete_SDK()
        raise MeadowlarkError(
            "Blink SDK successfully constructed. "
            "Found  %s SLM controllers. "
            "1 SLM controller expected. Abort" % num_boards_found.value)
    
    slm_lib.Read_SLM_temperature.restype = c_double
    #slm_lib.Read_Serial_Number.restype = c_ulong
    slm_lib.Get_last_error_message.restype = c_char_p
     
    return slm_lib, image_lib
  


class MeadowlarkSlm1920(AbstractDeformableMirror):
    '''
    Class to ...
    
    Parameters
    ----------
    slm_lib: 
    '''

    def __init__(self, slm_lib, image_lib, lut_filename, wfc_filename, wl_calibration):
        self._slm_lib = slm_lib
        self._image_lib = image_lib
        self._lut_filename = lut_filename
        self._wfc_filename = wfc_filename
        self._wl_calibration = wl_calibration #in meters
        self._logger= Logger.of('Meadowlark SLM 1920')
        self._logger.notice("Creating instance of MeadowlarkSlm1920")
        
        self._board_number = c_uint(1)
        self._wait_For_Trigger = c_uint(0)
        self._flip_immediate = c_uint(0) #only supported on the 1024
        self._timeout_ms = c_uint(5000)
        self._center_x = c_float(256)
        self._center_y = c_float(256)
        self._VortexCharge = c_uint(3)
        self._fork = c_uint(0)
        self._RGB = c_uint(0)
        
        # Both pulse options can be false, but only one can be true. You either generate a pulse when the new image begins loading to the SLM
        # or every 1.184 ms on SLM refresh boundaries, or if both are false no output pulse is generated.
        self._OutputPulseImageFlip = c_uint(0)
        self._OutputPulseImageRefresh = c_uint(0) #only supported on 1920x1152, FW rev 1.8. 
        
        self._read_parameters_and_write_zero_image()
           
    
    def _read_parameters_and_write_zero_image(self):
        self._logger.notice("Reading SLM height")
        self._height = c_uint(self._slm_lib.Get_image_height(self._board_number))
        self._logger.notice("Reading SLM width")
        self._width = c_uint(self._slm_lib.Get_image_width(self._board_number))
        self._logger.notice("Reading SLM depth")
        self._depth = c_uint(self._slm_lib.Get_image_depth(self._board_number)) #Bits per pixel
        self._logger.notice("Computing bytes values")
        self._bytes = c_uint(self._depth.value//8)
#        center_x = c_uint(width.value//2)
#        center_y = c_uint(height.value//2)
        self._logger.notice('SLM height/width/depth %d/%d/%d' % (
            self._height.value, self._width.value, self._depth.value))
        if self._width.value != 1920:
            self._slm_lib.Delete_SDK()
            raise MeadowlarkError(
                "Width is %d. Only 1920 model are supported" % self._width)
        # if self._height.value != 1152:
        #     self._slm_lib.Delete_SDK()
        #     raise MeadowlarkError(
        #         "Height is %d. Only 1920x1152 models are supported"%self._height)
        # if self._depth.value !=8:
        #     self._slm_lib.Delete_SDK()
        #     raise MeadowlarkError(
        #         "Bit depth is %d. Only 1920x1152 models are supported"%self._depth)
        self._pixel_pitch_in_um = 9.2
        self._height_in_mm = 10.7
        self._width_in_mm = 17.6
        
        #***you should replace *bit_linear.LUT with your custom LUT file***
        #but for now open a generic LUT that linearly maps input graylevels to output voltages
        #***Using *bit_linear.LUT does NOT give a linear phase response***
        self._logger.notice("Loading LUT file %s" % self._lut_filename)
        self._slm_lib.Load_LUT_file(self._board_number,
                                    str.encode(self._lut_filename));
        self._logger.notice('SLM LUT loaded %s' % self._lut_filename)
        
        # loading WaveFront Correction file 
        self._logger.notice("Loading WFC file %s" % self._wfc_filename)
        im = Image.open(self._wfc_filename)
        self._logger.notice('WFC file loaded %s' % self._lut_filename)
        wfc = np.array(im, dtype = np.uint8)
        self._wfc = np.reshape(wfc,(self.getNumberOfActuators(),))
        

        # Create one vector to hold values for the SLM image and fill the wavefront correction with a blank
        self._logger.notice("Write image zeros")
        image_zero = np.zeros([self._width.value*self._height.value*self._bytes.value], np.uint8, 'C');
        self._write_image(image_zero)
        
    # def _load_calibration_scale(self):
    #     self._gray_scale, self._voltage_scale = np.loadtxt(self._lut_filename, unpack=True)

    def _write_image(self, image_np):
        retVal = self._slm_lib.Write_image(
        self._board_number, 
        image_np.ctypes.data_as(POINTER(c_ubyte)), 
        self._height.value*self._width.value*self._bytes.value, 
        self._wait_For_Trigger, 
        self._flip_immediate, 
        self._OutputPulseImageFlip, 
        self._OutputPulseImageRefresh, 
        self._timeout_ms)
        if(retVal == -1):
            self._slm_lib.Delete_SDK()
            raise MeadowlarkError("Write Image error. DMA Failed.")
        else: 
        #check the buffer is ready to receive the next image
            retVal = self._slm_lib.ImageWriteComplete(self._board_number, self._timeout_ms);
            if(retVal == -1):
                raise ("ImageWriteComplete failed, trigger never received?")
                self._slm_lib.Delete_SDK()
                
    def _write_image_from_wavefront(self, wavefront, add_correction = True):
        '''
        Writes a Bitmap image on SLM, from a wavefront map that is converted into
        a modulo 256 array
        
        Parameters
        ----------
        wavefront (numpy array 1D or 2D):
            if one dimensional, the store method must be Row-major order
            for instance wavefront = np.reshape(2Darray,(Dim,) 'C')
        
        add_correction (bool):
            if True, wavefront correction (wfc) is applied to the image.
            Otherwise, is a null vector.
        Returns
        -------
        image : (numpy array 1D)  
            returns a one dimensional numpy array with np.uint8 entries. 
            Is the sum of the i and wfc images
        '''
        if add_correction is True:
            wfc = self._wfc
        else:
            wfc = np.zeros(self.getNumberOfActuators(), dtype = np.uint8)
        
        bmp_array_image = self._convert2_modulo256(wavefront, norm=None)
        
        bmp_array_image = np.reshape(bmp_array_image, (self._height.value * self._width.value,), 'C')
        
        image = bmp_array_image + wfc
        self._write_image(image)
        
        return image
    
    def _convert2_modulo256(self, array, norm = None):
        '''
        Converts the input array into a modulo 256 numpy array  
         
        Parameters
        ----------
        
        array: (numpy array 1D o 2D)
        
        norm (scalar in meters):
         if None, is set to the calibration wavelength, the one from
         the LUT calibration file, for instance 635 e-9m 
         
         Returns
         -------
         data: returns a modulo 256 numpy array
              
        '''
        if norm is None:
            norm  = self._wl_calibration
        
        data  = array*255/norm
        data = np.round(data)
        return data.astype(np.uint8)
    
    # def Volt2Gray(self, cmd_vector):
    #     # TODO: check if the outputs on the calibration lut file are actually voltages
    #     '''
    #     This function converts the input voltage(?) array and returns gray scaled array
    #     through the LUT file calibration.
    #     '''
    #     assert len(cmd_vector)==self.getNumberOfActuators()
    #     gray_vector = np.zeros(self.getNumberOfActuators())
    #     # TODO avoid for loop, it takes too much time for 10e7 elements
    #     for idx, volt in enumerate(cmd_vector):
    #         gray_index = np.where(np.logical_or(self._voltage_scale==volt, np.isclose(self._voltage_scale,volt,atol=0.5)))[0][0]
    #         gray_vector[idx] = self._gray_scale[gray_index]
    #
    #     return np.array(gray_vector,dtype=np.uint8)
        
    @override
    def setZonalCommand(self, zonalCommand, add_correction = True):
        '''
        Sets zonal commands on SLM.
         
        Parameters
        ----------
        
        zonalCommand: (numpy array, 1D)
            wavefront to be applied to the SLM in units of meters
            the zonalCommand is summed to the reference wavefront specified 
            in the config file before being applied by the SLM
              
        add_correction (bool):
            if True, wavefront correction (wfc) is applied to the image.
            Otherwise, is a null vector.
        '''
        assert len(zonalCommand)==self.getNumberOfActuators()
        self._zonal_command = zonalCommand
        self._applied_command = self._write_image_from_wavefront(self._zonal_command, add_correction)
        

    @override
    def getZonalCommand(self):
        return self._zonal_command

    # @override
    # def getSerialNumber(self):
    #     return c_ulong(self._slm_lib.Read_Serial_Number(self._board_number)).value

    @override
    def getNumberOfActuators(self):
        return self._height.value * self._width.value
    @override 
    def getHeightInPixels(self):
        return self._height.value
    
    @override 
    def getWidthInPixels(self):
        return self._width.value
    
    @override
    def getHeightInMillimeters(self):
        return self._height_in_mm
    
    @override
    def getWidthInMillimeters(self):
        return self._width_in_mm
    
    @override 
    def getPixelHeigthInMicrometers(self):
        return self._height_in_mm/self._height.value*1e3
    
    @override 
    def getPixelWidthInMicrometers(self):
        return self._width_in_mm/self._width.value*1e3
    
    @override
    def getActuatorsPitchInMicrometers(self):
        return self._pixel_pitch_in_um
    
    @override 
    def getTemperatureInCelsius(self):
        return self._slm_lib.Read_SLM_temperature(self._board_number)
    
    @override
    def serialNumber(self):
        return self._slm_lib.Read_Serial_Number(self._board_number)
    @override 
    def getLastErrorMessage(self):
        return self._slm_lib.Get_last_error_message()
    
    @override
    def deinitialize(self):
        self._logger.notice('Deleting SLM SDK')
        self._slm_lib.Delete_SDK()
