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
    def __init__(self, auth_token, name=None, gets=GETS, posts=POSTS,
                base_url=BASE_URL):
        self._auth_token = auth_token
        self._name = name
        self._gets = gets
        self._posts

    def _request(self, method, params={}):
        if 'auth_token' not in params:
            params['auth_token'] = self._auth_token
        url = "%s/%s/%s" % (self._base_url, self._name, method)
        if method in self._gets[self._name]:
            r = requests.get(url, params=params)
        elif method in self._posts[self._name]:
            r = requests.post(url, params=params)
        return json.loads(r.content)

    def __getattr__(self, attr_name):
        if self._name is None:
            return self.__class__(
                auth_token=self._auth_token,
                name=attr_name
            )
        else:
            def wrapper(*args, **kwargs):
                return self._request(attr_name, *args, **kwargs)
            return wrapper
