#!/usr/bin/env python
import os
import sys
import codecs
import time
from jabberbot import botcmd, JabberBot, xmpp
from ConfigParser import ConfigParser
from optparse import OptionParser
from inspect import ismethod
from lazy_reload import lazy_reload

from hippybot.hipchat import HipChatApi
from hippybot.daemon.daemon import Daemon

# List of bot commands that can't be registered, as they would conflict with
# internal HippyBot methods
RESERVED_COMMANDS = (
    'api',
)

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
    _all_msg_handlers = []
    _last_message = ''
    _last_send_time = time.time()
    _restart = False

    def __init__(self, config):
        self._config = config

        prefix = config['connection']['username'].split('_')[0]
        self._channels = [u"%s_%s@%s" % (prefix, c.strip().lower().replace(' ',
                '_'), 'conf.hipchat.com') for c in
                config['connection']['channels'].split('\n')]

        username = u"%s@chat.hipchat.com" % (config['connection']['username'],)
        # Set this here as JabberBot sets username as private
        self._username = username
        super(HippyBot, self).__init__(username=username,
                                        password=config['connection']['password'])
        # Make sure we don't timeout after 150s
        self.PING_FREQUENCY = 50

        for channel in self._channels:
            self.join_room(channel, config['connection']['nickname'])

        plugins = config.get('plugins', {}).get('load', [])
        if plugins:
            plugins = plugins.strip().split('\n')
        self._plugin_modules = plugins
        self._plugins = {}

        self.load_plugins()

        self._at_name = u'@"%s" ' % (config['connection']['nickname'],)
        self._at_short_name = u"@%s " % (config['connection']['nickname']
                                        .split(' ')[0].lower(),)

    def from_bot(self, mess):
        """Helper method to test if a message was sent from this bot.
        """
        if unicode(mess.getFrom()).endswith("/%s" % (
                        self._config['connection']['nickname'],)):
            return True
        else:
            return False

    def to_bot(self, mess):
        """Helper method to test if a message was directed at this bot.
        Returns a tuple of a flag set to True if the message was to the bot,
        and the message strip without the "at" part.
        """
        respond_to_all = self._config.get('hipchat', {}).get(
            'respond_to_all', False
            )
        to = True
        if (respond_to_all and mess.startswith('@all ')):
            mess = mess[5:]
        elif mess.startswith(self._at_short_name):
            mess = mess[len(self._at_short_name):]
        elif mess.startswith(self._at_name):
            mess = mess[len(self._at_name):]
        else:
            to = False
        return to, mess

    def send_message(self, mess):
        """Send an XMPP message
        Overridden from jabberbot to update _last_send_time
        """
        self._last_send_time = time.time()
        self.connect().send(mess)

    def callback_message(self, conn, mess):
        """Message handler, this is where we route messages and transform
        direct messages and message aliases into the command that will be
        matched by JabberBot.callback_message() to a registered command.
        """
        message = unicode(mess.getBody()).strip()
        if not message:
            return

        at_msg, message = self.to_bot(message)

        if len(self._all_msg_handlers) > 0:
            for handler in self._all_msg_handlers:
                try:
                    handler(mess)
                except Exception, e:
                    self.log.exception(
                            'An error happened while processing '
                            'a message ("%s") from %s: %s"' %
                            (mess.getType(), mess.getFrom(),
                                traceback.format_exc(e)))

        if u' ' in message:
            cmd = message.split(u' ')[0]
        else:
            cmd = ''

        if cmd in self._command_aliases:
            message = u"%s%s" % (self._command_aliases[cmd],
                                message[len(cmd):])
            cmd = self._command_aliases[cmd]

        ret = None
        if at_msg or cmd in self._global_commands:
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
        my_room_JID = u'/'.join((room, username))
        pres = xmpp.Presence(to=my_room_JID)
        if password is not None:
            pres.setTag('x',namespace=NS_MUC).setTagData('password',password)
        else:
            pres.setTag('x',namespace=NS_MUC)

        # Don't pull the history back from the server on joining channel
        pres.getTag('x').addChild('history', {'maxchars': '0',
                                                'maxstanzas': '0'})
        self.connect().send(pres)

    def _idle_ping(self):
        """Pings the server, calls on_ping_timeout() on no response.

        To enable set self.PING_FREQUENCY to a value higher than zero.

        Overridden from jabberbot in order to send a single space message
        to HipChat, as XMPP ping doesn't seem to cut it.
        """
        if self.PING_FREQUENCY \
            and time.time() - self._last_send_time > self.PING_FREQUENCY:
            self._last_send_time = time.time()
            self.send_message(' ')

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
                        if command in RESERVED_COMMANDS:
                            self.log.error('Plugin "%s" attempted to register '
                                        'reserved command "%s", skipping..' % (
                                            plugin, command
                                        ))
                            continue
                        funcs.append((command, m))

                # Check for commands that don't need to be directed at
                # hippybot, e.g. they can just be said in the channel
                self._global_commands.extend(getattr(plugin,
                                                'global_commands', []))
                # Check for "special commands", e.g. those that can't be
                # represented in a python method name
                self._command_aliases.update(getattr(plugin,
                                                'command_aliases', {}))

                # Check for handlers for all XMPP message types,
                # this can be used for low-level checking of XMPP messages
                self._all_msg_handlers.extend(getattr(plugin,
                                                'all_msg_handlers', []))
            else:
                funcs = [(name, command)]

            for command, func in funcs:
                setattr(self, command, func)
                self.commands[command] = func
        if mess:
            return 'Reloading plugin modules and classes..'

    _api = None
    @property
    def api(self):
        """Accessor for lazy-loaded HipChatApi instance
        """
        if self._api is None:
            auth_token = self._config.get('hipchat', {}).get(
                'api_auth_token', None)
            if auth_token is None:
                self._api = False
            else:
                self._api = HipChatApi(auth_token=auth_token)
        return self._api

class HippyDaemon(Daemon):
    config = None
    def run(self):
        try:
            bot = HippyBot(self.config._sections)
            bot.serve_forever()
        except Exception, e:
            print >> sys.stderr, "ERROR: %s" % (e,)
            return 1
        else:
            return 0

def main():
    import logging
    logging.basicConfig()

    parser = OptionParser(usage="""usage: %prog [options]""")

    parser.add_option("-c", "--config", dest="config_path", help="Config file path")
    parser.add_option("-d", "--daemon", dest="daemonise", help="Run as a"
            " daemon process", action="store_true")
    parser.add_option("-p", "--pid", dest="pid", help="PID file location if"
            " running with --daemon")
    (options, pos_args) = parser.parse_args()

    if not options.config_path:
        print >> sys.stderr, 'ERROR: Missing config file path'
        return 1

    config = ConfigParser()
    config.readfp(codecs.open(os.path.abspath(options.config_path), "r", "utf8"))

    pid = options.pid
    if not pid:
        pid = os.path.abspath(os.path.join(os.path.dirname(
            options.config_path), 'hippybot.pid'))

    runner = HippyDaemon(pid)
    runner.config = config
    if options.daemonise:
        ret = runner.start()
        if ret is None:
            return 0
        else:
            return ret
    else:
        return runner.run()

if __name__ == '__main__':
    sys.exit(main())
