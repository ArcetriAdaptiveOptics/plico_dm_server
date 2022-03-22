from plico_dm_server.controller.abstract_deformable_mirror import \
    AbstractDeformableMirror
from plico.utils.decorator import override


class MeadowlarkSlm(AbstractDeformableMirror):

    def __init__(self, meadolark_class_python, identificativo_forse):
        self._slm = meadolark_class_python

    @override
    def setZonalCommand(self, zonalCommand):
        self._slm.fai()
        pass

    @override
    def getZonalCommand(self):
        pass

    @override
    def serialNumber(self):
        pass

    @override
    def getNumberOfActuators(self):
        return 12345678

    @override
    def deinitialize(self):
        pass
