#!/usr/bin/env python
import unittest
import numpy as np
from plico_dm_server.controller.simulated_deformable_mirror import \
    SimulatedDeformableMirror
from plico_dm.client.abstract_deformable_mirror_client import SnapshotEntry
from plico_dm.calibration.in_memory_calibration_manager import \
    InMemoryCalibrationManager
from plico_dm_server.controller.deformable_mirror_controller \
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
        self._serverName = 'server description'
        self._ports = None
        self._dmSerialNumber = '0123456'
        self._mirror = SimulatedDeformableMirror(self._dmSerialNumber)
        self._rpcHandler = MyRpcHandler()
        self._replySocket = MyReplySocket()
        self._statusSocket = MyPublisherSocket()
        self._calMgr = InMemoryCalibrationManager()
        self._createDefaultFlat()
        self._ctrl = DeformableMirrorController(
            self._serverName,
            self._ports,
            self._mirror,
            self._replySocket,
            self._statusSocket,
            self._rpcHandler,
            self._calMgr,
            self._flatDmTag)

    def _createDefaultFlat(self):
        self._flatDmCommand = np.random.rand(
            self._mirror.getNumberOfActuators())
        self._flatDmTag = 'foo_foo_flatters'
        self._calMgr.saveZonalCommand(self._flatDmTag,
                                      self._flatDmCommand)

    def testGetSnapshot(self):
        snapshot = self._ctrl.getSnapshot('baar')
        serialNumberKey = 'baar.%s' % SnapshotEntry.SERIAL_NUMBER
        self.assertEqual(self._dmSerialNumber, snapshot[serialNumberKey])

    def testGetSnapshotWithNoFlat(self):
        # Overwrite flat temporarily
        self._ctrl.load_reference(None)
        snapshot = self._ctrl.getSnapshot('baar')
        refCmdTagKey = 'baar.%s' % SnapshotEntry.REFERENCE_COMMAND_TAG
        self.assertEqual('None', snapshot[refCmdTagKey])
        # Restore previous flat
        self._ctrl.load_reference('foo_foo_flatters')

    def testSetGetModalCommands(self):
        nModes = self._ctrl._getNumberOfModes()
        shapeCommands = np.arange(nModes) * 3.14
        self._ctrl.setShape(shapeCommands)
        actualShape = self._ctrl.getShape()
        self.assertTrue(np.allclose(shapeCommands, actualShape))

    def testStep(self):
        self._ctrl.step()

    def testSetFlatReferenceAtInit(self):
        wanted = self._flatDmCommand
        got = self._mirror.getZonalCommand()
        self.assertTrue(np.allclose(
            wanted, got), "%s %s" % (wanted, got))
        self.assertEqual(self._flatDmTag,
                         self._ctrl.getFlatTag())

    def testCommandsAreSummedToFlatShape(self):
        command = np.random.rand(self._ctrl._getNumberOfModes())
        self._ctrl.setShape(command)
        wanted = self._flatDmCommand + command
        got = self._mirror.getZonalCommand()
        self.assertTrue(np.allclose(
            wanted, got), "%s %s" % (wanted, got))

    def testGetReferenceShape(self):
        ref_shape = self._ctrl.get_reference_shape()
        np.testing.assert_allclose(ref_shape, self._flatDmCommand)

    def testSaveCurrentShapeAsReference(self):
        nModes = self._ctrl._getNumberOfModes()
        shapeCommands = np.arange(nModes) * 2

        current_reference = self._ctrl.get_reference_shape()
        self._ctrl.setShape(shapeCommands)
        self._ctrl.save_current_shape_as_reference('foofoo')
        self._ctrl.load_reference('foofoo')

        np.testing.assert_allclose(
            shapeCommands + current_reference,
            self._ctrl.get_reference_shape())

    def test_load_reference_with_tag(self):
        flat = np.random.rand(self._mirror.getNumberOfActuators())
        self._calMgr.saveZonalCommand('flat', flat)
        self._ctrl.load_reference('flat')
        np.testing.assert_allclose(flat, self._ctrl._flatCmd)

    def test_load_reference_with_none(self):
        zero = np.zeros(self._mirror.getNumberOfActuators())
        self._ctrl.load_reference(None)
        np.testing.assert_allclose(zero, self._ctrl._flatCmd)

if __name__ == "__main__":
    unittest.main()
