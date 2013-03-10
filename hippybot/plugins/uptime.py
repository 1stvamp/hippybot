import subprocess
from hippybot.decorators import botcmd

class Plugin(object):
	@botcmd
	def uptime(self, mess, args, **kwargs):
		"""Get current uptime information"""
		self.bot.log.info("uptime: %s" % mess)
		return subprocess.check_output('uptime')
