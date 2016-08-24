from collections import Counter
from hippybot.decorators import botcmd

class Plugin(object):
    """HippyBot plugin to make the bot complete a wave if 3 people in a
    row do the action "\o/".
    """
    global_commands = ['\o/', 'wave']
    command_aliases = {'\o/': 'wave'}
    counts = Counter()

    def __init__(self, config):
        pass

    @botcmd
    def wave(self, mess, args):
        """
        If enough people \o/, techbot will too.
        Everyone loves a follower, well, techbot is here to fulfill that need
        """
        channel = unicode(mess.getFrom()).split('/')[0]
        self.bot.log.info("\o/ %s" %self.counts[channel])

        if not self.bot.from_bot(mess):
            self.counts[channel] += 1
            if self.counts[channel] == 3:
                self.counts[channel] = 0
                return r'\o/'
