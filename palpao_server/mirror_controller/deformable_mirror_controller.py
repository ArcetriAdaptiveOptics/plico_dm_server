import threading
import numpy as np
from plico.utils.logger import Logger
from plico.utils.decorator import override, synchronized
from plico.utils.timekeeper import TimeKeeper
from plico.utils.stepable import Stepable
from plico.utils.snapshotable import Snapshotable
from plico.utils.hackerable import Hackerable
from palpao.types.deformable_mirror_status import DeformableMirrorStatus
from palpao.client.abstract_deformable_mirror_client import SnapshotEntry
from plico.utils.serverinfoable import ServerInfoable





class DeformableMirrorController(Stepable, Snapshotable, Hackerable,
                                 ServerInfoable):

    def __init__(self,
                 servername,
                 ports,
                 deformableMirror,
                 replySocket,
                 statusSocket,
                 rpcHandler,
                 calibrationManager,
                 flatZonalCommandTag):
        self._mirror= deformableMirror
        self._replySocket= replySocket
        self._statusSocket= statusSocket
        self._rpcHandler= rpcHandler
        self._calMgr= calibrationManager
        self._flatTag= flatZonalCommandTag
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
        self._modalCommand= None
        self._modalBasis= None
#        self._setModalBasis('zonal')
        self._initialize()
        self._logger.notice('Deformable Mirror Controller created')


    def _initialize(self):
        self.setFlatCommand(self._flatTag)
        self.setShape(np.zeros(self._getNumberOfModes()))


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


    def setFlatCommand(self, flatTag):
        self._flatCmd= self._calMgr.loadZonalCommand(flatTag)
        self._flatTag= flatTag


    def getFlatTag(self):
        return self._flatTag


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


    def _getNumberOfActuators(self):
        return self._mirror.getNumberOfActuators()


    def _getNumberOfModes(self):
#        self._modalBasis.shape[1]
        return self._getNumberOfActuators()


#    @synchronized("_mutexStatus")
#    def _setModalBasis(self, modalBasisTag):
#        if modalBasisTag == 'zonal':
#            self._modalBasis= np.identity(self._getNumberOfActuators())
#            self._modalBasisTag= modalBasisTag

    def _convertModalToZonal(self, modalCommand):
        return modalCommand.copy()


    def _convertZonalToModal(self, zonalCommand):
        return zonalCommand.copy()


    def setShape(self, modalAmplitudes):
        zonalCommand= self._convertModalToZonal(modalAmplitudes)
        self._mirror.setZonalCommand(zonalCommand + self._flatCmd)
        self._modalCommand= modalAmplitudes.copy()
        self._commandCounter+= 1
        with self._mutexStatus:
            self._mirrorStatus= None


    def getShape(self):
        zonalCmd= self._mirror.getZonalCommand() - self._flatCmd
        return self._convertZonalToModal(zonalCmd)


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
                self._getNumberOfActuators(),
                self._getNumberOfModes(),
                self._mirror.getZonalCommand(),
                self._commandCounter)
            self._logger.debug(self._mirrorStatus)
        return self._mirrorStatus


    def _publishStatus(self):
        self._rpcHandler.publishPickable(self._statusSocket,
                                         self._getMirrorStatus())
