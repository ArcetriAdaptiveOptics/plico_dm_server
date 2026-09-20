#!/usr/bin/env python

from plico.utils.decorator import override
from plico.utils.logger import Logger
from plico_dm_server.controller.abstract_deformable_mirror import \
    AbstractDeformableMirror


class SimulatedDeformableMirror(AbstractDeformableMirror):
    """In-process DM sim. Default 36 acts; pass nActuators=140 for BMC Multi-DM."""

    NUMBER_OF_ACTUATORS = 36
    BMC_MULTI_DM_ACTUATORS = 140

    def __init__(self, serialNumber, nActuators=None):
        self._serialNumber = serialNumber
        self._nActuators = (
            self.NUMBER_OF_ACTUATORS if nActuators is None else int(nActuators))
        self._logger = Logger.of('Simulated Deformable Mirror')
        self._zonalCommand = None

    def isReady(self):
        return True

    @override
    def setZonalCommand(self, zonalCommand):
        assert zonalCommand.shape == (self._nActuators,), \
            "zonal command must be a vector of %d elements" % self._nActuators
        self._zonalCommand = zonalCommand

    @override
    def getZonalCommand(self):
        return self._zonalCommand

    @override
    def serialNumber(self):
        return self._serialNumber

    @override
    def getNumberOfActuators(self):
        return self._nActuators

    @override
    def deinitialize(self):
        pass
