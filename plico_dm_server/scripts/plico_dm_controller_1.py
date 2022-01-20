#!/usr/bin/env python
import sys
from plico_dm_server.controller.runner import Runner
from plico.utils.config_file_manager import ConfigFileManager
from plico_dm_server.utils.constants import Constants

__version__ = "$Id: plico_dm_controller_1.py 30 2018-01-27 10:18:23Z lbusoni $"



def main():
    runner= Runner()
    configFileManager= ConfigFileManager(Constants.APP_NAME,
                                         Constants.APP_AUTHOR,
                                         Constants.THIS_PACKAGE)
    configFileManager.installConfigFileFromPackage()
    argv= ['', configFileManager.getConfigFilePath(),
           Constants.DEFORMABLE_MIRROR_1_CONFIG_SECTION]
    sys.exit(runner.start(argv))


if __name__ == '__main__':
    main()
