import threading
from plico.utils.logger import Logger
from plico.utils.decorator import logEnterAndExit, override, synchronized
from plico.utils.timekeeper import TimeKeeper
from plico.utils.stepable import Stepable
from plico.utils.snapshotable import Snapshotable
from plico.utils.hackerable import Hackerable
from palpao.types.deformable_mirror_status import DeformableMirrorStatus
from palpao.client.abstract_deformable_mirror_client import SnapshotEntry
from plico.utils.serverinfoable import ServerInfoable


__version__= "$Id: deformable_mirror_controller.py 27 2018-01-27 08:48:07Z lbusoni $"




class DeformableMirrorController(Stepable, Snapshotable, Hackerable,
                                 ServerInfoable):

    def __init__(self,
                 servername,
                 ports,
                 deformableMirror,
                 replySocket,
                 statusSocket,
                 rpcHandler):
        self._mirror= deformableMirror
        self._replySocket= replySocket
        self._statusSocket= statusSocket
        self._rpcHandler= rpcHandler
        self._logger= Logger.of('DeformableMirrorController')
        Hackerable.__init__(self, self._logger)
        ServerInfoable.__init__(self, servername,
                                ports,
                                self._logger)
        self._isTerminated= False
        self._stepCounter= 0
        self._commandCounter= 0
        self._timekeep = TimeKeeper()
        self._mirrorStatus= None
        self._mutexStatus= threading.RLock()


    @override
    def step(self):
        self._rpcHandler.handleRequest(self, self._replySocket, multi=True)
        self._publishStatus()
        if self._timekeep.inc():
            self._logger.notice(
                'Stepping at %5.2f Hz' % (self._timekeep.rate))
        self._stepCounter+= 1


    def _getStepCounter(self):
        return self._stepCounter


    def terminate(self):
        self._logger.notice("Got request to terminate")
        try:
            self._mirror.deinitialize()
        except Exception as e:
            self._logger.warn("Could not deinitialize mirror: %s" %
                              str(e))
        self._isTerminated= True


    @override
    def isTerminated(self):
        return self._isTerminated


    def setZonalCommand(self, actuatorCommands):
        self._mirror.setZonalCommand(actuatorCommands)
        self._zonalCommand= actuatorCommands
        self._commandCounter+= 1
        with self._mutexStatus:
            self._mirrorStatus= None


    def getZonalCommand(self):
        return self._zonalCommand


    def getSnapshot(self, prefix):
        status= self._getMirrorStatus()
        snapshot= {}
        snapshot[SnapshotEntry.COMMAND_COUNTER]= status.commandCounter()
        snapshot[SnapshotEntry.SERIAL_NUMBER]= \
            self._getDeformableMirrorSerialNumber()
        snapshot[SnapshotEntry.STEP_COUNTER]= self._getStepCounter()
        return Snapshotable.prepend(prefix, snapshot)


    def _getDeformableMirrorSerialNumber(self):
        return self._mirror.serialNumber()



    @synchronized("_mutexStatus")
    def _getMirrorStatus(self):
        if self._mirrorStatus is None:
            self._logger.debug('get MirrorStatus')
            self._mirrorStatus= DeformableMirrorStatus(
                self._mirror.getZonalCommand(),
                self._commandCounter)
        return self._mirrorStatus


    def _publishStatus(self):
        self._rpcHandler.publishPickable(self._statusSocket,
                                         self._getMirrorStatus())
