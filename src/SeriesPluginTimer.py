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
		
		splog("SeriesPluginTimer")
		splog(name, timer.name)
		
		# We have to compare the length,
		# because of the E2 special chars handling for creating the filenames
		#if timer.name == name:
		# Mad Men != Mad_Men
		
		epgcache = eEPGCache.getInstance()
		
		if timer.eit:
			event = epgcache.lookupEventId(timer.service_ref.ref, timer.eit)
			splog("LookupEventId event found")
			
		else:
			#timer.service_ref.toString()
			#timer.service_ref.ref.toString()
			events = epgcache.lookupEvent(["N" , (timer.service_ref.ref, 0, begin, end)]);
			splog("LookupEvent event(s) found", len(events) )
			splog(events)
			event = events and events[0]
		
		if (not event):
			splog("Skip timer because no event was found", timer.name, name, len(timer.name), len(name))
			return
		
		if not ( len(timer.name) == len(name) == len(event.getEventName()) ):
			splog("Skip timer because it is already modified", timer.name, name, event and event.getEventName(), len(timer.name), len(name), len(event.getEventName()) )
			return
		
		if timer.begin < time() + 60:
			splog("Skipping an event because it starts in less than 60 seconds", timer.name )
			return
		
		if timer.isRunning():
			splog("Skipping timer because it is already running", timer.name )
			return
		
		if timer.justplay:
			splog("Skipping justplay timer", timer.name )
			return
		
		self.timer = timer
		
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
		#if self.seriesPlugin and self.seriesPlugin.queueEmpty() and SeriesPluginTimer.data:
		if self.seriesPlugin and SeriesPluginTimer.data:
			splog("SeriesPluginTimer " + " ".join(SeriesPluginTimer.data))
			
#TBD Because of E2 Update 05.2013
		#from threading import currentThread
		#if currentThread().getName() == 'MainThread':
#NoTimerPopUpPossibleActually
#			if config.plugins.seriesplugin.timer_popups.value:
#				try:
#					AddPopup(
#						"SeriesPlugin:\n" + "\n".join(SeriesPluginTimer.data),
#						MessageBox.TYPE_ERROR,
#						0,
#						'SP_PopUp_ID_TimerFinished'
#					)
#				except Exception, e:
#					splog("SeriesPluginTimer AddPopup Exception:", str(e))
			
			SeriesPluginTimer.data = []
			
