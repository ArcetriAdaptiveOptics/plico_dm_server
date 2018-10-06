#!/usr/bin/env python
import unittest
import numpy as np
from palpao_server.mirror_controller.simulated_deformable_mirror import \
    SimulatedDeformableMirror
from palpao.client.abstract_deformable_mirror_client import SnapshotEntry
from palpao.calibration.in_memory_calibration_manager import InMemoryCalibrationManager
from palpao_server.mirror_controller.deformable_mirror_controller \
    import DeformableMirrorController



class MyReplySocket():
    pass


class MyPublisherSocket():
    pass


class MyRpcHandler():

    def handleRequest(self, obj, socket, multi):
        pass


    def publishPickable(self, socket, obj):
        pass


class DeformableMirrorControllerTest(unittest.TestCase):

    def setUp(self):
        self._serverName= 'server description'
        self._ports= None
        self._dmSerialNumber= '0123456'
        self._mirror= SimulatedDeformableMirror(self._dmSerialNumber)
        self._rpcHandler= MyRpcHandler()
        self._replySocket= MyReplySocket()
        self._statusSocket= MyPublisherSocket()
        self._calMgr= InMemoryCalibrationManager()
        self._createDefaultFlat()
        self._ctrl= DeformableMirrorController(
            self._serverName,
            self._ports,
            self._mirror,
            self._replySocket,
            self._statusSocket,
            self._rpcHandler,
            self._calMgr,
            self._flatDmTag)


    def _createDefaultFlat(self):
        self._flatDmCommand= np.random.rand(
            self._mirror.getNumberOfActuators())
        self._flatDmTag='foo_foo_flatters'
        self._calMgr.saveZonalCommand(self._flatDmTag,
                                      self._flatDmCommand)


    def testGetSnapshot(self):
        snapshot= self._ctrl.getSnapshot('baar')
        serialNumberKey= 'baar.%s' % SnapshotEntry.SERIAL_NUMBER
        self.assertEqual(self._dmSerialNumber, snapshot[serialNumberKey])


    def testSetGetModalCommands(self):
        nModes= self._ctrl._getNumberOfModes()
        shapeCommands= np.arange(nModes) * 3.14
        self._ctrl.setShape(shapeCommands)
        actualShape= self._ctrl.getShape()
        self.assertTrue(np.allclose(shapeCommands, actualShape))


    def testStep(self):
        self._ctrl.step()


    def testSetFlatReferenceAtInit(self):
        wanted= self._flatDmCommand
        got= self._mirror.getZonalCommand()
        self.assertTrue(np.allclose(
            wanted, got), "%s %s" % (wanted, got))
        self.assertEqual(self._flatDmTag,
                         self._ctrl.getFlatTag())


    def testCommandsAreSummedToFlatShape(self):
        command= np.random.rand(self._ctrl._getNumberOfModes())
        self._ctrl.setShape(command)
        wanted= self._flatDmCommand + command
        got= self._mirror.getZonalCommand()
        self.assertTrue(np.allclose(
            wanted, got), "%s %s" % (wanted, got))


if __name__ == "__main__":
    unittest.main()
