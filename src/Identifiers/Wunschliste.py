# by betonme @2012

# Imports
from Components.config import config

from Tools.BoundFunction import boundFunction

from urllib import urlencode

from iso8601 import parse_date
from HTMLParser import HTMLParser

from datetime import datetime

import re

from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase


# Constants
SERIESLISTURL     = "http://www.wunschliste.de/ajax/search_dropdown.pl?"
EPISODEIDURLATOM  = "http://www.wunschliste.de/xml/atom.pl?"
#EPISODEIDURLRSS  = "http://www.wunschliste.de/xml/rss.pl?"
EPISODEIDURLPRINT = "http://www.wunschliste.de/epg_print.pl?"


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
		
		# Series: EpisodeTitle (Season/Episode) - Weekday Date, Time / Channel (Country)
		# Two and a Half Men: Der Mittwochs-Mann (1.5) - Mi 02.05., 19.50:00 Uhr / TNT Serie (Pay-TV)
		# Two and a Half Men: Der Mittwochs-Mann (1.5) - Mi 02.05., 19.50:00 Uhr / TNT Serie
		# Der Troedeltrupp - Das Geld liegt im Keller: Folge 109 (109) - Do 03.05., 16.15:00 Uhr / RTL II
		# Not yet
		# Galileo: U.a.: Die schaerfste Chili der Welt - Fr 04.05., 19.05:00 Uhr / ProSieben
		# Galileo: Magazin mit Aiman Abdallah, BRD 2012 - Mi 09.05., 06.10:00 Uhr / ProSieben
		# Gute Zeiten, schlechte Zeiten: Folgen 4985 - 4988 (21.84) - Sa 05.05., 11.00:00 Uhr / RTL
		self.regexpatom = re.compile('(.+): (.+) \((\d*?)\.?(\d+)\) - .+ \/ ([^\(]+)')
		
		# (Season.Episode) - EpisodeTitle
		# (21.84) Folge 4985
		# (105) Folge 105
		# Not yet
		# Galileo: Die schaerfste Chili der Welt
		# Galileo: Jumbo auf Achse: Muelltonnenkoch
		# Gute Zeiten, schlechte Zeiten: Folgen 4985 - 4988 (21.84) - Sa 05.05., 11.00:00 Uhr / RTL
		self.regexpprint = re.compile('\((\d*?)\.?(\d+)\) (.+)')

	@classmethod
	def knowsToday(cls):
		# Use the print page
		return True

	@classmethod
	def knowsFuture(cls):
		# Use the atom feed
		return True

	def getSeriesList(self, callback, show_name):
		# On Success: Return a series list of id, name tuples
		# On Failure: Return a empty list or None
		
		print "Wunschliste getSeriesList"
		
		self.getPage(
						boundFunction(self.getSeriesListCallback, callback),
						show_name,
						SERIESLISTURL + urlencode({ 'q' : show_name })
					)

	def getSeriesListCallback(self, callback, data=None):
		print "Wunschliste getSeriesListCallback"
		print callback, data
		serieslist = []
		if data:
			for line in data.splitlines():
				values = line.split("|")
				print values
				if len(values) == 3:
					name, countryyear, id = values
					#serieslist.append( (id, name + " (" + countryyear + ")" ) )
					serieslist.append( (id, name) )
				else:
					print "Wunschliste: ParseError: " + str(line)
		serieslist.reverse()
		callback( serieslist )

	def getEpisode(self, callback, show_name, short, description, begin, end=None, channel=None):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or None
		
		# Check preconditions
		if not show_name:
			print _("Skip Wunschliste: No show name specified")
			return callback( None )
		if not begin:
			print _("Skip Wunschliste: No begin timestamp specified")
			return callback( None )
		
		print "Wunschliste getEpisode"
		
		self.getSeriesList(
						boundFunction(self.getSeriesCallback, callback, show_name, short, description, begin, end, channel),
						show_name
					)

	def getSeriesCallback(self, callback, show_name, short, description, begin, end, channel, ids=None):
		print "Wunschliste getSeriesCallback"
		#print data
		if ids:
			#for id_name in data:
			id, name = ids.pop()
			print id, name
			
			#Py2.6
			delta = abs(datetime.now() - begin)
			delta = delta.seconds + delta.days * 24 * 3600
			#Py2.7 delta = abs(datetime.now() - begin).total_seconds()
			if delta > 3*60*60:
				url = EPISODEIDURLATOM + urlencode({ 's' : id })
				self.getPage(
								boundFunction(self.getEpisodeFutureCallback, callback, show_name, short, description, begin, end, channel, ids),
								show_name+str(begin),
								url
							)
			else:
				url = EPISODEIDURLPRINT + urlencode({ 's' : id })
				self.getPage(
								boundFunction(self.getEpisodeTodayCallback, callback, show_name, short, description, begin, end, channel, ids),
								show_name+str(begin),
								url
							)
		
		else:
			callback( None )

	def getEpisodeFutureCallback(self, callback, show_name, short, description, begin, end, channel, ids, data=None):
		print "Wunschliste getEpisodeFutureCallback"
		
		margin_before = max( 15, (config.recording.margin_before.value or 15) ) * 60
		#margin_after = max( 15, (config.recording.margin_after.value or 15) ) * 60
		
		channel = self.unifyChannel(channel)
		
		if data is not None:
			# Handle malformed HTML issues
			data = data.replace('&amp;','&')  # target=\"_blank\"&amp;
			
			parser = WLAtomParser()
			parser.feed(data)
			#print parser.list
			
			trs = parser.list
			if trs:
				for tds in trs:
					if tds and len(tds) == 2:
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
							delta = abs(begin - xbegin)
							delta = delta.seconds + delta.days * 24 * 3600
							#Py2.7 delta = abs(begin - xbegin).total_seconds()
							print begin, xbegin, delta, margin_before, delta < margin_before
							if delta < margin_before:
								# We actually don't check the channel - Any ideas?
								result = self.regexpatom.match(xtitle)
								if result and len(result.groups()) >= 5:
									xchannel = self.unifyChannel(result.group(5))
									print channel, xchannel
									if channel == xchannel:
										# series = result.group(1)
										xtitle = result.group(2)
										xseason = int(result.group(3) or 1)
										xepisode = int(result.group(4) or 0)
										return self.foundEpisode( callback, show_name+str(begin), (xseason, xepisode, xtitle.decode('ISO-8859-1').encode('utf8')) )
								#else:
								#	return self.foundEpisode( callback, show_name+str(begin), (0, 0, xtitle.decode('ISO-8859-1').encode('utf8')) )
			
		if ids:
			self.getSeriesCallback(callback, show_name, short, description, begin, end, channel, ids)
		else:
			self.foundEpisode( callback, show_name+str(begin) )

	def getEpisodeTodayCallback(self, callback, show_name, short, description, begin, end, channel, ids, data=None):
		print "Wunschliste getEpisodeTodayCallback"
		
		margin_before = max( 15, (config.recording.margin_before.value or 15) ) * 60
		#margin_after = max( 15, (config.recording.margin_after.value or 15) ) * 60
		
		channel = self.unifyChannel(channel)
		print "Channel", channel
		
		if data is not None:
			parser = WLPrintParser()
			parser.feed(data)
			#print parser.list
			
			year = str(datetime.today().year)
			
			trs = parser.list
			if trs:
				for tds in trs:
					if tds and len(tds) == 5:
						xchannel, xdate, xbegin, xend, xtitle = tds
						
						#xchannel = channel.contents[0]
						xdate    = xdate[3:]+year
						#xbegin   = xbegin.
						xbegin   = datetime.strptime( xdate+xbegin, "%d.%m.%Y%H.%M Uhr" )
						#xend     = xend.contents[0]
						#xend     = datetime.strptime( xdate+xend, "%d.%m.%Y%H.%M Uhr" )
						#print xchannel, xdate, xbegin, xend, xtitle
						#print datebegin, xbegin, abs((datebegin - xbegin)), margin_before
						
						#Py2.6
						delta = abs(begin - xbegin)
						delta = delta.seconds + delta.days * 24 * 3600
						#Py2.7 delta = abs(begin - xbegin).total_seconds()
						print begin, xbegin, delta, margin_before, delta < margin_before
						if delta < margin_before:
							xchannel = self.unifyChannel(xchannel)
							print channel, xchannel
							if channel == xchannel:
								# We actually don't check the channel - Any ideas?
								result = self.regexpprint.match(xtitle)
								if result and len(result.groups()) >= 3:
									xseason = int(result.group(1) or 1)
									xepisode = int(result.group(2) or 0)
									xtitle = result.group(3)
									return self.foundEpisode( callback, show_name+str(begin), (xseason, xepisode, xtitle.decode('ISO-8859-1').encode('utf8')) )
							#else:
							#	return self.foundEpisode( callback, show_name+str(begin), (0, 0, xtitle.decode('ISO-8859-1').encode('utf8')) )
			
		if ids:
			self.getSeriesCallback(callback, show_name, short, description, begin, end, channel, ids)
		else:
			self.foundEpisode( callback, show_name+str(begin) )

	def getPage(self, callback, name, url, expires=None):
		# PHP Proxy with 3 day Caching
		# to minimize server requests
		url = 'http://betonme.lima-city.de/SeriesPlugin/proxy.php?' + urlencode({ 'url' : url })
		if expires:
			IdentifierBase.getPage(self, callback, name, url, expires)
		else:
			IdentifierBase.getPage(self, callback, name, url)
