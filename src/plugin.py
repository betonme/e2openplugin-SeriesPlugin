
import os, sys, traceback

# Localization
from . import _

from time import time

# GUI (Screens)
from Screens.MessageBox import MessageBox

# Config
from Components.config import config, ConfigSubsection, ConfigEnableDisable, ConfigNumber, ConfigSelection, ConfigYesNo, ConfigText, ConfigSelectionNumber

# Plugin
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

# Plugin internal
from SeriesPluginTimer import SeriesPluginTimer
from SeriesPluginInfoScreen import SeriesPluginInfoScreen
from SeriesPluginRenamer import SeriesPluginRenamer
from SeriesPluginConfiguration import SeriesPluginConfiguration
from Logger import splog


#######################################################
# Constants
NAME = "SeriesPlugin"
VERSION = "0.9.1.0"
DESCRIPTION = _("SeriesPlugin")
SHOWINFO = _("Show series info")
RENAMESERIES = _("Rename serie(s)")
SUPPORT = "http://bit.ly/seriespluginihad"
DONATE = "http://bit.ly/seriespluginpaypal"
ABOUT = "\n  " + NAME + " " + VERSION + "\n\n" \
				+ _("  (C) 2012 by betonme @ IHAD \n\n") \
				+ _("  {lookups:d} successful lookups.\n") \
				+ _("  How much time have You saved?\n\n") \
				+ _("  Support: ") + SUPPORT + "\n" \
				+ _("  Feel free to donate. \n") \
				+ _("  PayPal: ") + DONATE
try:
	from Tools.HardwareInfo import HardwareInfo
	DEVICE = HardwareInfo().get_device_name().strip()
except:
	DEVICE = ''


#######################################################
# Initialize Configuration
config.plugins.seriesplugin = ConfigSubsection()

config.plugins.seriesplugin.enabled                   = ConfigEnableDisable(default = False)

config.plugins.seriesplugin.menu_info                 = ConfigYesNo(default = True)
config.plugins.seriesplugin.menu_extensions           = ConfigYesNo(default = False)
config.plugins.seriesplugin.menu_movie_info           = ConfigYesNo(default = True)
config.plugins.seriesplugin.menu_movie_rename         = ConfigYesNo(default = True)

#TODO config.plugins.seriesplugin.open MessageBox or TheTVDB  ConfigSelection if hasTheTVDB

config.plugins.seriesplugin.identifier_elapsed        = ConfigText(default = "", fixed_size = False)
config.plugins.seriesplugin.identifier_today          = ConfigText(default = "", fixed_size = False)
config.plugins.seriesplugin.identifier_future         = ConfigText(default = "", fixed_size = False)

#config.plugins.seriesplugin.manager                   = ConfigSelection(choices = [("", "")], default = "")
#config.plugins.seriesplugin.guide                     = ConfigSelection(choices = [("", "")], default = "")

config.plugins.seriesplugin.pattern_file              = ConfigText(default = "/etc/enigma2/seriesplugin_patterns.json", fixed_size = False)
config.plugins.seriesplugin.pattern_title             = ConfigText(default = "{org:s} S{season:02d}E{episode:02d} {title:s}", fixed_size = False)
config.plugins.seriesplugin.pattern_description       = ConfigText(default = "S{season:02d}E{episode:02d} {title:s} {org:s}", fixed_size = False)

config.plugins.seriesplugin.channel_file              = ConfigText(default = "/etc/enigma2/seriesplugin_channels.xml", fixed_size = False)
config.plugins.seriesplugin.channel_popups            = ConfigYesNo(default = False)

config.plugins.seriesplugin.tidy_rename               = ConfigYesNo(default = False)
config.plugins.seriesplugin.rename_file               = ConfigYesNo(default = True)

config.plugins.seriesplugin.max_time_drift            = ConfigSelectionNumber(0, 600, 1, default = 15)

config.plugins.seriesplugin.autotimer_independent     = ConfigYesNo(default = False)
config.plugins.seriesplugin.independent_cycle         = ConfigSelectionNumber(5, 24*60, 5, default = 60)
config.plugins.seriesplugin.independent_retry         = ConfigYesNo(default = False)
#NoTimerPopUpPossibleActually
#config.plugins.seriesplugin.timer_popups              = ConfigYesNo(default = True)

config.plugins.seriesplugin.caching                   = ConfigYesNo(default = True)

#config.plugins.seriesplugin.debug                     = ConfigYesNo(default = False)
config.plugins.seriesplugin.write_log                 = ConfigYesNo(default = False)
config.plugins.seriesplugin.log_file                  = ConfigText(default = "/tmp/seriesplugin.log", fixed_size = False)
config.plugins.seriesplugin.log_reply_user            = ConfigText(default = "Dreambox User", fixed_size = False)
config.plugins.seriesplugin.log_reply_mail            = ConfigText(default = "myemail@home.com", fixed_size = False)

# Internal
config.plugins.seriesplugin.lookup_counter            = ConfigNumber(default = 0)
#config.plugins.seriesplugin.uid                       = ConfigText(default = str(time()), fixed_size = False)


#######################################################
# Start
def start(reason, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		# Startup
		if reason == 0:
			# Start on demand if it is requested
			if config.plugins.seriesplugin.autotimer_independent.value:
				from SeriesPluginIndependent import startIndependent
				startIndependent()
			
		# Shutdown
		elif reason == 1:
			from SeriesPlugin import resetInstance
			resetInstance()


#######################################################
# Plugin configuration
def setup(session, *args, **kwargs):
	try:
		session.open(SeriesPluginConfiguration)
	except Exception as e:
		splog(_("SeriesPlugin setup exception ") + str(e))
		#exc_type, exc_value, exc_traceback = sys.exc_info()
		#splog( exc_type, exc_value, exc_traceback )


#######################################################
# Event Info
def info(session, service=None, event=None, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
	#TBD Because of E2 Update 05.2013
			session.open(SeriesPluginInfoScreen, service, event)
		except Exception as e:
			splog(_("SeriesPlugin info exception ") + str(e))
			#exc_type, exc_value, exc_traceback = sys.exc_info()
			#splog( exc_type, exc_value, exc_traceback )


#######################################################
# Extensions menu
def extension(session, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
	#TBD Because of E2 Update 05.2013
			session.open(SeriesPluginInfoScreen)
		except Exception as e:
			splog(_("SeriesPlugin extension exception ") + str(e))
			#exc_type, exc_value, exc_traceback = sys.exc_info()
			#splog( exc_type, exc_value, exc_traceback )


#######################################################
# Movielist menu rename
def movielist_rename(session, service, services=None, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			if services:
				if not isinstance(services, list):
					services = [services]	
			else:
				services = [service]
			SeriesPluginRenamer(session, services)
		except Exception as e:
			splog(_("SeriesPlugin renamer exception ") + str(e))
			#exc_type, exc_value, exc_traceback = sys.exc_info()
			#splog( exc_type, exc_value, exc_traceback )


#######################################################
# Movielist menu info
def movielist_info(session, service, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
	#TBD Because of E2 Update 05.2013
			session.open(SeriesPluginInfoScreen, service)
		except Exception as e:
			splog(_("SeriesPlugin extension exception ") + str(e))
			#exc_type, exc_value, exc_traceback = sys.exc_info()
			#splog( exc_type, exc_value, exc_traceback )


#######################################################
# Timer renaming
def renameTimer(timer, name, begin, end, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			SeriesPluginTimer(timer, name, begin, end)
		except Exception as e:
			splog(_("SeriesPlugin label exception ") + str(e))
			#exc_type, exc_value, exc_traceback = sys.exc_info()
			#splog( exc_type, exc_value, exc_traceback )


# For compatibility reasons
def modifyTimer(timer, name, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		splog("SeriesPlugin modifyTimer is deprecated - Update Your AutoTimer!")
		try:
			SeriesPluginTimer(timer, name or timer.name, timer.begin, timer.end)
		except Exception as e:
			splog(_("SeriesPlugin label exception ") + str(e))
			#exc_type, exc_value, exc_traceback = sys.exc_info()
			#splog( exc_type, exc_value, exc_traceback )


# For compatibility reasons
def labelTimer(timer, begin=None, end=None, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		splog("SeriesPlugin labelTimer is deprecated - Update Your AutoTimer!")
		try:
			SeriesPluginTimer(timer, timer.name, timer.begin, timer.end)
		except Exception as e:
			splog(_("SeriesPlugin label exception ") + str(e))
			#exc_type, exc_value, exc_traceback = sys.exc_info()
			#splog( exc_type, exc_value, exc_traceback )


#######################################################
# Plugin main function
def Plugins(**kwargs):
	descriptors = []
	
	#TODO icon
	descriptors.append( PluginDescriptor(
																			name = NAME + " " + _("Setup"),
																			description = NAME + " " + _("Setup"),
																			where = PluginDescriptor.WHERE_PLUGINMENU,
																			fnc = setup,
																			needsRestart = False) )
	
	if config.plugins.seriesplugin.enabled.value:
		
		descriptors.append( PluginDescriptor(
																				#where = PluginDescriptor.WHERE_SESSIONSTART,
																				where = PluginDescriptor.WHERE_AUTOSTART,
																				needsRestart = False,
																				fnc = start) )

#TBD Because of E2 Update 05.2013
		if config.plugins.seriesplugin.menu_info.value:
			descriptors.append( PluginDescriptor(
																					name = SHOWINFO,
																					description = SHOWINFO,
																					where = PluginDescriptor.WHERE_EVENTINFO,
																					needsRestart = False,
																					fnc = info) )

#TBD Because of E2 Update 05.2013
		if config.plugins.seriesplugin.menu_extensions.value:
			descriptors.append(PluginDescriptor(
																				name = SHOWINFO,
																				description = SHOWINFO,
																				where = PluginDescriptor.WHERE_EXTENSIONSMENU,
																				fnc = extension,
																				needsRestart = False) )

#TBD Because of E2 Update 05.2013
		if config.plugins.seriesplugin.menu_movie_info.value:
			descriptors.append( PluginDescriptor(
																					name = SHOWINFO,
																					description = SHOWINFO,
																					where = PluginDescriptor.WHERE_MOVIELIST,
																					fnc = movielist_info,
																					needsRestart = False) )
		
		if config.plugins.seriesplugin.menu_movie_rename.value:
			descriptors.append( PluginDescriptor(
																					name = RENAMESERIES,
																					description = RENAMESERIES,
																					where = PluginDescriptor.WHERE_MOVIELIST,
																					fnc = movielist_rename,
																					needsRestart = False) )

	return descriptors


#######################################################
# Add / Remove menu functions
def addSeriesPlugin(menu, title, fnc):
	# Add to extension menu
	from Components.PluginComponent import plugins
	if plugins:
		for p in plugins.getPlugins( where = menu ):
			if p.name == title:
				# Plugin is already in menu
				break
		else:
			# Plugin not in menu - add it
			plugin = PluginDescriptor(
															name = title,
															description = title,
															where = menu,
															needsRestart = False,
															fnc = fnc)
			if menu in plugins.plugins:
				plugins.plugins[ menu ].append(plugin)


def removeSeriesPlugin(menu, title):
	# Remove from extension menu
	from Components.PluginComponent import plugins
	if plugins:
		for p in plugins.getPlugins( where = menu ):
			if p.name == title:
				plugins.plugins[ menu ].remove(p)
				break
