#!/usr/bin/env python
import unittest
from plico_dm_server.bmc_calibration.mems_command_linearization import MemsCommandLinearization
import numpy as np
from tempfile import gettempdir
import os 
from astropy.io import fits




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

    def test_raises_if_actuators_list_is_bad_sorted(self):
        self.assertRaises(Exception, MemsCommandLinearization, 
                         np.array([3,2]),
                         self.mcl._cmd_vector,
                         self.mcl._deflection)
        
    def test_raises_if_cmd_vector_is_bad_sorted(self):
        self.assertRaises(Exception, MemsCommandLinearization,
                          self.mcl._actuators_list,
                          np.array([[0, 1],[4, 1]]),
                          self.mcl._deflection)
        
    def test_raises_if_mcl_attributes_have_wrong_dimensions(self):
        # same number of actuators and wrong number of pos/voltage cmds
        self.assertRaises(Exception, MemsCommandLinearization,
                          np.array([1, 2]),
                          np.array([[0, 1, 3], [4, 1, 9]]),
                          np.array([[1, 2], [3 ,4]]))
        # same number of pos/voltage cmds and wrong number of actuators
        self.assertRaises(Exception, MemsCommandLinearization,
                          np.array([1]),
                          np.array([[0, 1],[4, 1]]),
                          np.array([[1, 2], [3, 4]]))
        # all wrong
        self.assertRaises(Exception, MemsCommandLinearization,
                          np.array([1]),
                          np.array([[0, 1, 3], [4, 1, 3], [1, 1, 1]]),
                          np.array([[1, 2], [3, 4]]))
        
        
    def test_actuator_list(self):
        np.testing.assert_allclose(self.mcl.actuators_list(),
                                   self._actuator_list)
    
    def test_volatage_deflection_law(self):
        self.assertTrue(np.allclose(
            self.mcl._calibrated_position,
            self.mcl._calibrated_cmd**2 *1e-6,
            rtol = 0.001))
        
        for act in np.arange(len(self.mcl._actuators_list)):
            coeff = np.polyfit(self.mcl._calibrated_cmd[act,:],
                               self.mcl._calibrated_position[act,:],
                               2)
            fit_positions = coeff[0]*self.mcl._calibrated_cmd[act,:]**2 + \
                coeff[1]*self.mcl._calibrated_cmd[act,:] + coeff[2]
            self.assertTrue(np.allclose(fit_positions,
                                        self.mcl._calibrated_position[act,:],
                                        rtol = 1e-3))

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
    
    def test_load_from_file(self):
        
        act_list2save = np.array([1.,2.])
        cmd2save = np.array([[1.,2.],[3.,4.]])
        pos2save = np.array([[5.,6.],[7.,8.]])
        ref2save ='PIPPO'
        hdr = fits.Header()
        hdr['REF_TAG'] = ref2save
        
        fname = os.path.join(gettempdir(),'pippo.fits')
        fits.writeto(fname, act_list2save, hdr, overwrite=True)
        fits.append(fname, cmd2save)
        fits.append(fname, pos2save)    
        
        loaded_mcl = MemsCommandLinearization.load(fname)
        
        self.assertTrue(np.allclose(act_list2save, loaded_mcl.actuators_list()))
        self.assertTrue(np.allclose(cmd2save, loaded_mcl._cmd_vector))
        self.assertTrue(np.allclose(pos2save, loaded_mcl._deflection))
        self.assertTrue(ref2save, loaded_mcl._reference_shape_tag)
        
        del loaded_mcl
        
        os.remove(fname)
    
    def test_save_and_load(self):
        fname  = os.path.join(gettempdir(), 'pippo2.fits')
        self.mcl._reference_shape_tag = 'PIPPO'
        self.mcl.save(fname, overwrite = True)
        
        loaded_mcl = MemsCommandLinearization.load(fname)
        
        self.assertTrue(np.allclose(self.mcl._actuators_list, loaded_mcl._actuators_list))
        self.assertTrue(np.allclose(self.mcl._cmd_vector, loaded_mcl._cmd_vector))
        self.assertTrue(np.allclose(self.mcl._deflection, loaded_mcl._deflection))
        self.assertTrue(self.mcl._reference_shape_tag, loaded_mcl._reference_shape_tag)
        
        del loaded_mcl
        
        os.remove(fname)
        
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()