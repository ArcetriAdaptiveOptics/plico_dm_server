import abc
from plico.utils.decorator import returns, returnsForExample
import numpy as np

__version__= "$Id: abstract_modulator.py 270 2017-04-27 16:38:09Z lbusoni $"


class AbstractModulator(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def name(self):
        assert False


    @abc.abstractmethod
    def setRadiusInMilliRad(self, radiusInMilliRad):
        assert False


    @abc.abstractmethod
    def setFrequencyInHz(self):
        assert False


    @abc.abstractmethod
    def setCenterInMilliRad(self, center):
        assert False


    @abc.abstractmethod
    @returns(float)
    def getRadiusInMilliRad(self):
        assert False


    @abc.abstractmethod
    @returns(float)
    def getFrequencyInHz(self):
        assert False


    @abc.abstractmethod
    @returnsForExample(np.array([-1.3, 2.3]))
    def getCenterInMilliRad(self):
        assert False


    @abc.abstractmethod
    @returnsForExample(np.zeros((9, 4000)))
    def getDiagnosticData(self):
        assert False
