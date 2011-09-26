import os
_CWD = os.path.dirname(__file__)
def get_version_string():
    return open(os.path.join(_CWD, 'version.txt'), 'r').read().strip()

def get_version():
    return get_version_string().split('.')

__version__ = get_version_string()
