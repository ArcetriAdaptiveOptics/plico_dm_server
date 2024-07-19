#!/usr/bin/env python
import os
import sys
import subprocess
import shutil
import unittest
import logging
import numpy as np
from test.test_helper import TestHelper, Poller, MessageInFileProbe,\
    ExecutionProbe
from plico.utils.configuration import Configuration
from plico.rpc.zmq_remote_procedure_call import ZmqRemoteProcedureCall
from plico.utils.logger import Logger
from plico.client.serverinfo_client import ServerInfoClient
from plico_dm_server.utils.starter_script_creator import StarterScriptCreator
from plico_dm_server.utils.process_startup_helper import ProcessStartUpHelper
from plico_dm.client.deformable_mirror_client import DeformableMirrorClient
from plico_dm_server.controller.runner import Runner
from plico.utils.process_monitor_runner import RUNNING_MESSAGE as MONITOR_RUNNING_MESSAGE
from plico.rpc.sockets import Sockets
from plico.rpc.zmq_ports import ZmqPorts
from plico_dm_server.utils.constants import Constants
from plico_dm.client.abstract_deformable_mirror_client import SnapshotEntry


@unittest.skipIf(sys.platform.startswith("win"), "doesn't run on Windows")
class IntegrationTest(unittest.TestCase):

    TEST_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            "./tmp/")
    LOG_DIR = os.path.join(TEST_DIR, "log")
    CONF_FILE = 'test/integration/conffiles/plico_dm_server.conf'
    CALIB_FOLDER = 'test/integration/calib'
    CONF_SECTION = Constants.PROCESS_MONITOR_CONFIG_SECTION

    PROCESS_MONITOR_LOG_PATH = os.path.join(LOG_DIR, "%s.log" % CONF_SECTION)
    BIN_DIR = os.path.join(TEST_DIR, "apps", "bin")
    SOURCE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                              "../..")

    def setUp(self):
        self._setUpBasicLogging()
        self.server = None
        self._wasSuccessful = False

        self._removeTestFolderIfItExists()
        self._makeTestDir()
        self.configuration = Configuration()
        self.configuration.load(self.CONF_FILE)
        self.rpc = ZmqRemoteProcedureCall()
        self._server_config_prefix = self.configuration.getValue(
                                       Constants.PROCESS_MONITOR_CONFIG_SECTION,
                                       'server_config_prefix')

        calibrationRootDir = self.configuration.calibrationRootDir()
        self._setUpCalibrationTempFolder(calibrationRootDir)

        self.CONTROLLER_1_LOGFILE = os.path.join(self.LOG_DIR, '%s%d.log' % (self._server_config_prefix, 1))
        self.CONTROLLER_2_LOGFILE = os.path.join(self.LOG_DIR, '%s%d.log' % (self._server_config_prefix, 2))
        self.PROCESS_MONITOR_PORT = self.configuration.getValue(
                                       Constants.PROCESS_MONITOR_CONFIG_SECTION,
                                       'port', getint=True)


    def _setUpBasicLogging(self):
        logging.basicConfig(level=logging.DEBUG)
        self._logger = Logger.of('Integration Test')

    def _makeTestDir(self):
        os.makedirs(self.TEST_DIR)
        os.makedirs(self.LOG_DIR)
        os.makedirs(self.BIN_DIR)

    def _setUpCalibrationTempFolder(self, calibTempFolder):
        shutil.copytree(self.CALIB_FOLDER,
                        calibTempFolder)

    def _removeTestFolderIfItExists(self):
        if os.path.exists(self.TEST_DIR):
            shutil.rmtree(self.TEST_DIR)

    def tearDown(self):
        TestHelper.dumpFileToStdout(self.PROCESS_MONITOR_LOG_PATH)
        TestHelper.dumpFileToStdout(self.CONTROLLER_1_LOGFILE)
        TestHelper.dumpFileToStdout(self.CONTROLLER_2_LOGFILE)

        if self.server is not None:
            TestHelper.terminateSubprocess(self.server)

        if self._wasSuccessful:
            self._removeTestFolderIfItExists()

    def _createStarterScripts(self):
        ssc = StarterScriptCreator()
        ssc.setInstallationBinDir(self.BIN_DIR)
        ssc.setPythonPath(self.SOURCE_DIR)
        ssc.setConfigFileDestination(self.CONF_FILE)
        ssc.installExecutables()

    def _startProcesses(self):
        psh = ProcessStartUpHelper()
        serverLog = open(os.path.join(self.LOG_DIR, "server.out"), "wb")
        self.server = subprocess.Popen(
            [psh.processProcessMonitorStartUpScriptPath(),
             self.CONF_FILE,
             self.CONF_SECTION],
            stdout=serverLog, stderr=serverLog)
        Poller(5).check(MessageInFileProbe(
            MONITOR_RUNNING_MESSAGE(Constants.SERVER_PROCESS_NAME), self.PROCESS_MONITOR_LOG_PATH))

    def _testProcessesActuallyStarted(self):
        Poller(5).check(MessageInFileProbe(
            Runner.RUNNING_MESSAGE, self.CONTROLLER_1_LOGFILE))
        Poller(5).check(MessageInFileProbe(
            Runner.RUNNING_MESSAGE, self.CONTROLLER_2_LOGFILE))

    def _buildClients(self):
        ports1 = ZmqPorts.fromConfiguration(
            self.configuration,
            '%s%d' % (self._server_config_prefix, 1))
        self.client1 = DeformableMirrorClient(
            self.rpc, Sockets(ports1, self.rpc))
        ports2 = ZmqPorts.fromConfiguration(
            self.configuration,
            '%s%d' % (self._server_config_prefix, 2))
        self.client2 = DeformableMirrorClient(
            self.rpc, Sockets(ports2, self.rpc))
        self.clientAll = ServerInfoClient(
            self.rpc,
            Sockets(ZmqPorts('localhost', self.PROCESS_MONITOR_PORT), self.rpc).serverRequest(),
            self._logger)

    def _testSetShape(self):
        numberOfModes = self.client1.get_number_of_modes()
        mirrorModalAmplitude = np.arange(numberOfModes) * 3.141
        self.client1.set_shape(mirrorModalAmplitude)
        Poller(3).check(ExecutionProbe(
            lambda: self.assertTrue(
                np.allclose(
                    mirrorModalAmplitude,
                    self.client1.get_shape()))))

    def _testSaveAndLoadReference(self):
        numberOfModes = self.client1.get_number_of_modes()
        mirrorShape = np.arange(numberOfModes) * 3.141
        self.client1.set_shape(mirrorShape)
        current_reference = self.client1.get_reference_shape()
        self.client1.save_current_shape_as_reference('foogoo')
        self.client1.load_reference('foogoo')
        np.testing.assert_allclose(
            current_reference + mirrorShape,
            self.client1.get_reference_shape())

    def _checkBackdoor(self):
        self.client1.execute(
            "import numpy as np; "
            "self._myarray= np.array([1, 2])")
        self.assertEqual(
            repr(np.array([1, 2])),
            self.client1.eval("self._myarray"))
        self.client1.execute("self._foobar= 42")
        self.assertEqual(
            "42",
            self.client1.eval("self._foobar"))

    def _testGetStatus(self):
        status = self.client1.get_status()
        cmdCounter = status.command_counter
        self.client1.set_shape(
            self.client1.get_shape() * 2.0)
        Poller(3).check(ExecutionProbe(
            lambda: self.assertEqual(
                cmdCounter + 1,
                self.client1.get_status().command_counter)))

    def _testGetSnapshot(self):
        snapshot = self.client1.get_snapshot('aa')
        snKey = 'aa.%s' % SnapshotEntry.SERIAL_NUMBER
        self.assertTrue(snKey in snapshot.keys())

    def _testServerInfo(self):
        serverInfo = self.client1.serverInfo()
        self.assertEqual('ALPAO DM277 Deformable Mirror Server',
                         serverInfo.name)
        self.assertEqual('localhost', serverInfo.hostname)

    def testMain(self):
        self._buildClients()
        self._createStarterScripts()
        self._startProcesses()
        self._testProcessesActuallyStarted()
        self._testSetShape()
        self._testSaveAndLoadReference()
        self._testGetStatus()
        self._testGetSnapshot()
        self._testServerInfo()
        self._checkBackdoor()
        self._wasSuccessful = True


if __name__ == "__main__":
    unittest.main()
