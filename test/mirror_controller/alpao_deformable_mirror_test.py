#!/usr/bin/env python
import unittest
import numpy as np
from palpao_server.mirror_controller.alpao_deformable_mirror import \
    AlpaoDeformableMirror
from palpao_server.mirror_controller.fake_alpao_dm import FakeAlpaoDm


class BmcDeformableMirrorTest(unittest.TestCase):


    def setUp(self):
        self._serialNumber= FakeAlpaoDm.VALID_SERIAL_NUMBER
        self._alpaoDm= FakeAlpaoDm(self._serialNumber)
        self._dm= AlpaoDeformableMirror(self._alpaoDm,
                                        self._serialNumber)


    def tearDown(self):
        self._dm.deinitialize()


    def testGetNumberOfActuators(self):
        self.assertEqual(
            self._alpaoDm.NUMBER_OF_ACTUATORS,
            self._dm.getNumberOfActuators())


    def testSetZonalCommandWithWrongSizeRaises(self):
        wrongNumberOfActuators= self._dm.getNumberOfActuators() + 2
        zonalCommand= np.zeros(wrongNumberOfActuators)
        self.assertRaises(
            Exception,
            self._dm.setZonalCommand, zonalCommand)


    def testSetAndGetZonalCommand(self):
        zonalCommand= np.arange(self._dm.getNumberOfActuators())
        self._dm.setZonalCommand(zonalCommand)
        actualCommand= self._dm.getZonalCommand()
        self.assertTrue(np.allclose(actualCommand, zonalCommand))


if __name__ == "__main__":
    unittest.main()
