# by betonme @2012

from collections import defaultdict

from thread import start_new_thread

#Twisted 12.x
#from twisted.web.client import getPage as twGetPage
#Twisted 8.x
from twisted.web.client import _parse, HTTPClientFactory
from twisted.internet import reactor
from twisted.internet.error import ConnectionDone

from Tools.BoundFunction import boundFunction

# Internal
from ModuleBase import ModuleBase
from Helper import Cacher, Throttler, Limiter, ChannelUnifier, INTER_QUERY_TIME


class IdentifierBase(ModuleBase, Cacher, Throttler, Limiter, ChannelUnifier):
	def __init__(self):
		ModuleBase.__init__(self)
		Cacher.__init__(self)
		Throttler.__init__(self)
		Limiter.__init__(self)
		ChannelUnifier.__init__(self)
		
		#Twisted 12.x use
		#self.deferreds = []
		#Twisted 8.x
		self.connectors = defaultdict(list)

	################################################
	# Twisted functions
	def getPage(self, callback, id, url, expires=INTER_QUERY_TIME):
		print "SSBase getPage"
		print url
		
		# Handle throttling
		self.throttle(url)
		cached = self.getCached(url, expires)
		
		if cached:
			print "SSBase cached"
			#self.base_callback(None, callback, url, cached)
			connector = Connector()
			self.connectors[id].append(connector)
			start_new_thread(self.base_callback, (connector, callback, id, url, cached))
		
		else:
			print "SSBase not cached"
			self.start(url)
			try:
				#Twisted 12.x use
				#deferred = twGetPage(url, timeout = 5)
				#deferred.addCallback(boundFunction(self.base_callback, deferred, callback, url))
				#deferred.addErrback(boundFunction(self.base_errback, deferred, callback))
				#self.deferreds.append(deferred)
				#Twisted 8.x
				contextFactory = None
				scheme, host, port, path = _parse(url)
				factory = HTTPClientFactory(url,                           timeout=30)  # Change later
				if scheme == 'https':
					from twisted.internet import ssl
					if contextFactory is None:
						extFactory = ssl.ClientContextFactory()
					connector = reactor.connectSSL(host, port, factory, contextFactory)
				else:
					connector = reactor.connectTCP(host, port, factory)
				deferred = factory.deferred
				self.connectors[id].append(connector)
				#End Twisted 8.x
				
				deferred.addCallback(boundFunction(self.base_callback, connector, callback, id, url))
				deferred.addErrback(boundFunction(self.base_errback, connector, callback, id, url))
				
			except Exception, e:
				import os, sys, traceback
				print _("SeriesPlugin getPage exception ") + str(e)
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
				self.cancel(id)
				callback()

	def base_callback(self, connector, callback, id, url, page=None, *args, **kwargs):
		print "callback", args, kwargs
		try:
			self.end()
			if connector and connector in self.connectors.get(id, []):
				self.connectors[id].remove(connector)
			if page:
				self.doCache(url, page)
			callback( page )
		except Exception, e:
			import os, sys, traceback
			print _("SeriesPlugin getPage exception ") + str(e)
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

	def base_errback(self, connector, callback, id, url, *args, **kwargs):
		self.end()
		if connector in self.connectors.get(id, []):
			self.connectors[id].remove(connector)
		print "errback", args, kwargs
		for arg in args:
			print arg
			print arg.type
			if isinstance(arg, ConnectionDone):
				print "RETRY"
				start_new_thread(self.getPage(callback, id, url))
				return
			if isinstance(arg, Exception):
				print _("Twisted failed:\n%s\n%s") % (arg.type, arg.value)
			elif arg:
				print _("Twisted failed\n%s") % str(arg)
		#TODO Wait and Retry on twisted.internet.error.ConnectionDone
		#TODO Wait and Retry on twisted.internet.error.TimeOut
		#TODO Wait and Retry on Page contains: Server is busy or similar
		self.cancel(id)
		callback( None )

	def cancel(self, id=""):
		try:
			#Twisted 12.x use
			#if self.deferreds:
			#	for deferred in self.deferreds:
			#		deferred.cancel()
			#Twisted 8.x
			if self.connectors:
				#
				if id:
					# Cancel only 
					keys = [id]
				else:
					keys = self.connectors.keys()
				
				for key in keys:
					connectors = self.connectors.pop(key, [])
					#while connectors:
					for connector in connectors:
					#for connector in connectors[:]:
						#connector = connectors.pop()
						connector.disconnect()
						#self.connectors.remove(connector)
		except Exception, e:
			print "CANCEL ", str(e)

	def foundEpisode(self, callback, id, episode=None, *args, **kwargs):
		print "foundEpisode", id, episode, args, kwargs, self.connectors
		if episode:
			# We found a matching episode
			self.cancel(id)
			callback(episode)
		else:
			if not self.connectors.get(id, []):
				# There are no pending requests
				callback( None )


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

	def getSeriesList(self, callback, show_name):
		# On Success: Return a series list of id, name tuples
		# On Failure: Return a empty list or None
		callback( None )
		
	def getEpisode(self, callback, show_name, short, description, begin, end, channel):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or None
		callback( None )
