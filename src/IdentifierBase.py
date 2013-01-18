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

from time import sleep
from urllib import urlencode
from urllib2 import urlopen, URLError, Request, build_opener, HTTPCookieProcessor


from Tools.BoundFunction import boundFunction

# Internal
from ModuleBase import ModuleBase
from Cacher import Cacher, INTER_QUERY_TIME
from Logger import splog


import recipeMemUse as MemoryUsage


class IdentifierBase(ModuleBase, Cacher):
	def __init__(self):
		ModuleBase.__init__(self)
		Cacher.__init__(self)
		self.callback = None
		self.name = ""
		self.begin = None
		self.end = None
		self.channel = ""
		self.ids = []
		
		self.returnvalue = None

	################################################
	# URL functions
	def getPage(self, callback, url, headers={}, expires=INTER_QUERY_TIME, counter=0):
		splog("SSBase getPage", url)
		
		cached = self.getCached(url, expires)
		
		
		VmSize = MemoryUsage.memory()
		splog("SP VmSize: "+str(VmSize/1024/1024)+" Mb" )
		VmRSS  = MemoryUsage.resident()
		splog("SP VmRSS:  "+str(VmRSS/1024/1024)+" Mb" )
		VmStk  = MemoryUsage.stacksize()
		splog("SP VmStk:  "+str(VmStk/1024/1024)+" Mb" )
		
		
		if cached:
			splog("SSBase cached")
			callback( cached )
		
		else:
			splog("SSBase not cached")
			
			try:
				#req = Request(url)
				#response = urlopen(req)
				#response = urlopen(url , timeout=30).read()
				
				#values = {'name' : 'A B'}

				req = Request(url, headers=headers)
				response = urlopen(req).read()
				
			except URLError, e:
				if counter > 2:
					raise
					return
				elif hasattr(e, "code"):
					print e.code, e.msg, counter
					sleep(2)
					self.getPage(callback, url, headers, expires, counter+1)
					return
				else:
					raise
			
			data = callback( response )
			#splog("SSBase data to cache: ", data) 
			if data:
				self.doCache(url, data)

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

	def getEpisode(self, callback, name, begin, end, channels):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or None
		callback( None )
