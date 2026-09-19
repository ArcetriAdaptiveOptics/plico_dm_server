import threading
import numpy as np
from plico.utils.logger import Logger
from plico.utils.decorator import override, synchronized, logEnterAndExit
from plico.utils.timekeeper import TimeKeeper
from plico.utils.stepable import Stepable
from plico.utils.snapshotable import Snapshotable
from plico.utils.hackerable import Hackerable
from plico.utils.serverinfoable import ServerInfoable
from plico_dm.types.modulator_status import ModulatorStatus
from plico_dm.client.abstract_modulator_client import SnapshotEntry


class ModulatorController(Stepable, Snapshotable, Hackerable,
                          ServerInfoable):
    """ZMQ RPC surface for a PWFS modulator (Prisma-shaped method names)."""

    def __init__(self,
                 servername,
                 ports,
                 modulator,
                 replySocket,
                 statusSocket,
                 rpcHandler):
        self._modulator = modulator
        self._replySocket = replySocket
        self._statusSocket = statusSocket
        self._rpcHandler = rpcHandler
        self._logger = Logger.of('ModulatorController')
        Hackerable.__init__(self, self._logger)
        ServerInfoable.__init__(self, servername, ports, self._logger)
        self._isTerminated = False
        self._stepCounter = 0
        self._commandCounter = 0
        self._timekeep = TimeKeeper()
        self._modulatorStatus = None
        self._mutexStatus = threading.RLock()
        self._logger.notice('Modulator Controller created for %s' %
                            self._modulator.name())

    @override
    def step(self):
        self._rpcHandler.handleRequest(self, self._replySocket, multi=True)
        self._publishStatus()
        if self._timekeep.inc():
            self._logger.notice(
                'Stepping at %5.2f Hz' % (self._timekeep.rate))
        self._stepCounter += 1

    def terminate(self):
        self._logger.notice("Got request to terminate")
        self._isTerminated = True

    @override
    def isTerminated(self):
        return self._isTerminated

    def _invalidateStatus(self):
        with self._mutexStatus:
            self._modulatorStatus = None
        self._commandCounter += 1

    @logEnterAndExit('Entering setModulatorFrequencyInHz',
                     'Executed setModulatorFrequencyInHz')
    def setModulatorFrequencyInHz(self, frequencyInHz):
        self._modulator.setFrequencyInHz(frequencyInHz)
        self._invalidateStatus()

    @logEnterAndExit('Entering setModulatorRadiusInMilliRad',
                     'Executed setModulatorRadiusInMilliRad')
    def setModulatorRadiusInMilliRad(self, radiusInMilliRad):
        self._modulator.setRadiusInMilliRad(radiusInMilliRad)
        self._invalidateStatus()

    @logEnterAndExit('Entering setModulatorCenterInMilliRad',
                     'Executed setModulatorCenterInMilliRad')
    def setModulatorCenterInMilliRad(self, centerInMilliRad):
        self._modulator.setCenterInMilliRad(
            np.asarray(centerInMilliRad, dtype=float))
        self._invalidateStatus()

    @logEnterAndExit('Entering offsetModulatorCenterByMilliRad',
                     'Executed offsetModulatorCenterByMilliRad')
    def offsetModulatorCenterByMilliRad(self, offsetInMilliRad):
        currCenter = self._modulator.getCenterInMilliRad()
        self.setModulatorCenterInMilliRad(
            np.asarray(currCenter, dtype=float) +
            np.asarray(offsetInMilliRad, dtype=float))

    def getModulatorDiagnosticData(self):
        return self._modulator.getDiagnosticData()

    def getSnapshot(self, prefix):
        status = self._getModulatorStatus()
        snapshot = {}
        snapshot[SnapshotEntry.MODULATOR_AMPLITUDE] = \
            status.modulatorRadiusInMilliRad
        snapshot[SnapshotEntry.MODULATOR_FREQUENCY] = \
            status.modulatorFrequencyInHz
        snapshot[SnapshotEntry.MODULATOR_CENTER_AXIS_0] = \
            status.modulatorCenterInMilliRad[0]
        snapshot[SnapshotEntry.MODULATOR_CENTER_AXIS_1] = \
            status.modulatorCenterInMilliRad[1]
        snapshot[SnapshotEntry.COMMAND_COUNTER] = status.command_counter
        snapshot[SnapshotEntry.NAME] = status.name
        return Snapshotable.prepend(prefix, snapshot)

    @synchronized("_mutexStatus")
    def _getModulatorStatus(self):
        if self._modulatorStatus is None:
            self._modulatorStatus = ModulatorStatus(
                self._modulator.getFrequencyInHz(),
                self._modulator.getRadiusInMilliRad(),
                self._modulator.getCenterInMilliRad(),
                command_counter=self._commandCounter,
                name=self._modulator.name())
        return self._modulatorStatus

    def _publishStatus(self):
        self._rpcHandler.publishPickable(
            self._statusSocket, self._getModulatorStatus())
