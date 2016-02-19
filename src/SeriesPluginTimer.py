﻿# -*- coding: utf-8 -*-
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

import os

# for localized messages
from . import _

from time import time
from enigma import eEPGCache
from ServiceReference import ServiceReference

# Config
from Components.config import *

from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup
from Tools.BoundFunction import boundFunction

# Plugin internal
from SeriesPlugin import getInstance, refactorTitle, refactorDescription, refactorDirectory
from Logger import log

TAG = "SeriesPlugin"

#######################################################
# Label timer
class SeriesPluginTimer(object):

	data = []
	counter = 0;
	
	def __init__(self):
		
		log.debug("SeriesPluginTimer: New instance")

	def getEpisode(self, timer, name, begin, end, block):
		
		log.info("timername, service, name, begin, end:", timer.name, str(timer.service_ref.ref), name, begin, end)
		
		if hasattr(timer, 'sp_in_queue'):
			if timer.sp_in_queue:
				msg = _("Skipping timer because it is already in queue")
				log.warning(msg, timer.name)
				timer.log(601, "[SeriesPlugin]" + " " + msg )
				return
		
		# We have to compare the length,
		# because of the E2 special chars handling for creating the filenames
		#if timer.name == name:
		# Mad Men != Mad_Men
		
		if TAG in timer.tags:
			msg = _("Skipping timer because it is already handled") + "\n\n" + _("Can be configured within the setup")
			log.warning(msg, timer.name)
			timer.log(607, "[SeriesPlugin]" + " " + msg )
			return
		
		if config.plugins.seriesplugin.timer_eit_check.value:
			
			event = None
			epgcache = eEPGCache.getInstance()
			
			if timer.eit:
				event = epgcache.lookupEventId(timer.service_ref.ref, timer.eit)
				log.debug("lookupEventId", timer.eit, event)
			if not(event):
				event = epgcache.lookupEventTime( timer.service_ref.ref, begin + ((end - begin) /2) );
				log.debug("lookupEventTime", event )
			
			if event:
				if not ( len(timer.name) == len(name) == len(event.getEventName()) ):
					msg = _("Skipping timer because it is already modified %s" % (timer.name) )
					log.warning(msg)
					timer.log(602, "[SeriesPlugin]" + " " + msg )
					return
			else:
				if ( len(timer.name) == len(name) ):
					msg = _("Skipping timer because no event was found")
					log.warning(msg, timer.name)
					timer.log(603, "[SeriesPlugin]" + " " + msg )
					return
		
		if timer.begin < time() + 60:
			msg = _("Skipping timer because it starts in less than 60 seconds")
			log.debug(msg, timer.name)
			timer.log(604, "[SeriesPlugin]" + " " + msg )
			return
		
		if timer.isRunning():
			msg = _("Skipping timer because it is already running")
			log.debug(msg, timer.name)
			timer.log(605, "[SeriesPlugin]" + " " + msg )
			return
		
		if timer.justplay:
			msg = _("Skipping timer because it is a just play timer")
			log.debug(msg, timer.name)
			timer.log(606, "[SeriesPlugin]" + " " + msg )
			return
		
		timer.log(600, "[SeriesPlugin]" + " " + _("Try to find infos for %s" % (timer.name) ) )
		
		seriesPlugin = getInstance()
		
		if timer.service_ref:
			log.debug("getEpisode:", name, begin, end, block)
			
			timer.sp_in_queue = True
			
			return seriesPlugin.getEpisode(
					boundFunction(self.timerCallback, timer),
					name, begin, end, timer.service_ref, future=True, block=block
				)
		else:
			msg = _("Skipping lookup because no channel is specified")
			log.warning(msg)
			self.timerCallback(timer, msg)
			return None

	def timerCallback(self, timer, data=None):
		log.debug("timerCallback", data)
		
		if data and isinstance(data, dict) and timer:
			
			# Episode data available, refactor name and description
			timer.name = str(refactorTitle(timer.name, data))
			timer.description = str(refactorDescription(timer.description, data))
			
			timer.dirname = str(refactorDirectory(timer.dirname or config.usage.default_path.value, data))
			timer.calculateFilename()
			
			msg = _("Success: %s" % (timer.name))
			log.debug(msg)
			timer.log(610, "[SeriesPlugin]" + " " + msg)
			
			if config.plugins.seriesplugin.timer_add_tag.value:
				timer.tags.append(TAG)
		
		elif data:
			msg = _("Failed: %s." % ( str( data ) ))
			log.debug(msg)
			timer.log(611, "[SeriesPlugin]" + " " + msg)
			SeriesPluginTimer.data.append(
				str(timer.name) + ": " + msg
			)
		
		else:
			msg = _("No data available")
			log.debug(msg)
			timer.log(612, "[SeriesPlugin]" + " " + msg)
			SeriesPluginTimer.data.append(
				str(timer.name) + ": " + msg
			)
		
		timer.sp_in_queue = False
		
		if config.plugins.seriesplugin.timer_popups.value or config.plugins.seriesplugin.timer_popups_success.value:
			
			SeriesPluginTimer.counter = SeriesPluginTimer.counter +1
			
			if SeriesPluginTimer.data or config.plugins.seriesplugin.timer_popups_success.value:
				
				# Maybe there is a better way to avoid multiple Popups
				from SeriesPlugin import getInstance
				
				instance = getInstance()
				
				if instance.thread.empty() and instance.thread.finished():
				
					if SeriesPluginTimer.data:
						AddPopup(
							"SeriesPlugin:\n" + _("Timer rename has been finished with %d errors:\n") % (len(SeriesPluginTimer.data)) +"\n" +"\n".join(SeriesPluginTimer.data),
							MessageBox.TYPE_ERROR,
							int(config.plugins.seriesplugin.timer_popups_timeout.value),
							'SP_PopUp_ID_TimerFinished'
						)
					else:
						AddPopup(
							"SeriesPlugin:\n" + _("%d timer renamed successfully") % (SeriesPluginTimer.counter),
							MessageBox.TYPE_INFO,
							int(config.plugins.seriesplugin.timer_popups_timeout.value),
							'SP_PopUp_ID_TimerFinished'
						)
					SeriesPluginTimer.data = []
					SeriesPluginTimer.counter = 0
		
		return timer
