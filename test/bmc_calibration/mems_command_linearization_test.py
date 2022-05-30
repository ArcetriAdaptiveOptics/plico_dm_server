#!/usr/bin/env python
import unittest
from plico_dm_server.bmc_calibration.mems_command_linearization import MemsCommandLinearization
import numpy as np




class MemsCommandLinearizationTest(unittest.TestCase):

    def create_mcl(self):
        self._cmd_vector = np.array([np.linspace(0,1,10),
                        np.linspace(0.1, 1.1, 10)])
        self._actuator_list= np.array([2,3])
        self._deflection = self._cmd_vector ** 2 * 1e-6
        return MemsCommandLinearization(self._actuator_list,
                                        self._cmd_vector,
                                        self._deflection)

    def setUp(self):
        self.mcl = self.create_mcl()


    def tearDown(self):
        pass


    def test_actuator_list(self):
        np.testing.assert_allclose(self.mcl.actuators_list(),
                                   self._actuator_list)

    def test_p2c_without_interpolation(self):
        wanna_go_in = self._deflection[:, 3]
        got_cmd = self.mcl.p2c(wanna_go_in)
        wanted_cmd = self._cmd_vector[:,3]
        np.testing.assert_allclose(got_cmd,
                                   wanted_cmd)


    def test_c2p_without_interpolation(self):
        have_cmd = self._cmd_vector[:,3]
        corresponding_position = self._deflection[:, 3]
        computed_position = self.mcl.c2p(have_cmd)
        np.testing.assert_allclose(computed_position,
                                   corresponding_position)


    def test_p2c_with_interpolation(self):
        wanna_go_in = np.array([0.5e-6, 300e-9])
        got_cmd = self.mcl.p2c(wanna_go_in)
        wanted_cmd =np.sqrt(wanna_go_in * 1e6)
        np.testing.assert_allclose(got_cmd,
                                   wanted_cmd, rtol=0.001)

    def test_c2p_with_interpolation(self):
        have_cmd = self._cmd_vector[:,3]+0.2312
        corresponding_position = have_cmd**2 * 1e-6
        computed_position = self.mcl.c2p(have_cmd)
        np.testing.assert_allclose(computed_position,
                                   corresponding_position, rtol=0.001)


    def test_p2c_outside_valid_range(self):
        wanna_go_in = np.array([1e3, 1e-6])
        got_cmd = self.mcl.p2c(wanna_go_in)
        wanted_cmd = np.clip(np.sqrt(wanna_go_in * 1e6),
                             self._cmd_vector.min(axis=1),
                             self._cmd_vector.max(axis=1))
        np.testing.assert_allclose(got_cmd,
                                   wanted_cmd, rtol=0.001)

    def test_raises_if_vector_is_wrong_size(self):
        self.assertRaises(Exception, self.mcl.p2c, np.zeros(3))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()