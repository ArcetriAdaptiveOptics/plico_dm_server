#!/usr/bin/env python
import numpy as np
from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico_dm_server.controller.abstract_modulator import AbstractModulator


class SimulatedModulator(AbstractModulator):
    """Laptop-friendly PWFS modulator with no hardware dependency."""

    def __init__(self, name):
        AbstractModulator.__init__(self)
        self._name = name
        self._radiusInMilliRad = 10.
        self._frequencyInHz = 100.
        self._centerInMilliRad = np.zeros(2)
        self._logger = Logger.of("Simulated Modulator")
        self._logger.notice('Initialized')

    @override
    def name(self):
        return self._name

    @override
    def setRadiusInMilliRad(self, radiusInMilliRad):
        self._radiusInMilliRad = float(radiusInMilliRad)

    @override
    def getRadiusInMilliRad(self):
        return self._radiusInMilliRad

    @override
    def setFrequencyInHz(self, frequencyInHz):
        self._frequencyInHz = float(frequencyInHz)

    @override
    def getFrequencyInHz(self):
        return self._frequencyInHz

    @override
    def setCenterInMilliRad(self, center):
        self._centerInMilliRad = np.asarray(center, dtype=float)

    @override
    def getCenterInMilliRad(self):
        return self._centerInMilliRad

    @override
    def getDiagnosticData(self):
        nPoints = 4000
        dt = 40e-6
        t = np.linspace(0, dt * nPoints, nPoints, endpoint=False)
        x = (self._radiusInMilliRad *
             np.sin(t * self._frequencyInHz * 2 * np.pi) +
             self._centerInMilliRad[0])
        y = (self._radiusInMilliRad *
             np.cos(t * self._frequencyInHz * 2 * np.pi) +
             self._centerInMilliRad[1])
        diagnArray = np.zeros((9, nPoints))
        diagnArray[0] = t
        diagnArray[1] = x
        diagnArray[2] = y
        diagnArray[5] = x
        diagnArray[6] = y
        return diagnArray
