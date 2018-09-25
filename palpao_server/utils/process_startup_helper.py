import os



class ProcessStartUpHelper(object):

    def __init__(self):
        self._moduleRoot= 'palpao_server'


    def deformableMirrorStartUpScriptPath(self):
        return os.path.join(self._moduleRoot,
                            'mirror_controller',
                            'palpao_run_mirror_controller.py')


    def killAllProcessesStartUpScriptPath(self):
        return os.path.join(self._moduleRoot,
                            'utils',
                            'palpao_kill_processes.py')


    def processProcessMonitorStartUpScriptPath(self):
        return os.path.join(self._moduleRoot,
                            'process_monitor',
                            'palpao_run_process_monitor.py')


    def processProcessMonitorStopScriptPath(self):
        return os.path.join(self._moduleRoot,
                            'utils',
                            'palpao_server_stop.py')
