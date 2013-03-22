import os
import os.path
import sqlite3dbm
from threading import RLock
from hippybot.hipchat import HipChatApi
from hippybot.decorators import directcmd, botcmd

CONFIG_DIR = os.path.expanduser("~/.techbot")
DB = os.path.expanduser("~/.techbot/techbot.db")

class Plugin(object):
	"""Plugin to handle knewton locking semantics
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

	@botcmd
	def lock(self, mess, args, **kwargs):
		"""
		Establish a lock over a resource.
		Only you can unlock, but anyone can break.
		Format: @NickName lock <lockname> (message)
		"""
		self.bot.log.info("lock: %s" % mess)
		room, owner, lock, note = self.get_lock_fundamentals(mess)
		try:
			response = self.set_lock(lock, owner, room, note)
			return response
		except Exception, e:
			return str(e)

	@botcmd
	def locks(self, mess, args, **kwargs):
		"""
		Get a list of locks
		Format: @NickName locks (print all locks)
		"""
		self.bot.log.info("locks: %s" % mess)
		return self.get_locks()

	@botcmd
	def unlock(self, mess, args, **kwargs):
		"""
		Release a lock you have over a resource.
		Only the person who established it can unlock it, but anyone can break it.
		Format: @NickName unlock <lockname>
		"""
		self.bot.log.info("unlock: %s" % mess)
		room, owner, lock, _ = self.get_lock_fundamentals(mess)
		try:
			return self.release_lock(lock, owner)
		except Exception, e:
			return str(e)

	@botcmd(name='break')
	def break_lock(self, mess, args, **kwargs):
		"""
		Break a lock someone else has over a resource.
		This is bad, but sadly necessary.
		Format: @NickName break <lockname>
		"""
		self.bot.log.info("break: %s" % mess)
		room, owner, lock, _ = self.get_lock_fundamentals(mess)
		try:
			return self.release_lock(lock, owner, break_lock=True)
		except Exception, e:
			return str(e)

	def get_lock_fundamentals(self, mess):
		room = str(mess.getFrom()).split('/')[0]
		owner = str(mess.getFrom()).split('/')[1]
		body = mess.getBody()
		tokens = body.split(" ")
		tokens.pop(0) # lock
		lock = tokens.pop(0)
		return room, owner, lock, ' '.join(tokens)

	def kill_all_humans(self):
		# For future use
		pass

	def set_lock(self, lock, owner, room, note):
		with self.rlock:
			locks = self.db.get('lock', {})
			if locks.get(lock):
				elock, eowner, enote, eroom = locks.get(lock)
				if eowner != owner:
					raise Exception("Lock already held: \n"
						"    %s: %s (%s)" % (lock, eowner, enote))
			locks[lock] = (lock, owner, note, room)
			self.db['lock'] = locks
			return "Lock established: \n    %s: %s %s" % (
				lock, owner, note)

	def get_locks(self):
		locks = self.db.get('lock', {})
		message = ["Existing Locks:"]
		for lock, owner, note, _ in locks.values():
			message.append("    %s: %s %s" %(
				lock, owner, note))
		if len(message) == 1:
			message.append("    NONE")
		return '\n'.join(message)

	def release_lock(self, lock, owner, break_lock=False):
		with self.rlock:
			locks = self.db.get('lock', {})
			if locks.get(lock):
				elock, eowner, enote, eroom = locks.get(lock)
				if eowner == owner:
					break_lock = False
			else:
				raise Exception("Lock does not exist: \n"
					"    %s" % (lock))
			del locks[lock]
			self.db['lock'] = locks
			if break_lock:
				return "LOCK BROKEN: \n    %s: %s" % (lock, owner)
			else:
				return "Lock released: \n    %s: %s" % (lock, owner)




