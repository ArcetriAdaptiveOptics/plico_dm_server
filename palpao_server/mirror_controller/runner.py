import os
import time
from plico.utils.base_runner import BaseRunner
from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico.utils.control_loop import FaultTolerantControlLoop
from palpao_server.mirror_controller.simulated_deformable_mirror import \
    SimulatedDeformableMirror
from palpao_server.mirror_controller.deformable_mirror_controller import \
    DeformableMirrorController
from plico.rpc.zmq_ports import ZmqPorts
from palpao.calibration.calibration_manager import CalibrationManager
from palpao_server.mirror_controller.bmc_deformable_mirror import \
    BmcDeformableMirror
from palpao_server.mirror_controller.alpao_deformable_mirror import \
    AlpaoDeformableMirror
import sys



class Runner(BaseRunner):

    RUNNING_MESSAGE = "Mirror controller is running."

    def __init__(self):
        BaseRunner.__init__(self)


    def _tryGetDefaultFlatTag(self):
        try:
            mirrorDeviceSection= self.configuration.getValue(
                self.getConfigurationSection(), 'mirror')
            return self.configuration.getValue(
                mirrorDeviceSection, 'default_flat_tag')
        except KeyError as e:
            self._logger.warn(str(e))
            return None


    def _createDeformableMirrorDevice(self):
        mirrorDeviceSection= self.configuration.getValue(
            self.getConfigurationSection(), 'mirror')
        mirrorModel= self.configuration.deviceModel(mirrorDeviceSection)
        if mirrorModel == 'simulatedMEMSMultiDM':
            self._createSimulatedDeformableMirror(mirrorDeviceSection)
        elif mirrorModel == 'simulatedDM':
            self._createSimulatedDeformableMirror(mirrorDeviceSection)
        elif mirrorModel == 'alpaoDM':
            self._createAlpaoMirror(mirrorDeviceSection)
        elif mirrorModel == 'piTipTilt':
            self._createPITipTiltMirror(mirrorDeviceSection)
        elif mirrorModel == 'bmc':
            self._createBmcDeformableMirror(mirrorDeviceSection)
        else:
            raise KeyError('Unsupported mirror model %s' % mirrorModel)


    def _createSimulatedDeformableMirror(self, mirrorDeviceSection):
        dmSerialNumber= self.configuration.getValue(
            mirrorDeviceSection, 'serial_number')
        self._mirror= SimulatedDeformableMirror(dmSerialNumber)


    def _createAlpaoMirror(self, mirrorDeviceSection):
        serialNumber= self.configuration.getValue(mirrorDeviceSection,
                                                  'serial_number')
        self._logger.notice("Creating ALPAO device SN %s" % serialNumber)
        libFolder= self.configuration.getValue(mirrorDeviceSection,
                                               'lib_folder')
        sys.path.append(libFolder)
        from asdk import DM
        alpaoDm= DM(serialNumber)
        self._mirror= AlpaoDeformableMirror(alpaoDm, serialNumber)


    def _createBmcDeformableMirror(self, mirrorDeviceSection):
        serialNumber= self.configuration.getValue(mirrorDeviceSection,
                                                  'serial_number')
        self._logger.notice("Creating BMC device SN %s" % serialNumber)
        import bmc
        bmcDm= bmc.BmcDm()
        self._logger.notice("BMC version <%s>" % bmcDm.version_string())
        self._mirror= BmcDeformableMirror(bmcDm, serialNumber)


    def _createPITipTiltMirror(self, mirrorDeviceSection):
        from palpao_server.mirror_controller.pi_tip_tilt_mirror \
            import PhysikInstrumenteTipTiltMirror
        from pi_gcs.gcs2 import GeneralCommandSet2
        from pi_gcs.tip_tilt_2_axes import TipTilt2Axis

        hostname= self.configuration.getValue(
            mirrorDeviceSection, 'ip_address')
        serialNumber= self.configuration.getValue(mirrorDeviceSection,
                                                  'serial_number')
        cfg= self._calibrationManager.loadPiTipTiltCalibration(
            serialNumber)
        cfg.hostname= hostname
        gcs=GeneralCommandSet2()
        tt=TipTilt2Axis(gcs, cfg)
        tt.setUp()
        self._mirror= PhysikInstrumenteTipTiltMirror(
            serialNumber, tt)


    def _createCalibrationManager(self):
        calibrationRootDir= self.configuration.calibrationRootDir()
        self._calibrationManager= CalibrationManager(calibrationRootDir)


    def _setUp(self):
        self._logger= Logger.of("Deformable Mirror Controller runner")

        self._zmqPorts= ZmqPorts.fromConfiguration(
            self.configuration, self.getConfigurationSection())
        self._replySocket = self.rpc().replySocket(
            self._zmqPorts.SERVER_REPLY_PORT)
        self._statusSocket = self.rpc().publisherSocket(
            self._zmqPorts.SERVER_STATUS_PORT)

        self._logger.notice('reply socket on port %d' %
                            self._zmqPorts.SERVER_REPLY_PORT)
        self._logger.notice('status socket on port %d' %
                            self._zmqPorts.SERVER_STATUS_PORT)

        self._createCalibrationManager()

        self._createDeformableMirrorDevice()

        flatFileTag= self._tryGetDefaultFlatTag()

        self._controller= DeformableMirrorController(
            self.name,
            self._zmqPorts,
            self._mirror,
            self._replySocket,
            self._statusSocket,
            self.rpc(),
            self._calibrationManager,
            flatFileTag)


    def _runLoop(self):
        self._logRunning()

        FaultTolerantControlLoop(
            self._controller,
            Logger.of("Deformable Mirror Controller control loop"),
            time,
            0.001).start()
        self._logger.notice("Terminated")


    @override
    def run(self):
        self._setUp()
        self._runLoop()
        return os.EX_OK


    @override
    def terminate(self, signal, frame):
        self._controller.terminate()
