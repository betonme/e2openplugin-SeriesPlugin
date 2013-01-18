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

# Config
from Components.config import *

from ServiceReference import ServiceReference

from Tools.BoundFunction import boundFunction

# Plugin internal
from SeriesPlugin import getInstance, refactorTitle, refactorDescription


#######################################################
# Label timer
class SeriesPluginTimer(object):
	def __init__(self, timer, name, begin, end):
		self.timer = timer
		self.seriesPlugin = getInstance()
		
		print "SeriesPluginTimer label"
		print name, timer.name
		
		if timer.service_ref:
			channel = timer.service_ref.getServiceName()
			print channel
			
			self.seriesPlugin.getEpisode(
					self.timerCallback,
					name, begin, end, channel, future=True
				)
		else:
			print "SeriesPluginTimer: No channel specified"
			self.callback()

	def timerCallback(self, data=None):
		print "SeriesPluginTimer timerCallback"
		print data
		timer = self.timer
		if data and timer:
			# Episode data available, refactor name and description
			timer.name = refactorTitle(timer.name, data)
			print timer.name
			timer.description = refactorDescription(timer.description, data)
			print timer.description

