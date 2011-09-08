from hippybot.decorators import directcmd

class Plugin(object):
    """Plugin to return passed arguments rot13'ed, @'d to the originating user.
    """
    @directcmd
    def rot13(self, mess, args):
        return args.encode('rot13')
