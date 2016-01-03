# -*- coding: utf-8 -*-
from __init__ import _

import xmlrpclib

from Components.config import config

# Internal
from Plugins.Extensions.SeriesPlugin.Logger import logDebug, logInfo

class WebChannels(object):
	def __init__(self):
		
		from Plugins.Extensions.SeriesPlugin.plugin import REQUEST_PARAMETER
		self.server = xmlrpclib.ServerProxy(config.plugins.seriesplugin.serienserver_url.value + REQUEST_PARAMETER, verbose=False)

	def getWebChannels(self):
		
		logDebug("SerienServer getWebChannels()")
		
		result = self.server.sp.cache.getWebChannels()
		logDebug("SerienServer getWebChannels result:", result)
		
		return result
