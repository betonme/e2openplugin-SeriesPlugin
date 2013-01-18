
import os, sys, traceback

# Localization
from . import _

# GUI (Screens)
from Screens.MessageBox import MessageBox

# Config
from Components.config import config, ConfigSubsection, ConfigEnableDisable, ConfigNumber, ConfigSelection, ConfigYesNo, ConfigText

# Plugin
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

# Plugin internal


#######################################################
# Constants
NAME = "SeriesPlugin"
VERSION = "0.3"
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

scheme_fallback = [
		("", ""),
		("{org:s} S{season:02d}E{episode:02d}"            , "Org S01E01"),
		("{org:s} S{season:02d}E{episode:02d} {title:s}"  , "Org S01E01 Title"),
		("{title:s} {org:s}"                             , "Title Org"),
		("S{season:02d}E{episode:02d} {title:s} {org:s}" , "S01E01 Title Org"),
		("{title:s} S{season:02d}E{episode:02d} {org:s}" , "Title S01E01 Org"),
		("{title:s} S{season:d}E{episode:d} {org:s}"     , "Title S1E1 Org"),
	]


#######################################################
# Initialize Configuration
config.plugins.seriesplugin = ConfigSubsection()

config.plugins.seriesplugin.enabled                   = ConfigEnableDisable(default = False)

config.plugins.seriesplugin.menu_info                 = ConfigYesNo(default = True)
config.plugins.seriesplugin.menu_extensions           = ConfigYesNo(default = False)
config.plugins.seriesplugin.menu_movie_info           = ConfigYesNo(default = True)
config.plugins.seriesplugin.menu_movie_rename         = ConfigYesNo(default = True)

#TODO config.plugins.seriesplugin.open MessageBox or TheTVDB  ConfigSelection if hasTheTVDB

config.plugins.seriesplugin.identifier_elapsed        = ConfigSelection(choices = [("", "")], default = "")
config.plugins.seriesplugin.identifier_today          = ConfigSelection(choices = [("", "")], default = "")
config.plugins.seriesplugin.identifier_future         = ConfigSelection(choices = [("", "")], default = "")
config.plugins.seriesplugin.manager                   = ConfigSelection(choices = [("", "")], default = "")
config.plugins.seriesplugin.guide                     = ConfigSelection(choices = [("", "")], default = "")

config.plugins.seriesplugin.pattern_file              = ConfigText(default = "/etc/enigma2/seriesplugin.cfg", fixed_size = False)

config.plugins.seriesplugin.pattern_title             = ConfigSelection(choices = scheme_fallback, default = "{org:s} S{season:02d}E{episode:02d} {title:s}")
config.plugins.seriesplugin.pattern_description       = ConfigSelection(choices = scheme_fallback, default = "S{season:02d}E{episode:02d} {title:s}\n{org:s}")

# Internal
config.plugins.seriesplugin.lookup_counter            = ConfigNumber(default = 0)

#TODO Show messagebox before rename in movielist


#######################################################
# Plugin configuration
def setup(session, *args, **kwargs):
	#from SeriesPluginConfiguration import SeriesPluginConfiguration
	#session.open(SeriesPluginConfiguration)
	try:
		### For testing only
		import SeriesPluginConfiguration
		reload(SeriesPluginConfiguration)
		###
		session.open(SeriesPluginConfiguration.SeriesPluginConfiguration)
	except Exception, e:
		print _("SeriesPlugin setup exception ") + str(e)
		exc_type, exc_value, exc_traceback = sys.exc_info()
		traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)


#######################################################
# Event Info
def info(session, service=None, *args, **kwargs):
	#from SeriesPluginInfoScreen import SeriesPluginInfoScreen
	#SeriesPluginInfoScreen(session, ref)
	try:
		### For testing only
		import SeriesPluginInfoScreen
		reload(SeriesPluginInfoScreen)
		###
		
		#SeriesPluginInfoScreen.SeriesPluginInfoScreen(session, service)
		session.open(SeriesPluginInfoScreen.SeriesPluginInfoScreen, service)
	except Exception, e:
		print _("SeriesPlugin info exception ") + str(e)
		exc_type, exc_value, exc_traceback = sys.exc_info()
		traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)


#######################################################
# Extensions menu
def extension(session, *args, **kwargs):
	#from SeriesPluginInfoScreen import SeriesPluginInfoScreen
	#SeriesPluginInfoScreen(session)
	try:
		### For testing only
		import SeriesPluginInfoScreen
		reload(SeriesPluginInfoScreen)
		###
		SeriesPluginInfoScreen.SeriesPluginInfoScreen(session)
	except Exception, e:
		print _("SeriesPlugin extension exception ") + str(e)
		exc_type, exc_value, exc_traceback = sys.exc_info()
		traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)


#######################################################
# Movielist menu rename
def movielist_rename(session, service, services=None, *args, **kwargs):
	#from SeriesPluginRenamer import SeriesPluginRenamer
	#SeriesPluginRenamer(session, service)
	try:
		### For testing only
		import SeriesPluginRenamer
		reload(SeriesPluginRenamer)
		###
		session.open(SeriesPluginRenamer.SeriesPluginRenamer, service, services)
	except Exception, e:
		print _("SeriesPlugin renamer exception ") + str(e)
		exc_type, exc_value, exc_traceback = sys.exc_info()
		traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)


#######################################################
# Movielist menu info
def movielist_info(session, service, services=None, *args, **kwargs):
	#from SeriesPluginInfoScreen import SeriesPluginInfoScreen
	#SeriesPluginInfoScreen(session, service, services)
	try:
		### For testing only
		import SeriesPluginInfoScreen
		reload(SeriesPluginInfoScreen)
		###
		session.open(SeriesPluginInfoScreen.SeriesPluginInfoScreen, service)
	except Exception, e:
		print _("SeriesPlugin extension exception ") + str(e)
		exc_type, exc_value, exc_traceback = sys.exc_info()
		traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)


#######################################################
# Timer labeling
def labelTimer(timer, begin=None, end=None, *args, **kwargs):
	#from SeriesPluginTimer import SeriesPluginTimer
	#SeriesPluginTimer(timer, begin, end, *args, **kwargs)
	try:
		### For testing only
		import SeriesPluginTimer
		reload(SeriesPluginTimer)
		###
		SeriesPluginTimer.SeriesPluginTimer(timer, begin, end)
	except Exception, e:
		print _("SeriesPlugin label exception ") + str(e)
		exc_type, exc_value, exc_traceback = sys.exc_info()
		traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)


#######################################################
# Plugin main function
def Plugins(**kwargs):
	descriptors = []
	
	#TODO TEST for recording nameing schema
	
	#TODO icon
	descriptors.append( PluginDescriptor(
																			name = NAME + " " + _("Setup"),
																			description = NAME + " " + _("Setup"),
																			where = PluginDescriptor.WHERE_PLUGINMENU,
																			fnc = setup,
																			needsRestart = False) )
	
	if config.plugins.seriesplugin.enabled.value:
		
		descriptors.append( PluginDescriptor(
																				where = PluginDescriptor.WHERE_SESSIONSTART,	#.WHERE_AUTOSTART, 
																				fnc   = sessionstart,													# fnc=autostart,
																				needsRestart = False) )
		
		if config.plugins.seriesplugin.menu_info.value:
			descriptors.append( PluginDescriptor(
																					name = SHOWINFO,
																					description = SHOWINFO,
																					where = PluginDescriptor.WHERE_EVENTINFO,
																					needsRestart = False,
																					fnc = info) )
		
		if config.plugins.seriesplugin.menu_extensions.value:
			descriptors.append(PluginDescriptor(
																				name = SHOWINFO,
																				description = SHOWINFO,
																				where = PluginDescriptor.WHERE_EXTENSIONSMENU,
																				fnc = extension,
																				needsRestart = False) )
		
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
			plugins.plugins[ menu ].append(plugin)

def removeSeriesPlugin(menu, title):
	# Remove from extension menu
	from Components.PluginComponent import plugins
	if plugins:
		for p in plugins.getPlugins( where = menu ):
			if p.name == title:
				plugins.plugins[ menu ].remove(p)
				break


#######################################################
# Sessionstart

sptest = None
def sessionstart(reason, **kwargs):
	if reason == 0: # startup
		if kwargs.has_key("session"):
			global sptest
			session = kwargs["session"]
			# Initialize seriesplugin
			#sptest = SPTest(session)
	
	# Shutdown
	elif reason == 1:
		if sptest:
			sptest.close()
			sptest = None

import os
from SeriesPlugin import SeriesPlugin

class SPTest(SeriesPlugin):
	def __init__(self, session):
		self.session = session
		SeriesPlugin.__init__(self)
		self.appendEvents()
	
	def close(self):
		self.removeEvents()
	

