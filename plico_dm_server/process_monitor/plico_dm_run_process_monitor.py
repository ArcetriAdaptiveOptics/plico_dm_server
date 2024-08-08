#!/usr/bin/env python
import sys
from plico.utils.process_monitor_runner import ProcessMonitorRunner
from plico_dm_server.utils.constants import Constants

if __name__ == '__main__':
    prefix = Constants.DEFAULT_SERVER_CONFIG_SECTION_PREFIX
    runner = ProcessMonitorRunner(Constants.SERVER_PROCESS_NAME,
                                  default_server_config_prefix=prefix)
    sys.exit(runner.start(sys.argv))
