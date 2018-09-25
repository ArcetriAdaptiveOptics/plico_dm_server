import abc
import numpy
from plico.utils.decorator import returns
from six import with_metaclass


__version__= "$Id: abstract_deformable_mirror.py 27 2018-01-27 08:48:07Z lbusoni $"


class AbstractDeformableMirror(with_metaclass(abc.ABCMeta, object)):

    @abc.abstractmethod
    def setZonalCommand(self):
        assert False


    @abc.abstractmethod
    @returns(numpy.ndarray)
    def getZonalCommand(self):
        assert False


    @abc.abstractmethod
    @returns(str)
    def serialNumber(self):
        assert False
