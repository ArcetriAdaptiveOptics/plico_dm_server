#!/usr/bin/env python
import unittest
from palpao_server.mirror_controller.simulated_deformable_mirror \
    import SimulatedDeformableMirror



class SimulatedDeformableMirrorTest(unittest.TestCase):


    def setUp(self):
        serialNumber= '1123'
        self._dm= SimulatedDeformableMirror(serialNumber)


    def tearDown(self):
        pass


    def testNumberOfActuator(self):
        self.assertEqual(SimulatedDeformableMirror.NUMBER_OF_ACTUATORS,
                         self._dm.getNumberOfActuators())


if __name__ == "__main__":
    unittest.main()
