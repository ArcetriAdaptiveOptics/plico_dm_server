from plico_dm_server.controller.abstract_deformable_mirror import \
    AbstractDeformableMirror
from plico.utils.decorator import override
import os
from ctypes import cdll, CDLL, c_uint, c_bool, c_float, byref, c_ubyte, POINTER
from plico.utils.logger import Logger
import numpy as np


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
        
    return slm_lib, image_lib
    


class MeadowlarkSlm1920(AbstractDeformableMirror):

    def __init__(self, slm_lib, image_lib, lut_filename):
        self._slm_lib = slm_lib
        self._image_lib = image_lib
        self._lut_filename = lut_filename
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
  
        
        #***you should replace *bit_linear.LUT with your custom LUT file***
        #but for now open a generic LUT that linearly maps input graylevels to output voltages
        #***Using *bit_linear.LUT does NOT give a linear phase response***
        self._logger.notice("Loading LUT file %s" % self._lut_filename)
        self._slm_lib.Load_LUT_file(self._board_number,
                                    str.encode(self._lut_filename));
        self._logger.notice('SLM LUT loaded %s' % self._lut_filename)

        # Create one vector to hold values for the SLM image and fill the wavefront correction with a blank
        self._logger.notice("Write image zeros")
        image_zero = np.zeros([self._width.value*self._height.value*self._bytes.value], np.uint8, 'C');
        self._write_image(image_zero)

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
   

    @override
    def setZonalCommand(self, zonalCommand):
        pass

    @override
    def getZonalCommand(self):
        pass

    @override
    def serialNumber(self):
        pass

    @override
    def getNumberOfActuators(self):
        return self._height.value * self._width.value

    @override
    def deinitialize(self):
        self._logger.notice('Deleting SLM SDK')
        self._slm_lib.Delete_SDK()
