import threading
import pprint
import time


class Plugin(object):
    """This simple plugin just prints to STDOUT the configuration of the bot.
    You can change it, for example, in order to poke some API periodically and
    collect the results into some local/global variable in order to use later.

    Saying, you want to refresh the amount of EC2 nodes and their parameters,
    or something like that.
    """

    def __init__(self, config):
        print 'Initializing Plugin'
        self._config = config

        self.poll_thread = threading.Thread(name='example_thread',
                                            target=self.example_thread)
        self.poll_thread.start()

    def example_thread(self):
        """Refreshes the rooms periodically"""

        print 'Example thread started'

        while True:
            try:
                pprint.pprint(self._config)
                """For example, you have something like this in your
                hippybot.conf:

                .. code-block:: ini

                    [aws]
                    aws_user = arn:aws:iam::888888888888:user/_admin
                    aws_access_key_id = AKIAxxxxxxxxxxxxxRBA
                    aws_secret_access_key = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                    aws_region = us-west-2

                Here you can initialize and poke EC2 API using boto and fetch
                the credentials as:

                .. code-block:: python

                    self._config['aws']['aws_user']
                    self._config['aws']['aws_access_key_id']
                    self._config['aws']['aws_secret_access_key']
                    self._config['aws']['aws_region']
                """
            except Exception:
                import traceback
                print 'Got an exception in GetRooms Plugin get_rooms thread'
                traceback.print_exc()

            time.sleep(360)
