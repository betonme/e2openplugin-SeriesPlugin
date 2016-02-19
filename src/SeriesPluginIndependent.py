﻿# -*- coding: utf-8 -*-
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

#TODO Add optional popup

# for localized messages
from . import _

# Config
from Components.config import *

import NavigationInstance
from enigma import eTimer
from time import localtime
#from ServiceReference import ServiceReference

# Plugin internal
from SeriesPluginTimer import SeriesPluginTimer
from Logger import log


# Globals
instance = None


def startIndependent():
	global instance
	instance = SeriesPluginIndependent()
	return instance

def stopIndependent():
	#Rename to closeInstance
	global instance
	if instance:
		instance.stop()
		instance = None

def runIndependent():
	try:
		
		spt = SeriesPluginTimer()
		
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
			
			#Maybe later
			# Add a series whitelist
			# Configured with a dialog
			# Stored in a db or xml
			
			spt.getEpisode(timer)
			
	except Exception as e:
		log.exception( _("Independent mode exception") + "\n" + str(e))


#######################################################
# Label timer
class SeriesPluginIndependent(object):

	data = []
	
	def __init__(self):
		self.etimer = eTimer()
		self.etimer_conn = None
		try:
			self.etimer_conn = self.etimer.timeout.connect(self.run)
		except:
			self.etimer.callback.append(self.run)
		cycle = int(config.plugins.seriesplugin.independent_cycle.value)
		if cycle > 0:
			self.etimer.start( (cycle * 60 * 1000) )
		# Start timer as single shot, just for testing
		#self.etimer.start( 10, True )

	def run(self):
		log.debug("SeriesPluginIndependent: run",  strftime("%a, %d %b %Y %H:%M:%S", localtime()) )

		runIndependent()

	def stop(self):
		self.etimer_conn = None
		try:
			self.etimer.callback.remove(self.run)
		except:
			pass
