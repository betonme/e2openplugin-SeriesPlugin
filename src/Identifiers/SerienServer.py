﻿# -*- coding: utf-8 -*-
# by betonme @2012

# Imports
import re

from Components.config import config

from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup

from time import time, mktime
from datetime import datetime

# Internal
from Plugins.Extensions.SeriesPlugin.__init__ import _
from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase2
from Plugins.Extensions.SeriesPlugin.Logger import logDebug, logInfo
from Plugins.Extensions.SeriesPlugin.Channels import lookupChannelByReference
from Plugins.Extensions.SeriesPlugin.TimeoutServerProxy import TimeoutServerProxy


class SerienServer(IdentifierBase2):
	def __init__(self):
		IdentifierBase2.__init__(self)
		
		self.server = TimeoutServerProxy()
	
	@classmethod
	def knowsElapsed(cls):
		return True

	@classmethod
	def knowsToday(cls):
		return True

	@classmethod
	def knowsFuture(cls):
		return True

	def getLogo(self, future=True, today=False, elapsed=False):
		if future:
			return "Wunschliste"
		elif today:
			return "Wunschliste"
		else:
			return "Fernsehserien"

	def getEpisode(self, name, begin, end=None, service=None):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or String or None
		
		
		# Check preconditions
		if not name:
			msg =_("Skip: No show name specified")
			logInfo(msg)
			return msg
		if not begin:
			msg = _("Skip: No begin timestamp specified")
			logInfo(msg)
			return msg
		if not service:
			msg = _("Skip: No service / channel specified")
			logInfo(msg)
			return msg
		
		
		self.name = name
		self.begin = begin
		self.end = end
		self.service = service
		
		logInfo("SerienServer getEpisode, name, begin, end=None, service", name, begin, end, service)
		
		# Prepare parameters
		webChannels = lookupChannelByReference(service)
		if not webChannels:
			msg = _("No matching channel found.") + "\n\n" + _("Please open the Channel Editor and add the channel manually.")
			logInfo(msg)
			AddPopup(
				msg,
				MessageBox.TYPE_ERROR,
				-1,
				'SP_PopUp_ID_Error'
			)
			return msg
		
		unixtime = str(begin)
		max_time_drift = self.max_time_drift
		
		# Lookup
		for webChannel in webChannels:
			logDebug("SerienServer getSeasonEpisode(): [\"%s\",\"%s\",\"%s\",%s]" % (name, webChannel, unixtime, max_time_drift))
			
			result = self.server.getSeasonEpisode( name, webChannel, unixtime, self.max_time_drift )
			
			if result and isinstance(result, dict):
				result['service'] = service
				result['channel'] = webChannel
			
			logDebug("SerienServer getSeasonEpisode result:", type(result), result)
			
			return result

		else:
			return ( _("No match found") )
