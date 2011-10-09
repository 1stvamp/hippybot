"""Installer for hippybot
"""

import os
cwd = os.path.dirname(__file__)
__version__ = open(os.path.join(cwd, 'hippybot', 'version.txt'), 'r').read().strip()

try:
        from setuptools import setup, find_packages
except ImportError:
        from ez_setup import use_setuptools
        use_setuptools()
        from setuptools import setup, find_packages
setup(
    name='hippybot',
    description='Python Hipchat bot',
    long_description=open('README.rst').read(),
    version=__version__,
    author='Wes Mason',
    author_email='wes[at]1stvamp[dot]org',
    url='http://github.com/1stvamp/hippybot',
    packages=find_packages(exclude=['ez_setup']),
    install_requires=open('requirements.txt').readlines(),
    package_data={'hippybot': ['version.txt']},
    include_package_data=True,
    extras_require={
        'plugins': open('extras_requirements.txt').readlines(),
    },
    entry_points={
        'console_scripts': ['hippybot = hippybot.bot:main',],
    },
    license='BSD'
)
