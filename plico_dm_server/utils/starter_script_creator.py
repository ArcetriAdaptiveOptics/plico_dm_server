import os
from plico_dm_server.utils.constants import Constants
from plico_dm_server.utils.process_startup_helper import ProcessStartUpHelper
from plico.utils.starter_script_creator_base import StarterScriptCreatorBase


class StarterScriptCreator(StarterScriptCreatorBase):

    def __init__(self):
        StarterScriptCreatorBase.__init__(self)

    def installExecutables(self):
        psh = ProcessStartUpHelper()

        self._createAStarterScript(
            os.path.join(self._binDir, Constants.START_PROCESS_NAME),
            psh.processProcessMonitorStartUpScriptPath(),
            Constants.PROCESS_MONITOR_CONFIG_SECTION
        )
        self._createAStarterScript(
            os.path.join(self._binDir, Constants.SERVER_PROCESS_NAME),
            psh.controllerStartUpScriptPath(),
            '$2'  # Section name is a bash parameter
        )
        self._createAStarterScript(
            os.path.join(self._binDir, Constants.KILL_ALL_PROCESS_NAME),
            psh.killAllProcessesStartUpScriptPath(),
            'foo'
        )
        self._createAStarterScript(
            os.path.join(self._binDir, Constants.STOP_PROCESS_NAME),
            psh.processProcessMonitorStopScriptPath(),
            'not used'
        )

