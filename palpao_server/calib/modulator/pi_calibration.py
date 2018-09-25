from pi_gcs.tip_tilt_configuration import TipTiltConfiguration


__version__= "$Id: pi_calibration.py 189 2017-01-12 13:48:08Z pygo $"


class PhysikInstrumenteCalibration(object):

    def _createConfig(self, aLin, aOff, bLin, bOff):
        cfg= TipTiltConfiguration()
        cfg.positionToMilliRadAxisALinearCoeff= aLin
        cfg.positionToMilliRadAxisAOffsetCoeff= aOff
        cfg.positionToMilliRadAxisBLinearCoeff= bLin
        cfg.positionToMilliRadAxisBOffsetCoeff= bOff
        return cfg


    def getCalibrationFor(self, serialNumber):
        if serialNumber == 'ideal':
            return self._createConfig(0.5, -25., 0.5, -25.)
        if serialNumber == '110032051':
            return self._createConfig(0.87, -43.5, 0.87, -43.5)
        else:
            raise KeyError(
                "Calibration not available for device with serial number %s" %
                serialNumber)
