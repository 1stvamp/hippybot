from hippybot.decorators import botcmd

class Plugin(object):
    """HippyBot plugin to make the bot complete a mexican wave if 2 people in a
    row do the action "\o/".
    """
    global_commands = ['mexican_wave']
    command_aliases = {r'\o/': 'mexican_wave'}
    counts = {}
    @botcmd
    def mexican_wave(self, mess, args):
        channel = unicode(mess.getFrom()).split('/')[0]

        if channel not in self.counts:
            self.counts[channel] = 0

        if self.bot._last_message.strip() != 'mexican_wave':
            self.counts[channel] = 0

        if not self.bot.from_bot(mess):
            self.counts[channel] += 1

            if self.counts[channel] == 2:
                self.counts[channel] = 0
                return r'\o/'
