"""Installer for hippybot
"""

try:
        from setuptools import setup, find_packages
except ImportError:
        from ez_setup import use_setuptools
        use_setuptools()
        from setuptools import setup, find_packages
setup(
    name='hippybot',
    description='Python Hipchat bot',
    version='1.0.0',
    author='Wes Mason',
    author_email='wes[at]1stvamp[dot]org',
    url='http://github.com/1stvamp/hippybot',
    packages=find_packages(exclude=['ez_setup']),
    install_requires=open('requirements.txt').readlines(),
    entry_points={
        'console_scripts': ['hippybot = hippybot.bot:main',],
    },
    license='BSD'
)
