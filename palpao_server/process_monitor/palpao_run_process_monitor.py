#!/usr/bin/env python
import sys
from palpao_server.process_monitor.runner import Runner



if __name__ == '__main__':
    runner= Runner()
    sys.exit(runner.start(sys.argv))
