#!/usr/bin/env python
import sys
from plico_dm_server.controller.runner import Runner


def main():
    runner = Runner()
    sys.exit(runner.start(sys.argv))


if __name__ == '__main__':
    main()
