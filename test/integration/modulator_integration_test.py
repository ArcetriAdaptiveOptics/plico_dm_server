#!/usr/bin/env python
"""Lightweight integration: start one simulated modulator controller and talk RPC."""
import os
import sys
import subprocess
import shutil
import unittest
import logging
import numpy as np
from test.test_helper import TestHelper, Poller, MessageInFileProbe
from plico.utils.configuration import Configuration
from plico.rpc.zmq_remote_procedure_call import ZmqRemoteProcedureCall
from plico.utils.logger import Logger
from plico_dm_server.utils.starter_script_creator import StarterScriptCreator
from plico_dm_server.utils.process_startup_helper import ProcessStartUpHelper
from plico_dm.client.modulator_client import ModulatorClient
from plico_dm_server.controller.runner import Runner
from plico.rpc.sockets import Sockets
from plico.rpc.zmq_ports import ZmqPorts


@unittest.skipIf(sys.platform.startswith("win"), "doesn't run on Windows")
class ModulatorIntegrationTest(unittest.TestCase):

    TEST_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            "./tmp/")
    LOG_DIR = os.path.join(TEST_DIR, "log")
    CONF_FILE = 'test/integration/conffiles/plico_dm_server.conf'
    CALIB_FOLDER = 'test/integration/calib'
    CONF_SECTION = 'modulator1'
    SOURCE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                              "../..")

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self._logger = Logger.of('Modulator Integration Test')
        self.server = None
        self._wasSuccessful = False
        if os.path.exists(self.TEST_DIR):
            shutil.rmtree(self.TEST_DIR)
        os.makedirs(self.TEST_DIR)
        os.makedirs(self.LOG_DIR)
        os.makedirs(os.path.join(self.TEST_DIR, "apps", "bin"))
        self.configuration = Configuration()
        self.configuration.load(self.CONF_FILE)
        self.rpc = ZmqRemoteProcedureCall()
        calibRoot = self.configuration.calibrationRootDir()
        shutil.copytree(self.CALIB_FOLDER, calibRoot)
        # force_log_dir in conf → test/integration/tmp/log
        self.CONTROLLER_LOGFILE = os.path.join(
            self.configuration.loggingDir(), '%s.log' % self.CONF_SECTION)

    def tearDown(self):
        if os.path.exists(self.CONTROLLER_LOGFILE):
            TestHelper.dumpFileToStdout(self.CONTROLLER_LOGFILE)
        if self.server is not None:
            TestHelper.terminateSubprocess(self.server)
        if self._wasSuccessful and os.path.exists(self.TEST_DIR):
            shutil.rmtree(self.TEST_DIR)

    def _createStarterScripts(self):
        ssc = StarterScriptCreator()
        ssc.setInstallationBinDir(os.path.join(self.TEST_DIR, "apps", "bin"))
        ssc.setPythonPath(self.SOURCE_DIR)
        ssc.setConfigFileDestination(self.CONF_FILE)
        ssc.installExecutables()

    def _startController(self):
        psh = ProcessStartUpHelper()
        serverLog = open(os.path.join(self.LOG_DIR, "modulator_server.out"), "wb")
        self.server = subprocess.Popen(
            [sys.executable,
             psh.controllerStartUpScriptPath(),
             self.CONF_FILE,
             self.CONF_SECTION],
            stdout=serverLog, stderr=serverLog,
            cwd=self.SOURCE_DIR)
        Poller(10).check(MessageInFileProbe(
            Runner.MODULATOR_RUNNING_MESSAGE, self.CONTROLLER_LOGFILE))

    def testModulatorRadiusAndFrequency(self):
        self._createStarterScripts()
        self._startController()
        ports = ZmqPorts.fromConfiguration(self.configuration, self.CONF_SECTION)
        client = ModulatorClient(self.rpc, Sockets(ports, self.rpc))
        client.setRadiusInMilliRad(2.25)
        client.setFrequencyInHz(17.0)
        client.setCenterInMilliRad(np.array([0.05, -0.05]))
        self.assertAlmostEqual(2.25, client.getRadiusInMilliRad(), places=5)
        self.assertAlmostEqual(17.0, client.getFrequencyInHz(), places=5)
        np.testing.assert_array_almost_equal(
            np.array([0.05, -0.05]), client.getCenterInMilliRad())
        self._wasSuccessful = True


if __name__ == '__main__':
    unittest.main()
