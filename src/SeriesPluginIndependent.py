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

# for localized messages
from . import _

# Config
from Components.config import *

import NavigationInstance
from enigma import eTimer
from time import gmtime
#from ServiceReference import ServiceReference

from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup

# Plugin internal
from SeriesPlugin import getInstance, refactorTitle, refactorDescription
from SeriesPluginTimer import SeriesPluginTimer
from Logger import splog


# Globals
instance = None


def startIndependent():
	global instance
	if instance is None:
		instance = SeriesPluginIndependent()
	return instance

def stopIndependent():
	#Rename to closeInstance
	global instance
	if instance is not None:
		instance.stop()
		instance = None


#######################################################
# Label timer
class SeriesPluginIndependent(object):

	data = []
	
	def __init__(self):
		self.etimer = eTimer()
		self.etimer.callback.append(self.run)
		cycle = int(config.plugins.seriesplugin.independent_cycle.value)
		if cycle > 0:
			self.etimer.start( (cycle * 60 * 1000) )
		# Start timer as single shot, just for testing
		#self.etimer.start( 10, True )

	def stop(self):
		if self.etimer.isActive():
			self.etimer.stop()

	def run(self):
		splog("SeriesPluginIndependent run ###########################################")
		splog( strftime("%a, %d %b %Y %H:%M:%S", gmtime()) )
		try:
		
			for timer in NavigationInstance.instance.RecordTimer.timer_list:
				
				if timer.isRunning() or timer.justplay:
					continue
				
				if not timer.repeated:
					if hasattr(timer, 'serieslookupdone') and timer.serieslookupdone:
						continue
				
				#Maybe later add a series whitelist xml
				SeriesPluginTimer(timer, timer.name, timer.begin, timer.end)
				
				timer.serieslookupdone = True
		
		except Exception, e:
			splog(_("SeriesPluginIndependent run exception ") + str(e))
		