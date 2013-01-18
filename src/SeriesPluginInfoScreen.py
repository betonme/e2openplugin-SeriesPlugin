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
#from time import time
from datetime import datetime

# Config
from Components.config import config

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

from enigma import eEPGCache, eServiceReference, eServiceCenter, iServiceInformation, ePicLoad, eServiceEvent
from ServiceReference import ServiceReference

from RecordTimer import RecordTimerEntry, parseEvent, AFTEREVENT
from Screens.TimerEntry import TimerEntry
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
	
	def __init__(self, session, service=None, event=None):
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
		
		self["key_red"] = Button("")				# Rename or Record
		self["key_green"] = Button(_(""))		# Trakt Seen / Not Seen
		self["key_yellow"] = Button("")			# Show all Episodes of current season
		self["key_blue"] = Button("")				# Show all Seasons
		
		self.redButtonFunction = None
		
		#TODO HelpableActionMap
		self["actions"] = ActionMap(["OkCancelActions", "EventViewActions", "DirectionActions", "ColorActions"],
		{
			"cancel":    self.close,
			"ok":        self.close,
			"up":        self["event_description"].pageUp,
			"down":      self["event_description"].pageDown,
			"red":       self.redButton,
			"prevEvent": self.prevEpisode,
			"nextEvent": self.nextEpisode,
			
			#TODO
			#"pageUp":    self.pageUp,
			#"pageDown":  self.pageDown,
			#"openSimilarList": self.openSimilarList
		})
		
		self.epg = eEPGCache.getInstance()
		self.serviceHandler = eServiceCenter.getInstance()
		
		self.seriesPlugin = getInstance()
		
		print service, event
		self.service = service
		self.event = event
		
		self.name = ""
		self.short = ""
		self.data = None
		
		self.onLayoutFinish.append( self.layoutFinished )

	def layoutFinished(self):
		self.setTitle( _("SeriesPlugin Info") )
		
		self.getEpisode()

	def getEpisode(self):
		self.name = ""
		self.short = ""
		self.data = None
		begin, end, duration = 0, 0, 0
		ext, channel = "", ""
		
		today = True #OR future
		elapsed = False
		
		service = self.service
		
		ref = None
		
		if isinstance(service, eServiceReference):
			#ref = service  #Problem EPG
			if service.getPath():
				ref = service
				# Service is a movie reference
				info = self.serviceHandler.info(service)
				rec_ref_str = info.getInfoString(service, iServiceInformation.sServiceref)
				channel = ServiceReference(rec_ref_str).getServiceName() or ""
				# Get information from record meta files
				self.event = info and info.getEvent(service)
				today = False
				elapsed = True
				print "SeriesPluginInfoScreen eServiceReference movie", str(ref)
			else:
				# Service is channel reference
				ref = eServiceReference(str(service))
				channel = ServiceReference(ref).getServiceName() or ""
				#ref = eServiceReference(service.toString())#
				# Get information from event
				print "SeriesPluginInfoScreen eServiceReference channel", str(ref)
		
		elif isinstance(service, ServiceReference):
			ref = service.ref
			channel = service.getServiceName()
			print "SeriesPluginInfoScreen ServiceReference", str(ref)
		
		elif isinstance(service, ChannelSelectionBase):
			ref = service.getCurrentSelection()
			channel = ServiceReference(ref).getServiceName() or ""
			print "SeriesPluginInfoScreen ChannelSelectionBase", str(ref)
		
		# Fallbacks
		if ref is None:
			ref = self.session and self.session.nav.getCurrentlyPlayingServiceReference()
			channel = ServiceReference(ref).getServiceName() or ""
			print "SeriesPluginInfoScreen Fallback ref", str(ref)
		
		if not isinstance(self.event, eServiceEvent):
			self.event = ref.valid() and self.epg.lookupEventTime(ref, -1)
			#num = event and event.getNumOfLinkageServices() or 0
			#for cnt in range(num):
			#	subservice = event.getLinkageService(sref, cnt)
			# Get information from epg
			today = True
			elapsed = False
			print "SeriesPluginInfoScreen Fallback event", str(ref)
		
		self.service = ref
		
		
		if self.event:
			self.name = self.event.getEventName() or ""
			begin = self.event.getBeginTime() or 0
			duration = self.event.getDuration() or 0
			end = begin + duration or 0
			# We got the exact margins, no need to adapt it
			self.short = self.event.getShortDescription() or ""
			ext = self.event.getExtendedDescription() or ""
			print "SeriesPluginInfoScreen event"
		
		if not begin:
			info = self.serviceHandler.info(ref)
			print "SeriesPluginInfoScreen info"
			if info:
				print "SeriesPluginInfoScreen if info"
				begin = info.getInfo(ref, iServiceInformation.sTimeCreate) or 0
				if begin:
					duration = info.getLength(ref) or 0
					end = begin + duration or 0
					print "SeriesPluginInfoScreen sTimeCreate"
				else:
					end = os.path.getmtime(ref.getPath()) or 0
					duration = info.getLength(ref) or 0
					begin = end - duration or 0
					print "SeriesPluginInfoScreen sTimeCreate else"
			elif ref:
				path = ref.getPath()
				print "SeriesPluginInfoScreen getPath"
				if path and os.path.exists(path):
					begin = os.path.getmtime(path) or 0
					print "SeriesPluginInfoScreen getctime"
			#else:
				#MAYBE we could also try to parse the filename
			# We don't know the exact margins, we will assume the E2 default margins
			begin = begin + (config.recording.margin_before.value * 60)
			end = end - (config.recording.margin_after.value * 60)
		
		self.updateScreen(self.name, _("Retrieving Season, Episode and Title..."), self.short, ext, begin, duration, channel)
		
		identifier = self.seriesPlugin.getEpisode(
				self.episodeCallback, 
				self.name, begin, end, channel, today=today, elapsed=elapsed
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
			season, episode, title = self.data = data
		
		#LATER
		#	self.seriesPlugin.getStates(
		#			boundFunction(self.stateCallback, show_name, short, ext), 
		#			show_name, season, episode
		#		)
			custom = _("Season: {season:d}  Episode: {episode:d}\n{title:s}").format( 
							**{'season': season, 'episode': episode, 'title': title} )
			
			try:
				self.setColorButtons()
			except Exception, e:
				# Screen already closed
				print "SeriesPluginInfoScreen:", str(e)
		else:
			custom = _("No matching episode found")
		
		# Check if the dialog is already closed
		try:
			self["event_episode"].setText( custom )
		except Exception, e:
			# Screen already closed
			print "SeriesPluginInfoScreen:", str(e)


	def updateScreen(self, name, episode, short, ext, begin, duration, channel):
		# Adapted from EventView
		self["event_title"].setText( name )
		self["event_episode"].setText( episode )
		
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


	def setColorButtons(self):
		print "event eit", self.event and self.event.getEventId()
		if self.service and self.data:
			
			path = self.service.getPath()
			
			if path and os.path.exists(path):
				# Record file exists
				self["key_red"].setText(_("Rename"))
				self.redButtonFunction = self.rename
			elif self.event and self.event.getEventId():
				# Event exists
				self["key_red"].setText(_("Record"))
				self.redButtonFunction = self.record
			else:
				self["key_red"].setText(_(""))
				self.redButtonFunction = None
		else:
			self["key_red"].setText(_(""))
			self.redButtonFunction = None

	def redButton(self):
		if callable(self.redButtonFunction):
			self.redButtonFunction()

	def prevEpisode(self):
		if self.service and self.data:
			pass

	def nextEpisode(self):
		if self.service and self.data:
			pass

	def rename(self):
		ref = self.service
		if ref and self.data:
			path = ref.getPath()
			if path and os.path.exists(path):
				from SeriesPluginRenamer import rename
				if rename(ref, self.name, self.short, self.data):
					self.session.open(MessageBox, _("Successfully renamed") )
				else:
					self.session.open(MessageBox, _("Renaming failed") )

	# Adapted from EventView timerAdd
	def record(self):
		if self.event and self.service:
			event = self.event
			ref = self.service
			if event is None:
				return
			eventid = event.getEventId()
			refstr = ref.toString()
			for timer in self.session.nav.RecordTimer.timer_list:
				if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
					cb_func = lambda ret : not ret or self.removeTimer(timer)
					self.session.openWithCallback(cb_func, MessageBox, _("Do you really want to delete %s?") % event.getEventName())
					break
			else:
				newEntry = RecordTimerEntry(ServiceReference(ref), checkOldTimers = True, dirname = preferredTimerPath(), *parseEvent(self.event))
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
			#self["key_green"].setText(_("Remove timer"))
			#self.key_green_choice = self.REMOVE_TIMER
		else:
			#self["key_green"].setText(_("Add timer"))
			#self.key_green_choice = self.ADD_TIMER
			print "Timeredit aborted"

	def finishSanityCorrection(self, answer):
		self.finishedAdd(answer)

