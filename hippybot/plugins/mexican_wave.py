from jabberbot import botcmd

class Plugin(object):
    """HippyBot plugin to make the bot complete a mexican wave if 2 people in a
    row do the action "\o/".
    """
    global_commands = ['mexican_wave']
    command_aliases = {r'\o/': 'mexican_wave'}
    count = 0
    @botcmd
    def mexican_wave(self, mess, args):
        if self.bot._last_message.strip() != 'mexican_wave':
            self.count = 0
        if not unicode(mess.getFrom()).endswith("/%s" % (
                            self.bot._config['connection']['nickname'],)):
            self.count += 1
            if self.count == 2:
                self.count = 0
                return r'\o/'
