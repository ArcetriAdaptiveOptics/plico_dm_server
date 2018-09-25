#!/usr/bin/env python
import sys
from palpao_server.mirror_controller.runner import Runner
from plico.utils.config_file_manager import ConfigFileManager
from palpao_server.utils.constants import Constants

__version__ = "$Id: palpao_mirror_controller_1.py 30 2018-01-27 10:18:23Z lbusoni $"



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
