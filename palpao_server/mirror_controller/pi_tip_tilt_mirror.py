from plico.utils.decorator import override
from plico.utils.logger import Logger
from palpao_server.mirror_controller.abstract_deformable_mirror import \
    AbstractDeformableMirror


class PhysikInstrumenteTipTiltMirror(AbstractDeformableMirror):


    def __init__(self, serialNumber, tipTiltMirror):
        self._logger= Logger.of('PI TT Mirror')
        self._serialNumber= serialNumber
        self._tt= tipTiltMirror
        self._tt.stopModulation()
        self._tt.disableControlLoop()


    @override
    def setZonalCommand(self, zonalCommand):
        self._tt.setOpenLoopValue(zonalCommand)


    @override
    def getZonalCommand(self):
        return self._tt.getOpenLoopValue()


    @override
    def serialNumber(self):
        return self._serialNumber


    @override
    def deinitialize(self):
        pass


    @override
    def getNumberOfActuators(self):
        return 2
