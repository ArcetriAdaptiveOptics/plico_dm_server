import abc
from plico.utils.decorator import returns, returnsNone
from six import with_metaclass



class AbstractDeformableMirror(with_metaclass(abc.ABCMeta, object)):



    @abc.abstractmethod
    @returns(str)
    def serialNumber(self):
        assert False


    @abc.abstractmethod
    def getNumberOfActuators(self):
        """ Number of actuators of the deformable mirror

        Return the number of actuators of the deformable mirror.
        number of degrees of freedom.

        Return:
            numberOfActuators (int): the number of actuators of the deformable mirror.
        """
        assert False


    @abc.abstractmethod
    @returnsNone
    def setZonalCommand(self, command):
        """ Set deformable mirror command

        Set the DM shape

        Parameters:
            command (:obj:ndarray): an array containing the required value for the actuators
                The size of the array must be equal to the number of actuators of the DM


        """
        assert False


    @abc.abstractmethod
    @returnsNone
    def getZonalCommand(self):
        """ Get Deformable Mirror command

        return the current DM command

        Return:
            shape (:obj:ndarray): an array containing the measured value for the actuators
                The size of the array must be equal to the number of actuators of the DM

        The value are measured if the DM has an internal metrology on position
        The shape sequence is taken into account.
        """
        assert False


    @abc.abstractmethod
    @returnsNone
    def deinitialize(self):
        assert False
