﻿# -*- coding: utf-8 -*-
# by betonme @2012

import os, sys
import json
import re
import math

from sys import maxint

from Components.config import config
from Tools.BoundFunction import boundFunction

# Imports
from urllib import urlencode

from time import time
from datetime import datetime, timedelta

# Internal
from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase
from Plugins.Extensions.SeriesPlugin.Channels import compareChannels
from Plugins.Extensions.SeriesPlugin.Logger import splog

from bs4 import BeautifulSoup
#from HTMLParser import HTMLParser

import codecs
utf8_encoder = codecs.getencoder("utf-8")


# Constants
SERIESLISTURL = "http://www.fernsehserien.de/suche?"
EPISODEIDURL = 'http://www.fernsehserien.de%s/sendetermine/%d'

max_time_drift = int(config.plugins.seriesplugin.max_time_drift.value) * 60

Headers = {
		'User-Agent' : 'Mozilla/5.0',
		'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
		'Accept-Encoding':'',
		'Accept-Language':'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4',
		'Cache-Control':'no-cache',
		'Connection':'keep-alive',
		'Host':'www.fernsehserien.de',
		'Pragma':'no-cache'
	}


def str_to_utf8(s):
	# Convert a byte string with unicode escaped characters
	splog("FS: str_to_utf8: s: ", repr(s))
	# Python 2.x can't convert the special chars nativly
	utf8_str = utf8_encoder(s)[0]
	splog("FS: str_to_utf8: s: ", repr(utf8_str))
	return utf8_str


class Fernsehserien(IdentifierBase):
	def __init__(self):
		IdentifierBase.__init__(self)

	@classmethod
	def knowsElapsed(cls):
		return True

	@classmethod
	def knowsToday(cls):
		return True

	@classmethod
	def knowsFuture(cls):
		return True

	def getEpisode(self, name, begin, end=None, channels=[]):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or String or None
		
		self.begin = begin
		#self.year = datetime.fromtimestamp(begin).year
		self.end = end
		self.channels = channels
		
		self.series = ""
		self.first = None
		self.last = None
		self.page = 0
		
		self.knownids = []
		self.returnvalue = None
		
		# Check preconditions
		if not name:
			splog(_("Skip Fernsehserien: No show name specified"))
			return _("Skip Fernsehserien: No show name specified")
		if not begin:
			splog(_("Skip Fernsehserien: No begin timestamp specified"))
			return _("Skip Fernsehserien: No begin timestamp specified")
		
		if self.begin > datetime.now():
			self.future = True
		else:
			self.future = False
		splog("Fernsehserien getEpisode future", self.future)
	
		while name:	
			ids = self.getSeries(name)
			
			while ids:
				idserie = ids.pop()
				
				if idserie and len(idserie) == 2:
					id, idname = idserie
					
					# Handle encodings
					self.series = str_to_utf8(idname)
					
					self.page = 0
					#if self.future:
					#	self.page = 0
					#else:
					#	self.page = -1
					
					self.first = None
					self.last = None
					
					while self.page is not None:
						result = self.getNextPage(id)
						if result:
							return result
					
			else:
				name = self.getAlternativeSeries(name)
		
		else:
			return ( self.returnvalue or _("No matching series found") )

	def getSeries(self, name):
		parameter =  urlencode({ 'term' : re.sub("[^a-zA-Z0-9*]", " ", name) })
		url = SERIESLISTURL + parameter
		data = self.getPage(url, Headers)
		
		if data and isinstance(data, basestring):
			data = self.parseSeries(data)
			self.doCacheList(url, data)
		
		if data and isinstance(data, list):
			splog("Fernsehserien ids", data)
			return self.filterKnownIds(data)

	def parseSeries(self, data):
		serieslist = []
		for line in json.loads(data):
			id = line['id']
			idname = line['value']
			splog(id, idname)
			serieslist.append( ( id, idname ) )
		serieslist.reverse()
		return serieslist

	def parseNextPage(self, data):
		trs = []
		
		# Handle malformed HTML issues
		data = data.replace('\\"','"')  # target=\"_blank\"
		data = data.replace('\'+\'','') # document.write('<scr'+'ipt
		
		soup = BeautifulSoup(data)
		
		table = soup.find('table', 'sendetermine')
		if table:
			for trnode in table.find_all('tr'):
				# TODO skip first header row
				tdnodes = trnode and trnode.find_all('td')
				
				if tdnodes:
					# Filter for known rows
					#if len(tdnodes) == 7 and len(tdnodes[2].string) >= 15:
					
					if len(tdnodes) >= 6 and tdnodes[2].string and len(tdnodes[2].string) >= 15:
						tds = []
						for tdnode in tdnodes:
							tds.append(tdnode.string or "")
						trs.append( tds )
					# This row belongs to the previous
					elif trs and len(tdnodes) == 5:
						#if trs[-1][5] and tdnodes[3].string:
						trs[-1][5] += ' ' + (tdnodes[3].string or "")
						#if trs[-1][6] and tdnodes[4].string:
						trs[-1][6] += ' ' + (tdnodes[4].string or "")
					#else:
					#	splog( "tdnodes", len(tdnodes), tdnodes )
				
				#else:
				#	splog( "tdnodes", tdnodes )
		
		#splog(trs)
		return trs

	def getNextPage(self, id):
		url = EPISODEIDURL % (id, self.page)
		data = self.getPage(url, Headers)
		
		if data and isinstance(data, basestring):
			splog("getNextPage: basestring")
			data = self.parseNextPage(data)
			self.doCacheList(url, data)
		
		if data and isinstance(data, list):
			splog("getNextPage: list")
			
			trs = data
			# trs[x] = [None, u'31.10.2012', u'20:15\u201321:15 Uhr', u'ProSieben', u'8.', u'15', u'Richtungswechsel']

			yepisode = None
			ydelta = maxint
			
			#first = trs[0][2]
			#last = trs[-1][2]
			#print first[0:5]
			#print last[6:11] 
			
			# trs[0] first line [2] second element = timestamps [a:b] use first time
			first = datetime.strptime( trs[0][2][0:5] + trs[0][1], "%H:%M%d.%m.%Y" )
			
			# trs[-1] last line [2] second element = timestamps [a:b] use second time
			#last = datetime.strptime( trs[-1][2][6:11] + trs[-1][1], "%H:%M%d.%m.%Y" )
			# Problem with wrap around use also start time
			# Sa 30.11.2013 23:35 - 01:30 Uhr ProSieben 46 3. 13 Showdown 3
			last = datetime.strptime( trs[-1][2][0:5] + trs[-1][1], "%H:%M%d.%m.%Y" )
			
			#first = first - timedelta(seconds=max_time_drift)
			#last = last + timedelta(seconds=max_time_drift)
			
			new_page = (self.first != first or self.last != last)
			splog("getNextPage: first_on_prev_page, first, last_on_prev_page, last, if: ", self.first, first, self.last, last, new_page)
			if new_page:
				self.first = first
				self.last = last
				
				test_future_timespan = ( (first-timedelta(seconds=max_time_drift)) <= self.begin and self.begin <= (last+timedelta(seconds=max_time_drift)) ) 
				test_past_timespan = ( (first+timedelta(seconds=max_time_drift)) >= self.begin and self.begin >= (last+timedelta(seconds=max_time_drift)) )
				splog("first_on_page, self.begin, last_on_page, if, if:", first, self.begin, last, test_future_timespan, test_past_timespan )
				if ( test_future_timespan or test_past_timespan ):
					#search in page for matching datetime
					for tds in trs:
						if tds and len(tds) >= 6:  #7:
							# Grey's Anathomy
							# [None, u'31.10.2012', u'20:15\u201321:15 Uhr', u'ProSieben', u'8.', u'15', u'Richtungswechsel']
							# 
							# Gute Zeiten 
							# [None, u'20.11.2012', u'06:40\u201307:20 Uhr', u'NDR', None, u'4187', u'Folge 4187']
							# [None, u'01.12.2012', u'10:45\u201313:15 Uhr', u'RTL', None, u'5131', u'Folge 5131']
							# [None, u'\xa0', None, u'5132', u'Folge 5132']
							# [None, u'\xa0', None, u'5133', u'Folge 5133']
							# [None, u'\xa0', None, u'5134', u'Folge 5134']
							# [None, u'\xa0', None, u'5135', u'Folge 5135']
							
							# Wahnfried
							# [u'Sa', u'26.12.1987', u'\u2013', u'So', u'27.12.1987', u'1Plus', None]
							
							# First part: date, times, channel
							xdate, xbegin = tds[1:3]
							#splog( "tds", tds )
							
							#xend = xbegin[6:11]
							xbegin = xbegin[0:5]
							xbegin = datetime.strptime( xbegin+xdate, "%H:%M%d.%m.%Y" )
							#xend = datetime.strptime( xend+xdate, "%H:%M%d.%m.%Y" )
							#print "xbegin", xbegin
							
							#Py2.6
							delta = abs(self.begin - xbegin)
							delta = delta.seconds + delta.days * 24 * 3600
							#Py2.7 delta = abs(self.begin - xbegin).total_seconds()
							splog(self.begin, xbegin, delta, max_time_drift)
							
							if delta <= max_time_drift:
								
								if compareChannels(self.channels, tds[3]):
									
									if delta < ydelta:
										
										splog( "tds", len(tds), tds )
										if len(tds) >= 10:
											# Second part: s1e1, s1e2,
											xseason = tds[7] or "1"
											xepisode = tds[8]
											xtitle = " ".join(tds[10:])  # Use all available titles
										elif len(tds) >= 7:
											# Second part: s1e1, s1e2,
											xseason = tds[4]
											xepisode = tds[5]
											if xseason and xseason.find(".") != -1:
												xseason = xseason[:-1]
												xtitle = " ".join(tds[6:])  # Use all available titles
											else:
												xseason = "1"
												xtitle = " ".join(tds[6:])  # Use all available titles
										elif len(tds) == 6:
											xseason = "0"
											xepisode = "0"
											xtitle = tds[5]
										if xseason and xepisode and xtitle and self.series:
										
											# Handle encodings
											xtitle = str_to_utf8(xtitle)
											
											yepisode = (xseason, xepisode, xtitle, self.series)
											ydelta = delta
									
									else: #if delta >= ydelta:
										break
								
								else:
									self.returnvalue = _("Check the channel name")
								
							elif yepisode:
								break
					
					if yepisode:
						return ( yepisode )
				
				else:
					# TODO calculate next page : use firstrow lastrow datetime
					if not self.future:
						if first > self.begin:
							self.page -= 1
							return
					
					else:
						if self.begin > last:
							self.page += 1
							return
		
		self.page = None
		return
