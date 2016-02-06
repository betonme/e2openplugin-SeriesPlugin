# -*- coding: utf-8 -*-
# by http://stackoverflow.com/questions/372365/set-timeout-for-xmlrpclib-serverproxy

import xmlrpclib
import httplib
import socket

from Components.config import config

# Internal
from Logger import logDebug, logInfo


class TimeoutServerProxy(xmlrpclib.ServerProxy):
	def __init__(self, *args, **kwargs):
		
		from Plugins.Extensions.SeriesPlugin.plugin import REQUEST_PARAMETER
		uri = config.plugins.seriesplugin.serienserver_url.value + REQUEST_PARAMETER
		
		timeout = config.plugins.seriesplugin.socket_timeout.value
		
		xmlrpclib.ServerProxy.__init__(self, uri, verbose=True, *args, **kwargs)
		
		socket.setdefaulttimeout( float(timeout) )
		
		self.skip = []

	def getWebChannels(self):
		result = None
		try:
			result = self.sp.cache.getWebChannels()
		except Exception as e:
			logInfo("Exception in xmlrpc: " + str(e) + ' - ' + str(result))
		return result

	def getSeasonEpisode( self, name, webChannel, unixtime, max_time_drift ):
		result = None
		if name in self.skip:
			return result
		try:
			result = self.sp.cache.getSeasonEpisode( name, webChannel, unixtime, max_time_drift )
			logDebug("SerienServer getSeasonEpisode result:", result)
		except Exception as e:
			logInfo("Exception in xmlrpc: " + str(e) + ' - ' + str(result))
			self.skip.append(name)
			result = str(e)
		return result
