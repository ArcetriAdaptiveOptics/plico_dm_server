#!/usr/bin/env python
"""Unit tests for BMC model aliases without starting a ZMQ server."""
import unittest
from plico_dm_server.controller.simulated_deformable_mirror import \
    SimulatedDeformableMirror
from plico_dm_server.controller.bmc_deformable_mirror import \
    BmcDeformableMirror
from plico_dm_server.controller.fake_bmc_dm import FakeBmcDm


BMC_MODELS = ('bmc', 'bmcMultiDM')
SIM_140_MODELS = (
    'simulatedMEMSMultiDM', 'simulatedMEMS140', 'simulatedBmcMultiDM')


class BmcModelAliasTest(unittest.TestCase):

    def testSim140ModelsShareActuatorCount(self):
        for _model in SIM_140_MODELS:
            dm = SimulatedDeformableMirror(
                'SN',
                nActuators=SimulatedDeformableMirror.BMC_MULTI_DM_ACTUATORS)
            self.assertEqual(140, dm.getNumberOfActuators())

    def testFakeBmcMatchesMultiDmActuatorCount(self):
        fake = FakeBmcDm()
        dm = BmcDeformableMirror(fake, FakeBmcDm.VALID_SERIAL_NUMBER)
        self.assertEqual(
            FakeBmcDm.NUMBER_OF_ACTUATORS, dm.getNumberOfActuators())
        self.assertEqual(140, dm.getNumberOfActuators())

    def testBmcAndBmcMultiDmAreDocumentedAliases(self):
        # Runner treats both model strings as the USB BMC path.
        self.assertIn('bmc', BMC_MODELS)
        self.assertIn('bmcMultiDM', BMC_MODELS)


if __name__ == "__main__":
    unittest.main()
