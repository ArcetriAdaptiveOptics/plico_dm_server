#!/usr/bin/env python
import unittest
import numpy as np
from palpao_server.mirror_controller.pi_tip_tilt_mirror import \
    PhysikInstrumenteTipTiltMirror
from pi_gcs.fake_tip_tilt_2_axis import FakeTipTilt2Axis


class MyTipTilt2Axis(FakeTipTilt2Axis):
    pass


class PhysikInstrumenteTipTiltMirrorTest(unittest.TestCase):


    def setUp(self):
        self._serialNumber= '123123'
        self._tt= MyTipTilt2Axis()
        self._dm= PhysikInstrumenteTipTiltMirror(
            self._serialNumber,
            self._tt)


    def tearDown(self):
        self._dm.deinitialize()


    def testModulationIsStoppedAndControLoopIsDisabled(self):
        self.assertFalse(self._tt.isModulationEnabled())
        self.assertFalse(self._tt.isControlLoopEnabled())


    def testGetNumberOfActuators(self):
        self.assertEqual(2, self._dm.getNumberOfActuators())


    def testSetZonalCommand(self):
        zonalCommand= np.array([1, 2])
        self._dm.setZonalCommand(zonalCommand)
        self.assertTrue(np.allclose(
            zonalCommand,
            self._tt.getOpenLoopValue()))


if __name__ == "__main__":
    unittest.main()
