import numpy as np
from plico.utils.decorator import override
from plico.utils.logger import Logger
from palpao_server.mirror_controller.abstract_deformable_mirror \
    import AbstractDeformableMirror


class BmcError(Exception):
    """Exception raised for Boston Micromachines Corporation error.

    Attributes:
        errorCode -- BMC error code
        message -- explanation of the error
    """

    def __init__(self, errorCode, message):
        self.errorCode = errorCode
        self.message = message


class BmcDeformableMirror(AbstractDeformableMirror):

    BMC_NO_ERR= 0

    def __init__(self, bmcDm, bmcSerialNumber):
        self._dm= bmcDm
        self._serialNumber= bmcSerialNumber
        self._logger= Logger.of('BMC Deformable Mirror')
        self._logger.notice("opening device <%s>" % self._serialNumber)
        self._openDm(self._serialNumber)
        # TODO: is this really needed? Does BmcDm really crash?
        self._initializeToZero()


    def _initializeToZero(self):
        self._logger.notice(
            "set mirror to zero. Avoid crashes"
            " when get_actuator_data is called before send_data")
        self.setZonalCommand(np.zeros(self.getNumberOfActuators()))


    def _raiseBmcError(self, errCode):
        if errCode != self.BMC_NO_ERR:
            try:
                errString= self._dm.error_string(errCode)
            except Exception:
                errString= \
                    "Unknown error message, cannot convert error code"
            raise BmcError(errCode, errString)


    def _openDm(self, serial):
        self._raiseBmcError(self._dm.open_dm(str(serial)))


    def _closeDm(self):
        self._raiseBmcError(self._dm.close_dm())


    @override
    def setZonalCommand(self, zonalCommand):
        self._raiseBmcError(self._dm.send_data(zonalCommand))


    @override
    def getZonalCommand(self):
        return np.array(self._dm.get_actuator_data())


    @override
    def serialNumber(self):
        return self._serialNumber


    @override
    def getNumberOfActuators(self):
        return self._dm.num_actuators()


    @override
    def deinitialize(self):
        self._closeDm()
