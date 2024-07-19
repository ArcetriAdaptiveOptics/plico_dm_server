#!/usr/bin/env python
import sys
from plico.utils.process_monitor_runner import ProcessMonitorRunner
from plico_dm_server.utils.constants import Constants

if __name__ == '__main__':
    runner = ProcessMonitorRunner(Constants.SERVER_PROCESS_NAME)
    sys.exit(runner.start(sys.argv))
