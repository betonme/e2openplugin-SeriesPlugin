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

# Config
from Components.config import *
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText

from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Setup import SetupSummary

from Plugins.Plugin import PluginDescriptor

# Plugin internal
from SeriesPlugin import resetInstance, getInstance


#######################################################
# Configuration screen
class SeriesPluginConfiguration(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = [ "SeriesServiceConfiguration", "Setup" ]
		
		from plugin import NAME, VERSION
		self.setup_title = NAME + " " + _("Configuration") + " " + VERSION
		
		self.onChangedEntry = [ ]
		
		# Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		
		# Define Actions
		self["custom_actions"] = ActionMap(["SetupActions", "ChannelSelectBaseActions"],
		{
			"cancel":				self.keyCancel,
			"save":					self.keySave,
			"nextBouquet":	self.pageUp,
			"prevBouquet":	self.pageDown,
		}, -2) # higher priority
		
		resetInstance()
		self.seriesPlugin = getInstance()
		
		# Load patterns
		from plugin import readPatternFile
		patterns = readPatternFile()
		if patterns:
			config.plugins.seriesplugin.pattern_title.setChoices(patterns, config.plugins.seriesplugin.pattern_title.value)
			config.plugins.seriesplugin.pattern_description.setChoices(patterns, config.plugins.seriesplugin.pattern_description.value)
		
		# Initialize Configuration
		self.list = []
		self.buildConfig()
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)
		
		self.changed()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_(self.setup_title))

	def buildConfig(self):
		#    _config list entry
		#    _                                                                                 , config element
		
		self.list.append( getConfigListEntry(  _("Enable SeriesPlugin")                          , config.plugins.seriesplugin.enabled ) )
		
		if config.plugins.seriesplugin.enabled.value:
			self.list.append( getConfigListEntry(  _("Show in info menu")                          , config.plugins.seriesplugin.menu_info ) )
			self.list.append( getConfigListEntry(  _("Show in extensions menu")                    , config.plugins.seriesplugin.menu_extensions ) )
			self.list.append( getConfigListEntry(  _("Show Info in movie list menu")               , config.plugins.seriesplugin.menu_movie_info ) )
			self.list.append( getConfigListEntry(  _("Show Rename in movie list menu")             , config.plugins.seriesplugin.menu_movie_rename ) )
			
			#if len( config.plugins.seriesplugin.identifier_elapsed.choices ) > 1:
			self.list.append( getConfigListEntry(  _("Select identifier for elapsed events")       , config.plugins.seriesplugin.identifier_elapsed ) )
			#if len( config.plugins.seriesplugin.identifier_today.choices ) > 1:
			self.list.append( getConfigListEntry(  _("Select identifier for today events")         , config.plugins.seriesplugin.identifier_today ) )
			#if len( config.plugins.seriesplugin.identifier_future.choices ) > 1:
			self.list.append( getConfigListEntry(  _("Select identifier for future events")        , config.plugins.seriesplugin.identifier_future ) )
			
			#if len( config.plugins.seriesplugin.manager.choices ) > 1:
#			self.list.append( getConfigListEntry(  _("Select manager service")                     , config.plugins.seriesplugin.manager ) )
			#if len( config.plugins.seriesplugin.guide.choices ) > 1:
#			self.list.append( getConfigListEntry(  _("Select guide service")                       , config.plugins.seriesplugin.guide ) )
			
			self.list.append( getConfigListEntry(  _("Episode pattern file")                       , config.plugins.seriesplugin.pattern_file ) )
			self.list.append( getConfigListEntry(  _("Record title episode pattern")               , config.plugins.seriesplugin.pattern_title ) )
			self.list.append( getConfigListEntry(  _("Record description episode pattern")         , config.plugins.seriesplugin.pattern_description ) )
			
			self.list.append( getConfigListEntry(  _("Max time drift to match episode")            , config.plugins.seriesplugin.max_time_drift ) )
			self.list.append( getConfigListEntry(  _("Tidy up filename on SP Rename")              , config.plugins.seriesplugin.rename_tidy ) )
			self.list.append( getConfigListEntry(  _("E2: Composition of the recording filenames") , config.recording.filename_composition ) )

	def changeConfig(self):
		self.list = []
		self.buildConfig()
		self["config"].setList(self.list)

	def changed(self):
		for x in self.onChangedEntry:
			x()
		self.changeConfig()

	# Overwrite ConfigListScreen keySave function
	def keySave(self):
		self.saveAll()
		
		from plugin import overwriteAutoTimer, recoverAutoTimer
		
		if config.plugins.seriesplugin.enabled.value:
			overwriteAutoTimer()
		else:
			recoverAutoTimer()
		
		# Set new configuration
		from plugin import addSeriesPlugin, removeSeriesPlugin, SHOWINFO, RENAMESERIES, info, extension, movielist_info, movielist_rename
		
		#TODO handle plugin entries like IBTS
		
		if config.plugins.seriesplugin.menu_info.value:
			addSeriesPlugin(PluginDescriptor.WHERE_EVENTINFO, SHOWINFO, info)
		else:
			removeSeriesPlugin(PluginDescriptor.WHERE_EVENTINFO, SHOWINFO)
		
		if config.plugins.seriesplugin.menu_extensions.value:
			addSeriesPlugin(PluginDescriptor.WHERE_EXTENSIONSMENU, SHOWINFO, extension)
		else:
			removeSeriesPlugin(PluginDescriptor.WHERE_EXTENSIONSMENU, SHOWINFO)
		
		if config.plugins.seriesplugin.menu_movie_info.value:
			addSeriesPlugin(PluginDescriptor.WHERE_MOVIELIST, SHOWINFO, movielist_info)
		else:
			removeSeriesPlugin(PluginDescriptor.WHERE_MOVIELIST, SHOWINFO)
		
		if config.plugins.seriesplugin.menu_movie_rename.value:
			addSeriesPlugin(PluginDescriptor.WHERE_MOVIELIST, RENAMESERIES, movielist_rename)
		else:
			removeSeriesPlugin(PluginDescriptor.WHERE_MOVIELIST, RENAMESERIES)
		
		resetInstance()
		self.close()

	# Overwrite ConfigListScreen keyCancel function
	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	# Overwrite Screen close function
	def close(self):
		from plugin import ABOUT
		about = ABOUT.format( **{'lookups': config.plugins.seriesplugin.lookup_counter.value} )
		self.session.openWithCallback(self.closeConfirm, MessageBox, about, MessageBox.TYPE_INFO)

	def closeConfirm(self, dummy=None):
		# Call baseclass function
		Screen.close(self)

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def pageUp(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)

	def pageDown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)

