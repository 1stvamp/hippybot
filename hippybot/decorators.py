from functools import wraps
from jabberbot import botcmd

def directcmd(func):
    @wraps(func)
    def wrapper(self, origin, args):
        message = func(self, origin, args)
        username = unicode(origin.getFrom()).split('/')[1].replace(" ","")
        return u'@%s %s' % (username, message)
    return botcmd(wrapper)

def contentcmd(*args, **kwargs):
    """Decorator for bot commentary"""

    def decorate(func, name=None):
        setattr(func, '_jabberbot_content_command', True)
        setattr(func, '_jabberbot_command_name', name or func.__name__)
        return func

    if len(args):
        return decorate(args[0], **kwargs)
    else:
        return lambda func: decorate(func, **kwargs)
