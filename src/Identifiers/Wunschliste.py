# by betonme @2012

# Imports
from Components.config import config

from Tools.BoundFunction import boundFunction

from urllib import urlencode

from iso8601 import parse_date
from HTMLParser import HTMLParser

from datetime import datetime

import re

# Internal
from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase
from Plugins.Extensions.SeriesPlugin.Helper import unifyChannel


# Constants
SERIESLISTURL     = "http://www.wunschliste.de/ajax/search_dropdown.pl?"
EPISODEIDURLATOM  = "http://www.wunschliste.de/xml/atom.pl?"
#EPISODEIDURLRSS  = "http://www.wunschliste.de/xml/rss.pl?"
EPISODEIDURLPRINT = "http://www.wunschliste.de/epg_print.pl?"

# Series: EpisodeTitle (Season.Episode) - Weekday Date, Time / Channel (Country)
# Two and a Half Men: Der Mittwochs-Mann (1.5) - Mi 02.05., 19.50:00 Uhr / TNT Serie (Pay-TV)
# Two and a Half Men: Der Mittwochs-Mann (1.5) - Mi 02.05., 19.50:00 Uhr / TNT Serie
# Two and a Half Men: Der Mittwochs-Mann (1) (1.5) - Mi 02.05., 19.50:00 Uhr / TNT Serie
# Der Troedeltrupp - Das Geld liegt im Keller: Folge 109 (109) - Do 03.05., 16.15:00 Uhr / RTL II
# Galileo: U.a.: Die schaerfste Chili der Welt - Fr 04.05., 19.05:00 Uhr / ProSieben
# Galileo: Magazin mit Aiman Abdallah, BRD 2012 - Mi 09.05., 06.10:00 Uhr / ProSieben
# Gute Zeiten, schlechte Zeiten: Folgen 4985 - 4988 (21.84) - Sa 05.05., 11.00:00 Uhr / RTL
# Channel is between last / and ( or line end
ComiledRegexpAtomChannel = re.compile('\/(?!.*\/) ([^\(]+)')
# Date is between last - and channel
ComiledRegexpAtomDate = re.compile('-(?!.*-) (.+)')
# Find optional episode
ComiledRegexpAtomEpisode = re.compile('\((?!.*\()(.+)\) ')
# Series: Title
ComiledRegexpAtomTitle = re.compile('.+: (.+)')

# (Season.Episode) - EpisodeTitle
# (21.84) Folge 4985
# (105) Folge 105
# (4.11/4.11) Mama ist die Beste/Rund um die Uhr
# Galileo: Die schaerfste Chili der Welt
# Galileo: Jumbo auf Achse: Muelltonnenkoch
# Gute Zeiten, schlechte Zeiten: Folgen 4985 - 4988 (21.84) - Sa 05.05., 11.00:00 Uhr / RTL
ComiledRegexpPrintTitle = re.compile( '(\(.*\) )?(.+)')


ComiledRegexpEpisode = re.compile( '((\d+)\.)?(\d+)')


class WLAtomParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.title = False
		self.updated = False
		self.titlestr = ''
		self.updatedstr = ''
		self.list = []

	def handle_starttag(self, tag, attributes):
		if tag == 'title':
			self.title = True
		elif tag == 'updated':
			self.updated = True

	def handle_endtag(self, tag):
		if tag == 'title':
			self.title = False
		elif tag == 'updated':
			self.updated = False
		elif tag == 'entry':
			self.list.append( (self.titlestr, self.updatedstr) )
			self.titlestr = ''
			self.updatedstr = ''

	def handle_data(self, data):
		if self.title:
			self.titlestr += data
		elif self.updated:
			self.updatedstr = data


class WLPrintParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.tr= False
		self.td= False
		self.data = []
		self.list = []

	def handle_starttag(self, tag, attributes):
		if tag == 'td':
			self.td= True
		elif tag == 'tr':
			self.tr= True

	def handle_endtag(self, tag):
		if tag == 'td':
			self.td= False
		elif tag == 'tr':
			self.tr= False
			self.list.append(self.data)
			self.data= []

	def handle_data(self, data):
		if self.tr and self.td:
			self.data.append(data)


class Wunschliste(IdentifierBase):
	def __init__(self):
		IdentifierBase.__init__(self)

	@classmethod
	def knowsToday(cls):
		# Use the print page
		return True

	@classmethod
	def knowsFuture(cls):
		# Use the atom feed
		return True

	def getEpisode(self, callback, name, begin, end=None, channel=None):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or None
		
		self.callback = callback
		self.name = name
		self.begin = begin
		self.end = end
		self.channel = channel
		self.ids = []
		self.when = 0
		
		# Check preconditions
		if not name:
			print _("Skip Wunschliste: No show name specified")
			return callback()
		if not begin:
			print _("Skip Wunschliste: No begin timestamp specified")
			return callback()
		
		print "Wunschliste getEpisode"
		
		#Py2.6
		delta = abs(datetime.now() - self.begin)
		delta = delta.seconds + delta.days * 24 * 3600
		#Py2.7 delta = abs(datetime.now() - self.begin).total_seconds()
		if delta > 3*60*60:
			self.when = True
		else:
			self.when = False
		
		self.getSeries()

	def getAlternativeSeries(self):
		self.name = " ".join(self.name.split(" ")[:-1])
		if self.name:
			self.getSeries()
		else:
			self.callback()
	
	def getSeries(self):
		self.getPage(
						self.getSeriesCallback,
						SERIESLISTURL + urlencode({ 'q' : self.name })
					)

	def getSeriesCallback(self, data=None):
		print "Wunschliste getSeriesListCallback"
		serieslist = []
		
		if data and isinstance(data, basestring):
		#if data and not isinstance(data, list):
			for line in data.splitlines():
				values = line.split("|")
				if len(values) == 3:
					idname, countryyear, id = values
					print id, idname
					serieslist.append( id )
				else:
					print "Wunschliste: ParseError: " + str(line)
			serieslist.reverse()
			data = serieslist
		
		if data and isinstance(data, list):
			self.ids = data[:]
			self.getNextSeries()
		else:
			self.getAlternativeSeries()
		return data

	def getNextSeries(self):
		print "Wunschliste getNextSeries", self.ids
		if self.ids:
			#for id_name in data:
			id = self.ids.pop()
			
			if self.when:
				url = EPISODEIDURLATOM + urlencode({ 's' : id })
				self.getPage(
								self.getEpisodeFutureCallback,
								url
							)
			else:
				url = EPISODEIDURLPRINT + urlencode({ 's' : id })
				self.getPage(
								self.getEpisodeTodayCallback,
								url
							)
		
		else:
			self.callback()

	def getEpisodeFutureCallback(self, data=None):
		print "Wunschliste getEpisodeFutureCallback"
		
		if data and isinstance(data, basestring):
		#if data and not isinstance(data, WLAtomParser):
			# Handle malformed HTML issues
			data = data.replace('&amp;','&')  # target=\"_blank\"&amp;
			
			parser = WLAtomParser()
			parser.feed(data)
			#print parser.list
			
			data = parser
		
		if data and isinstance(data, WLAtomParser):
			trs = data.list
			if trs:
			
				for tds in trs:
					if tds and len(tds) >= 2:
						xtitle, xupdated = tds
						if xtitle is not None and xupdated is not None:
							#import iso8601
							#http://code.google.com/p/pyiso8601/
							xbegin = parse_date(xupdated)
							xbegin = xbegin.replace(tzinfo=None)
		
							#import pytz
							#xbegin = pytz.UTC.localize(xbegin)
							#xbegin = mktime(xbegin.timetuple())
		
							# Alternative
							#from dateutil import parser
							#http://labix.org/python-dateutil
							#xbegin = parser.parse(xupdated)
		
							#Py2.6
							delta = abs(self.begin - xbegin)
							delta = delta.seconds + delta.days * 24 * 3600
							#Py2.7 delta = abs(self.begin - xbegin).total_seconds()
							print self.begin, xbegin, delta, int(config.plugins.seriesplugin.max_time_drift.value)*60
							if delta <= int(config.plugins.seriesplugin.max_time_drift.value) * 60:
								result = ComiledRegexpAtomChannel.search(xtitle)
								if result and len(result.groups()) >= 1:
									xchannel = unifyChannel(result.group(1))
									print self.channel, xchannel, len(self.channel), len(xchannel)
									if self.compareChannels(self.channel, xchannel):
										# Slice string to remove channel
										xtitle = xtitle[:result.start()]
										result = ComiledRegexpAtomDate.search(xtitle)
										if result and len(result.groups()) >= 1:
											# Slice string to remove date
											xtitle = xtitle[:result.start()]
											result = ComiledRegexpAtomEpisode.search(xtitle)
											if result and len(result.groups()) >= 1:
												# Extract season and episode
												xepisode = result.group(1)
												# Slice string to remove season and episode
												xtitle = xtitle[:result.start()]
												result = ComiledRegexpEpisode.search(xepisode)
												if result and len(result.groups()) >= 3:
													xseason = result and result.group(2) or "1"
													xepisode = result and result.group(3) or "0"
												else:
													xseason = "1"
													xepisode = "0"
											else:
												xseason = "1"
												xepisode = "0"
											result = ComiledRegexpAtomTitle.search(xtitle)
											if result and len(result.groups()) >= 1:
												# Extract episode title
												xtitle = result.group(1)
												self.callback( (xseason, xepisode, xtitle.decode('ISO-8859-1').encode('utf8')) )
												return data
		self.getNextSeries()
		return data

	def getEpisodeTodayCallback(self, data=None):
		print "Wunschliste getEpisodeTodayCallback"
		
		if data and isinstance(data, basestring):
		#if data and not isinstance(data, WLPrintParser):
			parser = WLPrintParser()
			parser.feed(data)
			#print parser.list
			
			data = parser
		
		if data and isinstance(data, WLPrintParser):
			trs = data.list
			if trs:
			
				year = str(datetime.today().year)
				for tds in trs:
					if tds and len(tds) >= 5:
						xchannel, xdate, xbegin, xend, xtitle = tds
						
						xdate    = xdate[3:]+year
						xbegin   = datetime.strptime( xdate+xbegin, "%d.%m.%Y%H.%M Uhr" )
						#xend     = datetime.strptime( xdate+xend, "%d.%m.%Y%H.%M Uhr" )
						#print xchannel, xdate, xbegin, xend, xtitle
						#print datebegin, xbegin, abs((datebegin - xbegin))
						
						#Py2.6
						delta = abs(self.begin - xbegin)
						delta = delta.seconds + delta.days * 24 * 3600
						#Py2.7 delta = abs(self.begin - xbegin).total_seconds()
						print self.begin, xbegin, delta, int(config.plugins.seriesplugin.max_time_drift.value)*60
						
						if delta <= int(config.plugins.seriesplugin.max_time_drift.value) * 60:
							xchannel = unifyChannel(xchannel)
							print self.channel, xchannel, len(self.channel), len(xchannel)
							if self.compareChannels(self.channel, xchannel):
								result = ComiledRegexpPrintTitle.search(xtitle)
								if result and len(result.groups()) >= 2:
									xepisode = result and result.group(1)
									xtitle = result and result.group(2)
									if xepisode:
										result = ComiledRegexpEpisode.search(xepisode)
										if result and len(result.groups()) >= 3:
											xseason = result and result.group(2) or "1"
											xepisode = result and result.group(3) or "0"
										else:
											xseason = "1"
											xepisode = "0"
									else:
										xseason = "1"
										xepisode = "0"
									self.callback( (xseason, xepisode, xtitle.decode('ISO-8859-1').encode('utf8')) )
									return data
		self.getNextSeries()
		return data

	def getPage(self, callback, url, expires=None):
		# PHP Proxy with 3 day Caching
		# to minimize server requests
		url = 'http://betonme.lima-city.de/SeriesPlugin/proxy.php?' + urlencode({ 'url' : url })
		if expires:
			IdentifierBase.getPage(self, callback, url, expires)
		else:
			IdentifierBase.getPage(self, callback, url)
