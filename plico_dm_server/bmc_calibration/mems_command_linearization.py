import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import fsolve
from scipy.interpolate import interp1d
from astropy.io import fits

class MemsCommandLinearization():

    def __init__(self,
                 actuators_list,
                 cmd_vector,
                 deflection,
                 reference_shape_tag=None):
        self._actuators_list = actuators_list
        self._cmd_vector = cmd_vector
        self._deflection = deflection
        self._reference_shape_tag = reference_shape_tag

        self._n_used_actuators = len(self._actuators_list)
        self._create_interpolation()
        self._create_calibration_curves()

    # def _create_interpolation(self):
    #     # WARNING: interp 1d suppone che l argomento sia un array
    #     # di valori monotonicamente crescenti(o comunque li riordina) e
    #     # le deflessioni non lo sono, per questo motivo in
    #     # plot_interpolated_functions osservo delle forti oscillazioni
    #     self._finter = [interp1d(
    #         self._deflection[i], self._cmd_vector[i], kind='cubic')
    #         for i in range(self._cmd_vector.shape[0])]
    # prova

    def actuators_list(self):
        return self._actuators_list

    def _create_interpolation(self):
        self._finter = [CubicSpline(self._cmd_vector[i], self._deflection[i], bc_type='natural')
                        for i in range(self._cmd_vector.shape[0])]

    def _create_calibration_curves(self):
        '''
        Generates actuator deflections and cmds spans
        from the interpolated functions
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
        assert len(position_vector) == self._n_used_actuators, \
            "Position vector should have %d elements, got %d" % (
                self._n_used_actuators, len(position_vector))

        cmd_vector = np.zeros(self._n_used_actuators)
        for idx, act in enumerate(self._actuators_list):
            cmd_vector[idx] = self._linear_p2c(int(act), position_vector[idx])

        return cmd_vector

    def c2p(self, cmd_vector):
        assert len(cmd_vector) == self._n_used_actuators, \
            "Command vector should have %d elements, got %d" % (
                self._n_used_actuators, len(cmd_vector))

        position_vector = np.zeros(self._n_used_actuators)
        for idx, act in enumerate(self._actuators_list):
            fidx = self._get_act_idx(act)
            position_vector[idx] = self._finter[fidx](cmd_vector[idx])

        return position_vector
        

    def _solve_p2c(self, act, p):
        '''
        returns required cmd for a given position/deflection
        implemented via scipy.optimize.fsolve
        slows routine?
        '''
        idx = self._get_act_idx(act)

        def func(cmd): return np.abs(p - self._finter[idx](cmd))
        abs_difference = np.abs(p - self._finter[idx](self._cmd_vector[idx]))
        min_abs_difference = abs_difference.min()
        idx_guess = np.where(abs_difference == min_abs_difference)[0][0]
        guess = self._cmd_vector[idx, idx_guess]

        cmd = fsolve(func, x0=guess)
        return cmd[0]

    def _linear_p2c(self, act, pos):
        '''
        returns required cmd for a given position/deflection
        implemented via linear interpolation between 2 points
        close to pos and returns the required cmd
        should be faster then solve_p2c
        '''
        idx = self._get_act_idx(act)
        cmd_span = self._calibrated_cmd[idx]
        pos_span = self._calibrated_position[idx]
        max_clipped_pos = np.max(pos_span)
        min_clipped_pos = np.min(pos_span)
        # avro una sensibilita dell ordine di 1.e-4 in tensione,ok
        if(pos > max_clipped_pos):
            idx_clipped_cmd = np.where(max_clipped_pos == pos_span)[0][0]
            return cmd_span[idx_clipped_cmd]
        if(pos < min_clipped_pos):
            idx_clipped_cmd = np.where(min_clipped_pos == pos_span)[0][0]
            return cmd_span[idx_clipped_cmd]
        else:
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
        for a given pos, returns the cmd relative to the closest
        stroke to pos
        '''
        idx = self._get_act_idx(act)
        cmd_span = self._calibrated_cmd[idx]
        pos_span = self._calibrated_position[idx]
        max_clipped_pos = np.max(pos_span)
        min_clipped_pos = np.min(pos_span)
        if(pos > max_clipped_pos):
            idx_clipped_cmd = np.where(max_clipped_pos == pos_span)[0][0]
            return cmd_span[idx_clipped_cmd]
        if(pos < min_clipped_pos):
            idx_clipped_cmd = np.where(min_clipped_pos == pos_span)[0][0]
            return cmd_span[idx_clipped_cmd]
        else:
            pos_a = pos_span[pos_span <= pos].max()
            pos_b = pos_span[pos_span >= pos].min()
            if(abs(pos - pos_a) > abs(pos - pos_b)):
                pos_c = pos_b
            else:
                pos_c = pos_a
            idx_cmd = np.where(pos_span == pos_c)[0][0]
            return cmd_span[idx_cmd]

    def save(self, fname):
        hdr = fits.Header()
        hdr['REF_TAG'] = self._reference_shape_tag
        fits.writeto(fname, self._actuators_list, hdr)
        fits.append(fname, self._cmd_vector)
        fits.append(fname, self._deflection)

    @staticmethod
    def load(fname):
        header = fits.getheader(fname)
        hduList = fits.open(fname)
        actuators_list = hduList[0].data
        cmd_vector = hduList[1].data
        deflection = hduList[2].data
        reference_shape_tag = header['REF_TAG']
        return MemsCommandLinearization(
            actuators_list, cmd_vector, deflection, reference_shape_tag)
