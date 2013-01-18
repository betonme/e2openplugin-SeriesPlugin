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

from ServiceReference import ServiceReference

from Tools.BoundFunction import boundFunction

from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup

# Plugin internal
from SeriesPlugin import getInstance, refactorTitle, refactorDescription
from Logger import splog


#######################################################
# Label timer
class SeriesPluginTimer(object):
	def __init__(self, timer, name, begin, end):
		self.timer = timer
		
		splog("SeriesPluginTimer")
		splog(name, timer.name)
		
		self.seriesPlugin = getInstance()
		
		if timer.service_ref:
			channel = timer.service_ref.getServiceName()
			splog(channel)
			
			self.seriesPlugin.getEpisode(
					self.timerCallback,
					name, begin, end, channel, future=True
				)
		else:
			splog("SeriesPluginTimer: No channel specified")
			self.callback()

	def timerCallback(self, data=None):
		splog("SeriesPluginTimer timerCallback")
		splog(data)
		timer = self.timer
		
		if data and len(data) == 4 and timer:
			# Episode data available, refactor name and description
			from SeriesPluginRenamer import newLegacyEncode
			timer.name = refactorTitle(timer.name, data)
			#timer.name = newLegacyEncode(refactorTitle(timer.name, data))
			timer.description = refactorDescription(timer.description, data)
		
		#TODO avoid to many PopUps
		
		elif data:
			AddPopup(
				_("SeriesPlugin: Timer lookup failed\n") + str( data ) + " : " + timer.name + "\n",
				MessageBox.TYPE_ERROR,
				0,
				'SP_PopUp_ID_TimerFinished'
			)
		
		else:
			AddPopup(
				_("SeriesPlugin: Timer lookup failed\n") + timer.name,
				MessageBox.TYPE_ERROR,
				0,
				'SP_PopUp_ID_TimerFinished'
			)
