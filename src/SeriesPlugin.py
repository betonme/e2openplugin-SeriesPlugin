# by betonme @2012

import re
import os, sys, traceback
from time import time, gmtime, strftime
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
from Logger import splog

# Constants
IDENTIFIER_PATH = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Identifiers/" )
MANAGER_PATH    = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Managers/" )
GUIDE_PATH      = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Guides/" )


# Globals
instance = None

ComiledRegexpNonDecimal = re.compile(r'[^\d.]+')


def getInstance():
	global instance
	if instance is None:
		splog("SERIESPLUGIN NEW INSTANCE")
		instance = SeriesPlugin()
	splog( strftime("%a, %d %b %Y %H:%M:%S", gmtime()) )
	return instance

def resetInstance():
#Rename to closeInstance
	global instance
	if instance is not None:
		#Maybe clear caches?
		instance.stop()
		instance = None


def refactorTitle(org, data):
	if data:
		season, episode, title = data
		if config.plugins.seriesplugin.pattern_title.value and not config.plugins.seriesplugin.pattern_title.value == "Off":
			return config.plugins.seriesplugin.pattern_title.value.strip().format( **{'org': org, 'season': season, 'episode': episode, 'title': title} )
		else:
			return org
	else:
		return org

def refactorDescription(org, data):
	if data:
		season, episode, title = data
		if config.plugins.seriesplugin.pattern_description.value and not config.plugins.seriesplugin.pattern_description.value == "Off":
			description = config.plugins.seriesplugin.pattern_description.value.strip().format( **{'org': org, 'season': season, 'episode': episode, 'title': title} )
			description = description.replace("\n", " ")
			return description
		else:
			return org
	else:
		return org

class QueueWithTimeOut(Queue):
	def __init__(self):
		Queue.__init__(self)
	def join_with_timeout(self, timeout):
		self.all_tasks_done.acquire()
		endtime = time() + timeout
		while self.unfinished_tasks:
			remaining = endtime - time()
			if remaining <= 0.0:
				break
			self.all_tasks_done.wait(remaining)
		self.all_tasks_done.release()


##glock = Lock()

class SeriesPluginWorkerThread(Thread):
	#lock = Lock()
	
	def __init__(self, queue):
		Thread.__init__(self)
		self.queue = queue
		self.item = None
		###self.lock = Lock()
	
	def run(self):
		#if True: 
		while True:
			###self.lock.acquire()
			#SeriesPluginWorkerThread.lock.acquire()
			##glock.acquire()
			#try:
			self.item = self.queue.get()
			if self.item == None:
			#except queue.Empty:
				splog('SeriesPluginWorkerThread has been finished')
				###self.lock.release()
				#SeriesPluginWorkerThread.lock.release()
				##glock.release()
				return
			
			splog('SeriesPluginWorkerThread is processing')
			service, callback, name, begin, end, channel = self.item
			
			# do processing stuff here
			try:
				service.getEpisode(
					self.workerCallback,
					name, begin, end, channel
				)
			except Exception, e:
				splog("SeriesPluginWorkerThread Exception:", str(e))
				# Exception finish job with error
				self.workerCallback()
	
	def workerCallback(self, data=None):
		splog('SeriesPluginWorkerThread callback')
		service, callback, name, begin, end, channel = self.item
		
		if data:
			season, episode, title = data
			season = int(ComiledRegexpNonDecimal.sub('', season))
			episode = int(ComiledRegexpNonDecimal.sub('', episode))
			title = title.strip()
			callback( (season, episode, title) )
		else:
			callback()
		
		# kill the thread
		self.queue.task_done()
		###self.lock.release()
		#SeriesPluginWorkerThread.lock.release()
		##glock.release()
		
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
		
		# Queue empty check
		if self.queue.empty():
			config.plugins.seriesplugin.lookup_counter.save()
		
		# Wait for next job
		#self.run()


class SeriesPlugin(Modules):
	def __init__(self):
		splog("SeriesPlugin")
		Modules.__init__(self)
		self.queue = QueueWithTimeOut() #Queue()
		
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
		splog(self.identifier_elapsed)
		self.identifier_today = self.instantiateModuleWithName( self.identifiers, config.plugins.seriesplugin.identifier_today.value )
		splog(self.identifier_today)
		self.identifier_future = self.instantiateModuleWithName( self.identifiers, config.plugins.seriesplugin.identifier_future.value )
		splog(self.identifier_future)
		
		self.managers = self.loadModules(MANAGER_PATH, ManagerBase)
		if self.managers:
			managers = self.managers.keys()
			config.plugins.seriesplugin.manager.setChoices( managers )
			if not config.plugins.seriesplugin.manager.value:
				config.plugins.seriesplugin.manager.value = managers[0]
		if config.plugins.seriesplugin.manager.value:
			self.manager = self.instantiateModuleWithName( self.managers, config.plugins.seriesplugin.manager.value )
			splog(self.manager)
		
		self.guides = self.loadModules(GUIDE_PATH, GuideBase)
		if self.guides:
			guides = self.guides.keys()
			config.plugins.seriesplugin.guide.setChoices( guides )
			if not config.plugins.seriesplugin.guide.value:
				config.plugins.seriesplugin.guide.value = guides[0]
		if config.plugins.seriesplugin.guide.value:
			self.guide = self.instantiateModuleWithName( self.guides, config.plugins.seriesplugin.guide.value )
			splog(self.guide)

	def isActive(self):
		return self.worker and self.worker.isAlive()

	def stop(self):
		if self.queue and not self.queue.empty():
			active = self.isActive()
			splog("SeriesPluginWorker isAlive", active)
			if active:
				splog("Wait a moment")
				# Wait for the worker thread (in seconds)
				self.queue.join_with_timeout(10)
		#if config.plugins.seriesplugin.lookup_counter.isChanged():
		#	config.plugins.seriesplugin.lookup_counter.save()


	################################################
	# Identifier functions
	def getEpisode(self, callback, name, begin, end=None, channel=None, future=False, today=False, elapsed=False):
		#available = False
		
		name = unifyName(name)
		begin = datetime.fromtimestamp(begin)
		end = datetime.fromtimestamp(end)
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
				splog("self.worker and self.worker.isAlive()", self.worker and self.worker.isAlive())
				if not (self.worker and self.worker.isAlive()):
					# Start new worker
					self.worker = SeriesPluginWorkerThread(self.queue)
					self.worker.daemon = True
					self.worker.start()
				
				self.queue.put( (service, callback, name, begin, end, channel) )
				
			except Exception, e:
				splog(_("SeriesPlugin getEpisode exception ") + str(e))
				exc_type, exc_value, exc_traceback = sys.exc_info()
				#traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
				splog( exc_type, exc_value, exc_traceback.format_exc() )
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
		splog("SeriesPlugin getStatesCallback")
		splog(state)
		
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
