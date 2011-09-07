from jabberbot import botcmd

class Plugin(object):
    @botcmd
    def rot13(self, mess, args):
        """Returns passed arguments rot13'ed"""
        return args.encode('rot13')
