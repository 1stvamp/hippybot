Introduction
============

HippyBot is a Hipchat.com chatroom bot written in Python. It is technically just a Jabber/XMPP bot, but it has customised features for connecting to and working on Hipchat.

HippyBot includes a simple plugin API for adding commands.

Installation
============

There a few ways you can install Hippybot:

Download and install with ``setup.py``::

    python setup.py install

Install from PyPi::

    easyy_install hippybot
    # or using pip
    pip install hippybot

Configuration
=============

There is an example configuration file distrubed with HippyBot called ``hippybot.conf.example``, copy this and edit it. You will need to add an account to your Hipchat group for the bot to connect as. While logged in as the account go to the XMPP_ settings page to get the details you'll need to edit the config file.

Usage
=====

Run HippyBot from a terminal like so::

    hippybot -c path/to/your/config/file.conf

Note: this won't daemonize the bot, to do this at present (although an inbuilt daemon mode **is on** the todo list) you'll need to backkground it either using the usual unix way (``hippybot -c configpath 2>&1 >> /var/logs/hippybot.log &``) or a daemonizer/event controller such as Canonical's ``upstart``. Another way is also to run the bot as normal within a ``screen`` session, if you do this I'd suggest using a util like ``tee`` to make sure a log file is still kept.

You should see the bot join any channels listed in the config file. You can then target the bot with commands using the at-sign notation, e.g.::

    @botname rot13 hello world

If you have the ``rot13`` example plugin set to load (via the plugins section of the config file) then the bot will reply to you using at-sign notation with a ROT13'd (each character offset by 13) version of the text "hello world".

The bot has 2 inbuilt commands:

 * ``load_plugins``: this will reload any updated plugins (note it will also reset the internal state of any loaded plugins, e.g. the counter in the *mexican wave* plugin). Note it **does not** reload the bot's configuration file and so will not load new plugins.
 * ``reload``: this will reload the bot itself, reloading the configuration file, reconnecting to HipChat and reloading any plugins, in the process. Note: it does not end the main process, you would have to do that yourself from the terminal (for example if HippyBot were updated).

Plugins
=======

There are 2 plugins currently distributed with HippyBot:

 * ``rot13``: this is mostly included as an example, it ROT13s, any text spoken directly to the bot, back at the speaker.
 * ``mexican wave``: this is a fun plugin that completes a mexican wave if 2 people in a row say ``\o/`` in a channel, e.g.::

    John Smith: \o/
    Joe Bloggs: \o/
    Hippy Bot:  \o/

Plugin API
==========

HippyBot includes a very simple plugin API. To add commands to HippyBot you just need an importable Python package (e.g. a directory in the ``PYTHON_PATH`` that includes a file named ``__init__.py``), and place your plugin in it's own Python file (the ROT13 plugin lives in ``rot13.py``).

You then can include a function that matches the same name as the file and is the same command you want to register, and use either the ``botcmd`` or ``directcmd`` decorators::

   # hello_world.py
   from hippybot.decorators import directcmd

   @directcmd
   def hello_world(bot, mess, args):
       return u'Hello world!'

This registers the command ``hello world`` as a direct command, that means the text "Hello world!" will be directly spoken back to the user using at-sign notation. The ``botcmd`` decorator on the other hand will respond in the channel without targetting the original speaker.
By default these function based plugins only support direct commands (spoken to the bot using at-sign notation), however you can create more complex plugins with greater control using class based plugins.

To create class based plugins create the Python module as normal, with any descriptive name you want, and include a class named ``Plugin`` in the module, for example the hello world plugin can be written like::

    # hello_world.py
    from hippybot.decorators import botcmd, directcmd

    class Plugin(object):
        global_commands = ['hello_world']
        command_aliases = {'hi!': 'hello'}
        
        @botcmd
        def hello_world(self, mess, args):
            return u'Hello world!'
        
        @directcmd
        def hello(self, mess, args):
            return u'Well hello there..'

This uses 2 special properties:

 * ``global_commands``: a list of command *method names* that can be triggered without targetting the bot using at-sign notation (just say the command in the channel without mentioning the bot).
 * ``command_aliases``: dict of command aliases and the methods they map to, this is a way of triggering a command from a string that can't be used as a Python method name (e.g. using special symbols such as the "\o/" trigger used in the *mexican wave* plugin).
