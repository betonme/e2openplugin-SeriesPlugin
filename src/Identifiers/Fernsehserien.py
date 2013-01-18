# by betonme @2012

import math
import re
from sys import maxint

from Components.config import config

# Imports
from urlparse import urljoin
from urllib import urlencode
from urllib2 import Request, urlopen, URLError

from HTMLParser import HTMLParser

from datetime import datetime, timedelta

from Tools.BoundFunction import boundFunction

from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase


# Constants
SERIESLISTURL = "http://www.wunschliste.de/ajax/search_dropdown.pl?"
EPISODEIDURL = 'http://www.fernsehserien.de/'
EPISODEIDPARAMETER = 'index.php?serie=%s&seite=%d&sender=%s&start=%d'


class FSParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		# Hint: xpath from Firebug without tbody elements
		xpath = '/html/body/div[2]/div[2]/div/table/tr[3]/td/div/table[2]/tr/td[2]/table'
		self.xpath = [ e for e in xpath.split('/') if e ]
		self.xpath.reverse()

		self.lookfor = self.xpath.pop()
		self.waitforendtag = 0

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

		if tag == self.lookfor:
				if self.waitforendtag > 0: self.waitforendtag -= 1
				self.table = False

	def handle_data(self, data):
		if self.tr and self.td:
				self.data.append(data)



class Fernsehserien(IdentifierBase):
	def __init__(self):
		IdentifierBase.__init__(self)

	@classmethod
	def knowsElapsed(cls):
		return True

#	@classmethod
#	def knowsToday(cls):
#		return True

#	@classmethod
#	def knowsFuture(cls):
#		return True

	def getSeriesList(self, callback, show_name):
		# On Success: Return a series list of id, name tuples
		# On Failure: Return a empty list or None
		print "Fernsehserien getSeriesList"
		
		self.getPage(
						boundFunction(self.getSeriesListCallback, callback),
						show_name,
						SERIESLISTURL + urlencode({ 'q' : show_name })
					)

	def getSeriesListCallback(self, callback, data=None):
		print "Fernsehserien getSeriesListCallback"
		serieslist = []
		if data:
			for line in data.splitlines():
				values = line.split("|")
				if len(values) == 3:
					name, countryyear, id = values
					#serieslist.append( (id, name + " (" + countryyear + ")" ) )
					serieslist.append( (id, name) )
				else:
					print "Fernsehserien: ParseError: " + str(line)
		serieslist.reverse()
		callback( serieslist )

	def getEpisode(self, callback, show_name, short, description, begin, end=None, channel=None):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or None
		
		# Check preconditions
		if not show_name:
			print _("Skip Fernsehserien: No show name specified")
			return callback( None )
		if not begin:
			print _("Skip Fernsehserien: No begin timestamp specified")
			return callback( None )
		
		print "Fernsehserien getEpisode"
		
		self.getSeriesList(
						boundFunction(self.getSeriesCallback, callback, show_name, short, description, begin, end, channel),
						show_name
					)

	def getSeriesCallback(self, callback, show_name, short, description, begin, end, channel, ids=None):
		print "Fernsehserien getSeriesCallback"
		if ids:
			#for id_name in data:
			id, name = ids.pop()
			print id, name
			#Py2.6
			delta = abs(datetime.now() - begin)
			delta = delta.seconds + delta.days * 24 * 3600
			#Py2.7 delta = abs(datetime.now() - begin).total_seconds()
			if delta > 3*60*60:
			#if begin - time.time() < -2*60*60:
				# Older than 3 hours
				print "Past events"
				type = 6 # Past events
			else:
				print "Today events"
				type = 8 # Today events
			
			channel = self.unifyChannel(channel)
			
			self.getNextPage(callback, show_name, short, description, begin, end, channel, ids, id, type)
				
		else:
			callback( None )

	def getNextPage(self, callback, show_name, short, description, begin, end, channel, ids, id, type, page=0, lastpage=0, minpages=-1, maxpages=maxint):
		
		print "page, lastpage, minpages, maxpages ", page, lastpage, minpages, maxpages
		nextpage = int(page)
		if maxpages <= nextpage: nextpage = maxpages - 1
		if nextpage <= minpages: nextpage = minpages + 1
		lastpage = nextpage
		start = nextpage * 100 or -1 # Norm to x00 -> Caching is only working for equal URLs
		print "page, lastpage, minpages, maxpages, start ", page, lastpage, minpages, maxpages, start
		
		url = urljoin(EPISODEIDURL, EPISODEIDPARAMETER % (id, type, "", start))
		if ( minpages < nextpage < maxpages ):
			self.getPage(
									boundFunction(self.getEpisodeFromPage, callback, show_name, short, description, begin, end, channel, ids, id, type, page, lastpage, minpages, maxpages),
									show_name+str(begin),
									url
								)
		
		else:
			if ids:
				self.getSeriesCallback(callback, show_name, short, description, begin, end, channel, ids)
			else:
				self.foundEpisode( callback, show_name+str(begin) )

	def getEpisodeFromPage(self, callback, show_name, short, description, begin, end, channel, ids, id, type, page, lastpage, minpages, maxpages, data=None):
		print "Fernsehserien getEpisodeCallback"
		
		margin_before = max( 15, (config.recording.margin_before.value or 15) ) * 60
		#margin_after = max( 15, (config.recording.margin_after.value or 15) ) * 60
		
		if data is not None:
			
			# Handle malformed HTML issues
			data = data.replace('\\"','"')  # target=\"_blank\"
			data = data.replace('\'+\'','') # document.write('<scr'+'ipt
			
			parser = FSParser()
			parser.feed(data)
			#print parser.list
			
			trs = parser.list
			if not trs:
				# Store maxpages as callback parameter
				print "minpages < maxpages", (minpages < maxpages)
				if minpages < maxpages:
					maxpages = min(maxpages, lastpage) if maxpages else lastpage
					print "min, max, lastpage, ", minpages, maxpages, lastpage
					#lastpage
					#calculate next fallback page:
					diffpages = (maxpages-minpages) // 2 # integer division = floor = round down            # TEST / 4 !!!     # diffpages = diffpages / 2 #/ 100 * 100 # Norm to x00
					page = minpages + diffpages
					lastpage = page
					print "min, max, lastpage, diffpages, page, ", minpages, maxpages, lastpage, diffpages, page
					return self.getNextPage(callback, show_name, short, description, begin, end, channel, ids, id, type, page, lastpage, minpages, maxpages)
			
			else:
				first = trs[0]
				first = datetime.strptime( first[1]+first[2].split("-")[0], "%d.%m.%y%H:%M" ) - timedelta(seconds=margin_before)
				last = trs[-1]
				last = datetime.strptime( last[1]+last[2].split("-")[0], "%d.%m.%y%H:%M" )
				
				print "first, begin, last, if ", first, begin, last, ( first <= begin and begin <= last )
				if ( first <= begin and begin <= last ):
					#search in page for matching datetime
					for tds in trs:
						if tds and len(tds) == 6 :
							# Di	27.03.12	08:50-09:15	ProSieben	3.01	Der Nordpol-Plan
							# Mi	02.05.12	16:15-17:05	RTL II	105	Folge 105
							xday, xdate, xbegin, xchannel, xseason, xtitle = tds
							
							xbegin, xend = xbegin.split("-")
							xbegin = datetime.strptime( xdate+xbegin, "%d.%m.%y%H:%M" )
							#xend = datetime.strptime( xdate+xend, "%d.%m.%y%H:%M" )
							
							#Py2.6
							delta = abs(begin - xbegin)
							delta = delta.seconds + delta.days * 24 * 3600
							#Py2.7 delta = abs(begin - xbegin).total_seconds()
							print begin, xbegin, delta, margin_before, delta < margin_before
							if delta < margin_before:
								xchannel = self.unifyChannel(xchannel)
								print channel, xchannel
								if channel == xchannel:
									if xseason.find("."):
										xseason, xepisode = xseason.split(".")
									else:
										xepisode = 1
									return self.foundEpisode( callback, show_name+str(begin), ( (int(xseason or 1), int(xepisode or 0), xtitle.decode('iso-8859-1').encode('utf8')) ) )
				
				else:
					#calculate next page : use firtsrow lastrow datetime
					print "( first > begin )", ( first > begin )
					print "( begin > last )", ( begin > last )
					if ( first > begin ):
						maxpages = min(maxpages, lastpage) if maxpages else lastpage
					elif ( begin > last ):
						minpages = max(minpages, lastpage) if minpages else lastpage
					
					#Py2.6
					diff = abs(begin - last)
					diff = diff.seconds + diff.days * 24 * 3600
					#Py2.7 diff = abs(begin - last).total_seconds()
					
					#Py2.6
					pageination = abs(last - first)
					pageination = pageination.seconds + pageination.days * 24 * 3600
					#Py2.7 pageination = abs(last - first).total_seconds()
					
					diffpages = abs(diff / pageination)
					page = lastpage + diffpages
					print "minpages, pageination, diff, diffpages, page ", minpages, pageination, diff, diffpages, page
					return self.getNextPage(callback, show_name, short, description, begin, end, channel, ids, id, type, page, lastpage, minpages, maxpages)
		
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
