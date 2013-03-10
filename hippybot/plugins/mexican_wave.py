from collections import Counter
from hippybot.decorators import botcmd

class Plugin(object):
    """HippyBot plugin to make the bot complete a mexican wave if 2 people in a
    row do the action "\o/".
    """
    global_commands = ['\o/', 'wave']
    command_aliases = {'\o/': 'wave'}
    counts = Counter()
    @botcmd
    def mexican_wave(self, mess, args):
        channel = unicode(mess.getFrom()).split('/')[0]
        self.bot.log.info("\o/ %s" %self.counts[channel])

        if not self.bot.from_bot(mess):
            self.counts[channel] += 1
            if self.counts[channel] == 2:
                self.counts[channel] = 0
                return r'\o/'
