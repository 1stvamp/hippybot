import random
from hippybot.decorators import botcmd

class Plugin(object):
	@botcmd
	def hype(self, mess, args, **kwargs):
		"""
		Ask NickName to get some hype up into this room.  Sick.
		Format: @NickName hype
		"""
		self.bot.log.info("hype: %s" % mess)
		return select_hype()

def select_hype():
	hype = [
		"/me pumps its fist in the air (Yeah!!)",
		"Gangnam Style!",
		"Sick!",
		"Aaaaay! You know what it is!",
		"Yoooooouuuuu!",
		"Get money!",
		"Ballllllin!",
		"Jeah!",
		"Get it!",
		"/me just popped a bottle",
		"/me is making it rain",
		"/me is getting so low right now"]
	return random.choice(hype)
