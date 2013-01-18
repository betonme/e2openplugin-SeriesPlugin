# by betonme @2012

from collections import defaultdict

from thread import start_new_thread

#Twisted 12.x
#from twisted.web.client import getPage as twGetPage
#Twisted 8.x
#from twisted.web.client import _parse, HTTPClientFactory
#from twisted.internet import reactor
#Twisted All
#from twisted.python.failure import Failure

from urllib2 import urlopen #, Request

from Tools.BoundFunction import boundFunction

# Internal
from ModuleBase import ModuleBase
from Helper import Cacher, INTER_QUERY_TIME  #, Retry
from Logger import splog


class IdentifierBase(ModuleBase, Cacher):  #, Retry):
	def __init__(self):
		ModuleBase.__init__(self)
		Cacher.__init__(self)
		#Retry.__init__(self)
		self.callback = None
		self.name = ""
		self.begin = None
		self.end = None
		self.channel = ""
		self.ids = []

	################################################
	# Twisted functions
	def getPage(self, callback, url, expires=INTER_QUERY_TIME):
		splog("SSBase getPage")
		splog(url)
		
		cached = self.getCached(url, expires)
		if cached:
			splog("SSBase cached")
			callback( cached )
		
		else:
			splog("SSBase not cached")
			try:
				#req = Request(url)
				#response = urlopen(req)
				response = urlopen(url , timeout=30)
				data = callback( response.read() )
				if data:
					self.doCache(url, data)
				
			except Exception, e:
				import os, sys, traceback
				splog(_("SeriesPlugin getPage exception ") + str(e))
				exc_type, exc_value, exc_traceback = sys.exc_info()
				#traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
				#splog( exc_type, exc_value, exc_traceback.format_exc() )
				splog( exc_type, exc_value, traceback.format_stack() )
				
				#self.cancel()
				callback()

	@staticmethod
	def compareChannels(local, remote):
		if local == remote:
			# The channels are equal
			return True
		elif local in remote or remote in local:
			# Parts of the channels are equal
			return True
		elif local == "":
			# The local channel is empty
			return True
		elif "unknown" in local:
			# The local channel is unknown
			return True
		
		return False


	################################################
	# Service prototypes
	@classmethod
	def knowsElapsed(cls):
		# True: Service knows elapsed air dates
		# False: Service doesn't know elapsed air dates
		return False

	@classmethod
	def knowsToday(cls):
		# True: Service knows today air dates
		# False: Service doesn't know today air dates
		return False

	@classmethod
	def knowsFuture(cls):
		# True: Service knows future air dates
		# False: Service doesn't know future air dates
		return False

	def getEpisode(self, callback, name, begin, end, channel):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or None
		callback( None )
