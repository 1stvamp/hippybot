import requests
try:
    import simplejson as json
except ImportError:
    import json

GETS = {
    'rooms': (
        'history', 'list', 'show'
    ),
    'users': (
        'list', 'show'
    )
}

POSTS = {
    'rooms': (
        'create', 'delete', 'message'
    ),
    'users': (
        'create', 'delete', 'update'
    )
}

BASE_URL = 'https://api.hipchat.com/v1'

class HipChat(object):
    """Lightweight Hipchat.com REST API wrapper
    """
    def __init__(self, auth_token, name=None):
        self.auth_token = auth_token
        self.name = name

    def _request(self, method, params={}):
        if 'auth_token' not in params:
            params['auth_token'] = self.auth_token
        url = "%s/%s/%s" % (BASE_URL, self.name, method)
        if method in GETS[self.name]:
            r = requests.get(url, params=params)
        elif method in POSTS[self.name]:
            r = requests.post(url, params=params)
        return json.loads(r.content)

    def __getattr__(self, attr_name):
        if self.name is None:
            return self.__class__(
                auth_token=self.auth_token,
                name=attr_name
            )
        else:
            def wrapper(*args, **kwargs):
                return self._request(attr_name, *args, **kwargs)
            return wrapper
