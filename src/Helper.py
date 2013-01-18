# by betonme @2012

import re

from time import time, sleep

try:
	#Python >= 2.7
	from collections import OrderedDict
except:
	from OrderedDict import OrderedDict

# Max Age (in seconds) of each feed in the cache
INTER_QUERY_TIME = 60*60*24


# Dummy Connector for cached pages
class Connector(object):
	def disconnect(self):
		pass


class Cacher(object):
	def __init__(self):
		# This dict structure will be the following:
		# { 'URL': (TIMESTAMP, value) }
		self.cache = {}

	def getCached(self, url, expires):
		# Try to get the tuple (TIMESTAMP, FEED_STRUCT) from the dict if it has
		# already been downloaded. Otherwise assign None to already_got
		already_got = self.cache.get(url, None)
		
		# Ok guys, we got it cached, let's see what we will do
		if already_got:
			# Well, it's cached, but will it be recent enough?
			elapsed_time = time() - already_got[0]
			
			# Woooohooo it is, elapsed_time is less than INTER_QUERY_TIME so I
			# can get the page from the memory, recent enough
			if elapsed_time < expires:
				return already_got[1]
			
			else:	
				# Uhmmm... actually it's a bit old, I'm going to get it from the
				# Net then, then I'll parse it and then I'll try to memoize it
				# again
				return None
			
		else: 
			# Well... We hadn't it cached in, so we need to get it from the Net
			# now, It's useless to check if it's recent enough, it's not there.
			return None

	def doCache(self, url, page):
		self.cache[url] = (time(), page)


class Throttler(object):
	# Causes subsequent requests to the same web server to be delayed
	# a specific amount of seconds. The first request to the server
	# always gets made immediately
	# Also throttle if there are already to many open requests 
	def __init__(self, throttleDelay=5):
		# The number of seconds to wait between subsequent requests
		self.throttleDelay = throttleDelay
		self.lastRequestTime = {}

	def throttle(self, url):
		currentTime = time()
		if ((url in self.lastRequestTime)
			and (time() - self.lastRequestTime[url] < self.throttleDelay)):
			throttleTime = (self.throttleDelay - (currentTime - self.lastRequestTime[url]))
			print "Throttle for %s seconds %s" % (throttleTime, url)
			sleep(throttleTime)
		self.lastRequestTime[url] = currentTime


class Limiter(object):
	# Causes subsequent requests to the same web server to be delayed
	# a specific amount of seconds. The first request to the server
	# always gets made immediately
	# Also throttle if there are already to many open requests 
	def __init__(self, limitDelay=5, limitRequests=3):
		# The number of seconds to wait between subsequent requests
		self.limitDelay = limitDelay
		self.limitRequests = limitRequests
		self.openRequests = 0

	def start(self, url):
		self.openRequests += 1
		print "Open requests: %s" % self.openRequests
		if (self.openRequests > self.limitRequests):
			print "Limiter: Sleeping for %s seconds %s" % (self.limitDelay, url)
			sleep(self.limitDelay)
	
	def end(self):
		self.openRequests = max(0, self.openRequests-1)


ChannelDict = OrderedDict([
	(' I$',   '1'),
	(' II$',  '2'),
	(' III$', '3'),
	(' HD', ''),
	('ARD', 'Das Erste'),
	('\+', 'Plus'),
	('0', 'null'),
	('1', 'eins'),
	('2', 'zwei'),
	('3', 'drei'),
	('4', 'vier'),
	('5', 'fuenf'),
	('6', 'sechs'),
	('7', 'sieben'),
	('8', 'acht'),
	('9', 'neun'),
	('\xc3\xa4', 'ae'),
	('\xc3\xb6', 'oe'),
	('\xc3\xbc', 'ue'),
	('\xc3\x84', 'ae'),
	('\xc3\x96', 'oe'),
	('\xc3\x9c', 'ue'),
	('\xc3\x9f', 'ss'),
	(' ', ''),
	('.', ''),
	('-', ''),
	('_', ''),
	('/', ''),
	('\\', ''),
	('\'', ''),
])


class ChannelUnifier(object):
	def __init__(self):
		self.rc = re.compile('|'.join(map(re.escape, ChannelDict)))
	
	def unifyChannel(self, text):
		def translate(match):
			return ChannelDict[match.group(0)]
		return self.rc.sub(translate, text).lower()
