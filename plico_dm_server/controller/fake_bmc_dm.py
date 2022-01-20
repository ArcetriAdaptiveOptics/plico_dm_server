
class FakeBmcDm():

    VALID_SERIAL_NUMBER= '0123456789AB'
    VERSION_STRING= '3.2.0'
    NUMBER_OF_ACTUATORS= 140
    NO_ERR= 0
    ERR_UNKNOWN= 1
    ERR_SERIAL_NUMBER= 4
    ERR_INVALID_ACTUATOR_COUNT= 7
    ERR_ACTUATOR_ID= 9
    ERR_NOT_OPEN= 29


    def _setupErrorMessages(self):
        self._errorMsg={
            self.NO_ERR: "All is well.",
            self.ERR_UNKNOWN: "General error.",
            self.ERR_SERIAL_NUMBER: "Invalid serial number.",
            self.ERR_INVALID_ACTUATOR_COUNT: "Invalid Number of actuators.",
            self.ERR_ACTUATOR_ID: "Incorrect actuator ID.",
            self.ERR_NOT_OPEN: "Tried to operate driver before opening."
        }


    def __init__(self):
        self._setupErrorMessages()
        self._lastErr= self.NO_ERR
        self._isOpened= False
        self._lastCommand= (0.,) * self.NUMBER_OF_ACTUATORS


    def open_dm(self, serialNumber):
        if serialNumber != self.VALID_SERIAL_NUMBER:
            self._lastErr= self.ERR_SERIAL_NUMBER
        else:
            self._isOpened= True
            self._lastErr= self.NO_ERR
        return self._lastErr


    def close_dm(self):
        self._lastErr= self.NO_ERR
        return self._lastErr


    def send_data(self, data):
        if not self._isOpened:
            self._lastErr= self.ERR_INVALID_ACTUATOR_COUNT
            return self._lastErr
        if not hasattr(data, '__iter__'):
            raise TypeError("argument must be iterable")
        if len(data) != self.NUMBER_OF_ACTUATORS:
            self._lastErr= self.ERR_INVALID_ACTUATOR_COUNT
            return self._lastErr
        else:
            self._lastCommand= tuple(data)
            self._lastErr= self.NO_ERR
        return self._lastErr


    def get_actuator_data(self):
        if not self._isOpened:
            self._lastErr= self.ERR_NOT_OPEN
            return self._lastErr
        else:
            self._lastErr= self.NO_ERR
            return self._lastCommand


    def num_actuators(self):
        if not self._isOpened:
            self._lastErr= self.NO_ERR
            return self._lastErr
        else:
            self._lastErr= self.NO_ERR
            return self.NUMBER_OF_ACTUATORS


    def poke(self):
        if not self._isOpened:
            self._lastErr= self.ERR_ACTUATOR_ID
            return self._lastErr
        else:
            self._lastErr= self.NO_ERR
            return self._lastErr


    def send_data_custom_mapping(self):
        raise Exception('method not implemented')


    def default_mapping(self):
        if not self._isOpened:
            return tuple()
        return tuple(range(self.NUMBER_OF_ACTUATORS))


    def set_segment(self):
        raise Exception('method not implemented')


    def get_segment_range(self):
        raise Exception('method not implemented')


    def load_calibration_file(self):
        raise Exception('method not implemented')


    def get_status(self):
        return self._lastErr


    def error_string(self, error_code):
        return self._errorMsg[error_code]


    def set_profiles_path(self, path):
        raise Exception('method not implemented')


    def set_maps_path(self, path):
        raise Exception('method not implemented')


    def set_calibrations_path(self, path):
        raise Exception('method not implemented')


    def configure_log(self, path, level):
        self._lastErr= self.NO_ERR
        return self._lastErr


    def version_string(self):
        return self.VERSION_STRING
