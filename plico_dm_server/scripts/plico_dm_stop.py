#!/usr/bin/env python
import logging
from plico.utils.kill_process_by_name import killProcessByName
from plico_dm_server.utils.constants import Constants

__version__= "$Id: plico_dm_stop.py 27 2018-01-27 08:48:07Z lbusoni $"



def main():
    logging.basicConfig(level=logging.INFO)
    processNames= [Constants.START_PROCESS_NAME,
                   Constants.SERVER_PROCESS_NAME,
                   ]

    for each in processNames:
        killProcessByName(each)
