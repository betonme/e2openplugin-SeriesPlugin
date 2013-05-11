# by betonme @2012

import re
import os, sys, traceback
from time import gmtime, strftime
from datetime import datetime

# Localization
from . import _

from datetime import datetime

from Components.config import config

from enigma import eServiceReference, iServiceInformation, eServiceCenter, ePythonMessagePump
from ServiceReference import ServiceReference

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
from Channels import ChannelsBase, removeEpisodeInfo, lookupServiceAlternatives
from Logger import splog

#from CancelableThread import QueueWithTimeOut, CancelableThread, synchronized, myLock
from Queue import Queue
from threading import Thread


# Constants
IDENTIFIER_PATH = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Identifiers/" )
MANAGER_PATH    = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Managers/" )
GUIDE_PATH      = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Guides/" )


# Globals
instance = None

CompiledRegexpNonDecimal = re.compile(r'[^\d]+')

def dump(obj):
	for attr in dir(obj):
		splog( "config.plugins.seriesplugin.%s = %s" % (attr, getattr(obj, attr)) )

def getInstance():
	global instance
	if instance is None:
		from plugin import VERSION
		splog("SERIESPLUGIN NEW INSTANCE " + VERSION)
		try:
			dump(config.plugins.seriesplugin.dict)
		except Exception, e:
			pass
		instance = SeriesPlugin()
	splog( strftime("%a, %d %b %Y %H:%M:%S", gmtime()) )
	return instance

def resetInstance():
	#Rename to closeInstance
	global instance
	if instance is not None:
		splog("SERIESPLUGIN INSTANCE STOP")
		instance.stop()
		instance = None
	from Cacher import cache
	global cache
	cache = {}


def refactorTitle(org, data):
	if data:
		season, episode, title, series = data
		if config.plugins.seriesplugin.pattern_title.value and not config.plugins.seriesplugin.pattern_title.value == "Off":
			#if season == 0 and episode == 0:
			#	return config.plugins.seriesplugin.pattern_title.value.strip().format( **{'org': org, 'title': title, 'series': series} )
			#else:
			return config.plugins.seriesplugin.pattern_title.value.strip().format( **{'org': org, 'season': season, 'episode': episode, 'title': title, 'series': series} )
		else:
			return org
	else:
		return org

def refactorDescription(org, data):
	if data:
		season, episode, title, series = data
		if config.plugins.seriesplugin.pattern_description.value and not config.plugins.seriesplugin.pattern_description.value == "Off":
			#if season == 0 and episode == 0:
			#	description = config.plugins.seriesplugin.pattern_description.value.strip().format( **{'org': org, 'title': title, 'series': series} )
			#else:
			description = config.plugins.seriesplugin.pattern_description.value.strip().format( **{'org': org, 'season': season, 'episode': episode, 'title': title, 'series': series} )
			description = description.replace("\n", " ")
			return description
		else:
			return org
	else:
		return org


class SeriesPluginWorkerThread(Thread): #(CancelableThread):
	# LATER stop thread this way:
	# http://www.rootninja.com/thread-control-in-python-how-to-safely-stop-a-thread/
	def __init__(self, queue):
		Thread.__init__(self) #CancelableThread.__init__(self)
		self.queue = queue
		#self.messagePump = ePythonMessagePump()
		#self.messagePump.recv_msg.get().append(self.gotThreadMsg)
		self.item = None
	
#	def gotThreadMsg(self, msg):
#		#TEST Because of E2 Update 05.2013
#		identifier, callback, name, begin, end, service, channels = self.item  # self.queue.get() + self.queue.task_done()
#		if callable(callback):
#			callback(msg)

#		AddPopup(
#					msg,
#					MessageBox.TYPE_INFO,
#					0,
#					'SP_PopUp_ID'
#				)
	
	#@synchronized(myLock)
	def run(self):
		while True:
			self.item = self.queue.get()
			if self.item == None:
			#except queue.Empty:
				splog('SeriesPluginWorkerThread has been finished')
				return
			
			identifier, callback, name, begin, end, service, channels = self.item
			splog('SeriesPluginWorkerThread is processing: ', identifier)
			
			# do processing stuff here
			result = None
			
			try:
				result = identifier.getEpisode(
					name, begin, end, service, channels
				)
			except Exception, e:
				splog("SeriesPluginWorkerThread Identifier Exception:", str(e))
				
				# Exception finish job with error
				result = str(e)
			
			try:
				splog("SeriesPluginWorkerThread result")
				if result and len(result) == 4:
					season, episode, title, series = result
					season = int(CompiledRegexpNonDecimal.sub('', season))
					episode = int(CompiledRegexpNonDecimal.sub('', episode))
					title = title.strip()
					splog("SeriesPluginWorkerThread result callback")
					callback( (season, episode, title, series) )
					#self.messagePump.send( (season, episode, title, series) )
				else:
					splog("SeriesPluginWorkerThread result failed")
					#self.messagePump.send( result )
					callback( result )
			except Exception, e:
				splog("SeriesPluginWorkerThread Callback Exception:", str(e))
			
			config.plugins.seriesplugin.lookup_counter.value += 1
#TBD Because of E2 Update 05.2013
#			if (config.plugins.seriesplugin.lookup_counter.value == 10) \
#				or (config.plugins.seriesplugin.lookup_counter.value == 100) \
#				or (config.plugins.seriesplugin.lookup_counter.value % 1000 == 0):
#				from plugin import ABOUT
#				about = ABOUT.format( **{'lookups': config.plugins.seriesplugin.lookup_counter.value} )
#				AddPopup(
#					about,
#					MessageBox.TYPE_INFO,
#					0,
#					'SP_PopUp_ID_About'
#				)
			
			splog("SeriesPluginWorkerThread queue task done")
			
			# kill the thread
			self.queue.task_done()
			
			# Queue empty check
			if self.queue.empty():
				config.plugins.seriesplugin.lookup_counter.save()
			
			# Wait for next job
			#self.run()
			
			splog("SeriesPluginWorkerThread finished")


class SeriesPlugin(Modules, ChannelsBase):
	def __init__(self):
		splog("SeriesPlugin")
		Modules.__init__(self)
		ChannelsBase.__init__(self)
		
		self.serviceHandler = eServiceCenter.getInstance()
		
		self.queue = Queue() #QueueWithTimeOut()
		
		#http://bugs.python.org/issue7980
		datetime.strptime('2012-01-01', '%Y-%m-%d')
		
		self.worker = SeriesPluginWorkerThread(self.queue)
		self.worker.daemon = True
		self.worker.start()
		
		self.identifiers = self.loadModules(IDENTIFIER_PATH, IdentifierBase)
		
		self.identifier_elapsed = self.instantiateModuleWithName( self.identifiers, config.plugins.seriesplugin.identifier_elapsed.value )
		splog(self.identifier_elapsed)
		
		self.identifier_today = self.instantiateModuleWithName( self.identifiers, config.plugins.seriesplugin.identifier_today.value )
		splog(self.identifier_today)
		
		self.identifier_future = self.instantiateModuleWithName( self.identifiers, config.plugins.seriesplugin.identifier_future.value )
		splog(self.identifier_future)

	def stop(self):
		splog("SeriesPluginWorker stop")
		if self.worker:
			splog("SeriesPluginWorker isAlive", self.worker.isAlive())
			splog("SeriesPluginWorker queue empty", self.queue.empty())
			if self.queue: # and self.worker.isAlive():
				splog("SeriesPluginWorker Queue join")
				self.queue.join_with_timeout(1)
			splog("SeriesPluginWorker Worker terminate")
			self.worker.terminate()
		self.worker = None
		if config.plugins.seriesplugin.lookup_counter.isChanged():
			config.plugins.seriesplugin.lookup_counter.save()
		self.saveXML()

	def queueEmpty(self):
		return self.queue and self.queue.qsize()
	
	################################################
	# Identifier functions
	def getEpisode(self, callback, name, begin, end=None, service=None, future=False, today=False, elapsed=False):
		#available = False
		
		name = removeEpisodeInfo(name)
		begin = datetime.fromtimestamp(begin)
		end = datetime.fromtimestamp(end)
		
		channels = lookupServiceAlternatives(service)
		
		#MAYBE for all valid identifier in identifiers:
		
		# Return a season, episode, title tuple
		
		if elapsed:
			identifier = self.identifier_elapsed
		elif today:
			identifier = self.identifier_today
		elif future:
			identifier = self.identifier_future
		else:
			identifier = None
		
		if identifier:
			try:
				#available = True
				splog("SeriesPlugin Worker isAlive queueSize", self.worker and self.worker.isAlive(), self.queue and self.queue.qsize())
				if not self.queue:
					# Create new queue
					splog("SeriesPlugin new Queue")
					self.queue = Queue() #QueueWithTimeOut()
				if not (self.worker and self.worker.isAlive()):
					
					# Create new queue
					splog("SeriesPlugin new Queue")
					self.queue = Queue() #QueueWithTimeOut()
					
					# Start new worker
					splog("SeriesPlugin new Worker")
					self.worker = SeriesPluginWorkerThread(self.queue)
					self.worker.daemon = True
					self.worker.start()
				
				self.queue.put( (identifier, callback, name, begin, end, service, channels) )
				
			except Exception, e:
				splog(_("SeriesPlugin getEpisode exception ") + str(e))
				callback( str(e) )
			return identifier.getName()
			
		#if not available:
		else:
			callback( "No identifier available" )

	def cancel(self):
		self.stop()
