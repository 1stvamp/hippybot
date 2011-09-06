#!/usr/bin/env python
import os
import sys
from jabberbot import botcmd, JabberBot
from ConfigParser import ConfigParser
from optparse import OptionParser

class HippyBot(JabberBot):
    channels = []
    def __init__(self, config):
        self.config = config
        prefix = config['connection']['username'].split('_')[0]
        self.channels = ["%s_%s@%s" % (prefix, c.strip(), 'conf.hipchat.com')
                for c in config['connection']['channels'].split('\n')]
        username = "%s@chat.hipchat.com" % (config['connection']['username'],)
        super(HippyBot, self).__init__(username=username,
                                        password=config['connection']['password'])
        for channel in self.channels:
            self.join_room(channel, config['connection']['nickname'])

def main():
    parser = OptionParser(usage="""usage: %prog [options]""")

    parser.add_option("-c", "--config", dest="config_path", help="Config file path")
    (options, pos_args) = parser.parse_args()

    if not options.config_path:
        print >> sys.stderr, 'ERROR: Missing config file path'
        return 1

    config = ConfigParser()
    config.read(options.config_path)
    bot = HippyBot(config._sections)
    bot.serve_forever()
    return 0

if __name__ == '__main__':
    sys.exit(main())
