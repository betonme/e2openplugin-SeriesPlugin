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
from EpisodePatterns import readPatternFile
from Logger import splog, Logger


def checkList(cfg):
	if cfg.value not in cfg.choices.choices:
		if cfg.default in cfg.choices.choices:
			cfg.value = cfg.default
		else:
			cfg.value = cfg.choices.choices[0]
	print cfg.value


#######################################################
# Configuration screen
class SeriesPluginConfiguration(ConfigListScreen, Screen, Logger):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = [ "SeriesServiceConfiguration", "Setup" ]
		
		from plugin import NAME, VERSION
		self.setup_title = NAME + " " + _("Configuration") + " " + VERSION
		
		self.onChangedEntry = [ ]
		
		# Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_blue"] = StaticText(_("Send Log"))
		self["key_blue"] = StaticText("")
		
		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ChannelSelectBaseActions", "ColorActions"],
		{
			"cancel":		self.keyCancel,
			"save":			self.keySave,
			"nextBouquet":	self.pageUp,
			"prevBouquet":	self.pageDown,
			"blue":			self.blue,
		}, -2) # higher priority
		
		resetInstance()
		self.seriesPlugin = getInstance()
		
		# Create temporary identifier config elements
		identifiers = self.seriesPlugin.identifiers
		identifiers_elapsed = [k for k,v in identifiers.items() if v.knowsElapsed()]
		identifiers_today   = [k for k,v in identifiers.items() if v.knowsToday()]
		identifiers_future  = [k for k,v in identifiers.items() if v.knowsFuture()]
		self.cfg_identifier_elapsed = NoSave( ConfigSelection(choices = identifiers_elapsed, default = config.plugins.seriesplugin.identifier_elapsed.value or identifiers_elapsed[0]) )
		self.cfg_identifier_today   = NoSave( ConfigSelection(choices = identifiers_today,   default = config.plugins.seriesplugin.identifier_today.value   or identifiers_today[0]) )
		self.cfg_identifier_future  = NoSave( ConfigSelection(choices = identifiers_future,  default = config.plugins.seriesplugin.identifier_future.value  or identifiers_future[0]) )
		
		# Load patterns
		patterns = readPatternFile()
		self.cfg_pattern_title       = NoSave( ConfigSelection(choices = patterns, default = config.plugins.seriesplugin.pattern_title.value ) )
		self.cfg_pattern_description = NoSave( ConfigSelection(choices = patterns, default = config.plugins.seriesplugin.pattern_description.value ) )
		checkList( self.cfg_pattern_title )
		checkList( self.cfg_pattern_description )		
		
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
		#    _                                                                                   , config element
		
		self.list.append( getConfigListEntry(  _("Enable SeriesPlugin")                          , config.plugins.seriesplugin.enabled ) )
		
		if config.plugins.seriesplugin.enabled.value:
			self.list.append( getConfigListEntry(  _("Show in info menu")                          , config.plugins.seriesplugin.menu_info ) )
			self.list.append( getConfigListEntry(  _("Show in extensions menu")                    , config.plugins.seriesplugin.menu_extensions ) )
			self.list.append( getConfigListEntry(  _("Show Info in movie list menu")               , config.plugins.seriesplugin.menu_movie_info ) )
			self.list.append( getConfigListEntry(  _("Show Rename in movie list menu")             , config.plugins.seriesplugin.menu_movie_rename ) )
			
			#if len( config.plugins.seriesplugin.identifier_elapsed.choices ) > 1:
			self.list.append( getConfigListEntry(  _("Select identifier for elapsed events")       , self.cfg_identifier_elapsed ) )
			#if len( config.plugins.seriesplugin.identifier_today.choices ) > 1:
			self.list.append( getConfigListEntry(  _("Select identifier for today events")         , self.cfg_identifier_today ) )
			#if len( config.plugins.seriesplugin.identifier_future.choices ) > 1:
			self.list.append( getConfigListEntry(  _("Select identifier for future events")        , self.cfg_identifier_future ) )
			
			#if len( config.plugins.seriesplugin.manager.choices ) > 1:
#			self.list.append( getConfigListEntry(  _("Select manager service")                     , config.plugins.seriesplugin.manager ) )
			#if len( config.plugins.seriesplugin.guide.choices ) > 1:
#			self.list.append( getConfigListEntry(  _("Select guide service")                       , config.plugins.seriesplugin.guide ) )
			
			self.list.append( getConfigListEntry(  _("Episode pattern file")                       , config.plugins.seriesplugin.pattern_file ) )
			self.list.append( getConfigListEntry(  _("Record title episode pattern")               , self.cfg_pattern_title ) )
			self.list.append( getConfigListEntry(  _("Record description episode pattern")         , self.cfg_pattern_description ) )
			
			self.list.append( getConfigListEntry(  _("Alternative channel names file")             , config.plugins.seriesplugin.channel_file ) )
			self.list.append( getConfigListEntry(  _("Ask for channel matching")                   , config.plugins.seriesplugin.channel_popups ) )
			
			self.list.append( getConfigListEntry(  _("Tidy up filename on Rename")                 , config.plugins.seriesplugin.tidy_rename ) )
			
			self.list.append( getConfigListEntry(  _("Max time drift to match episode")            , config.plugins.seriesplugin.max_time_drift ) )
					
			self.list.append( getConfigListEntry(  _("AutoTimer independent mode")                 , config.plugins.seriesplugin.autotimer_independent ) )
			if config.plugins.seriesplugin.autotimer_independent.value:
				self.list.append( getConfigListEntry(  _("Check timer every x minutes")            , config.plugins.seriesplugin.independent_cycle ) )
			self.list.append( getConfigListEntry(  _("Show Timer error popups")                    , config.plugins.seriesplugin.timer_popups ) )
			
			self.list.append( getConfigListEntry(  _("Check Timer Eit")                            , config.plugins.seriesplugin.check_timer_eit ) )
			
			self.list.append( getConfigListEntry(  _("E2: Composition of the recording filenames") , config.recording.filename_composition ) )
			
			self.list.append( getConfigListEntry(  _("Debug: Write Log")                           , config.plugins.seriesplugin.write_log ) )
			if config.plugins.seriesplugin.write_log.value:
				self.list.append( getConfigListEntry(  _("Debug: Log file path")                   , config.plugins.seriesplugin.log_file ) )
				self.list.append( getConfigListEntry(  _("Debug: Forum user name")                 , config.plugins.seriesplugin.log_reply_user ) )
				self.list.append( getConfigListEntry(  _("Debug: User mail address")               , config.plugins.seriesplugin.log_reply_mail ) )

	def changeConfig(self):
		self.list = []
		self.buildConfig()
		self["config"].setList(self.list)

	def changed(self):
		for x in self.onChangedEntry:
			x()
		current = self["config"].getCurrent()[1]
		if (current == config.plugins.seriesplugin.enabled or 
			current == config.plugins.seriesplugin.autotimer_independent or 
			current == config.plugins.seriesplugin.write_log):
			self.changeConfig()

	# Overwrite ConfigListScreen keySave function
	def keySave(self):
		self.saveAll()
		
		config.plugins.seriesplugin.identifier_elapsed.value = self.cfg_identifier_elapsed.value
		config.plugins.seriesplugin.identifier_today.value   = self.cfg_identifier_today.value
		config.plugins.seriesplugin.identifier_future.value  = self.cfg_identifier_future.value
		config.plugins.seriesplugin.pattern_title.value       = self.cfg_pattern_title.value
		config.plugins.seriesplugin.pattern_description.value = self.cfg_pattern_description.value
		config.plugins.seriesplugin.save()
		
		from plugin import overwriteAutoTimer, recoverAutoTimer
		
		if config.plugins.seriesplugin.enabled.value:
			overwriteAutoTimer()
		else:
			recoverAutoTimer()
		
		# Set new configuration
		from plugin import addSeriesPlugin, removeSeriesPlugin, SHOWINFO, RENAMESERIES, info, extension, movielist_info, movielist_rename
		
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
		
		if config.plugins.seriesplugin.autotimer_independent.value:
			from SeriesPluginIndependent import startIndependent
			startIndependent()
		
		# To set new module configuration
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

	def blue(self):
		self.sendLog()
