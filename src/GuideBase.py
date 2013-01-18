# by betonme @2012

from time import time

from twisted.web.client import getPage as twGetPage

from Tools.BoundFunction import boundFunction

from ModuleBase import ModuleBase


# Max Age (in seconds) of each feed in the cache
INTER_QUERY_TIME = 600


# This dict structure will be the following:
# { 'URL': (TIMESTAMP, value) }
cache = {}


class GuideBase(ModuleBase):
	def __init__(self):
		ModuleBase.__init__(self)
		self.deferreds = []


	def getPage(self, callback, url, expires=INTER_QUERY_TIME):
		print "GSBase getPage"
		print url
		cached = self.getCached(url, expires)
		
		if cached:
			print "GSBase cached"
			self.base_callback(callback, url, cached)
		
		else:
			print "GSBase not cached"
			#TODO think about throttling http://code.activestate.com/recipes/491261/
			try:
				deferred = twGetPage(url, timeout = 5)
				deferred.addCallback(boundFunction(self.base_callback, callback, url))
				deferred.addErrback(boundFunction(self.base_errback, callback))
				self.deferreds.append(deferred)
			except Exception, e:
				import os, sys, traceback
				print _("SeriesPlugin getPage exception ") + str(e)
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
				callback()

	def base_callback(self, callback, url, page=None, *args, **kwargs):
		try:
			print "callback", args, kwargs
			#print page
			#print args
			#print kwargs
			if page:
				cache[url] = (time(), page)
				callback( page )
			else:
				callback( None )
		except Exception, e:
			import os, sys, traceback
			print _("SeriesPlugin getPage exception ") + str(e)
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

	def base_errback(self, callback, *args, **kwargs):
		print "errback", args, kwargs
		callback( None )

	def cancel(self):
		if self.deferreds:
			for deferred in deferreds:
				deferred.cancel
				#connector.disconnect()


	################################################
	# Service prototypes
	def getSeriesList(self, callback, show_name):
		# On Success: Return a series list of id, name tuples
		# On Failure: Return a empty list or None
		callback( None )
		
	def getEpisode(self, callback, show_name, short, description, begin, end, channel):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or None
		callback( None )

#TODO
