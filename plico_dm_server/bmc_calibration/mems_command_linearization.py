import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import fsolve
from scipy.interpolate import interp1d
from astropy.io import fits
from numpy import dtype

class MemsCommandLinearization():
    '''
    A Class used to control MEMS actuators' stroke with a linearized law
    between the force and the voltage to be applied.
    
    Allows to apply the desired command to each actuator both terms of tensions
    (in au) or physical deflection (in meters).  
    Transition from tensions to positions, and vice versa, is provided
    by actuators' calibrations.
    Actuators' calibration curves are sampled over 10**4 points
    (voltage-deflection).
    
    ...
    Attributes
    ----------
    actuators_list : numpy.ndarray
        1D numpy array containing the list of the selected actuators.
        Actuators labels must be sorted in ascending order.
    cmd_vector : numpy.ndarray
        two-dimensional numpy array, containing the applied tensions to each
        actuator in the calibration phase. Its shape must be equal to
        (Nact, Nmeas), where Nact is the total number of the DM's actuator
        and Nmeas is the number o voltage/deflections applied/measured for
        each actuator.
        For instance, from the calibration of the MEMS Multi 5.5 DM,
        with 140 actuators, with 20 measured deflection for each actuators
        the expected shape of cmd_vector is (140, 20).
    deflection : numpy.ndarray 
        two-dimensional numpy array, containing the measured deflections for each
        actuator in the calibration phase. Its shape must be equal to
        (Nact, Nmeas), where Nact is the total number of the DM's actuator
        and Nmeas is the number o voltage/deflections applied/measured for
        each actuator.
        For instance, from the calibration of the MEMS Multi 5.5 DM,
        with 140 actuators, with 20 measured deflection for each actuators
        the expected shape of deflection is (140, 20)
    reference_shape_tag = None : str
        Tag name of the MEMS deformable mirror reference shape. Default is None
        
    Methods
    -------
    actuator_list()
        Returns the list of the selected actuators.
    p2c(position_vector)
       Returns the voltage (au) to be applied to measure a certain deflection
       (in meters), for each actuator.
    c2p(cmd_vector)
        Returns the deflection (in meters) corresponding to the input voltage
        command (au) for each actuator.
    get_actuators_clipping_status()
        Returns the actuation status of the last command applied to MEMS DM.
    reset_clipping_status()
        Resets the array relative to the actuation status of the actuators.
    save(fname)
        Saves the attributes into a fits file.
    load(fname)
        Initialize the Class, loading its attributes from a fits file. 
        
    '''

    def __init__(self,
                 actuators_list,
                 cmd_vector,
                 deflection,
                 reference_shape_tag=None):
        Nact = len(actuators_list)
        cmd_vector_shape = cmd_vector.shape
        deflection_shape = deflection.shape
        assert np.all(actuators_list[:-1] <= actuators_list[1:]), \
            "actuators_list must be sorted in ascending order! "
        assert Nact == cmd_vector_shape[0] and \
            Nact == deflection_shape[0] and \
            cmd_vector_shape[1] == deflection_shape[1], \
            "Conflicting array dimensions! \
            len(actuator_list) = Nact, got  %d \n \
            cmd_vector.shape = (Nact, Nmaes), got (%d, %d)\n \
            deflection.shape = (Nact, Nmaes), got (%d, %d) \n \
            "% (Nact, Nact, cmd_vector_shape[0], Nact, deflection_shape[0]) 
        assert np.all(cmd_vector[1,:-1] <= cmd_vector[1,1:]), \
            "voltage must be sorted in ascending order for a correct interpolation! "
        
        self._actuators_list = actuators_list
        self._cmd_vector = cmd_vector
        self._deflection = deflection
        self._reference_shape_tag = reference_shape_tag

        self._n_used_actuators = len(self._actuators_list)
        self._create_interpolation()
        self._create_calibration_curves()
        self._clipping_vector = None

    def actuators_list(self):
        '''
        Returns the list of the selected actuators.
        
        Returns
        -------
        actuator_list : numpy.ndarray
            1-D numpy array containing the labels of the selected actuators.
        '''
        return self._actuators_list

    def _create_interpolation(self):
        '''
        Generates the interpolation function through a cubic spline
        for each actuator.
        '''
        self._finter = [CubicSpline(self._cmd_vector[i], self._deflection[i], bc_type='natural')
                        for i in range(self._cmd_vector.shape[0])]

    def _create_calibration_curves(self):
        '''
        Generates the actuators' calibration curves over a sampling of
        10**4 points (voltage-deflection).    
        '''
        self._calibration_points = 10000
        self._calibrated_position = np.zeros(
            (self._n_used_actuators, self._calibration_points))
        self._calibrated_cmd = np.zeros_like(self._calibrated_position)
        for idx, act in enumerate(self._actuators_list):
            cmd_min = self._cmd_vector[idx, 0]
            cmd_max = self._cmd_vector[idx, -1]
            self._calibrated_cmd[idx] = np.linspace(
                cmd_min, cmd_max, self._calibration_points)
            self._calibrated_position[idx] = self._finter[idx](
                self._calibrated_cmd[idx])

    def _get_act_idx(self, act):
        return np.argwhere(self._actuators_list == act)[0][0]

    def p2c(self, position_vector):
        '''
        Returns the voltage (au) to be applied to measure a certain deflection
        (in meters), for each actuator.
        
        Allows to compute the voltage vector command (cmd_vector), in
        au, corresponding to actuators' deflections (position_vector), in meters.  
        Conversion from position to voltage command (and vice versa) is provided by the 
        calibration and linearization rutines, that relies on a Cubic spline
        interpolationof the measured deflection as a function of the applied
        voltage for each actuator.  
        Actuators' calibration curves are sampled over 10**4 points
        (voltage-deflection).
        If an element of the input array exceeds the calibration range values,
        the corresponding actuator is clipped to the maximum or minimum 
        deflection value and then converted to the corresponding voltage command.
        
        Parameters
        ----------
        position_vector : numpy.ndarray
          
            
        Returns
        -------
        cmd_vector : numpy.ndarray
            
        '''
        assert len(position_vector) == self._n_used_actuators, \
            "Position vector should have %d elements, got %d" % (
                self._n_used_actuators, len(position_vector))

        cmd_vector = np.zeros(self._n_used_actuators)
        for idx, act in enumerate(self._actuators_list):
            cmd_vector[idx] = self._linear_p2c(int(act), position_vector[idx])

        return cmd_vector

    def c2p(self, cmd_vector):
        '''
        Returns the deflection (in meters) corresponding to the input voltage
        command (au) for each actuator.
        
        Allows to compute the position vector command (position_vector), in
        meters, corresponding to actuators' voltage commands (cmd_vector), in au.  
        Conversion from position to voltage command (and vice versa) is provided
        by the calibration and linearization rutines, that relies on a Cubic
        spline interpolation of the measured deflection as a function of the
        applied voltage for each actuator.  
        Actuators' calibration curves are sampled over 10**4 points
        (voltage-deflection).
        If an element in the input array exceeds the calibration range values,
        the corresponding actuator is clipped to the maximum or minimum voltage
        value and then converted into the corresponding deflection.
        
        Parameters
        ----------
        cmd_vector : numpy.ndarray
            one dimensional numpy array containing the voltage command values
            of the selected actuators
        
        Returns
        -------
        position_vector : numpy.ndarray
            one dimensional numpy array containing the the actuators deflections
            relative to cmd_vector 
        '''
        assert len(cmd_vector) == self._n_used_actuators, \
            "Command vector should have %d elements, got %d" % (
                self._n_used_actuators, len(cmd_vector))
        if self._clipping_vector is None:
            self._clipping_vector = np.zeros(self._n_used_actuators, dtype = int)
        
        for act in self._actuators_list:
            idx = self._get_act_idx(act)
            cmd_span = self._calibrated_cmd[idx, :]
            max_cmd = cmd_span.max()
            min_cmd = cmd_span.min()
            if cmd_vector[idx] > max_cmd :
                self._clipping_vector[idx] = 1
                cmd_vector[idx] = max_cmd
            if cmd_vector[idx] < min_cmd : 
                self._clipping_vector[idx] = -1
                cmd_vector[idx] = min_cmd
            else:
                self._clipping_vector[idx] = 0
        
        position_vector = np.zeros(self._n_used_actuators)
        for idx, act in enumerate(self._actuators_list):
            fidx = self._get_act_idx(act)
            position_vector[idx] = self._finter[fidx](cmd_vector[idx])

        return position_vector
        
    # def _solve_p2c(self, act, p):
    #     '''
    #     returns required cmd for a given position/deflection
    #     implemented via scipy.optimize.fsolve
    #     slows routine?
    #     '''
    #     idx = self._get_act_idx(act)
    #
    #     def func(cmd): return np.abs(p - self._finter[idx](cmd))
    #     abs_difference = np.abs(p - self._finter[idx](self._cmd_vector[idx]))
    #     min_abs_difference = abs_difference.min()
    #     idx_guess = np.where(abs_difference == min_abs_difference)[0][0]
    #     guess = self._cmd_vector[idx, idx_guess]
    #
    #     cmd = fsolve(func, x0=guess)
    #     return cmd[0]

    def _linear_p2c(self, act, pos):
        '''
        For a given position (pos) and actuator (act), returns the voltage
        command as a linear interpolation between the two points of the 
        actuator's calibration curve closest to pos. The calibration curve is
        sampled over 10**4 points.
        
        Parameters
        -----------
        act : int
            Label of the actuator.
        pos : float
            Deflection in meters.
        Returns
        -------
        cmd : float
            Voltage command able to reproduce the deflection pos.
            Expressed in au.
        '''
        if self._clipping_vector is None:
            self._clipping_vector = np.zeros(self._n_used_actuators, dtype = int)
            
        idx = self._get_act_idx(act)
        cmd_span = self._calibrated_cmd[idx]
        pos_span = self._calibrated_position[idx]
        max_clipped_pos = np.max(pos_span)
        min_clipped_pos = np.min(pos_span)
        # avro una sensibilita dell ordine di 1.e-4 in tensione,ok
        if(pos > max_clipped_pos):
            self._clipping_vector[idx] = 1
            idx_clipped_cmd = np.where(max_clipped_pos == pos_span)[0][0]
            return cmd_span[idx_clipped_cmd]
        if(pos < min_clipped_pos):
            self._clipping_vector[idx] = -1
            idx_clipped_cmd = np.where(min_clipped_pos == pos_span)[0][0]
            return cmd_span[idx_clipped_cmd]
        else:
            self._clipping_vector[idx] = 0
            pos_a = pos_span[pos_span <= pos].max()
            pos_b = pos_span[pos_span >= pos].min()
            # nel caso di funz biunivoca, viene scelto un
            # punto corrispondente a pos, ma non so quale
            # ma la coppia di indici e corretta
            idx_cmd_a = np.where(pos_span == pos_a)[0][0]
            idx_cmd_b = np.where(pos_span == pos_b)[0][0]
            x = [pos_b, pos_a]
            y = [cmd_span[idx_cmd_b], cmd_span[idx_cmd_a]]
            f = interp1d(x, y)
            return float(f(pos))

    def _sampled_p2c(self, act, pos):
        '''
        For a given position (pos) and actuator (act), returns the voltage
        command able to reproduce the closest deflection requested, compared to 
        the ones in the actuator's calibration curve. The calibration curve is
        sampled over 10**4 points.
        
        Parameters
        -----------
        act : int
            Label of the actuator.
        pos : float
            Deflection in meters.
        Returns
        -------
        cmd : float
            Voltage command able to reproduce the deflection closest to pos.
            Expressed in au.
            
        '''
        if self._clipping_vector is None:
            self._clipping_vector = np.zeros(self._n_used_actuators, dtype = int)
            
        idx = self._get_act_idx(act)
        cmd_span = self._calibrated_cmd[idx]
        pos_span = self._calibrated_position[idx]
        max_clipped_pos = np.max(pos_span)
        min_clipped_pos = np.min(pos_span)
        if(pos > max_clipped_pos):
            self._clipping_vector[idx] = 1
            idx_clipped_cmd = np.where(max_clipped_pos == pos_span)[0][0]
            return cmd_span[idx_clipped_cmd]
        if(pos < min_clipped_pos):
            self._clipping_vector[idx] = -1
            idx_clipped_cmd = np.where(min_clipped_pos == pos_span)[0][0]
            return cmd_span[idx_clipped_cmd]
        else:
            self._clipping_vector[idx] = 0
            pos_a = pos_span[pos_span <= pos].max()
            pos_b = pos_span[pos_span >= pos].min()
            if(abs(pos - pos_a) > abs(pos - pos_b)):
                pos_c = pos_b
            else:
                pos_c = pos_a
            idx_cmd = np.where(pos_span == pos_c)[0][0]
            return cmd_span[idx_cmd]

    def save(self, fname, overwrite=False):
        '''
        Saves the attributes into a fits file.
        
        Saves the actuators' list, vector of voltages and deflections and
        the name Tag of the reference shape of MEMS DM. 
        
        Parameters
        ----------
        fname : str
            path/file name of the fits file
        '''
        hdr = fits.Header()
        hdr['REF_TAG'] = self._reference_shape_tag
        fits.writeto(fname, self._actuators_list, hdr, overwrite=overwrite)
        fits.append(fname, self._cmd_vector)
        fits.append(fname, self._deflection)

    def get_actuators_clipping_status(self):
        '''
        Returns the actuation status of the last command applied to MEMS DM
        in a one dimensional numpy array with integer elements:
        +1 if the actuator reaches the maximum voltage or deflection command
         0 if the actuator doesn't clip
        -1 if the actuator reaches the minimum voltage or deflection command
        Note: the index of the returned array is the label of the corresponding
        actuator!
        
        Returns
        -------
        clipping_vector : numpy.ndarray or None
            one dimensional array with integer entries relative to each actuator
            clipping status (1, 0 or -1). If no commands have been applied yet
            returns None
        '''
        # if self._clipping_vector is None:
        #     self._clipping_vector = np.zeros(self._n_used_actuators, dtype = int)    
        return self._clipping_vector
    
    def reset_clipping_status(self):
        '''
        Resets the one dimensional array relative to the actuation status
        of the actuators.
        '''
        self._clipping_vector = None
    
    @staticmethod
    def load(fname):
        '''
        Initialize the Class, loading its attributes from a fits file.
        
        Its a static method, allowing to construct the class reading
        the actuators' list, vector of voltages and deflections and
        the name Tag of the reference shape from a fits file.  
        
        Parameters
        ----------
        fname : str
            path/file name of the fits file
        '''
        #header = fits.getheader(fname, 0)
        
        # with fits.open(fname) as hduList:
        #     actuators_list = hduList[0].data
        #     cmd_vector = hduList[1].data
        #     deflection = hduList[2].data
        #reference_shape_tag = header['REF_TAG']
        with fits.open(fname):
            reference_shape_tag = fits.getval(fname, 'REF_TAG')
            actuators_list = fits.getdata(fname, 0)
            cmd_vector = fits.getdata(fname, 1)
            deflection = fits.getdata(fname, 2)
        
        return MemsCommandLinearization(
            actuators_list, cmd_vector, deflection, reference_shape_tag)