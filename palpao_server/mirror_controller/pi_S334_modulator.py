import numpy as np
from plico.utils.logger import Logger
from plico.utils.decorator import override
import scipy.signal.signaltools
from palpao_server.mirror_controller.abstract_modulator import \
    AbstractModulator

__version__= "$Id: pi_S334_modulator.py 278 2017-06-12 06:06:05Z pygo $"


class PIS334Modulator(AbstractModulator):

    ADAPTIVE_MODULATION_NONE= 'None'
    ADAPTIVE_MODULATION_ELLIPSE= 'Ellipse'
    ADAPTIVE_MODULATION_FREEFORM= 'Freeform'

    def __init__(self, name, tipTiltMirror):
        AbstractModulator.__init__(self)
        self._name= name
        self._tt= tipTiltMirror

        self._radiusInMilliRad= 1.
        self._frequencyInHz= 20.
        self._centerInMilliRad= np.array([0, 0.])

        self._logger= Logger.of("PI S334 Modulator")
        self._logger.notice('Initialized')

        self._currentRadii= np.zeros(2)
        self._currentCenter= np.zeros(2)
        self._currentPhases= np.zeros(2)
        self._wantedTrajectory= None

        self._nAdaptiveIterationEllipse= 3
        self._nAdaptiveIterationFreeform= 3
        self._adaptiveModulationMethod= self.ADAPTIVE_MODULATION_ELLIPSE


    def useNoAdaptiveModulation(self):
        self._adaptiveModulationMethod= self.ADAPTIVE_MODULATION_NONE


    def useEllipticalAdaptiveModulation(self):
        self._adaptiveModulationMethod= self.ADAPTIVE_MODULATION_ELLIPSE


    def useFreeformAdaptiveModulation(self):
        self._adaptiveModulationMethod= self.ADAPTIVE_MODULATION_FREEFORM


    def _applyChanges(self):
        if self._adaptiveModulationMethod == self.ADAPTIVE_MODULATION_NONE:
            self._modulate()
        elif self._adaptiveModulationMethod == \
                self.ADAPTIVE_MODULATION_ELLIPSE:
            self._modulateWithAdaptiveEllipse()
        elif self._adaptiveModulationMethod == \
                self.ADAPTIVE_MODULATION_FREEFORM:
            self._modulateWithAdaptiveFreeform()
        else:
            raise Exception(
                "Programming error. Unknown modulation method %s" % str(
                    self._adaptiveModulationMethod))


    def _modulate(self):
        self._wantedTrajectory= self._circle(
            [self._radiusInMilliRad, self._radiusInMilliRad],
            self._frequencyInHz,
            [0, 0],
            self._centerInMilliRad,
            self._tt.getRecordedDataTimeStep())
        self._applyTrajectory(self._wantedTrajectory)


    @override
    def name(self):
        return self._name


    @override
    def setRadiusInMilliRad(self, radiusInMilliRad):
        self._radiusInMilliRad = radiusInMilliRad
        self._applyChanges()


    @override
    def getRadiusInMilliRad(self):
        return self._radiusInMilliRad


    @override
    def setFrequencyInHz(self, frequencyInHz):
        self._frequencyInHz = frequencyInHz
        self._applyChanges()


    @override
    def getFrequencyInHz(self):
        return self._frequencyInHz


    @override
    def setCenterInMilliRad(self, center):
        self._centerInMilliRad= center
        self._applyChanges()


    @override
    def getCenterInMilliRad(self):
        return self._centerInMilliRad


    def _modulateWithAdaptiveEllipse(self):
        self._modulate()
        self._currentRadii= [self._radiusInMilliRad, self._radiusInMilliRad]
        self._currentCenter= self._centerInMilliRad
        self._currentPhases= np.zeros(2)

        for _ in range(self._nAdaptiveIterationEllipse):
            (useRadii, useCenter, usePhases)= self._computeAdaptedParameters(
                [self._radiusInMilliRad, self._radiusInMilliRad],
                self._centerInMilliRad)
            self._startModulation(useRadii, self._frequencyInHz,
                                  usePhases, useCenter)
            self._logger.notice(
                "radii want/set: %s / %s" % (
                    [self._radiusInMilliRad, self._radiusInMilliRad],
                    self._currentRadii))
            self._logger.notice("center want/set: %s / %s" %
                                (self._centerInMilliRad, self._currentCenter))
            self._logger.notice("phases set: %s" % usePhases)
            # self._plotError()


    def _modulateWithAdaptiveFreeform(self):
        self._modulateWithAdaptiveEllipse()

        for _ in range(self._nAdaptiveIterationFreeform):
            trajectoryError= self._getError()
            applyCommand= self._lastAppliedTrajectory + trajectoryError
            self._applyTrajectory(applyCommand)
            # self._plotError()


    def _applyTrajectory(self, trajectory):
        self._tt.startFreeformModulation(trajectory[0], trajectory[1])
        self._lastAppliedTrajectory= trajectory


    def _startModulation(self, radii, freq, phases, center):
        trajectory= self._circle(radii, freq, phases, center,
                                 self._tt.getRecordedDataTimeStep())
        self._applyTrajectory(trajectory)
        self._currentRadii= radii
        self._currentCenter= center
        self._currentPhases= phases


    def _getTrajectory(self):
        diagn= self.getDiagnosticData()
        return diagn[1:3]


    def _computeAdaptedParameters(self, wantRadii, wantCenter):
        actualTrajectory= self._getTrajectory()

        dt= self._tt.getRecordedDataTimeStep()
        periodInPoints= round(1./ self._frequencyInHz / dt)
        phaseShiftX, phaseShiftY= self._estimatePhaseShift(actualTrajectory,
                                                           periodInPoints)
        corrPhases= np.array([0, (phaseShiftY - phaseShiftX)])
        gotRadii= np.ptp(actualTrajectory, axis=1) / 2.0
        corrRadii= gotRadii / wantRadii
        gotCenter= 0.5 * (np.max(actualTrajectory, axis=1) +
                          np.min(actualTrajectory, axis=1))
        corrCenter= gotCenter - wantCenter

        self._logger.notice("got radii %s, corr %s" % (gotRadii, corrRadii))
        self._logger.notice("got center %s, corr %s" % (gotCenter, corrCenter))

        return (self._currentRadii / corrRadii,
                self._currentCenter - corrCenter,
                self._currentPhases - corrPhases)


    @override
    def getDiagnosticData(self):
        import time
        self._tt.getRecordedData(4)
        time.sleep(0.2)
        diagn= self._tt.getRecordedData(4000)
        return np.vstack((diagn, self._wantedTrajectory))


    def _findShiftWithAutoCorrelation(self, wanted, measured, periodInPoints):
        wantedZeroMean= wanted - np.mean(wanted)
        measuredZeroMean= measured - np.mean(measured)
        corr= scipy.signal.signaltools.correlate(
            wantedZeroMean[0:periodInPoints],
            measuredZeroMean,
            mode='valid')
        return np.argmax(corr[0: periodInPoints])


    def _estimatePhaseShift(self, measuredTrajectory, periodInPoints):
        shiftX= self._findShiftWithAutoCorrelation(
            self._wantedTrajectory[0], measuredTrajectory[0], periodInPoints)
        shiftY= self._findShiftWithAutoCorrelation(
            self._wantedTrajectory[1], measuredTrajectory[1], periodInPoints)
        self._logger.notice("shift in points %d %d " % (shiftX, shiftY))
        phaseShiftX= shiftX / periodInPoints * np.pi * 2
        phaseShiftY= shiftY / periodInPoints * np.pi * 2
        return (phaseShiftX, phaseShiftY)


    def _getError(self):
        measuredTraj= self._getTrajectory()
        dt= self._tt.getRecordedDataTimeStep()
        periodInPoints= round(1./ self._frequencyInHz / dt)
        phaseShiftX, phaseShiftY= self._estimatePhaseShift(measuredTraj,
                                                           periodInPoints)

        (xd, yd)= self._circle([self._radiusInMilliRad,
                                self._radiusInMilliRad],
                               self._frequencyInHz,
                               [phaseShiftX, phaseShiftY],
                               self._centerInMilliRad,
                               dt)
        diffX= xd - measuredTraj[0]
        diffY= yd - measuredTraj[1]
        # diffX= np.roll(diffX, shiftX)
        # diffY= np.roll(diffY, shiftY)
        error= np.array([diffX, diffY])
        self._logger.notice("Error max %f min %f rms %f" % (
            error.max(), error.min(), error.std()))
        return error


    def getResidualRms(self):
        error= self._getError()
        errorRms= np.mean(np.linalg.norm(error, axis=0))
        return errorRms


    def _circle(self, radiusInMilliRad, frequencyInHz,
                dephaseInRadians, centerInMilliRad, dt):
        t= np.linspace(0, dt* 4000, 4000, endpoint=False)
        x= radiusInMilliRad[0] * \
            np.cos(t* frequencyInHz* 2* np.pi + dephaseInRadians[0]) + \
            centerInMilliRad[0]
        y= radiusInMilliRad[1] * \
            np.sin(t* frequencyInHz* 2* np.pi + dephaseInRadians[1]) + \
            centerInMilliRad[1]
        return np.array([x, y])


    def _sine(self, radiusInMilliRad, frequencyInHz,
              phaseInRadians, centerInMilliRad, dt):
        t= np.linspace(0, dt* 4000, 4000, endpoint=False)
        x= radiusInMilliRad * np.sin(
            t* frequencyInHz* 2* np.pi + phaseInRadians) + centerInMilliRad
        return x

    def _plotError(self):
        import matplotlib.pyplot as plt
        plt.subplot(211)
        err= self._getError()
        plt.plot(err[0], label='error axis A')
        plt.plot(err[1], label='error axis B')
        plt.legend()
        plt.subplot(212)
        traj= self._wantedTrajectory
        actualTraj= self._getTrajectory()
        plt.plot(traj[0], traj[1], 'b', label='wanted')
        plt.plot(actualTraj[0], actualTraj[1], 'r', label='got')
        plt.legend()
        plt.show()
