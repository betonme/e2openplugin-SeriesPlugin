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
import re

# for localized messages
from . import _
from datetime import datetime

# Config
from Components.config import *

from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Screens.MessageBox import MessageBox
from Screens.ChannelSelection import ChannelSelectionBase

from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap

from enigma import eEPGCache, eServiceReference, eServiceCenter, iServiceInformation, ePicLoad
from ServiceReference import ServiceReference

from RecordTimer import RecordTimerEntry, parseEvent, AFTEREVENT
from timer import TimerEntry
from Components.UsageConfig import preferredTimerPath
from Screens.TimerEdit import TimerSanityConflict

from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS


# Plugin internal
from SeriesPlugin import getInstance


# Constants
PIXMAP_PATH = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Logos/" )


#######################################################
# Info screen
class SeriesPluginInfoScreen(Screen):
	
	skinfile = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/skin.xml" )
	skin = open(skinfile).read()
	
	def __init__(self, session, service):
		Screen.__init__(self, session)
		self.session = session
		self.skinName = [ "SeriesPluginInfoScreen" ]
		
		self["logo"] = Pixmap()
		self["cover"] = Pixmap()
		self["state"] = Pixmap()
		
		self["event_title"] = Label()
		self["event_episode"] = Label()
		self["event_description"] = ScrollLabel()
		self["datetime"] = Label()
		self["channel"] = Label()
		self["duration"] = Label()
		
		self["key_red"] = Button("")	#TODO Record if current event or servicelist epg
		self["key_green"] = Button(_(""))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")
		
		#TODO HelpableActionMap
		self["actions"] = ActionMap(["OkCancelActions", "EventViewActions", "DirectionActions"],
		{
			"cancel":    self.close,
			"ok":        self.close,
			"up":        self["event_description"].pageUp,
			"down":      self["event_description"].pageDown,
			#TODO
			#"pageUp":    self.pageUp,
			#"pageDown":  self.pageDown,
			#"prevEvent": self.prevEvent,
			#"nextEvent": self.nextEvent,
			#"timerAdd":  self.timerAdd,
			#"openSimilarList": self.openSimilarList
		})
		
		self.epg = eEPGCache.getInstance()
		self.serviceHandler = eServiceCenter.getInstance()
		
		self.service = service
		
		self.seriesPlugin = getInstance()
		
		self.onLayoutFinish.append( self.layoutFinished )

	def layoutFinished(self):
		self.setTitle( _("SeriesPlugin Info") )
		self.getEpisode()

	def getEpisode(self):
		service = self.service
		if isinstance(service, ChannelSelectionBase):
			ref = service.getCurrentSelection()
			print "SeriesPluginInfoScreen ChannelSelectionBase" + str(ref)
		elif isinstance(service, eServiceReference):
			ref = service
			print "SeriesPluginInfoScreen eServiceReference" + str(ref)
		elif isinstance(service, ServiceReference):
			ref = service.ref
			print "SeriesPluginInfoScreen ServiceReference" + str(ref)
		else:
			ref = self.session and self.session.nav.getCurrentlyPlayingServiceReference()
			print "SeriesPluginInfoScreen else" + str(ref)
		
		event = ref and ref.valid() and self.epg.lookupEventTime(ref, -1)
		if event:
			# Get information from epg
			name = event.getEventName() or ""
			begin = event.getBeginTime() or 0
			duration = event.getDuration() or 0
			end = begin + duration or 0
			short = event.getShortDescription() or ""
			ext = event.getExtendedDescription() or ""
			channel = ServiceReference(ref).getServiceName() or ""
			today = True
			elapsed = False
			
			self.event = event
			self.currentService = ref
		#	if (not ref.flags & eServiceReference.isGroup) and ref.getPath() and ref.getPath()[0] == '/':
		#		self["key_green"].setText(_("Remove timer"))
		#	else:
		#		self["key_green"].setText(_("Add timer"))
		else:
			# Get information from record meta files
			name = ref.getName() or info.getName(ref) or ""
			
			info = self.serviceHandler.info(ref)
			begin = info and info.getInfo(ref, iServiceInformation.sTimeCreate) or -1
			if begin != -1:
				duration = info.getLength(ref) or 0
				end = begin + duration or 0
			else:
				end = os.path.getmtime(ref.getPath())
				duration = info.getLength(ref) or 0
				begin = end - duration or 0
				#MAYBE we could also try to parse the filename
			
			
			event = info.getEvent(ref)
			short = event and event.getShortDescription() or ""
			ext = event and event.getExtendedDescription() or ""
			rec_ref_str = info.getInfoString(ref, iServiceInformation.sServiceref)
			channel = ServiceReference(rec_ref_str).getServiceName() or _("unknown service")
			today = False
			elapsed = True
			
			self.event = None
			self.currentService = None
		print channel
		
		# Adapted from EventView
		self["event_title"].setText( name )
		self["event_episode"].setText( _("Retrieving Season, Episode and Title...") )
		text = ""
		if short and short != name:
			text = short
		if ext:
			if text:
				text += '\n'
			text += ext
		self["event_description"].setText(text)
		
		self["datetime"].setText( datetime.fromtimestamp(begin).strftime("%d.%m.%Y, %H:%M") )
		self["duration"].setText(_("%d min")%((duration)/60))
		self["channel"].setText(channel)
		
		#print name, short, ext, begin, end, channel, today, elapsed 
		
		identifier = self.seriesPlugin.getEpisode(
				self.episodeCallback, 
				name, begin, end, channel, today=today, elapsed=elapsed
			)
		
		if identifier:
			path = os.path.join(PIXMAP_PATH, identifier+".png")
			if os.path.exists(path):
				self.loadPixmap("logo", path )

	def episodeCallback(self, data=None):
		#TODO episode list handling
		#store the list and just open the first one
		
		print "SeriesPluginInfoScreen episodeCallback"
		#print data
		if data:
			# Episode data available
			season, episode, title = data
		
		#LATER
		#	self.seriesPlugin.getStates(
		#			boundFunction(self.stateCallback, show_name, short, ext), 
		#			show_name, season, episode
		#		)
			custom = _("Season: {season:d}  Episode: {episode:d}\n{title:s}").format( 
							**{'season': season, 'episode': episode, 'title': title} )
		else:
			custom = _("No matching episode found")
		
		# Check if the dialog is already closed
		if self.has_key("event_episode"):
			self["event_episode"].setText( custom )

	def stateCallback(self, show_name, short, description, state=None):
		pass


	# Handle pixmaps
	def loadPixmap(self, widget, path):
		sc = AVSwitch().getFramebufferScale()
		size = self[widget].instance.size()
		self.picload = ePicLoad()
		self.picload.PictureData.get().append( boundFunction(self.loadPixmapCallback, widget) )
		if self.picload:
			self.picload.setPara((size.width(), size.height(), sc[0], sc[1], False, 1, "#00000000")) # Background dynamically
			if self.picload.startDecode(path) != 0:
				del self.picload

	def loadPixmapCallback(self, widget, picInfo=None):
		if self.picload and picInfo:
			ptr = self.picload.getData()
			if ptr != None:
				self[widget].instance.setPixmap(ptr.__deref__())
				self[widget].show()
			del self.picload


	# Overwrite Screen close function
	def close(self):
		if self.seriesPlugin:
			self.seriesPlugin.cancel()
		# Call baseclass function
		Screen.close(self)



	# Adapted from EventView
	def removeTimer(self, timer):
		timer.afterEvent = AFTEREVENT.NONE
		self.session.nav.RecordTimer.removeEntry(timer)
		self["key_green"].setText(_("Add timer"))
		#self.key_green_choice = self.ADD_TIMER
	
	def timerAdd(self):
		if self.event and self.currentService:
			event = self.event
			serviceref = self.currentService
			if event is None:
				return
			eventid = event.getEventId()
			refstr = serviceref.ref.toString()
			for timer in self.session.nav.RecordTimer.timer_list:
				if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
					cb_func = lambda ret : not ret or self.removeTimer(timer)
					self.session.openWithCallback(cb_func, MessageBox, _("Do you really want to delete %s?") % event.getEventName())
					break
			else:
				newEntry = RecordTimerEntry(self.currentService, checkOldTimers = True, dirname = preferredTimerPath(), *parseEvent(self.event))
				self.session.openWithCallback(self.finishedAdd, TimerEntry, newEntry)

	def finishedAdd(self, answer):
		print "finished add"
		if answer[0]:
			entry = answer[1]
			simulTimerList = self.session.nav.RecordTimer.record(entry)
			if simulTimerList is not None:
				for x in simulTimerList:
					if x.setAutoincreaseEnd(entry):
						self.session.nav.RecordTimer.timeChanged(x)
				simulTimerList = self.session.nav.RecordTimer.record(entry)
				if simulTimerList is not None:
					self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
			self["key_green"].setText(_("Remove timer"))
			#self.key_green_choice = self.REMOVE_TIMER
		else:
			self["key_green"].setText(_("Add timer"))
			#self.key_green_choice = self.ADD_TIMER
			print "Timeredit aborted"

	def finishSanityCorrection(self, answer):
		self.finishedAdd(answer)

