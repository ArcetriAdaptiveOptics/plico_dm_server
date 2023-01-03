import numpy as np
from pickle import FALSE
#from ctypes import cdll, CDLL, c_uint, c_double, c_bool, c_float, byref, c_ubyte, POINTER, c_ulong, c_char_p


class FakeSlmLib():
    '''
    This Class simulates the main functions imported from the C++ header file "Blink_SDK_C_wrapper.h",
    used for Meadowlark Spatial Light Modulator 1920x1152 in our lab.
    It is used to test the related py module "meadolark_slm_1920.py".
    '''
    HEIGHT = 1152
    WIDTH = 1920
    DEPTH = 8
    BOARD_NUM = 1
    VALID_SERIAL_NUMBER = 4294967295
    FAIL_TASK = False
    NEED2CALL_WRITEIMAGECOMPLETE = False

    def __init__(self):
        pass

    def Get_image_height(self, board_number):
        return self.HEIGHT

    def Get_image_width(self, board_number):
        return self.WIDTH

    def Get_image_depth(self, board_number):
        return self.DEPTH

    def Create_SDK(self, bit_depth, num_boards_found, constructed_okay, is_nematic_type, RAM_write_enable, use_GPU, max_transients, num0):
        raise Exception('method not implemented')

    def Delete_SDK(self):
        pass

    def Load_LUT_file(self, board_number, str_lut_fname):
        pass

    def Write_image(self, board_number, image_np_data_as_POINTER, height_dot_width_dot_bytes_value, wait_For_Trigger, flip_immediate, OutputPulseImageFlip, OutputPulseImageRefresh, timeout_ms):
        # properly writes on slm
        if self.FAIL_TASK == False:
            retVal = 0
            self.NEED2CALL_WRITEIMAGECOMPLETE = True
        # write image error
        else:
            retVal = -1
            
        return retVal 

    def ImageWriteComplete(self, board_number, timeout_ms):
        # buffer ready to receive the next image
        if self.FAIL_TASK == False:
            retVal = 0
            self.NEED2CALL_WRITEIMAGECOMPLETE = False
        # fail
        else:
            retVal = -1
        return retVal

    def Read_SLM_temperature(self, board_number):
        return 25.2

    def Read_Serial_Number(self, board_number):
        return self.VALID_SERIAL_NUMBER

    def Get_last_error_message(self):
        pass


class FakeImageLib():

    def __init__(self):
        pass
    
