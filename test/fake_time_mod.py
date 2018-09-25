__version__= "$Id: fake_time_mod.py 25 2018-01-26 19:00:40Z lbusoni $"


class FakeTimeMod(object):

    def __init__(self, timeInvocationDurationSec=0.05):
        self._currentTime= 0.0
        self._timeInvocationDurationSec= timeInvocationDurationSec
        self._lastSleepDurationSec= None


    def time(self):
        self._currentTime+= self._timeInvocationDurationSec
        return self._currentTime


    def sleep(self, sleepDurationSec):
        self._lastSleepDurationSec= sleepDurationSec
        self._currentTime+= sleepDurationSec


    def hasSleepBeenInvoked(self):
        return self._lastSleepDurationSec is not None


    def getLastSleepDurationSec(self):
        return self._lastSleepDurationSec
