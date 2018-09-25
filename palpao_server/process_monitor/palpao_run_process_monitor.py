#!/usr/bin/env python
import sys
from palpao_server.process_monitor.runner import Runner

__version__ = "$Id: palpao_run_process_monitor.py 26 2018-01-26 19:06:25Z lbusoni $"


if __name__ == '__main__':
    runner= Runner()
    sys.exit(runner.start(sys.argv))
