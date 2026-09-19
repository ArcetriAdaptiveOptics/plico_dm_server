#!/usr/bin/env python
import unittest
import numpy as np
from plico.rpc.dummy_remote_procedure_call import DummyRpcHandler
from plico.rpc.zmq_ports import ZmqPorts
from plico_dm_server.controller.simulated_modulator import SimulatedModulator
from plico_dm_server.controller.modulator_controller import ModulatorController
from plico_dm.client.abstract_modulator_client import SnapshotEntry


class RecordingRpc(DummyRpcHandler):

    def __init__(self):
        self.published = []

    def handleRequest(self, obj, socket, multi=True):
        pass

    def publishPickable(self, socket, obj):
        self.published.append(obj)


class SimulatedModulatorTest(unittest.TestCase):

    def setUp(self):
        self.mod = SimulatedModulator('sim-unit')

    def testSetGet(self):
        self.mod.setRadiusInMilliRad(3.0)
        self.mod.setFrequencyInHz(25.0)
        self.mod.setCenterInMilliRad(np.array([0.2, -0.1]))
        self.assertEqual(3.0, self.mod.getRadiusInMilliRad())
        self.assertEqual(25.0, self.mod.getFrequencyInHz())
        np.testing.assert_array_almost_equal(
            np.array([0.2, -0.1]), self.mod.getCenterInMilliRad())
        diagn = self.mod.getDiagnosticData()
        self.assertEqual((9, 4000), diagn.shape)


class ModulatorControllerTest(unittest.TestCase):

    def setUp(self):
        self.mod = SimulatedModulator('ctrl-unit')
        self.rpc = RecordingRpc()
        ports = ZmqPorts('localhost', 18000)
        self.controller = ModulatorController(
            'test-modulator',
            ports,
            self.mod,
            replySocket=None,
            statusSocket=None,
            rpcHandler=self.rpc)

    def testRpcSurface(self):
        self.controller.setModulatorRadiusInMilliRad(1.7)
        self.controller.setModulatorFrequencyInHz(33.0)
        self.controller.setModulatorCenterInMilliRad(np.array([0.0, 0.5]))
        self.controller.offsetModulatorCenterByMilliRad(np.array([0.1, 0.0]))
        self.controller.step()
        status = self.rpc.published[-1]
        self.assertEqual(1.7, status.modulatorRadiusInMilliRad)
        self.assertEqual(33.0, status.modulatorFrequencyInHz)
        np.testing.assert_array_almost_equal(
            np.array([0.1, 0.5]), status.modulatorCenterInMilliRad)
        snap = self.controller.getSnapshot('m')
        self.assertEqual(
            33.0, snap['m.%s' % SnapshotEntry.MODULATOR_FREQUENCY])
        diagn = self.controller.getModulatorDiagnosticData()
        self.assertEqual((9, 4000), diagn.shape)


if __name__ == '__main__':
    unittest.main()
