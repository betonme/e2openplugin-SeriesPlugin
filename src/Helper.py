# by betonme @2012

import re

from time import time, sleep

try:
	#Python >= 2.7
	from collections import OrderedDict
except:
	from OrderedDict import OrderedDict

from twisted.internet.error import TimeoutError, DNSLookupError, \
																		ConnectionRefusedError, ConnectionDone, ConnectError, \
																		ConnectionLost
																		#ServerTimeoutError
from twisted.web.client import PartialDownloadError

# Max Age (in seconds) of each feed in the cache
INTER_QUERY_TIME = 60*60*24

# Global cache
# Do we have to cleanup it
cache = {}


# Dummy Connector for cached pages
class Connector(object):
	def disconnect(self):
		pass


class Cacher(object):
	def __init__(self):
		# This dict structure will be the following:
		# { 'URL': (TIMESTAMP, value) }
		#self.cache = {}
		#global cache
		#cache = {}
		pass

	def getCached(self, url, expires):
		#pullCache
		global cache
		# Try to get the tuple (TIMESTAMP, FEED_STRUCT) from the dict if it has
		# already been downloaded. Otherwise assign None to already_got
		already_got = cache.get(url, None)
		
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
		#pushCache
		global cache
		cache[url] = (time(), page)


ComiledRegexpSeries = re.compile('(.*)[ _][Ss]{,1}\d{1,2}[EeXx]\d{1,2}.*')  #Only for S01E01 OR 01x01 + optional title
def unifyName(text):
	# Remove Series Episode naming
	m = ComiledRegexpSeries.match(text)
	if m:
		#print m.group(0)     # Entire match
		#print m.group(1)     # First parenthesized subgroup
		if m.group(1):
			text = m.group(1)
	return text


ChannelReplaceDict = OrderedDict([
	('HD', ''),
	('III', 'drei'),
	('II',  'zwei'),
	('I',   'eins'),
	('ARD', 'DasErste'),
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
#	(' ', ''),
#	('.', ''),
#	('-', ''),
#	('_', ''),
#	('/', ''),
#	('\\', ''),
#	('\'', ''),
#	# Remove unicode start end of area
#	('\xc2\x86', ''),
#	('\xc2\x87', ''),
])
ComiledRegexpChannel = re.compile('|'.join(ChannelReplaceDict))
def unifyChannel(text):
	def translate(match):
		m = match.group(0)
		return ChannelReplaceDict.get(m, m)
	#return ComiledRegexpChannel.sub(translate, text).lower()
	#return ComiledRegexpChannel.sub(translate, text).lower().decode("utf-8").encode("latin1")
	#return str(ComiledRegexpChannel.sub(translate, text).lower().decode("utf-8").encode("latin1"))
	
	#name = ComiledRegexpChannel.sub(translate, text).lower()
	#return unicode(name,"utf-8").encode("ISO-8859-1")
	
	text = ComiledRegexpChannel.sub(translate, text)
	text = text.decode("utf-8").encode("latin1")
	pattern = re.compile('[\W_]+')
	text = pattern.sub('', text)
	return text.strip().lower()


class Retry(object):
	
	EXCEPTIONS_TO_RETRY = (TimeoutError, DNSLookupError,
												 ConnectionRefusedError, ConnectionDone, ConnectError,
												 ConnectionLost, PartialDownloadError)
	
	def __init__(self, retryLimit=3, retryDelay=5):
		self.retryLimit = retryLimit
		# The number of seconds to wait between retry requests
		self.retryDelay = retryDelay
		self.retryCounter = {}

	def retry(self, err, url):
		if isinstance(err, self.EXCEPTIONS_TO_RETRY):
			if self.retryCounter.get(url,0) <= self.retryLimit:
				self.retryCounter[url] = self.retryCounter.get(url,0) + 1
				sleep(self.retryDelay)
				return True
		# No retry because of major failure or retry limit has been reached
		return False
