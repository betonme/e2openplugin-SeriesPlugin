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
import NavigationInstance

# AutoTimerIgnoreEntry
try:
	from Plugins.Extensions.AutoTimer.AutoTimerComponent import AutoTimerIgnoreEntry
except ImportError as ie:
	AutoTimerIgnoreEntry = None

pattern1 = "S{season:d}E{episode:d}"
pattern2 = "S{season:02d}E{episode:02d}"

#######################################################
# Label timer
class SeriesPluginTimer(object):
	def __init__(self, timer, name, begin, end, avoidDuplicates=False, timers=None, moviedict=None, autotimer=None, *args, **kwargs):
		self.timer = timer
		
		splog("SeriesPluginTimer")
		splog(name, timer.name)
		
		self.seriesPlugin = getInstance()
		
		self.autoTimer = autotimer
		self.timers = timers
		self.moviedict = moviedict
		self.avoidDuplicates = avoidDuplicates
		splog("SeriesPluginTimer avoidDuplicates=" + str(self.avoidDuplicates))
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
			removeTimer = False
			if self.avoidDuplicates:
				dirname = timer.dirname
				# Update list of known episodes
				if not self.moviedict == None:
					self.seriesPlugin.addMoviesToEpisodes(dirname, self.moviedict)
				if not self.timers == None:
					self.seriesPlugin.addTimersToEpisodes(self.timers, False)
				# Check if the current Episode is already in the list...
				season, episode, title, series = data
				episode1 = pattern1.format( **{'season': season, 'episode': episode} )
				episode2 = pattern2.format( **{'season': season, 'episode': episode} )
				splog("SeriesPluginTimer: check duplicates for series: " + series)
				if series in self.seriesPlugin.existingEpisodes:
					splog("SeriesPluginTimer: series found")
					existingEpisodes = self.seriesPlugin.existingEpisodes[series]
					splog("SeriesPluginTimer: check duplicates for episode: " + episode1 + " ; " + episode2)	
					if episode1 in existingEpisodes or \
						episode2 in existingEpisodes:
						# If AutoTimer already knows about ignoreentries: Add this timer so that it will not be readded.
						if not AutoTimerIgnoreEntry is None:
							ignoreEntry = AutoTimerIgnoreEntry( serviceref=timer.service_ref, eit=timer.eit, begin=timer.begin, end=timer.end, name=timer.name, description=timer.description )
							splog("SeriesPluginTimer: Adding IgnoreEntry: " + ignoreEntry.name)
							if not self.autoTimer == None:
								self.autoTimer.addIgnore( ignoreEntry, writexml=True )
						removeTimer = True
					else:
						splog("SeriesPluginTimer: episode not found in " + str(existingEpisodes))
				else:
					splog("SeriesPluginTimer: series not found in " + str(self.seriesPlugin.existingEpisodes.keys()))
			if removeTimer:
				splog("SeriesPluginTimer: Removing Duplicate Timer:" + timer.name + " : " + str( data ))
				if timer in NavigationInstance.instance.RecordTimer.processed_timers:
					NavigationInstance.instance.RecordTimer.processed_timers.remove(timer)
				elif timer in NavigationInstance.instance.RecordTimer.timer_list:
					NavigationInstance.instance.RecordTimer.timer_list.remove(timer)
			else:
				series = timer.name
				timer.name = refactorTitle(timer.name, data)
				#from SeriesPluginRenamer import newLegacyEncode
				#timer.name = newLegacyEncode(refactorTitle(timer.name, data))
				timer.description = refactorDescription(timer.description, data)
				self.seriesPlugin.addEpisode(timer.name, timer.description, timer.extdesc, series=series)
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
