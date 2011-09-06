#!/usr/bin/env python
import os
import sys
from jabberbot import botcmd, JabberBot, xmpp
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
        self.mention_test = "@%s " % (config['connection']['nickname']
                                        .split(' ')[0].lower(),)

    def callback_message(self, conn, mess):
        message = mess.getBody()
        if not message:
            return
        if message.lstrip().startswith(self.mention_test):
            print message

    def join_room(self, room, username=None, password=None):
        """Join the specified multi-user chat room

        If username is NOT provided fallback to node part of JID"""
        # TODO fix namespacestrings and history settings
        NS_MUC = 'http://jabber.org/protocol/muc'
        if username is None:
            # TODO use xmpppy function getNode
            username = self.__username.split('@')[0]
        my_room_JID = '/'.join((room, username))
        pres = xmpp.Presence(to=my_room_JID)
        if password is not None:
            pres.setTag('x',namespace=NS_MUC).setTagData('password',password)
        else:
            pres.setTag('x',namespace=NS_MUC)
        # Don't pull the history back from the server on joining channel
        pres.getTag('x').addChild('history', {'maxchars': '0',
                                                'maxstanzas': '0'})
        self.connect().send(pres)

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
