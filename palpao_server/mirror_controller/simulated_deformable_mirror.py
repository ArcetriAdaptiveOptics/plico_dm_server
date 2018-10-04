#!/usr/bin/env python

from plico.utils.decorator import override
from plico.utils.logger import Logger
from palpao_server.mirror_controller.abstract_deformable_mirror import \
    AbstractDeformableMirror


class SimulatedDeformableMirror(AbstractDeformableMirror):

    NUMBER_OF_ACTUATORS= 36

    def __init__(self, serialNumber):
        self._serialNumber= serialNumber
        self._logger= Logger.of('Simulated Deformable Mirror')
        self._zonalCommand= None


    @override
    def setZonalCommand(self, zonalCommand):
        assert zonalCommand.shape == (self.NUMBER_OF_ACTUATORS,), \
            "zonal command must be a vector of %d elements" % \
            self.NUMBER_OF_ACTUATORS
        self._zonalCommand= zonalCommand


    @override
    def getZonalCommand(self):
        return self._zonalCommand


    @override
    def serialNumber(self):
        return self._serialNumber


    @override
    def getNumberOfActuators(self):
        return self.NUMBER_OF_ACTUATORS


    @override
    def deinitialize(self):
        pass
