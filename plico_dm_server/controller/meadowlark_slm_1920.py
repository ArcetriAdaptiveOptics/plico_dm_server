from plico_dm_server.controller.abstract_deformable_mirror import \
    AbstractDeformableMirror
from plico.utils.decorator import override
import os
from ctypes import cdll, CDLL, c_uint, c_double, c_bool, c_float, byref, \
    c_ubyte, POINTER, c_ulong, c_char_p
from plico.utils.logger import Logger
import numpy as np
from numpy import dtype
from PIL import Image



class MeadowlarkError(Exception):
    """Exception raised for Meadowlark Optics SDK error.

    ...

    Attributes:
        errorCode -- Meadowlark error code
        message -- explanation of the error
    """

    def __init__(self, message, errorCode=None):
        self.message = message
        self.errorCode = errorCode


def initialize_meadowlark_sdk(blink_dir_root):
    '''
    A function used to initializes SLM's hardware.

    The function opens communication and initializes the hardware,
    through Meadowlark's SDK. Loads DLL 'Blink_C_wrapper' and 'ImageGen' C 
    libraries, allowing SLM control.

    ...

    Parameters
    ----------
    blink_dir_root : str
        Path of 'Blink OverDrive Plus' directory.

    Returns
    -------
    slm_lib : ctype.CDLL
        Object/handle link to Dynamic Linked Library (DLL) 'Blink_C_wrapper',
        provided by Meadowlark's SDK. Allows SLM control.
    image_lib : ctype.CDLL
        Object/handle link to Dynamic Linked Library (DLL) 'ImageGen',
        provided by Meadowlark's SDK. Allows to write images on the Spatial
        Light Modulator.
    '''

    blink_c_wrapper_fname = os.path.join(
        blink_dir_root, 'SDK', 'Blink_C_wrapper')
    image_gen_fname = os.path.join(blink_dir_root, 'SDK', 'ImageGen')

    logger = Logger.of('Meadowlark SLM 1920')
    os.add_dll_directory(blink_dir_root)
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
    slm_lib.Create_SDK(bit_depth, byref(num_boards_found), byref(
        constructed_okay), is_nematic_type, RAM_write_enable, use_GPU,
        max_transients, 0)
    logger.notice('slm sdk created')

    if constructed_okay.value == 0:
        raise MeadowlarkError("Blink SDK did not construct successfully")

    if num_boards_found.value != 1:
        slm_lib.Delete_SDK()
        raise MeadowlarkError(
            "Blink SDK successfully constructed. "
            "Found  %s SLM controllers. "
            "1 SLM controller expected. Abort" % num_boards_found.value)

    slm_lib.Read_SLM_temperature.restype = c_double
    slm_lib.Read_Serial_Number.restype = c_ulong
    slm_lib.Get_last_error_message.restype = c_char_p

    return slm_lib, image_lib


class MeadowlarkSlm1920(AbstractDeformableMirror):
    '''
    A Class used to represent Meadowlark's Spatial Light Modulator (SLM) 1920x1152.

    Allows communication between Meadowlark's Software Development Kit (SDK)
    and the hardware.

    ...

    Attributes
    ----------
    slm_lib : ctypes.CDLL
        Object/handle link to Dynamic Linked Library (DLL) 'Blink_C_wrapper',
        provided by Meadowlark's SDK.
        Allows the control the Spatial Light Modulator.
    image_lib : ctypes.CDLL
        Object/handle link to Dynamic Linked Library (DLL) 'ImageGen',
        provided by Meadowlark's SDK.
        Allows to write images on the Spatial Light Modulator. Particularly:
        solids, stripes, checkerboards, random phases, blazed gratings, 
        sinusoidal, gratings, Bessel beams, holograms, Zernike polynomials,
        Fresnel lenses and superimposed images.
    lut_filename: str
        Path/file name of SLM's LUT calibration file. 
    wfc_filename : str
        Path/file name of SLM's Wavefront correction (wfc) file. 
    wl_calibration : float
        Wavelength, in meters, used for SLM calibration.

    Methods
    -------
    setZonalCommand(zonalCommand, add_correction = True)
        Applies actuators' commands in meters and writes the corresponding image
        on SLM's display.
    getZonalCommand()
        Returns the current command applied on SLM. 
    getNumberOfActuators()
        Returns the number of actuators, namely the number of SLM's pixels.
    getHeightInPixels()
        Returns the SLM's display height in pixels.
    getWidthInPixels()
        Returns the SLM's display width in pixels.
    getHeightInMillimeters()
        Returns the SLM's display height in millimeters.
    getWidthInMillimeters()
        Returns the SLM's display width in millimeters.
    getPixelHeightInMicrometers()
        Returns the Pixel's height in micron.
    getPixelWidthInMicrometers()
        Returns the Pixel's width in micron.
    getActuatorsPitchInMicrometers()
        Returns pixels pitch in micron.
    getTemperatureInCelsius()
        Returns SLM's current temperature in Celsius.
    serialNumber()
        Returns SLM's serial number.
    getLastErrorMessage()
        Prints the last encountered error message.
    deinitialize()
        Destroys the handle to the hardware, properly releases memory
        allocations, and shuts down the hardware. This is the last function
        that should be called when exiting your software.

    '''

    def __init__(self, slm_lib, image_lib, lut_filename, wfc_filename,
                 wl_calibration):
        self._slm_lib = slm_lib
        self._image_lib = image_lib
        self._lut_filename = lut_filename
        self._wfc_filename = wfc_filename
        self._wl_calibration = wl_calibration  # in meters
        self._logger = Logger.of('Meadowlark SLM 1920')
        self._logger.notice("Creating instance of MeadowlarkSlm1920")

        self._board_number = c_uint(1)
        self._wait_For_Trigger = c_uint(0)
        self._flip_immediate = c_uint(0)  # only supported on the 1024
        self._timeout_ms = c_uint(5000)
        self._center_x = c_float(256)
        self._center_y = c_float(256)
        self._VortexCharge = c_uint(3)
        self._fork = c_uint(0)
        self._RGB = c_uint(0)

        # Both pulse options can be false, but only one can be true. You either
        # generate a pulse when the new image begins loading to the SLM
        # or every 1.184 ms on SLM refresh boundaries, or if both are false no
        # output pulse is generated.
        self._OutputPulseImageFlip = c_uint(0)
        # only supported on 1920x1152, FW rev 1.8.
        self._OutputPulseImageRefresh = c_uint(0)

        self._read_parameters_and_write_zero_image()
        self._wl_calib_reset = None
        self._wfc_reset = None

    def isReady(self):
        return True

    def _read_parameters_and_write_zero_image(self):
        self._logger.notice("Reading SLM height")
        self._height = c_uint(
            self._slm_lib.Get_image_height(self._board_number))
        self._logger.notice("Reading SLM width")
        self._width = c_uint(self._slm_lib.Get_image_width(self._board_number))
        self._logger.notice("Reading SLM depth")
        self._depth = c_uint(self._slm_lib.Get_image_depth(
            self._board_number))  # Bits per pixel
        self._logger.notice("Computing bytes values")
        self._bytes = c_uint(self._depth.value // 8)
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
        # but for now open a generic LUT that linearly maps input graylevels to output voltages
        #***Using *bit_linear.LUT does NOT give a linear phase response***
        self._logger.notice("Loading LUT file %s" % self._lut_filename)
        self._slm_lib.Load_LUT_file(self._board_number,
                                    str.encode(self._lut_filename))
        self._logger.notice('SLM LUT loaded %s' % self._lut_filename)

        # loading WaveFront Correction file
        self._logger.notice("Loading WFC file %s" % self._wfc_filename)
        im = Image.open(self._wfc_filename)
        self._logger.notice('WFC file loaded %s' % self._wfc_filename)
        wfc = np.array(im, dtype=np.uint8)
        self._wfc = np.reshape(wfc, (self.getNumberOfActuators(),))

        # useless operation
        # Create one vector to hold values for the SLM image and fill the
        # wavefront correction with a blank
        self._logger.notice("Write image zeros")
        image_zero = np.zeros(
            [self._width.value * self._height.value * self._bytes.value], np.uint8, 'C')
        self._write_image(image_zero)

    # def _load_calibration_scale(self):
    #     self._gray_scale, self._voltage_scale = np.loadtxt(self._lut_filename, unpack=True)

    def _write_image(self, image_np):
        # TODO: rise error if image_np is not uint8
        if image_np.dtype != dtype('uint8'):
            raise MeadowlarkError("dtype elements of image_np must be uint8.")

        retVal = self._slm_lib.Write_image(
            self._board_number,
            image_np.ctypes.data_as(POINTER(c_ubyte)),
            self._height.value * self._width.value * self._bytes.value,
            self._wait_For_Trigger,
            self._flip_immediate,
            self._OutputPulseImageFlip,
            self._OutputPulseImageRefresh,
            self._timeout_ms)
        if(retVal == -1):
            self._slm_lib.Delete_SDK()
            raise MeadowlarkError("Write Image error. DMA Failed.")
        else:
            # check the buffer is ready to receive the next image
            retVal = self._slm_lib.ImageWriteComplete(
                self._board_number, self._timeout_ms)
            if(retVal == -1):
                raise MeadowlarkError(
                    "ImageWriteComplete failed, trigger never received?")
                self._slm_lib.Delete_SDK()

    def _write_image_from_wavefront(self, wavefront, add_correction=True):
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
        # TODO: controllare che a parita di input che sia 1D o 2D
        # dia lo stesso risultato
        if add_correction is True:
            wfc = self._wfc
        else:
            wfc = np.zeros(self.getNumberOfActuators(), dtype=np.uint8)

        bmp_array_image = self._convert2_modulo256(wavefront, norm=None)

        bmp_array_image = np.reshape(
            bmp_array_image, (self._height.value * self._width.value,), 'C')

        image = bmp_array_image + wfc
        self._write_image(image)

        return image

    def _convert2_modulo256(self, array, norm=None):
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
            norm = self._wl_calibration

        data = array * 256 / norm
        data = np.round(data)
        return data.astype(np.uint8)

    @override
    def setZonalCommand(self, zonalCommand, add_correction=True):
        '''
        Applies actuators' commands in units of meters and writes the
        corresponding image on SLM's display.

        The actuators' command is converted into a bit map image, defined as 
        an unsigned integer 8-bit numpy.ndarray (dtype = np.uint8) with a
        modulo256 operation, normalized to the calibration wavelength.
        Finally, writes the outcome bmp vector on SLM display.
        If add_correction is test to True, the written image on SLM is corrected
        with the Wavefront Correction file (WFC).

        Parameters
        ----------

        zonalCommand : numpy.ndarray
            wavefront to be applied to the SLM, in units of meters.

        add_correction: bool
            if is set to True, the applied image on SLM is the sum of the 
            corresponding bmp image of the input wavefront and the Wavefront
            correction File (WFC). Otherwise, the WFC corresponds to null vector:
            thus no correction is applied. Default value is set to True. 
        '''
        
        inputVectorShape = len(zonalCommand.shape)

        if inputVectorShape == 1:
            if len(zonalCommand) != self.getNumberOfActuators():
                raise MeadowlarkError(
                    "Wrong size for zonalCommand (1D array size is %d instead of %d)" % (
                        len(zonalCommand), self.getNumberOfActuators()))
        if inputVectorShape == 2:
            rows, cols = zonalCommand.shape
            if rows != self._height.value or cols != self._width.value:
                raise MeadowlarkError(
                    "Wrong shapes for zonalCommand (2D array shape is (%d, %d) instead of (%d, %d))" % (
                        zonalCommand.shape[0], zonalCommand.shape[-1], self._height.value, self._width.value))

        if inputVectorShape != 1 and inputVectorShape != 2:
            raise MeadowlarkError(
                "zonalCommand must be a 1- or 2-D numpy array!")
        if zonalCommand.dtype == np.uint8 : 
            raise MeadowlarkError(
                "zonalCommand must be defined in units of meters!")
        
        self._zonal_command = zonalCommand
        self._applied_command = self._write_image_from_wavefront(
            self._zonal_command, add_correction)

    @override
    def getZonalCommand(self):
        '''
        Returns the current command applied on SLM.

        Returns
        -------
        zonal_command : numpy.ndarray
            is a 1- or 2-D numpy array of the applied commands, in units
            of meters
        '''
        return self._zonal_command

    @override
    def getNumberOfActuators(self):
        '''
        Returns the number of actuators, namely the number of SLM's pixels.

        Returns
        -------
        Nact : int
            is the number of SLM pixels
        '''
        return self._height.value * self._width.value

    @override
    def getHeightInPixels(self):
        '''
        Returns the SLM's display height in pixels.

        Returns
        -------
        height : int
            is the number of pixels in SLM's display height
        '''
        return self._height.value

    @override
    def getWidthInPixels(self):
        '''
        Returns the SLM's display width in pixels.

        Returns
        -------
        width : int
            is the number of pixels in SLM's display width
        '''
        return self._width.value

    @override
    def getHeightInMillimeters(self):
        '''
        Returns the SLM's display height in millimeters.

        Returns
        -------
        height : float
            is the SLM's display height in millimeters
        '''
        return self._height_in_mm

    @override
    def getWidthInMillimeters(self):
        '''
        Returns the SLM's display width in millimeters.

        Returns
        -------
        width : float
            is the SLM's display width in millimeters
        '''

        return self._width_in_mm

    @override
    def getPixelHeigthInMicrometers(self):
        '''
        Returns the Pixel's height in micron.

        Returns
        -------
        height : float
            is the SLM's pixel height in micron
        '''
        return self._height_in_mm / self._height.value * 1e3

    @override
    def getPixelWidthInMicrometers(self):
        '''
        Returns the Pixel's width in micron.

        Returns
        -------
        width : float
            is the SLM's pixel width in micron
        '''
        return self._width_in_mm / self._width.value * 1e3

    @override
    def getActuatorsPitchInMicrometers(self):
        '''
        Returns pixels pitch in micron.

        Returns
        -------
        pitch : float
            Is the the center-to-center distance of the pixels, in micron.
        '''
        return self._pixel_pitch_in_um

    @override
    def getTemperatureInCelsius(self):
        '''
        Returns SLM's current temperature in Celsius.

        Returns
        -------
        temperature : float
            Actual temperature of SLM in Celsius degrees.
        '''
        return self._slm_lib.Read_SLM_temperature(self._board_number)

    @override
    def serialNumber(self):
        '''
        Returns SLM's serial number.

        Returns
        -------
        serial_number : int
            Serial number of Meadowlark SLM.
        '''
        return self._slm_lib.Read_Serial_Number(self._board_number)

    @override
    def getLastErrorMessage(self):
        '''
        Prints the last encountered error message.

        Returns
        -------
        last_error_message : str
            string of the last error message
        '''
        return self._slm_lib.Get_last_error_message()

    @override
    def deinitialize(self):
        '''
        Destroys the handle to the hardware, properly releases memory
        allocations, and shuts down the hardware. This is the last function
        that should be called when exiting your software.
        '''
        self._logger.notice('Deleting SLM SDK')
        self._slm_lib.Delete_SDK()
        
    # ImageGen function for Holograms Not implemented
    #
    # def InitializeHologramGenerator(self, iterations = 1):
    #     '''
    #     This function opens communication with the GPU, and specifies
    #     the height and width of the hologram that will be computed such
    #     that buffers can be allocated. This also allocates the number
    #     of iterations that will be used in computing the hologram.
    #     The hologram generator relies on the GPU to complete the required
    #     computations.
    #     Once done using the GPU to compute holograms, DestructHologramGenerator
    #     must be call.
    #
    #     Parameters
    #     ----------
    #
    #     iterations: (int)
    #         number of iterations that will be used in computing the hologram.
    #         Default is 1.
    #
    #     Returns
    #     -------
    #     retVal: (int)
    #         1 or 0 (?)
    #     '''
    #     # if width is None:
    #     #     width = self._width
    #     # if height is None:
    #     #     height = self._height
    #     retVal = self._image_lib.Initialize_HologramGenerator(
    #         self._width,
    #         self._height,
    #         self._depth,
    #         iterations,
    #         self._RGB)
    #     return retVal
    #
    # def DestructHologramGenerator(self):
    #     '''
    #     This function must be called when done using the GPU to compute holograms.
    #     '''
    #     self._image_lib.Destruct_HologramGenerator()
    #
    # # def GenerateHologram(self):
    # #   return 0
    #
    # def InitializeGerchbergSaxton(self):
    #     '''
    #     This function initializes the Gerchberg Saxton hologram generator.
    #     This procedure allows to make a hologram to create an image in the
    #     Fourier Plane.
    #     Once done using the GPU to compute holograms of images,
    #     DestructGerchbergSaxton must be call
    #     '''
    #     retVal = self._image_lib.Initialize_GerchbergSaxton()
    #     return retVal
    #
    # def DestructGerchbergSaxton(self):
    #     '''
    #     This must be called when done using the GPU to compute
    #     holograms of images.
    #     '''
    #     self._image_lib. Destruct_GerchbergSaxton()
    #
    # def ComputeGerchbergSaxtonHologram(self):
    #     '''
    #     This function computes a hologram of an image using a Gerchberg Saxton.
    #     The user should supply an array to be filled with image data by the GPU,
    #     an array containing the desired image to be created in the Fourier Plane,
    #     the height and width of the SLM, and the number of iterations used in
    #     the hologram computation.
    #     '''
