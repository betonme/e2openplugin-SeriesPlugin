# by betonme @2012

import math
from sys import maxint

from Components.config import config

# Imports
from urlparse import urljoin
from urllib import urlencode
from urllib2 import Request, urlopen, URLError

from HTMLParser import HTMLParser

from datetime import datetime

from Tools.BoundFunction import boundFunction

# Internal
from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase
from Plugins.Extensions.SeriesPlugin.Helper import unifyChannel
from Plugins.Extensions.SeriesPlugin.Logger import splog


# Constants
SERIESLISTURL = "http://www.wunschliste.de/ajax/search_dropdown.pl?"
EPISODEIDURL = 'http://www.fernsehserien.de/'
EPISODEIDPARAMETER = 'index.php?serie=%s&seite=%d&sender=%s&start=%d'


class FSParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		# Hint: xpath from Firebug without tbody elements
		xpath = '/html/body/div[2]/div[2]/div/table/tr[3]/td/div/table[2]/tr/td'
		self.xpath = [ e for e in xpath.split('/') if e ]
		self.xpath.reverse()

		self.lookfor = self.xpath.pop()
		self.waitforendtag = 0

		self.start = False
		self.table = False
		self.tr= False
		self.td= False
		self.data = []
		self.list = []

	def handle_starttag(self, tag, attributes):
		if self.waitforendtag == 0:
			if tag == self.lookfor:
				if self.xpath:
					self.lookfor = self.xpath.pop()
					s = self.lookfor.split('[')
					if len(s) == 2:
						self.lookfor = s[0]
						self.waitforendtag = int( s[1].split(']' )[0]) - 1
				else:
					self.start = True

		if self.start and tag == 'table':
			self.table = True

		if self.table:
			if tag == 'td':
				self.td= True
			elif tag == 'tr':
				self.tr= True

	def handle_endtag(self, tag):
		if self.table:
			if tag == 'td':
				self.td= False
			elif tag == 'tr':
				self.tr= False
				self.list.append(self.data)
				self.data= []

		if tag == 'table':
			self.table = False

		if tag == self.lookfor:
			if self.waitforendtag > 0: self.waitforendtag -= 1

	def handle_data(self, data):
		if self.tr and self.td:
			self.data.append(data)


class Fernsehserien(IdentifierBase):
	def __init__(self):
		IdentifierBase.__init__(self)
		self.id = 0
		self.when = 0
		self.page = 0
		self.lastpage = 0
		self.minpages = -1
		self.maxpages = maxint

	@classmethod
	def knowsElapsed(cls):
		return True

#	@classmethod
#	def knowsToday(cls):
#		return True

#	@classmethod
#	def knowsFuture(cls):
#		return True

	def getEpisode(self, callback, name, begin, end=None, channel=None):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or None
		
		self.callback = callback
		self.name = name
		self.begin = begin
		self.end = end
		self.channel = channel
		self.ids = []
		
		self.id = 0
		self.when = 0
		
		self.page = 0
		self.lastpage = 0
		self.minpages = -1
		self.maxpages = maxint
		
		# Check preconditions
		if not name:
			splog(_("Skip Fernsehserien: No show name specified"))
			return callback()
		if not begin:
			splog(_("Skip Fernsehserien: No begin timestamp specified"))
			return callback()
		
		splog("Fernsehserien getEpisode")
		
		#Py2.6
		delta = abs(datetime.now() - self.begin)
		delta = delta.seconds + delta.days * 24 * 3600
		#Py2.7 delta = abs(datetime.now() - self.begin).total_seconds()
		if delta > 3*60*60:
		#if self.begin - time.time() < -2*60*60:
			# Older than 3 hours
			splog("Past events")
			self.when = 6 # Past events
		else:
			splog("Today events")
			self.when = 8 # Today events
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
		splog("Fernsehserien getSeriesListCallback")
		serieslist = []
		
		if data and isinstance(data, basestring):
		#if data and not isinstance(data, list):
			for line in data.splitlines():
				values = line.split("|")
				if len(values) == 3:
					idname, countryyear, id = values
					splog(id, idname)
					serieslist.append( id )
				else:
					splog("Fernsehserien: ParseError: " + str(line))
			serieslist.reverse()
			data = serieslist
		
		if data and isinstance(data, list):
			self.ids = data[:]
			self.getNextSeries()
		else:
			self.getAlternativeSeries()
		return data

	def getNextSeries(self):
		splog("Fernsehserien getNextSeries", self.ids)
		if self.ids:
			#for id_name in data:
			self.id = self.ids.pop()
			
			self.page = 0
			self.lastpage = 0
			self.minpages = -1
			self.maxpages = maxint
			
			self.getNextPage()
		
		else:
			self.callback()

	def getNextPage(self):
		splog("page, lastpage, minpages, maxpages ", self.page, self.lastpage, self.minpages, self.maxpages)
		nextpage = int(self.page)
		if self.maxpages <= nextpage: nextpage = self.maxpages - 1
		if nextpage <= self.minpages: nextpage = self.minpages + 1
		self.lastpage = nextpage
		start = nextpage * 100 or -1 # Norm to x00 -> Caching is only working for equal URLs
		splog("page, lastpage, minpages, maxpages, start ", self.page, self.lastpage, self.minpages, self.maxpages, start)
		
		url = urljoin(EPISODEIDURL, EPISODEIDPARAMETER % (self.id, self.when, "", start))
		if ( self.minpages < nextpage < self.maxpages ):
			self.getPage(
									self.getEpisodeFromPage,
									url
								)
		
		else:
			self.getNextSeries()

	def getEpisodeFromPage(self, data=None):
		splog("Fernsehserien getEpisodeCallback")
		
		if data and isinstance(data, basestring):
		#if data and not isinstance(data, FSParser):
		#if data is not None:
			
			# Handle malformed HTML issues
			data = data.replace('\\"','"')  # target=\"_blank\"
			data = data.replace('\'+\'','') # document.write('<scr'+'ipt
			
			parser = FSParser()
			parser.feed(data)
			#splog(parser.list)
			
			data = parser
		
		if data: # and isinstance(data, FSParser): #Why is this not working after restarting the SeriesPlugin service
			trs = data.list
			if not trs:
				# Store self.maxpages as callback parameter
				splog("minpages < maxpages", (self.minpages < self.maxpages))
				if self.minpages < self.maxpages:
					self.maxpages = min(self.maxpages, self.lastpage) if self.maxpages else self.lastpage
					splog("min, max, lastpage, ", self.minpages, self.maxpages, self.lastpage)
					#self.lastpage
					#calculate next fallback page:
					diffpages = (self.maxpages-self.minpages) // 2 # integer division = floor = round down            # TEST / 4 !!!     # diffpages = diffpages / 2 #/ 100 * 100 # Norm to x00
					
					#TEST
					#self.lastpage = self.page
					self.page = self.minpages + diffpages
					self.lastpage = self.page
					#TEST END
					splog("min, max, lastpage, diffpages, page, ", self.minpages, self.maxpages, self.lastpage, diffpages, self.page)
					self.getNextPage()
					return data
			
			else:
				yepisode = None
				ydelta = maxint
				
				first = trs[0]
				first = datetime.strptime( first[1]+first[2].split("-")[0], "%d.%m.%y%H:%M" )
				last = trs[-1]
				last = datetime.strptime( last[1]+last[2].split("-")[0], "%d.%m.%y%H:%M" )
				
				splog("first, self.begin, last, if ", first, self.begin, last, ( first <= self.begin and self.begin <= last ))
				if ( first <= self.begin and self.begin <= last ):
					#search in page for matching datetime
					for tds in trs:
						if tds and len(tds) >= 6:
							#'Sa', '19.05.12', '15:00-15:30', 'SuperRTL', '1.12a', '1.12b', 'Das Gef\xe4ngnis Cabana /', ' Das Bootel'] 
							
							# Complete line
							# Di	27.03.12	08:50-09:15	ProSieben	3.01	Der Nordpol-Plan
							# Mi	02.05.12	16:15-17:05	RTL II	105	Folge 105
							
							# First part: day, date, times, channel
							xday, xdate, xbegin, xchannel = tds[:4]
							
							xbegin, xend = xbegin.split("-")
							xbegin = datetime.strptime( xdate+xbegin, "%d.%m.%y%H:%M" )
							#xend = datetime.strptime( xdate+xend, "%d.%m.%y%H:%M" )
							
							#Py2.6
							delta = abs(self.begin - xbegin)
							delta = delta.seconds + delta.days * 24 * 3600
							#Py2.7 delta = abs(self.begin - xbegin).total_seconds()
							splog(self.begin, xbegin, delta, int(config.plugins.seriesplugin.max_time_drift.value)*60)
							
							if delta <= int(config.plugins.seriesplugin.max_time_drift.value) * 60:
								xchannel = unifyChannel(xchannel)
								splog(self.channel, xchannel, len(self.channel), len(xchannel))
								
								if self.compareChannels(self.channel, xchannel):
									
									if delta < ydelta:
										# Second part: s1e1, s1e2, ..., title1, title2, ...
										xepisode = tds[4]                      # Use only the first one
										xtitle = "".join(tds[(len(tds)-4)/2+4:])  # Use all available titles
										
										if xepisode.find(".") != -1:
											xseason, xepisode = xepisode.split(".")
										else:
											xseason = "1"
											xepisode = "0"
										yepisode = (xseason or "1", xepisode or "0", xtitle.decode('iso-8859-1').encode('utf8'))
										ydelta = delta
										#self.callback( yepisode )
										#return data
									
									else: #if delta >= ydelta:
										break
							
							elif yepisode:
								break
					
					if yepisode:
						self.callback( yepisode )
						return data
				
				else:
					#calculate next page : use firtsrow lastrow datetime
					splog("( first > begin )", ( first > self.begin ))
					splog("( begin > last )", ( self.begin > last ))
					if ( first > self.begin ):
						self.maxpages = min(self.maxpages, self.lastpage) if self.maxpages else self.lastpage
					elif ( self.begin > last ):
						self.minpages = max(self.minpages, self.lastpage) if self.minpages else self.lastpage
					
					#Py2.6
					diff = abs(self.begin - last)
					diff = diff.seconds + diff.days * 24 * 3600
					#Py2.7 diff = abs(self.begin - last).total_seconds()
					
					#Py2.6
					pageination = abs(last - first)
					pageination = pageination.seconds + pageination.days * 24 * 3600
					#Py2.7 pageination = abs(last - first).total_seconds()
					
					diffpages = abs(diff / pageination)
					self.page = self.lastpage + diffpages
					splog("minpages, pageination, diff, diffpages, page ", self.minpages, pageination, diff, diffpages, self.page)
					self.getNextPage()
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
