#!/usr/bin/env python
import unittest
import numpy as np
from plico_dm_server.controller.simulated_deformable_mirror \
    import SimulatedDeformableMirror


class SimulatedDeformableMirrorTest(unittest.TestCase):

    def setUp(self):
        self._dm = SimulatedDeformableMirror('1123')

    def testNumberOfActuator(self):
        self.assertEqual(
            SimulatedDeformableMirror.NUMBER_OF_ACTUATORS,
            self._dm.getNumberOfActuators())

    def testBmcMultiDmActuatorCount(self):
        dm = SimulatedDeformableMirror(
            'BMC-SIM-140',
            nActuators=SimulatedDeformableMirror.BMC_MULTI_DM_ACTUATORS)
        self.assertEqual(140, dm.getNumberOfActuators())
        cmd = np.zeros(140)
        cmd[7] = 0.42
        dm.setZonalCommand(cmd)
        np.testing.assert_array_equal(cmd, dm.getZonalCommand())

    def testWrongShapeRaises(self):
        dm = SimulatedDeformableMirror('x', nActuators=140)
        with self.assertRaises(AssertionError):
            dm.setZonalCommand(np.zeros(36))


if __name__ == "__main__":
    unittest.main()
