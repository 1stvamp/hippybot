from jabberbot import botcmd

def directcmd(func):
    def wrapper(self, origin, args):
        message = func(self, origin, args)
        username = unicode(origin.getFrom()).split('/')[1].split(' ')[0].lower()
        return "@%s %s" % (username, message)
    return botcmd(wrapper)
