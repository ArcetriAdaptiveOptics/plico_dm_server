#!/usr/bin/env python
import logging
from plico.utils.kill_process_by_name import killProcessByName
from palpao_server.utils.constants import Constants

__version__= "$Id: palpao_stop.py 27 2018-01-27 08:48:07Z lbusoni $"



def main():
    logging.basicConfig(level=logging.INFO)
    processNames= [Constants.START_PROCESS_NAME,
                   Constants.MIRROR_CONTROLLER_1_PROCESS_NAME,
                   Constants.MIRROR_CONTROLLER_2_PROCESS_NAME,
                   ]

    for each in processNames:
        killProcessByName(each)
