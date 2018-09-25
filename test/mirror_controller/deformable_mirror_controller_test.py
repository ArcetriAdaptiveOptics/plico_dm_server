#!/usr/bin/env python
import unittest
import numpy as np
from palpao_server.mirror_controller.simulated_deformable_mirror import \
    SimulatedDeformableMirror
from palpao.client.abstract_deformable_mirror_client import SnapshotEntry
from palpao_server.mirror_controller.deformable_mirror_controller \
    import DeformableMirrorController

__version__ = "$Id: deformable_mirror_controller_test.py 26 2018-01-26 19:06:25Z lbusoni $"


class MyReplySocket():
    pass


class MyPublisherSocket():
    pass


class MyRpcHandler():

    def handleRequest(self, obj, socket, multi):
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
        self._ctrl= DeformableMirrorController(
            self._serverName,
            self._ports,
            self._mirror,
            self._replySocket,
            self._statusSocket,
            self._rpcHandler)


    def testGetSnapshot(self):
        snapshot= self._ctrl.getSnapshot('baar')
        serialNumberKey= 'baar.%s' % SnapshotEntry.SERIAL_NUMBER
        self.assertEqual(self._dmSerialNumber, snapshot[serialNumberKey])


    def testSetGetZonalCommands(self):
        actuatorCommands= np.arange(12) * 3.14
        self._ctrl.setZonalCommand(actuatorCommands)
        zonalCommands= self._ctrl.getZonalCommand()
        self.assertTrue(np.allclose(actuatorCommands, zonalCommands))


if __name__ == "__main__":
    unittest.main()
