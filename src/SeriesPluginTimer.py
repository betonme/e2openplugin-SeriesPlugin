#######################################################################
#
#    Series Plugin for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=TBD
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

# for localized messages
from . import _

from datetime import datetime

# Config
from Components.config import *

from enigma import eEPGCache
from ServiceReference import ServiceReference

from Tools.BoundFunction import boundFunction

# Plugin internal
from SeriesPlugin import getInstance


#######################################################
# Label timer
class SeriesPluginTimer(object):
	def __init__(self, timer, begin=None, end=None):
		
		self.seriesPlugin = getInstance()
		
		self.epgCache = eEPGCache.getInstance()
		
		self.labelTimer(timer, begin, end)

	def labelTimer(self, timer, begin=None, end=None):
		print "SeriesPluginTimer label"
		#TODO Later timer list handling
		
		# Overwrite begin / end or use timer values
		begin = begin or timer.begin
		end = end or timer.end
		
		begin = datetime.fromtimestamp(begin)
		end = datetime.fromtimestamp(end)
		
		short = timer.description
		print short
		
		if hasattr(timer, 'extdesc'):
			print "hasattr"
			extdesc = timer.extdesc
		else:
			print "epgcache"
			event = epgcache.lookupEventId(timer.service_ref.ref, timer.eit)
			extdesc = event and event.getExtendedDescription() or ''
		print extdesc
		
		print timer.service_ref
		channel = timer.service_ref and timer.service_ref.getServiceName()
		print channel
		
		
		self.seriesPlugin.getEpisode(
				boundFunction(self.callback, timer), 
				timer.name, short, extdesc, begin, end, channel, future=True
			)

	def callback(self, timer, data=None):
		print "SeriesPluginTimer callback"
		print data
		if data:
			# Episode data available, refactor name and description
			timer.name = self.seriesPlugin.refactorTitle(timer.name, data)
			print timer.name
			timer.description = self.seriesPlugin.refactorDescription(timer.description, data)
			print timer.description

