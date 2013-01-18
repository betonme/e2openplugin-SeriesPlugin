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

from time import time
from enigma import eEPGCache
from ServiceReference import ServiceReference

# Config
from Components.config import *

from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup

# Plugin internal
from SeriesPlugin import getInstance, refactorTitle, refactorDescription
from Logger import splog


#######################################################
# Label timer
class SeriesPluginTimer(object):

	data = []
	
	def __init__(self, timer, name, begin, end):
		
		# We have to compare the length,
		# because of the E2 special chars handling for creating the filenames
		#if timer.name == name:
		# Mad Men != Mad_Men
		epgcache = eEPGCache.getInstance()
		event = epgcache.lookupEventId(timer.service_ref.ref, timer.eit)
		
		if (not event):
			splog("Skip timer because no event was found", timer.name, name, len(timer.name), len(name))
		
		if not ( len(timer.name) == len(name) == len(event.getEventName()) ):
			splog("Skip timer because it is already modified", timer.name, name, event and event.getEventName(), len(timer.name), len(name), len(event.getEventName()) )
			return
		
		if timer.begin < time() + 60:
			splog("Skipping an event because it starts in less than 60 seconds", timer.name )
			return
		
		if timer.isRunning() and not timer.justplay:
			splog("Skipping timer because it is already running", timer.name )
			return
		
		if timer.justplay:
			splog("Skipping justplay timer", timer.name )
			return
		
		self.timer = timer
		
		splog("SeriesPluginTimer")
		splog(name, timer.name)
		
		self.seriesPlugin = getInstance()
		
		if timer.service_ref:
			#channel = timer.service_ref.getServiceName()
			#splog(channel)
			
			self.seriesPlugin.getEpisode(
					self.timerCallback,
					#name, begin, end, channel, future=True
					name, begin, end, str(timer.service_ref), future=True
				)
		else:
			splog("SeriesPluginTimer: No channel specified")
			self.timerCallback("No channel specified")

	def timerCallback(self, data=None):
		splog("SeriesPluginTimer timerCallback")
		splog(data)
		timer = self.timer
		
		if data and len(data) == 4 and timer:
			# Episode data available, refactor name and description
			from SeriesPluginRenamer import newLegacyEncode
			timer.name = refactorTitle(timer.name, data)
			#timer.name = newLegacyEncode(refactorTitle(timer.name, data))
			timer.description = refactorDescription(timer.description, data)
		
		elif data:
			SeriesPluginTimer.data.append(
				str(timer.name) + " " + str( data )
			)
		
		else:
			SeriesPluginTimer.data.append(
				str(timer.name) + " " + _("No data available")
			)
		
		# Maybe there is a better way to avoid multiple Popups
		#print "QUEUE SIZE", self.seriesPlugin.queue.qsize()
		if self.seriesPlugin and self.seriesPlugin.queueEmpty() and SeriesPluginTimer.data:
			if config.plugins.seriesplugin.timer_popups.value:
				AddPopup(
					"SeriesPlugin:\n" + "\n".join(SeriesPluginTimer.data),
					MessageBox.TYPE_ERROR,
					0,
					'SP_PopUp_ID_TimerFinished'
				)
			
			SeriesPluginTimer.data = []
			
