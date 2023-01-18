
import os
import numpy
from ctypes import cdll, CDLL, c_uint, c_bool, c_float, byref, POINTER, c_ubyte
from time import sleep


class SLM(object):

    def __init__(self):
        pass

    def _create_sdk(self):
        # slm_lib.Create_SDK
        pass

    def _write_image(self, nparray):
        # image_lib ?
        # slm_lib.WriteImage()
        # slm_lib.ImageWriteComplete()
        pass

    def _destroy(self):
        # slm_lib.Delete_SDK()
        pass

    def get_temparature(self):
        # slm.get
        pass

    def version(self):
        # slm_lib.getVersion()
        pass


def test_slm():
    # Load the DLL
    # Blink_C_wrapper.dll, Blink_SDK.dll, ImageGen.dll, FreeImage.dll and wdapi1021.dll
    # should all be located in the same directory as the program referencing the
    # library
    os.add_dll_directory(
        "C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus")
    cdll.LoadLibrary(
        "C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\Blink_C_wrapper")
    slm_lib = CDLL("Blink_C_wrapper")

    # Open the image generation library
    cdll.LoadLibrary(
        "C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\SDK\\ImageGen")
    image_lib = CDLL("ImageGen")

    # Basic parameters for calling Create_SDK
    bit_depth = c_uint(12)
    num_boards_found = c_uint(0)
    constructed_okay = c_uint(-1)
    is_nematic_type = c_bool(1)
    RAM_write_enable = c_bool(1)
    use_GPU = c_bool(1)
    max_transients = c_uint(20)
    board_number = c_uint(1)
    wait_For_Trigger = c_uint(0)
    flip_immediate = c_uint(0)  # only supported on the 1024
    timeout_ms = c_uint(5000)
    center_x = c_float(256)
    center_y = c_float(256)
    VortexCharge = c_uint(3)
    fork = c_uint(0)
    RGB = c_uint(0)

    # Both pulse options can be false, but only one can be true. You either generate a pulse when the new image begins loading to the SLM
    # or every 1.184 ms on SLM refresh boundaries, or if both are false no
    # output pulse is generated.
    OutputPulseImageFlip = c_uint(0)
    # only supported on 1920x1152, FW rev 1.8.
    OutputPulseImageRefresh = c_uint(0)

    # Call the Create_SDK constructor
    # Returns a handle that's passed to subsequent SDK calls
    slm_lib.Create_SDK(bit_depth, byref(num_boards_found), byref(
        constructed_okay), is_nematic_type, RAM_write_enable, use_GPU, max_transients, 0)

    if constructed_okay.value == 0:
        print ("Blink SDK did not construct successfully")

    if num_boards_found.value == 1:
        print ("Blink SDK was successfully constructed")
        print ("Found %s SLM controller(s)" % num_boards_found.value)
        height = c_uint(slm_lib.Get_image_height(board_number))
        width = c_uint(slm_lib.Get_image_width(board_number))
        depth = c_uint(slm_lib.Get_image_depth(board_number))  # Bits per pixel
        Bytes = c_uint(depth.value // 8)
        center_x = c_uint(width.value // 2)
        center_y = c_uint(height.value // 2)

        #***you should replace *bit_linear.LUT with your custom LUT file***
        # but for now open a generic LUT that linearly maps input graylevels to output voltages
        #***Using *bit_linear.LUT does NOT give a linear phase response***
        if width == 512:
            if depth == 8:
                slm_lib.Load_LUT_file(
                    board_number, b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\512x512_linearVoltage.LUT")
            if depth == 16:
                slm_lib.Load_LUT_file(
                    board_number, b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\512x512_16bit_linearVoltage.LUT")
        if width == 1920:
            slm_lib.Load_LUT_file(
                board_number, b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\1920x1152_linearVoltage.LUT")
        if width == 1024:
            slm_lib.Load_LUT_file(
                board_number, b"C:\\Program Files\\Meadowlark Optics\\Blink OverDrive Plus\\LUT Files\\1024x1024_linearVoltage.LUT")

        # Create two vectors to hold values for two SLM images with example
        # images, and fill the wavefront correction with a blank
        ImageOne = numpy.zeros(
            [width.value * height.value * Bytes.value], numpy.uint8, 'C')
        ImageTwo = numpy.zeros(
            [width.value * height.value * Bytes.value], numpy.uint8, 'C')
        WFC = numpy.zeros([width.value * height.value *
                           Bytes.value], numpy.uint8, 'C')

        # Write a blank pattern to the SLM to get going
        retVal = slm_lib.Write_image(board_number, ImageOne.ctypes.data_as(POINTER(c_ubyte)), height.value * width.value *
                                     Bytes.value, wait_For_Trigger, flip_immediate, OutputPulseImageFlip, OutputPulseImageRefresh, timeout_ms)
        if(retVal == -1):
            print ("DMA Failed")
            slm_lib.Delete_SDK()
        else:
            # Generate phase gradients
            VortexCharge = 5
            image_lib.Generate_LG(ImageOne.ctypes.data_as(POINTER(c_ubyte)), WFC.ctypes.data_as(POINTER(
                c_ubyte)), width.value, height.value, depth.value, VortexCharge, center_x.value, center_y.value, fork.value, RGB.value)
            VortexCharge = 3
            image_lib.Generate_LG(ImageTwo.ctypes.data_as(POINTER(c_ubyte)), WFC.ctypes.data_as(POINTER(
                c_ubyte)), width.value, height.value, depth.value, VortexCharge, center_x.value, center_y.value, fork.value, RGB.value)

            # Loop between our phase gradient images
            for i in range(0, 10):

                # write image returns on DMA complete, ImageWriteComplete returns when the hardware
                # image buffer is ready to receive the next image. Breaking this into two functions is
                # useful for external triggers. It is safe to apply a trigger when Write_image is complete
                # and it is safe to write a new image when ImageWriteComplete
                # returns
                retVal = slm_lib.Write_image(board_number, ImageOne.ctypes.data_as(POINTER(c_ubyte)), height.value * width.value *
                                             Bytes.value, wait_For_Trigger, flip_immediate, OutputPulseImageFlip, OutputPulseImageRefresh, timeout_ms)
                if(retVal == -1):
                    print ("DMA Failed")
                    break
                else:
                    # check the buffer is ready to receive the next image
                    retVal = slm_lib.ImageWriteComplete(
                        board_number, timeout_ms)
                    if(retVal == -1):
                        print ("ImageWriteComplete failed, trigger never received?")
                        break

                # This is in seconds. IF USING EXTERNAL TRIGGERS, SET THIS TO 0
                sleep(1.0)

                retVal = slm_lib.Write_image(board_number, ImageTwo.ctypes.data_as(POINTER(c_ubyte)), height.value * width.value *
                                             Bytes.value, wait_For_Trigger, flip_immediate, OutputPulseImageFlip, OutputPulseImageRefresh, timeout_ms)
                if(retVal == -1):
                    print ("DMA Failed")
                    break
                else:
                    # check the buffer is ready to receive the next image
                    retVal = slm_lib.ImageWriteComplete(
                        board_number, timeout_ms)
                    if(retVal == -1):
                        print ("ImageWriteComplete failed, trigger never received?")
                        break

                # This is in seconds. IF USING EXTERNAL TRIGGERS, SET THIS TO 0
                sleep(1.0)

            # Always call Delete_SDK before exiting
            slm_lib.Delete_SDK()
