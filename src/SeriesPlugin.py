# by betonme @2012

import os, sys, traceback
from datetime import datetime

from Queue import Queue
from threading import Thread, Lock

# Localization
from . import _

from Components.config import config

# Plugin framework
from Modules import Modules

# Tools
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.Notifications import AddPopup
from Screens.MessageBox import MessageBox

# Plugin internal
from IdentifierBase import IdentifierBase
from ManagerBase import ManagerBase
from GuideBase import GuideBase
from Helper import unifyName, unifyChannel


# Constants
IDENTIFIER_PATH = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Identifiers/" )
MANAGER_PATH    = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Managers/" )
GUIDE_PATH      = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Guides/" )


# Globals
instance = None


def getInstance():
	global instance
	if instance is None:
		print "SERIESPLUGIN NEW INSTANCE"
		instance = SeriesPlugin()
	return instance

def resetInstance():
	global instance
	if instance is not None:
		#TODO clear caches?
		instance.save()
		instance = None


def refactorTitle(org, data):
	season, episode, title = data
	if config.plugins.seriesplugin.pattern_title.value:
		return config.plugins.seriesplugin.pattern_title.value.format( **{'org': org, 'season': season, 'episode': episode, 'title': title} )
	else:
		return org

def refactorDescription(org, data):
	season, episode, title = data
	if config.plugins.seriesplugin.pattern_description.value:
		description = config.plugins.seriesplugin.pattern_description.value.format( **{'org': org, 'season': season, 'episode': episode, 'title': title} )
		description = description.replace("\n", " ")
		return description
	else:
		return org


class SeriesPluginWorkerThread(Thread):
	def __init__(self, queue):
		Thread.__init__(self)
		self.queue = queue
		self.item = None
		self.lock = Lock()
	
	def run(self):
		while True:
			self.lock.acquire()
			self.item = self.queue.get()
			print 'SeriesPluginWorkerThread is processing'
			service, callback, name, begin, end, channel = self.item
			
			# do processing stuff here
			service.getEpisode(
				self.workerCallback,
				name, begin, end, channel
			)
	
	def workerCallback(self, data=None):
		print 'SeriesPluginWorkerThread callback'
		service, callback, name, begin, end, channel = self.item
		callback(data)
		# kill the thread
		self.queue.task_done()
		#self.run()
		self.lock.release()
		
		config.plugins.seriesplugin.lookup_counter.value += 1
		if (config.plugins.seriesplugin.lookup_counter.value == 10) \
			or (config.plugins.seriesplugin.lookup_counter.value == 100) \
			or (config.plugins.seriesplugin.lookup_counter.value % 1000 == 0):
			from plugin import ABOUT
			about = ABOUT.format( **{'lookups': config.plugins.seriesplugin.lookup_counter.value} )
			AddPopup(
				about,
				MessageBox.TYPE_INFO,
				0,
				'SP_PopUp_ID_About'
			)


class SeriesPlugin(Modules):
	def __init__(self):
		print "SeriesPlugin"
		Modules.__init__(self)
		self.queue = Queue()
		#self.worker = Thread(target=fetchEpisodeInformation, args=(self.queue,))
		self.worker = SeriesPluginWorkerThread(self.queue)
		self.worker.daemon = True
		self.worker.start()
		
		self.identifiers = self.loadModules(IDENTIFIER_PATH, IdentifierBase)
		if self.identifiers:
			identifier_elapsed = [k for k,v in self.identifiers.items() if v.knowsElapsed()]
			config.plugins.seriesplugin.identifier_elapsed.setChoices( identifier_elapsed )
			if not config.plugins.seriesplugin.identifier_elapsed.value:
				config.plugins.seriesplugin.identifier_elapsed.value = identifier_elapsed[0]
			
			identifier_today = [k for k,v in self.identifiers.items() if v.knowsToday()]
			config.plugins.seriesplugin.identifier_today.setChoices( identifier_today )
			if not config.plugins.seriesplugin.identifier_today.value:
				config.plugins.seriesplugin.identifier_today.value = identifier_today[0]
			
			identifier_future = [k for k,v in self.identifiers.items() if v.knowsFuture()]
			config.plugins.seriesplugin.identifier_future.setChoices( identifier_future )
			if not config.plugins.seriesplugin.identifier_future.value:
				config.plugins.seriesplugin.identifier_future.value = identifier_future[0]
		
		self.identifier_elapsed = self.instantiateModuleWithName( self.identifiers, config.plugins.seriesplugin.identifier_elapsed.value )
		print self.identifier_elapsed
		self.identifier_today = self.instantiateModuleWithName( self.identifiers, config.plugins.seriesplugin.identifier_today.value )
		print self.identifier_today
		self.identifier_future = self.instantiateModuleWithName( self.identifiers, config.plugins.seriesplugin.identifier_future.value )
		print self.identifier_future
		
		self.managers = self.loadModules(MANAGER_PATH, ManagerBase)
		if self.managers:
			managers = self.managers.keys()
			config.plugins.seriesplugin.manager.setChoices( managers )
			if not config.plugins.seriesplugin.manager.value:
				config.plugins.seriesplugin.manager.value = managers[0]
		if config.plugins.seriesplugin.manager.value:
			self.manager = self.instantiateModuleWithName( self.managers, config.plugins.seriesplugin.manager.value )
			print self.manager
		
		self.guides = self.loadModules(GUIDE_PATH, GuideBase)
		if self.guides:
			guides = self.guides.keys()
			config.plugins.seriesplugin.guide.setChoices( guides )
			if not config.plugins.seriesplugin.guide.value:
				config.plugins.seriesplugin.guide.value = guides[0]
		if config.plugins.seriesplugin.guide.value:
			self.guide = self.instantiateModuleWithName( self.guides, config.plugins.seriesplugin.guide.value )
			print self.guide

	def save(self):
		config.plugins.seriesplugin.lookup_counter.save()


	################################################
	# Identifier functions
	def getEpisode(self, callback, name, begin, end=None, channel=None, future=False, today=False, elapsed=False):
		#available = False
		
		name = unifyName(name)
		begin = datetime.fromtimestamp(begin + config.recording.margin_before.value * 60)
		end = datetime.fromtimestamp(end + config.recording.margin_after.value * 60)
		channel = unifyChannel(channel)
		
		#MAYBE for all valid service in services:
		
		# Return a season, episode, title tuple
		
		if elapsed:
			service = self.identifier_elapsed
		elif today:
			service = self.identifier_today
		elif future:
			service = self.identifier_future
		else:
			service = None
		
		if service:
			#if ( future and service.knowsFuture() ) or \
			#	 ( today and service.knowsToday() ) or \
			#	 ( elapsed and service.knowsElapsed() ):
			try:
				#available = True
				#service.getEpisode(
				#	boundFunction(getEpisodeCallback, callback),
				#	name, begin, end, channel
				#)
				
				self.queue.put( (service, callback, name, begin, end, channel) )
			except Exception, e:
				print _("SeriesPlugin getEpisode exception ") + str(e)
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
				callback()
			return service.getName()
			
		#if not available:
		else:
			callback()

	################################################
	# Manager functions
	def getStates(self, callback, show_name, season, episode):
		if self.managers:
			# Return a season, episode, title tuple
			for manager in self.managers:
				name = manager.getName()
				manager.getState(
						boundFunction(self.getStatesCallback, callback, name),
						show_name, season, episode
					)
		else:
			callback()

	def getStatesCallback(self, callback, name, state):
		print "SeriesPlugin getStatesCallback"
		print state
		
		# Problem we have to collect all deferreds or cancel them
		#if state:
			#TODO list of states
			#states.append( (name, state) )
		callback( (name, state) )

	def cancel(self):
		if self.identifier_elapsed:
			self.identifier_elapsed.cancel()
		if self.identifier_today:
			self.identifier_today.cancel()
		if self.identifier_future:
			self.identifier_future.cancel()
