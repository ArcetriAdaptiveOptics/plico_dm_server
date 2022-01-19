#!/usr/bin/env python
import sys
from plico_dm_server.controller.runner import Runner

__version__ = "$Id: plico_dm_run_controller.py 25 2018-01-26 19:00:40Z lbusoni $"



def main():
    runner= Runner()
    sys.exit(runner.start(sys.argv))

if __name__ == '__main__':
    main()
