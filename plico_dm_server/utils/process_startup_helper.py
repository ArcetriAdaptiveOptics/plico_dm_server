import os



class ProcessStartUpHelper(object):

    def __init__(self):
        self._moduleRoot= 'plico_dm_server'


    def deformableMirrorStartUpScriptPath(self):
        return os.path.join(self._moduleRoot,
                            'controller',
                            'plico_dm_run_controller.py')


    def killAllProcessesStartUpScriptPath(self):
        return os.path.join(self._moduleRoot,
                            'utils',
                            'plico_dm_kill_processes.py')


    def processProcessMonitorStartUpScriptPath(self):
        return os.path.join(self._moduleRoot,
                            'process_monitor',
                            'plico_dm_run_process_monitor.py')


    def processProcessMonitorStopScriptPath(self):
        return os.path.join(self._moduleRoot,
                            'utils',
                            'plico_dm_server_stop.py')
