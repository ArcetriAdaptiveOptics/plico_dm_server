#!/usr/bin/env python
import unittest
import numpy as np
from palpao_server.mirror_controller.bmc_deformable_mirror import \
    BmcDeformableMirror, BmcError
from palpao_server.mirror_controller.fake_bmc_dm import FakeBmcDm



class BmcDeformableMirrorTest(unittest.TestCase):


    def setUp(self):
        self._serialNumber= FakeBmcDm.VALID_SERIAL_NUMBER
        self._bmcDm= FakeBmcDm()
        self._dm= BmcDeformableMirror(self._bmcDm,
                                      self._serialNumber)


    def tearDown(self):
        self._dm.deinitialize()


    def testCreateWithInvalidSerialNumberRaises(self):
        invalidSerial= 'asdasdf'
        self.assertRaises(
            BmcError, BmcDeformableMirror, self._bmcDm, invalidSerial)


    def testGetNumberOfActuators(self):
        self.assertEqual(
            self._bmcDm.NUMBER_OF_ACTUATORS,
            self._dm.getNumberOfActuators())


    def testSetZonalCommandWithWrongSizeRaises(self):
        wrongNumberOfActuators= self._dm.getNumberOfActuators() + 2
        zonalCommand= np.zeros(wrongNumberOfActuators)
        self.assertRaises(
            BmcError,
            self._dm.setZonalCommand, zonalCommand)


    def testSetAndGetZonalCommand(self):
        zonalCommand= np.arange(self._dm.getNumberOfActuators())
        self._dm.setZonalCommand(zonalCommand)
        actualCommand= self._dm.getZonalCommand()
        self.assertTrue(np.allclose(actualCommand, zonalCommand))


if __name__ == "__main__":
    unittest.main()
