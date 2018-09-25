#!/usr/bin/env python

from plico.utils.decorator import override
from plico.utils.logger import Logger
from palpao_server.mirror_controller.abstract_deformable_mirror import \
    AbstractInstrument


__version__ = "$Id: alpao_deformable_mirror.py 27 2018-01-27 08:48:07Z lbusoni $"


class PhysikInstrumenteTipTiltMirror(AbstractInstrument):


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

