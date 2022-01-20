
class FakeAlpaoDm():

    NUMBER_OF_ACTUATORS= 277
    NO_ERR= 0
    VALID_SERIAL_NUMBER= 'BAX182'
    VERSION_INFO= '305040164'

    def _setupErrorMessages(self):
        self._errorMsg={
        }


    def __init__(self, serialNumber):
        if serialNumber != self.VALID_SERIAL_NUMBER:
            raise SystemError('Invalid Serial Number')
        self._setupErrorMessages()
        self._lastErr= self.NO_ERR
        self._lastCommand= (0.,) * self.NUMBER_OF_ACTUATORS


    def Send(self, data):
        return 0


    def Get(self, key):
        if key == 'NbOfActuator':
            return float(self.NUMBER_OF_ACTUATORS)
        elif key == 'UseException':
            return float(0)
        elif key == 'VersionInfo':
            return float(self.VERSION_INFO)
        else:
            raise Exception('FIXME')


    def Set(self):
        raise Exception('method not implemented')


    def Reset(self):
        pass

    def Stop(self):
        pass
