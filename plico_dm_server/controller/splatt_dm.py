import numpy as np

import matlab.engine

from plico.utils.decorator import override, cacheResult
from plico.utils.logger import Logger
from plico_dm_server.controller.abstract_deformable_mirror import \
    AbstractDeformableMirror


class MatlabEngine(object):

    def __init__(self, working_dir, open_desktop=False):
        self.eng = matlab.engine.start_matlab()
        if open_desktop:
            self.eng.desktop(nargout=0)
        self.eng.cd(working_dir)

    def send_command(self,command):
        self.eng.eval(str(command)+';', nargout=0)

    def get_data(self,command_to_read_data):
        data = np.array(self.eng.eval(str(command_to_read_data)+';',nargout=1))
        return data

    def stop_engine(self):
        self.eng.quit()



class SPLATTError(Exception):
    pass



class SPLATTDeformableMirror(AbstractDeformableMirror):


    def __init__(self):
        self._eng = MatlabEngine(r'/home/labot/SPLATT_SW/Matlab_2024/Matlab/Scripts', True)
        self._logger= Logger.of('ALPAO Deformable Mirror')
        print('starting')
        self._eng.send_command('splattInit')
        print('init done')
        self._eng.send_command('splattStartup')
        print('startup done')
        self._shellset = False

    def set_shell(self):
        self._eng.send_command('splattSet')
        print('set done')
        self._shellset = True

    def get_capsens(self):
        return self._eng.get_data('lattGetPos()')

    def isReady(self):
        return self._shellset

    def send_matlab_command(self, cmd):
        return self._eng.send_command(cmd)

    def get_matlab_data(self, cmd):
        return self._eng.get_data(cmd)

    @override
    def setZonalCommand(self, zonalCommand):
        if not self._shellset:
            raise SPLATTError( "Shell is not set")
        if len(zonalCommand) != self.getNumberOfActuators():
            raise SPLATTError(
                "Wrong size for zonalCommand (size is "
                "%d instead of %d") % (
                    len(zonalCommand), self.getNumberOfActuators())
        self._eng.send_command('dsmMirrorCommand(%s)' % zonalCommand)
        self._lastZonalCommand= zonalCommand

    @override
    def getZonalCommand(self):
        return self._lastZonalCommand

    @override
    def serialNumber(self):
        '''SPLATT has on real serial number'''
        return 1

    @override
    @cacheResult
    def getNumberOfActuators(self):
        return int(self._eng.get_data('sys_data.mirrNAct'))

    @override
    def deinitialize(self):
        raise NotImplementedError

