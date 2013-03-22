import os
import os.path
import re
import sqlite3dbm
from threading import RLock
from hippybot.hipchat import HipChatApi
from hippybot.decorators import botcmd, contentcmd

CONFIG_DIR = os.path.expanduser("~/.techbot")
DB = os.path.expanduser("~/.techbot/score.db")

class Plugin(object):
	"""Plugin to handle knewton replacement of ++ bot in partychatapp
	"""
	def __init__(self):
		self.rlock = RLock()
		self.db = self.get_db()

	def get_db(self):
		self.create_dir()
		db = sqlite3dbm.sshelve.open(DB)
		return db

	def create_dir(self):
		if not os.path.exists(CONFIG_DIR):
			os.mkdir(CONFIG_DIR)

	@contentcmd
	def change_score(self, mess, **kwargs):
		message = mess.getBody()
		if message:
			room = str(mess.getFrom()).split("/")[0]
			user = str(mess.getFrom()).split("/")[1]
			results = []
			if message.find('++') > -1 or message.find('--') > -1:
				self.bot.log.info("plusplusbot: %s" % mess)
			if message.endswith("++") or message.endswith("--"):
				results.extend(self.process_message(message, room, user))
			for m in re.findall("\((.*?)\)", message):
				if m.endswith("++") or m.endswith("--"):
					results.extend(self.process_message(m, room, user))
			if len(results) > 0:
				return "\n".join(results)

	def process_message(self, message, room, user):
		results = []
		victim = message[:-2]
		excl = "woot!"
		plus = 1 
		if message.endswith('--'):
			excl = "ouch!"
			plus = -1
		with self.rlock:
			scores = self.db.get(room, {})
			score = scores.setdefault(victim, 0)
			score += plus
			scores[victim] = score
			self.db[room] = scores
			return ["[%s] %s [%s now at %s]" % (user, victim, excl, score)]

	@botcmd
	def scores(self, mess, args, **kwargs):
		"""
		Prints all scores from this room
		Format: @NickName scores
		"""
		self.bot.log.info("score: %s" % mess)
		room = str(mess.getFrom()).split("/")[0]
		ret = []
		with self.rlock:
			scores = self.db.get(room, {})
			for key in scores:
				ret.append("%s: %s" %(key, scores[key]))
		return '\n'.join(ret)

