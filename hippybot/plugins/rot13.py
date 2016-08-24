from hippybot.decorators import directcmd

class Plugin(object):
    """Plugin to return passed arguments rot13'ed, @'d to the originating user.
    """
    global_commands = ['rot13']
    command_aliases = {
        'rot': 'rot13',
        'r': 'rot13'
    }

    def __init__(self, config):
        pass

    @directcmd
    def rot13(self, mess, args):
        """
        ROT13 the message
        Format: @NickName rot13 <message>
        """
        self.bot.log.info("rot13: %s" % mess)
        return args.encode('rot13')
