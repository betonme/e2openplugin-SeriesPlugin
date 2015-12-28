# -*- coding: utf-8 -*-
# by betonme @2015

import os
import re

# Config
from Components.config import config

# XML
from xml.etree.cElementTree import ElementTree, parse, Element, SubElement, Comment
from Tools.XMLTools import stringToXML

# Plugin internal
from . import _
from XMLFile import XMLFile
from Logger import logDebug, logInfo

URL = "http://176.9.54.54/serienserver/xmltv/wunschliste.xml"


class XMLTVBase(XMLFile):
	
	def __init__(self):
		
		self.__version = "0"
		
		path = None
		
		# Check if xmltvimport exists
		if os.path.exists("/etc/epgimport"):
			logDebug("readXMLTVConfig: Found epgimport")
			path = "/etc/epgimport/wunschliste.sources.xml"
		
		# Check if xmltvimport exists
		elif os.path.exists("/etc/xmltvimport"):
			logDebug("readXMLTVConfig: Found xmltvimport")
			path = "/etc/xmltvimport/wunschliste.sources.xml"
		
		XMLFile.__init__(self, path)
		
		if path:
			self.__import_available = True
		else:
			self.__import_available = False
		
		self.readXMLTVConfig()

	def readXMLTVConfig(self):
		
		etree = self.readXML()
		
		if etree:
			self.__version = etree.getroot().get("version", "1")
			logDebug("readXMLTVConfig: Version " + self.__version)
	
	def writeXMLTVConfig(self):
		
		if int(self.__version[0]) >= 5:
			return;
		
		if self.__import_available:
			
			# Build Header
			from plugin import NAME, VERSION
			root = Element("sources")
			root.set('version', VERSION)
			root.set('created_by', NAME)
			root.append(Comment(_("Don't edit this manually unless you really know what you are doing")))
			
			element = SubElement( root, "source", type = "gen_xmltv", channels = "wunschliste.channels.xml" )
			
			SubElement( element, "description" ).text = "Wunschliste XMLTV"
			SubElement( element, "url" ).text = URL
			
			etree = ElementTree( root )
			
			self.writeXML( etree )
