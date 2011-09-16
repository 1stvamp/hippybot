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
    """Helper function to import a module given it's full path and return the
    module object.
    """
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

class HippyBot(JabberBot):
    """An XMPP/Jabber bot with specific customisations for working with the
    hipchat.com chatroom/IM service.
    """

    _global_commands = []
    _command_aliases = {}
    _last_message = ''
    _restart = False
    # Make sure we don't timeout after 150s
    PING_FREQUENCY = 60

    def __init__(self, config):
        self._config = config

        prefix = config['connection']['username'].split('_')[0]
        self._channels = ["%s_%s@%s" % (prefix, c.strip().lower().replace(' ',
                '_'), 'conf.hipchat.com') for c in
                config['connection']['channels'].split('\n')]

        username = "%s@chat.hipchat.com" % (config['connection']['username'],)
        # Set this here as JabberBot sets username as private
        self._username = username
        super(HippyBot, self).__init__(username=username,
                                        password=config['connection']['password'])

        for channel in self._channels:
            self.join_room(channel, config['connection']['nickname'])

        plugins = config.get('plugins', {}).get('load', [])
        if plugins:
            plugins = plugins.strip().split('\n')
        self._plugin_modules = plugins
        self._plugins = {}

        self.load_plugins()

        self._mention_test = "@%s " % (config['connection']['nickname']
                                        .split(' ')[0].lower(),)

    def from_bot(self, mess):
        """Helper method to test if a message was sent from this bot.
        """
        if unicode(mess.getFrom()).endswith("/%s" % (
                        self._config['connection']['nickname'],)):
            return True
        else:
            return False

    def callback_message(self, conn, mess):
        """Message handler, this is where we route messages and transform
        direct messages and message aliases into the command that will be
        matched by JabberBot.callback_message() to a registered command.
        """
        message = mess.getBody().strip()
        if not message:
            return

        direct_msg = False
        if message.startswith(self._mention_test):
            message = message[len(self._mention_test):]
            direct_msg = True

        cmd = message.split(' ')[0]
        if cmd in self._command_aliases:
            message = "%s%s" % (self._command_aliases[cmd], message[len(cmd):])
            cmd = self._command_aliases[cmd]

        ret = None
        if direct_msg or cmd in self._global_commands:
            mess.setBody(message)
            ret = super(HippyBot, self).callback_message(conn, mess)
        self._last_message = message
        if ret:
            return ret

    def join_room(self, room, username=None, password=None):
        """Overridden from JabberBot to provide history limiting.
        """
        NS_MUC = 'http://jabber.org/protocol/muc'
        if username is None:
            username = self._username.split('@')[0]
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
        """Internal handler and bot command to dynamically load and reload
        plugin classes based on the [plugins][load] section of the config.
        """
        for path in self._plugin_modules:
            name = path.split('.')[-1]
            if name in self._plugins:
                lazy_reload(self._plugins[name])
            module = do_import(path)
            self._plugins[name] = module

            # If the module has a function matching the module/command name,
            # then just use that
            command = getattr(module, name, None)

            if not command:
                # Otherwise we're looking for a class called Plugin which
                # provides methods decorated with the @botcmd decorator.
                plugin = getattr(module, 'Plugin')()
                plugin.bot = self
                commands = [c for c in dir(plugin)]
                funcs = []

                for command in commands:
                    m = getattr(plugin, command)
                    if ismethod(m) and getattr(m, '_jabberbot_command', False):
                        funcs.append((command, m))

                # Check for commands that don't need to be directed at
                # hippybot, e.g. they can just be said in the channel
                self._global_commands.extend(getattr(plugin,
                                                'global_commands', []))
                # Check for "special commands", e.g. those that can be
                # represented in a python method name
                self._command_aliases.update(getattr(plugin,
                                                'command_aliases', {}))
            else:
                funcs = [(name, command)]

            for command, func in funcs:
                setattr(self, command, func)
                self.commands[command] = func
        if mess:
            return 'Reloading plugin modules and classes..'

    @botcmd
    def restart(self, mess, args):
        """Command to restart the bot, reloading the config file in the
        process. Only works if the runner (see the main() function in this
        module) calling HippyBot handles the RestartBot exception.
        """
        self._restart = True
        self.quit()

    def shutdown(self):
        """If called after the `restart` command raises the RestartBot
        exception to trigger a re-init of the bot config and bot instance.
        """
        if self._restart:
            raise RestartBot

class RestartBot(Exception):
    """Interrupt to signal the bot should be restarted by it's runner
    function/class.
    """
    pass

def main():
    parser = OptionParser(usage="""usage: %prog [options]""")

    parser.add_option("-c", "--config", dest="config_path", help="Config file path")
    (options, pos_args) = parser.parse_args()

    if not options.config_path:
        print >> sys.stderr, 'ERROR: Missing config file path'
        return 1

    while True:
        config = ConfigParser()
        config.read(os.path.abspath(options.config_path))
        try:
            bot = HippyBot(config._sections)
            bot.serve_forever()
        except RestartBot:
            continue
        except IndexError, e:
            print >> sys.stderr, "ERROR: %s" % (e,)
            return 1
        else:
            return 0

if __name__ == '__main__':
    sys.exit(main())
