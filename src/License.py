import socket

from urllib import urlencode
#from urllib import quote_plus
from urllib2 import urlopen, URLError
from urlparse import urlparse as parse   #urlparse module is renamed to urllib.parse in Python 3

from Logger import splog

import os, sys
sys.path.append(os.path.dirname( os.path.realpath( __file__ ) ))
sys.path.append(os.path.dirname( os.path.realpath( __file__ ) ) + '/pyga')

#https://github.com/kra3/py-ga-mob
from pyga.requests import Tracker, Page, Session, Visitor

license = False

class License(object):
	def __init__(self):
		socket.setdefaulttimeout(5)
		self.requestLicense()
	
	def requestLicense(self):
		splog("[SP] checkLicense")
		global license
		
		if license:
			return True
		
		from plugin import VERSION
		
		response = urlopen("http://enigma2-seriesplugin.appspot.com/license.php?version="+VERSION, timeout=5).read()
		splog("[SP] License: ", response)
		if response == "Valid License":
			license = True
			return True
		else:
			license = False
			return False
	
	def checkLicense(self, url, cached):
	
		from Plugins.Extensions.SeriesPlugin.plugin import VERSION,DEVICE
		
		urlparts = parse(url)
		
		parameter = urlencode(
			{
				#'url' : url,
				'version' : VERSION,
				'cached'  : str(cached),
				'device'  : DEVICE
			}
		)
		
		tracker = Tracker('UA-31168065-1', urlparts.netloc)
		visitor = Visitor()
		session = Session()
		if urlparts.query:
			page = Page(urlparts.path + '?' + urlparts.query + '&' + parameter)
		else:
			page = Page(urlparts.path + '?' + parameter)
		tracker.track_pageview(page, session, visitor)
		
		if self.requestLicense():
			return True
		else:
			return False
