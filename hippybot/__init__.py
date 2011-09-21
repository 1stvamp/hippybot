def get_version_string():
    return open('./version.txt')

def get_version():
    return get_version_string().split('.')

__version__ = get_version_string()
