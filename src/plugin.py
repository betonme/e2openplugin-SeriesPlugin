
import os, sys, traceback

# Localization
from . import _

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
VERSION = "0.6.1"
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
		("Off", "Disabled"),
		("{org:s} S{season:02d}E{episode:02d}"            , "Org S01E01"),
		("{org:s} S{season:02d}E{episode:02d} {title:s}"  , "Org S01E01 Title"),
		("{title:s} {org:s}"                              , "Title Org"),
		("S{season:02d}E{episode:02d} {title:s} {org:s}"  , "S01E01 Title Org"),
		("{title:s} S{season:02d}E{episode:02d} {org:s}"  , "Title S01E01 Org"),
	]


def readPatternFile():
	path = config.plugins.seriesplugin.pattern_file.value
	obj = None
	patterns = None
	
	if os.path.exists(path):
		f = None
		try:
			import json
			f = open(path, 'rb')
			obj = json.load(f)
		except Exception, e:
			splog("[SeriesPlugin] Exception in readEpisodePatternsFile: " + str(e))
			obj = None
			patterns = scheme_fallback
		finally:
			if f is not None:
				f.close()
	if obj:
		header, patterns = obj
		patterns = [tuple(p) for p in patterns]
	return patterns


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

config.plugins.seriesplugin.pattern_file              = ConfigText(default = "/etc/enigma2/seriesplugin.cfg", fixed_size = False)
config.plugins.seriesplugin.pattern_title             = ConfigText(default = "{org:s} S{season:02d}E{episode:02d} {title:s}", fixed_size = False)
config.plugins.seriesplugin.pattern_description       = ConfigText(default = "S{season:02d}E{episode:02d} {title:s} {org:s}", fixed_size = False)

config.plugins.seriesplugin.tidy_rename               = ConfigYesNo(default = False)

config.plugins.seriesplugin.max_time_drift            = ConfigSelectionNumber(0, 600, 1, default = 15)

config.plugins.seriesplugin.write_log                 = ConfigYesNo(default = False)
config.plugins.seriesplugin.log_file                  = ConfigText(default = "/tmp/seriesplugin.log", fixed_size = False)
config.plugins.seriesplugin.log_reply_user            = ConfigText(default = "Dreambox User", fixed_size = False)
config.plugins.seriesplugin.log_reply_mail            = ConfigText(default = "myemail@home.com", fixed_size = False)

# Internal
config.plugins.seriesplugin.lookup_counter            = ConfigNumber(default = 0)


#######################################################
# Start
def start(reason, **kwargs):
	# Startup
	if reason == 0:
		# Start on demand if it is requested
		#from SeriesPlugin import getInstance
		#getInstance()
		pass
	# Shutdown
	elif reason == 1:
		from SeriesPlugin import resetInstance
		resetInstance()


#######################################################
# Plugin configuration
def setup(session, *args, **kwargs):
	#from SeriesPluginConfiguration import SeriesPluginConfiguration
	#session.open(SeriesPluginConfiguration)
	try:
		### For testing only
		#import SeriesPluginConfiguration
		#reload(SeriesPluginConfiguration)
		#session.open(SeriesPluginConfiguration.SeriesPluginConfiguration)
		###
		session.open(SeriesPluginConfiguration)
	except Exception, e:
		splog(_("SeriesPlugin setup exception ") + str(e))
		exc_type, exc_value, exc_traceback = sys.exc_info()
		#traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
		#splog( exc_type, exc_value, exc_traceback.format_exc() )
		splog( exc_type, exc_value, exc_traceback )


#######################################################
# Event Info
def info(session, service=None, event=None, *args, **kwargs):
	#from SeriesPluginInfoScreen import SeriesPluginInfoScreen
	#SeriesPluginInfoScreen(session, ref)
	try:
		### For testing only
		#import SeriesPluginInfoScreen
		#reload(SeriesPluginInfoScreen)
		#session.open(SeriesPluginInfoScreen.SeriesPluginInfoScreen, service, event)
		###
		session.open(SeriesPluginInfoScreen, service, event)
	except Exception, e:
		splog(_("SeriesPlugin info exception ") + str(e))
		exc_type, exc_value, exc_traceback = sys.exc_info()
		#traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
		#splog( exc_type, exc_value, exc_traceback.format_exc() )
		splog( exc_type, exc_value, exc_traceback )


#######################################################
# Extensions menu
def extension(session, *args, **kwargs):
	#from SeriesPluginInfoScreen import SeriesPluginInfoScreen
	#SeriesPluginInfoScreen(session)
	try:
		### For testing only
		#import SeriesPluginInfoScreen
		#reload(SeriesPluginInfoScreen)
		#session.open(SeriesPluginInfoScreen.SeriesPluginInfoScreen)
		###
		session.open(SeriesPluginInfoScreen)
	except Exception, e:
		splog(_("SeriesPlugin extension exception ") + str(e))
		exc_type, exc_value, exc_traceback = sys.exc_info()
		#traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
		#splog( exc_type, exc_value, exc_traceback.format_exc() )
		splog( exc_type, exc_value, exc_traceback )


#######################################################
# Movielist menu rename
def movielist_rename(session, service, services=None, *args, **kwargs):
	try:
		if services:
			if not isinstance(services, list):
				services = [services]	
		else:
			services = [service]
		
		### For testing only
		#import SeriesPluginRenamer
		#reload(SeriesPluginRenamer)
		#SeriesPluginRenamer.SeriesPluginRenamer(session, services)
		###
		SeriesPluginRenamer(session, services)
	except Exception, e:
		splog(_("SeriesPlugin renamer exception ") + str(e))
		exc_type, exc_value, exc_traceback = sys.exc_info()
		#traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
		#splog( exc_type, exc_value, exc_traceback.format_exc() )
		splog( exc_type, exc_value, exc_traceback )


#######################################################
# Movielist menu info
def movielist_info(session, service, *args, **kwargs):
	try:
		### For testing only
		#import SeriesPluginInfoScreen
		#reload(SeriesPluginInfoScreen)
		#session.open(SeriesPluginInfoScreen.SeriesPluginInfoScreen, service)
		###
		session.open(SeriesPluginInfoScreen, service)
	except Exception, e:
		splog(_("SeriesPlugin extension exception ") + str(e))
		exc_type, exc_value, exc_traceback = sys.exc_info()
		#traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
		#splog( exc_type, exc_value, exc_traceback.format_exc() )
		splog( exc_type, exc_value, exc_traceback )


#######################################################
# Timer renaming
def renameTimer(timer, name, begin, end, *args, **kwargs):
	# We have to compare the length,
	# because of the E2 special chars handling for creating the filenames
	#if timer.name == name:
	# Mad Men
	# Mad_Men
	if len(timer.name) == len(name):
		#from SeriesPluginTimer import SeriesPluginTimer
		#SeriesPluginTimer(timer, begin, end, *args, **kwargs)
		try:
			### For testing only
			#import SeriesPluginTimer
			#reload(SeriesPluginTimer)
			#SeriesPluginTimer.SeriesPluginTimer(timer)
			###
			SeriesPluginTimer(timer, name, begin, end)
		except Exception, e:
			splog(_("SeriesPlugin label exception ") + str(e))
			exc_type, exc_value, exc_traceback = sys.exc_info()
			#traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
			#splog( exc_type, exc_value, exc_traceback.format_exc() )
			splog( exc_type, exc_value, exc_traceback )
	else:
		splog("Skip timer because it is already modified", timer.name) #, name, len(timer.name), len(name)


# For compatibility reasons
def modifyTimer(timer, name, *args, **kwargs):
	if timer.name == name: # or len(timer.name) <= len(name):
		#from SeriesPluginTimer import SeriesPluginTimer
		#SeriesPluginTimer(timer, begin, end, *args, **kwargs)
		try:
			SeriesPluginTimer(timer, timer.name, timer.begin, timer.end)
		except Exception, e:
			splog(_("SeriesPlugin label exception ") + str(e))
			exc_type, exc_value, exc_traceback = sys.exc_info()
			#traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
			#splog( exc_type, exc_value, exc_traceback.format_exc() )
			splog( exc_type, exc_value, exc_traceback )
	else:
		splog("Skip timer because it is already modified", name)


# For compatibility reasons
def labelTimer(timer, begin=None, end=None, *args, **kwargs):
	#from SeriesPluginTimer import SeriesPluginTimer
	#SeriesPluginTimer(timer, begin, end, *args, **kwargs)
	try:
		SeriesPluginTimer(timer, timer.name, timer.begin, timer.end)
	except Exception, e:
		splog(_("SeriesPlugin label exception ") + str(e))
		exc_type, exc_value, exc_traceback = sys.exc_info()
		#traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
		#splog( exc_type, exc_value, exc_traceback.format_exc() )
		splog( exc_type, exc_value, exc_traceback )


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
		
		overwriteAutoTimer()
		
		descriptors.append( PluginDescriptor(
																				#where = PluginDescriptor.WHERE_SESSIONSTART,
																				where = PluginDescriptor.WHERE_AUTOSTART,
																				needsRestart = False,
																				fnc = start) )
		
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
# Overwrite AutoTimer support functions

try:
	from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
except:
	AutoTimer = None

ATmodifyTimer = None
ATcheckSimilarity = None


def overwriteAutoTimer():
	try:
		global ATmodifyTimer, ATcheckSimilarity
		if AutoTimer:
			if ATmodifyTimer is None:
				# Backup original function
				ATmodifyTimer = AutoTimer.modifyTimer
				# Overwrite function
				AutoTimer.modifyTimer = SPmodifyTimer
			if ATcheckSimilarity is None:
				# Backup original function
				ATcheckSimilarity = AutoTimer.checkSimilarity
				# Overwrite function
				AutoTimer.checkSimilarity = SPcheckSimilarity
	except:
		splog("SeriesPlugin found old AutoTimer")


def recoverAutoTimer():
	try:
		global ATmodifyTimer, ATcheckSimilarity
		if AutoTimer:
			if ATmodifyTimer:
				AutoTimer.modifyTimer = ATmodifyTimer
				ATmodifyTimer = None
			if ATcheckSimilarity:
				AutoTimer.checkSimilarity = ATcheckSimilarity
				ATcheckSimilarity = None
	except:
		splog("SeriesPlugin found old AutoTimer")


#######################################################
# Customized support functions

from difflib import SequenceMatcher
from ServiceReference import ServiceReference

def SPmodifyTimer(self, timer, name, shortdesc, begin, end, serviceref):
	# Never overwrite existing names, You will lost Your series informations
	#timer.name = name
	# Only overwrite non existing descriptions
	timer.description = timer.description or shortdesc
	timer.begin = int(begin)
	timer.end = int(end)
	timer.service_ref = ServiceReference(serviceref)

def SPcheckSimilarity(self, timer, name1, name2, shortdesc1, shortdesc2, extdesc1, extdesc2, force=False):
	# Check if the new title is part of the existing one
	foundTitle = name1 in name2 or name2 in name1
	
	if timer.searchForDuplicateDescription > 0 or force:
		foundShort = shortdesc1 in shortdesc2 or shortdesc2 in shortdesc1
		
		# NOTE: only check extended if short description already is a match because otherwise
		# it won't evaluate to True anyway
		if foundShort:
			# Some channels indicate replays in the extended descriptions
			# If the similarity percent is higher then 0.8 it is a very close match
			if timer.series_labeling and (extdesc1 == "" or extdesc2 == ""):
				foundExt = True
			else:
				foundExt = ( 0.8 < SequenceMatcher(lambda x: x == " ",extdesc1, extdesc2).ratio() )
	else:
		foundShort = True
		foundExt = True
	
	return foundTitle and foundShort and foundExt
