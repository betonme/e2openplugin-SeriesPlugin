# -*- coding: utf-8 -*-
# by betonme @2012

# Imports
import re
import xmlrpclib

from Components.config import config

from Tools.BoundFunction import boundFunction

from time import time, mktime
from datetime import datetime

# Internal
from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase
from Plugins.Extensions.SeriesPlugin.Logger import logDebug, logInfo
from Plugins.Extensions.SeriesPlugin.Channels import lookupChannelByReference
from Plugins.Extensions.SeriesPlugin import _

CompiledRegexpReplaceChars = re.compile("[^a-zA-Z0-9-\*]")


class SerienServer(IdentifierBase):
	def __init__(self):
		IdentifierBase.__init__(self)
		
		from Plugins.Extensions.SeriesPlugin.plugin import REQUEST_PARAMETER
		self.server = xmlrpclib.ServerProxy(config.plugins.seriesplugin.serienserver_url.value + REQUEST_PARAMETER, verbose=False)
	
	@classmethod
	def knowsElapsed(cls):
		return True

	@classmethod
	def knowsToday(cls):
		return True

	@classmethod
	def knowsFuture(cls):
		return True

	def getName(self):
		return "Wunschliste"

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
			msg = _("Skip: No service specified")
			logInfo(msg)
			return msg
		
		
		self.name = name
		self.begin = begin
		self.end = end
		self.service = service
		
		self.knownids = []
		
		logInfo("SerienServer getEpisode, name, begin, end=None, service", name, begin, end, service)
		
		# Prepare parameters
		name = CompiledRegexpReplaceChars.sub(" ", name.lower())
		webChannels = lookupChannelByReference(service)
		if not webChannels:
			msg = _("Check the channel name")
			logInfo(msg)
			return msg
		
		unixtime = str(int(mktime(begin.timetuple())))
		max_time_drift = self.max_time_drift
		
		# Lookup
		for webChannel in webChannels:
			logDebug("SerienServer getSeasonEpisode(): [\"%s\",\"%s\",\"%s\",%s]" % (name, webChannel, unixtime, max_time_drift))
			
			result = self.server.sp.cache.getSeasonEpisode( name, webChannel, unixtime, max_time_drift )
			logDebug("SerienServer getSeasonEpisode result:", result)
			
			if result:
				return ( result['season'], result['episode'], result['title'], result['series'] )

		else:
			if unixtime < time():
				return ( _("Please try Fernsehserien.de") )
			else:
				return ( _("No matching series found") )
