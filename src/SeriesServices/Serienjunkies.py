# by betonme @2012

# Imports
from urllib import urlencode
from urllib2 import Request, urlopen, URLError

import json

from xml.etree.cElementTree import XML
from Plugins.Extensions.AutoTimer.iso8601 import parse_date
from datetime import datetime
from time import mktime
import re

from Plugins.Extensions.AutoTimer.SeriesServiceBase import SeriesServiceBase

# Constants
SERIESLISTURL = "http://www.serienjunkies.de/i/autocomplete.php"	# limit=10
#SERIESLISTURL = "https://api.serienjunkies.de/allsearch.php"  # d=APIKEY & t=10

#"http://www.serienjunkies.de" #idid.ics #/supernatural/supernatural.ics
#"http://www.serienjunkies.de/rss/epg/serie" #id.xml #/supernatural.xml
EPISODEIDURL = "http://www.serienjunkies.de/..."

class Serienjunkies(SeriesServiceBase):
	def __init__(self):
		SeriesServiceBase.__init__(self)

		# Series: EpisodeTitle (Season/Episode) - Weekday Date, Time / Channel (Country)
		# .*:.*\(.*\..*\).*/.*\(.*\..*\)
		self.regexp = re.compile('(.+):(.*)\((\d+)\.(\d+)\)')
		
		# Used for a simple page caching
		self.cacheid = None
		self.cacheroot = None

	def getName(self):
		return "Serienjunkies.de"

	def getId(self):
		return "Sjde"

	def knowsElapsed(self):
		return False

	def getSeriesList(self, name):
		# On Success: Return a series list of id, name tuples
		# On Failure: Return a empty list or None
		values = { 'limit' : '10' }
		values = { 'q' : name }
		data = urlencode(values)
		req = Request(SERIESLISTURL, data)

		try:
			response = urlopen(req)
			data = response.read()
		except URLError as e:
			data = ""
			print "AutoTimer: Serienjunkies URLError"

		serieslist = []
		js = json.loads(data)
		if js and 'items' in js:
			for item in js['items']:
				# We could also check 'text' and 'info' in items
				name = item['text'] + " (" + item['info'] + ")"
				id = item['link']  # id contains leading "/"
				serieslist.append( (id, name) )
		else:
			print "AutoTimer: Serienjunkies: ParseError: " + str(data)
		return serieslist









	def getEpisodeId(self, id, begin, end=None, channel=None):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or None
		begin = begin and datetime.fromtimestamp(begin)
		end = end and datetime.fromtimestamp(end)

		if self.cacheid != id:
			self.cacheid = id
			values = { 's' : id }
			data = urlencode(values)
			req = Request(EPISODEIDURL, data)

			try:
				response = urlopen(req)
				print "URLOPEN"
				feed = response.read()
			except URLError as e:
				feed = ""
				print "AutoTimer: Serienjunkies URLError"

			#Won't work why - getroot is the problem
			#feed = urlopen(req)
			#tree = feed and parse(feed)
			#for entry in tree.findall('{http://www.w3.org/2005/Atom}entry'):
	
			root = feed and XML(feed)
			self.cacheroot = root

		else:
			root = self.cacheroot

		if root is not None:
			for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
				title = entry.find('{http://www.w3.org/2005/Atom}title')
				updated = entry.find('{http://www.w3.org/2005/Atom}updated')
				if title is not None and updated is not None:
					#import iso8601
					#http://code.google.com/p/pyiso8601/
					xbegin = parse_date(updated.text)

					#import pytz
					#xbegin = pytz.UTC.localize(xbegin)
					#xbegin = mktime(xbegin.timetuple())

					# Alternative
					#from dateutil import parser
					#http://labix.org/python-dateutil
					#xbegin = parser.parse(updated.text)

					if begin.date() == xbegin.date():
						# Same day
						if abs(mktime(begin.timetuple()) - mktime(xbegin.timetuple())) < 600:
							# Time difference is below 5 minutes
							# We actually don't check the channel - Any ideas?
							result = self.regexp.match(title.text)
							if result and len(result.groups())>=4:
								
								title = result.group(2)
								season = result.group(3)
								episode = result.group(4)
								return int(season), int(episode), title

		return None
