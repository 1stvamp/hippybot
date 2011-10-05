from functools import wraps
from jabberbot import botcmd

def directcmd(func):
    @wraps(func)
    def wrapper(self, origin, args):
        message = func(self, origin, args)
        username = unicode(origin.getFrom()).split('/')[1]
        return u'@"%s" %s' % (username, message)
    return botcmd(wrapper)
