#!/usr/bin/env python

from plico.utils.decorator import override
from plico.utils.logger import Logger
from palpao_server.mirror_controller.abstract_deformable_mirror import \
    AbstractDeformableMirror


__version__ = "$Id: alpao_deformable_mirror.py 27 2018-01-27 08:48:07Z lbusoni $"


class AlpaoDeformableMirror(AbstractDeformableMirror):


    def __init__(self):
        self._logger= Logger.of('ALPAO Deformable Mirror')


    @override
    def setZonalCommand(self, zonalCommand):
        assert False, 'Implement me'


    @override
    def getZonalCommand(self):
        assert False, 'Implement me'


    @override
    def serialNumber(self):
        assert False, 'Implement me'
