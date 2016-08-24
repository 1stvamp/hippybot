#!/usr/bin/env python
import codecs
import imp
import logging
import os
import sys
import time
import traceback
from ConfigParser import ConfigParser
from inspect import ismethod, getargspec
from optparse import OptionParser

from jabberbot import botcmd, JabberBot, xmpp
from lazy_reload import lazy_reload

from hippybot.daemon.daemon import Daemon
from hippybot.hipchat import HipChatApi

# List of bot commands that can't be registered, as they would conflict with
# internal HippyBot methods
RESERVED_COMMANDS = (
    'api',
)


class HippyBot(JabberBot):
    """An XMPP/Jabber bot with specific customisations for working with the
    hipchat.com chatroom/IM service.
    """

    _content_commands = {}
    _global_commands = []
    _command_aliases = {}
    _all_msg_handlers = []
    _last_message = ''
    _last_send_time = time.time()
    _restart = False

    def __init__(self, config):
        self._config = config

        prefix = config['connection']['username'].split('_')[0]

        self._channels = []
        for channel in config['connection']['channels'].split('\n'):
            # Only generate an XMPP room name from HipChat name if required
            muc_domain = config['connection'].get('muc_domain',
                                                  'conf.hipchat.com')
            if muc_domain not in channel:
                channel = u"%s_%s@%s" % (
                    prefix,
                    channel.strip().lower().replace(' ', '_'),
                    muc_domain)
            self._channels.append(channel)

        username = u"%s@%s" % (config['connection']['username'],
                               config['connection'].get('host',
                                                        'chat.hipchat.com'))
        # Set this here as JabberBot sets username as private
        self._username = username
        super(HippyBot, self).__init__(
            username=username,
            password=config['connection']['password'])
        # Make sure we don't timeout after 150s
        self.PING_FREQUENCY = 50

        for channel in self._channels:
            self.join_room(channel, config['connection']['nickname'])

        self._at_name = u"@%s " % (
            config['connection']['nickname'].replace(" ", ""),)
        self._at_short_name = u"@%s " % (
            config['connection']['nickname'].split(' ')[0].lower(),)

        plugins = config.get('plugins', {}).get('load', [])
        if plugins:
            plugins = plugins.strip().split('\n')
        self._plugin_modules = plugins
        self._plugins = {}
        load_path = config.get('plugins', {}).get('load_path', [])
        if load_path:
            load_path = load_path.strip().split('\n')
            self._load_path = []
            for path in load_path:
                if path[0:1] != '/':      # this is not an absolute path
                    self._load_path.append('%s/%s' % (os.getcwd(), path))
                else:
                    self._load_path.append(path)

        self.load_plugins()

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
        elif mess.lower().startswith(self._at_name.lower()):
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
        self.log.debug("Message: %s" % mess)
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
                        'a message ("%s") from %s: %s"' % (
                            mess.getType(), mess.getFrom(),
                            traceback.format_exc(e)))

        if u' ' in message:
            cmd = message.split(u' ')[0]
        else:
            cmd = message

        if cmd in self._command_aliases:
            message = u"%s%s" % (
                self._command_aliases[cmd],
                message[len(cmd):])
            cmd = self._command_aliases[cmd]

        ret = None
        if at_msg or cmd in self._global_commands:
            mess.setBody(message)
            ret = super(HippyBot, self).callback_message(conn, mess)
        self._last_message = message
        if ret:
            return ret
        for name in self._content_commands:
            cmd = self._content_commands[name]
            ret = cmd(mess)
            if ret:
                self.send_simple_reply(mess, ret)
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
            pres.setTag(
                'x', namespace=NS_MUC).setTagData('password', password)
        else:
            pres.setTag('x', namespace=NS_MUC)

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

    def rewrite_docstring(self, m):
        if m.__doc__ and m.__doc__.find("@NickName") > -1:
            m.__func__.__doc__ = m.__doc__.replace("@NickName", self._at_name)

    @botcmd(hidden=True)
    def load_plugins(self, mess=None, args=None):
        """Internal handler and bot command to dynamically load and reload
        plugin classes based on the [plugins][load] section of the config and
        with respect of [plugins][load_path] option.
        """
        for path in self._plugin_modules:
            name = path.split('.')[-1]
            if name in self._plugins:
                lazy_reload(self._plugins[name])
            (file, filename, data) = imp.find_module(name, self._load_path)
            if file:
                module = imp.load_module(name, file, filename, data)
            self._plugins[name] = module

            # If the module has a function matching the module/command name,
            # then just use that
            command = getattr(module, name, None)

            funcs = []
            content_funcs = []
            if not command:
                # Otherwise we're looking for a class called Plugin which
                # provides methods decorated with the @botcmd decorator.
                (plugin_args, _, _, _) = getargspec(
                    getattr(module, 'Plugin').__init__)
                if 'config' in plugin_args:
                    print 'Plugin has config parameter'
                    plugin = getattr(module, 'Plugin')(config=self._config)
                else:
                    print 'Plugin has no config parameter'
                    plugin = getattr(module, 'Plugin')()
                plugin.bot = self
                commands = [c for c in dir(plugin)]

                for command in commands:
                    m = getattr(plugin, command)
                    if ismethod(m) and getattr(m, '_jabberbot_command', False):
                        if command in RESERVED_COMMANDS:
                            self.log.error(
                                'Plugin "%s" attempted to register '
                                'reserved command "%s", skipping..' % (
                                    plugin, command
                                    ))
                            continue
                        self.rewrite_docstring(m)
                        name = getattr(m, '_jabberbot_command_name', False)
                        self.log.info("command loaded: %s" % name)
                        funcs.append((name, m))

                    if ismethod(m) and getattr(m, '_jabberbot_content_command',
                                               False):
                        if command in RESERVED_COMMANDS:
                            self.log.error(
                                'Plugin "%s" attempted to register '
                                'reserved command "%s", skipping..' % (
                                    plugin, command
                                    ))
                            continue
                        self.rewrite_docstring(m)
                        name = getattr(m, '_jabberbot_command_name', False)
                        self.log.info("command loaded: %s" % name)
                        content_funcs.append((name, m))

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
            for command, func in content_funcs:
                setattr(self, command, func)
                self._content_commands[command] = func
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
            api_server = self._config.get('hipchat', {}).get(
                'api_server', 'api.hipchat.com')
            if auth_token is None:
                self._api = False
            else:
                self._api = HipChatApi(
                    auth_token=auth_token, api_server=api_server)
        return self._api


class HippyDaemon(Daemon):
    config = None

    def run(self):
        try:
            bot = HippyBot(self.config._sections)
            bot.serve_forever()
        except Exception, e:
            print >> sys.stderr, "ERROR: %s" % (e,)
            print >> sys.stderr, traceback.format_exc()
            return 1
        else:
            return 0


def main():
    parser = OptionParser(usage="""usage: %prog [options]""")

    parser.add_option("-c", "--config", dest="config_path",
                      help="Config file path")
    parser.add_option("-d", "--daemon", dest="daemonise", help="Run as a"
                      " daemon process", action="store_true")
    parser.add_option("-l", '--log', dest='log_level',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='Set logging level')
    parser.add_option("-p", "--pid", dest="pid", help="PID file location if"
                      " running with --daemon")
    (options, pos_args) = parser.parse_args()

    if options.log_level:
        logging.basicConfig(level=getattr(logging, options.log_level))

    if not options.config_path:
        print >> sys.stderr, 'ERROR: Missing config file path'
        return 1

    config = ConfigParser()
    config.readfp(codecs.open(os.path.abspath(options.config_path), "r",
                              "utf8"))

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
