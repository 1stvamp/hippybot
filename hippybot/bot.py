#!/usr/bin/env python
import os
import sys
from jabberbot import JabberBot, botcmd
from configparser import ConfigParser
from optparse import OptionParser

class HippyBot(JabberBot):
    pass

def main():
    parser = OptionParser(usage="""usage: %prog [options]""")

    parser.add_option("-c", "--config", dest="confing_path", help="Config file path")
    (options, pos_args) = parser.parse_args()

    if not options.config_path:
        print >> sys.stderr, 'Missing config file path'
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
