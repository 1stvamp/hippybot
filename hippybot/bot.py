#!/usr/bin/env python
import os
import sys
from jabberbot import botcmd, JabberBot, xmpp
from ConfigParser import ConfigParser
from optparse import OptionParser
from inspect import ismethod
from lazy_reload import lazy_reload

import logging
logging.basicConfig()

def do_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

class HippyBot(JabberBot):
    def __init__(self, config):
        self.config = config

        # Make sure we don't timeout after 150s
        self.PING_FREQUENCY = 60

        prefix = config['connection']['username'].split('_')[0]
        self.channels = ["%s_%s@%s" % (prefix, c.strip(), 'conf.hipchat.com')
                for c in config['connection']['channels'].split('\n')]

        username = "%s@chat.hipchat.com" % (config['connection']['username'],)
        super(HippyBot, self).__init__(username=username,
                                        password=config['connection']['password'])

        for channel in self.channels:
            self.join_room(channel, config['connection']['nickname'])

        plugins = config.get('plugins', {}).get('load', [])
        if plugins:
            plugins = plugins.strip().split('\n')
        self.plugin_modules = plugins
        self.plugins = {}

        self.load_plugins()

        self.mention_test = "@%s " % (config['connection']['nickname']
                                        .split(' ')[0].lower(),)

    def callback_message(self, conn, mess):
        message = mess.getBody().strip()
        if not message:
            return

        if message.startswith(self.mention_test):
            mess.setBody(message[len(self.mention_test):])
            return super(HippyBot, self).callback_message(conn, mess)

    def join_room(self, room, username=None, password=None):
        """Overridden from JabberBot to provide history limiting.
        """
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

    @botcmd
    def load_plugins(self, mess=None, args=None):
        for path in self.plugin_modules:
            name = path.split('.')[-1]
            if name in self.plugins:
                lazy_reload(self.plugins[name])
            module = do_import(path)
            self.plugins[name] = module

            command = getattr(module, name, None)
            if not command:
                plugin = getattr(module, 'Plugin')()
                plugin.bot = self
                commands = [c for c in dir(plugin)]
                funcs = []
                for command in commands:
                    m = getattr(plugin, command)
                    if ismethod(m) and getattr(m, '_jabberbot_command', False):
                        funcs.append((command, m))
            else:
                funcs = [(name, command)]

            for command, func in funcs:
                setattr(self, command, func)
                self.commands[command] = func
        if mess:
            return 'Reloading plugin modules and classes..'

def main():
    parser = OptionParser(usage="""usage: %prog [options]""")

    parser.add_option("-c", "--config", dest="config_path", help="Config file path")
    (options, pos_args) = parser.parse_args()

    if not options.config_path:
        print >> sys.stderr, 'ERROR: Missing config file path'
        return 1

    config = ConfigParser()
    config.read(options.config_path)
    try:
        bot = HippyBot(config._sections)
        bot.serve_forever()
    except IndexError, e:
        print >> sys.stderr, "ERROR: %s" % (e,)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
