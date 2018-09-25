#!/usr/bin/env python

import time
import sys
import signal
import os
import subprocess
import psutil
from plico.utils.base_runner import BaseRunner
from plico.utils.decorator import override
from plico.utils.logger import Logger
from palpao_server.utils.constants import Constants
from palpao_server.utils.process_startup_helper import ProcessStartUpHelper



class Runner(BaseRunner):

    RUNNING_MESSAGE = "Monitor of processes is running."

    def __init__(self):
        BaseRunner.__init__(self)

        self._logger= None
        self._processes= []
        self._timeToDie= False
        self._psh= ProcessStartUpHelper()


    def _determineInstalledBinaryDir(self):
        try:
            self._binFolder= self._configuration.getValue(
                Constants.PROCESS_MONITOR_CONFIG_SECTION,
                'binaries_installation_directory')
        except KeyError:
            self._binFolder= None


    def _logRunning(self):
        self._logger.notice(self.RUNNING_MESSAGE)
        sys.stdout.flush()


    def _setSignalIntHandler(self):
        signal.signal(signal.SIGINT, self._signalHandling)


    def _signalHandling(self, signalNumber, stackFrame):
        self._logger.notice("Received signal %d (%s)" %
                            (signalNumber, str(stackFrame)))
        if signalNumber == signal.SIGINT:
            self._timeToDie= True


    def _terminateAll(self):
        self._logger.notice("Terminating all subprocesses using psutil")
        self._logger.notice("My pid %d" % os.getpid())
        parent= psutil.Process(os.getpid())
        for process in parent.children(recursive=True):
            try:
                self._logger.notice(
                    "Killing pid %d %s" % (process.pid, process.cmdline()))
                process.send_signal(signal.SIGTERM)
            except Exception as e:
                self._logger.error("Failed killing process %s: %s" %
                                   (str(process), str(e)))


    def _spawnMirrorController(self, name):
        if self._binFolder:
            cmd= [os.path.join(self._binFolder, name)]
        else:
            cmd= [name]
        self._logger.notice("MirrorController cmd is %s" % cmd)
        mirrorController= subprocess.Popen(cmd)
        self._processes.append(mirrorController)
        return mirrorController


    def _setup(self):
        self._logger= Logger.of("Palpao process monitor runner")
        self._setSignalIntHandler()
        self._logger.notice("Creating process Mirror Controller")
        self._determineInstalledBinaryDir()
        self._mirrorController1= self._spawnMirrorController(
            Constants.MIRROR_CONTROLLER_1_PROCESS_NAME)
        self._mirrorController2= self._spawnMirrorController(
            Constants.MIRROR_CONTROLLER_2_PROCESS_NAME)


    def _runLoop(self):
        self._logRunning()
        while self._timeToDie is False:
            time.sleep(1)
        self._terminateAll()



    @override
    def run(self):
        self._setup()
        self._runLoop()
        return os.EX_OK
