#!/usr/bin/env python

from plico.utils.decorator import override
from plico.utils.logger import Logger
from palpao_server.mirror_controller.abstract_deformable_mirror import \
    AbstractDeformableMirror


class AlpaoError(Exception):
    """Exception raised for ALPAO error.

    Attributes:
        errorCode -- BMC error code
        message -- explanation of the error
    """

    def __init__(self, errorCode, message):
        self.errorCode = errorCode
        self.message = message



class AlpaoDeformableMirror(AbstractDeformableMirror):


    def __init__(self, dm, serialNumber):
        self._dm= dm
        self._serialNumber= serialNumber
        self._logger= Logger.of('ALPAO Deformable Mirror')
        self._dm.Reset()


    @override
    def setZonalCommand(self, zonalCommand):
        self._dm.Send(zonalCommand)
        self._lastZonalCommand= zonalCommand


    @override
    def getZonalCommand(self):
        return self._lastZonalCommand


    @override
    def serialNumber(self):
        return self._serialNumber


    def getVersion(self):
        return int(self._dm.Get('VersionInfo'))


    @override
    def getNumberOfActuators(self):
        return int(self._dm.Get('NbOfActuator'))


    @override
    def deinitialize(self):
        self._dm.Stop()
        self._dm.Reset()

