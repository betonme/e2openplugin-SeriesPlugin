# -*- coding: utf-8 -*-
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

import os
import re


# Config
from Components.config import config

from enigma import eServiceReference, eServiceCenter
from ServiceReference import ServiceReference

from Screens.MessageBox import MessageBox
from Tools.BoundFunction import boundFunction

# XML
from xml.etree.cElementTree import ElementTree, tostring, parse, Element, SubElement, Comment
from Tools.XMLTools import stringToXML

# Plugin internal
from . import _
from Logger import splog

try:
	#Python >= 2.7
	from collections import OrderedDict
except:
	from OrderedDict import OrderedDict



ChannelReplaceDict = OrderedDict([
	('\(S\)', ''),
	('HD', ''),
	('III', 'drei'),
	('II',  'zwei'),
	#('I',   'eins'),
	('ARD', 'DasErste'),
	('\+', 'Plus'),
	('0', 'null'),
	('1', 'eins'),
	('2', 'zwei'),
	('3', 'drei'),
	('4', 'vier'),
	('5', 'fuenf'),
	('6', 'sechs'),
	('7', 'sieben'),
	('8', 'acht'),
	('9', 'neun'),
	('\xc3\xa4', 'ae'),
	('\xc3\xb6', 'oe'),
	('\xc3\xbc', 'ue'),
	('\xc3\x84', 'ae'),
	('\xc3\x96', 'oe'),
	('\xc3\x9c', 'ue'),
	('\xc3\x9f', 'ss'),
])
CompiledRegexpChannelUnify = re.compile('|'.join(ChannelReplaceDict))
CompiledRegexpChannelRemoveSpecialChars = re.compile('[^a-zA-Z0-9]')
def unifyChannel(text):
	def translate(match):
		m = match.group(0)
		return ChannelReplaceDict.get(m, m)
	
	text = CompiledRegexpChannelUnify.sub(translate, text)
	text = text.decode("utf-8").encode("latin1")
	text = CompiledRegexpChannelRemoveSpecialChars.sub('', text)
	return text.strip().lower()


def getServiceList(ref):
	root = eServiceReference(str(ref))
	serviceHandler = eServiceCenter.getInstance()
	return serviceHandler.list(root).getContent("SN", True)

def getTVBouquets():
	from Screens.ChannelSelection import service_types_tv
	return getServiceList(service_types_tv + ' FROM BOUQUET "bouquets.tv" ORDER BY bouquet')

def buildSTBchannellist(BouquetName = None):
	chlist = None
	chlist = []
	splog("SPC: read STB Channellist..")
	tvbouquets = getTVBouquets()
	splog("SPC: found %s bouquet: %s" % (len(tvbouquets), tvbouquets) )

	if not BouquetName:
		for bouquet in tvbouquets:
			bouquetlist = []
			bouquetlist = getServiceList(bouquet[0])
			for (serviceref, servicename) in bouquetlist:
				chlist.append((servicename, serviceref))
	else:
		for bouquet in tvbouquets:
			if bouquet[1] == BouquetName:
				bouquetlist = []
				bouquetlist = getServiceList(bouquet[0])
				for (serviceref, servicename) in bouquetlist:
					chlist.append((servicename, serviceref))
				break
	return chlist

def getChannelByRef(stb_chlist,serviceref):
	for (channelname,channelref) in stb_chlist:
		if channelref == serviceref:
			return channelname

	

class ChannelsFile(object):

	cache = ""
	mtime = -1
	
	def __init__(self):
		pass

	def readXML(self):
		path = config.plugins.seriesplugin.channel_file.value
		
		# Abort if no config found
		if not os.path.exists(path):
			splog("No configuration file present")
			return None
		
		# Parse if mtime differs from whats saved
		mtime = os.path.getmtime(path)
		if mtime == ChannelsFile.mtime:
			# No changes in configuration, won't read again
			return ChannelsFile.cache
		
		# Parse XML
		try:
			etree = parse(path).getroot()
		except Exception as e:
			splog("Exception in readXML: " + str(e))
			etree = None
			mtime = -1
		
		# Save time and cache file content
		ChannelsFile.mtime = mtime
		ChannelsFile.cache = etree
		return ChannelsFile.cache

	def writeXML(self, etree):
		path = config.plugins.seriesplugin.channel_file.value
		
		def indent(elem, level=0):
			i = "\n" + level*"  "
			if len(elem):
				if not elem.text or not elem.text.strip():
					elem.text = i + "  "
				if not elem.tail or not elem.tail.strip():
					elem.tail = i
				for elem in elem:
					indent(elem, level+1)
				if not elem.tail or not elem.tail.strip():
					elem.tail = i
			else:
				if level and (not elem.tail or not elem.tail.strip()):
					elem.tail = i
		
		indent(etree)
		data = tostring(etree, 'utf-8')
		
		f = None
		try:
			f = open(path, 'w')
			if data:
				f.writelines(data)
		except Exception as e:
			splog("Exception in writeXML: " + str(e))
		finally:
			if f is not None:
				f.close()
		
		# Save time and cache file content
		self.mtime = os.path.getmtime( path )
		self.cache = etree


class ChannelsBase(ChannelsFile):

	channels = {}  # channels[reference] = ( name, [ (name1, uname1), (name2, uname2), ... ] )
	channels_changed = False
	
	def __init__(self):
		ChannelsFile.__init__(self)
		if not ChannelsBase.channels:
			self.resetChannels()
		
	def resetChannels(self):
		ChannelsBase.channels = {}  # channels[reference] = ( name, [ (name1, uname1), (name2, uname2), ... ] )
		ChannelsBase.channels_changed = False
		
		self.loadXML()
		
		#chlist = buildSTBchannellist(config.plugins.seriesplugin.bouquet_main.value)
		#for servicename, serviceref in chlist:
		#	self.lookupServiceAlternatives(serviceref)
		
	#
	# Channel handling
	#
	def lookupServiceAlternatives(self, service):
		#splog("lookupServiceAlternatives service", service)
		serviceref = str(service)
		serviceref = re.sub('::.*', ':', serviceref)
		#splog("lookupServiceAlternatives ref", ref)
		#splog("lookupServiceAlternatives ref in channels", ref in channels)
		if serviceref not in ChannelsBase.channels:
			name = ServiceReference(serviceref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
			alternatives = [ ( name, unifyChannel(name) ), ]
			ChannelsBase.channels[serviceref] = ( name, alternatives )
			ChannelsBase.channels_changed = True
		
		#splog("lookupServiceAlternatives channels")
		#for channel in channels:
		#	splog(channel)
		#splog("lookupServiceAlternatives alternatives")
		#for alternative in alternatives:
		#	splog(alternative)
	
	def compareChannels(self, serviceref, remote):
		splog("SP compareChannels", serviceref, remote)
		if serviceref in ChannelsBase.channels:
			( name, alternatives ) = ChannelsBase.channels[serviceref]
			return True
			
		#	uremote = unifyChannel(remote)		
		#	splog("SP compareChannels", remote, uremote, len(uremote))
		#	
		#	for name, uname in alternatives:
		#		if uname == uremote:
		#			# The channels are equal
		#			splog("SP compareChannels", name, uname, uremote, len(uremote))
		#			return True
		#		elif uname in uremote or uremote in uname:
		#			# Parts of the channels are equal
		#			splog("SP compareChannels in", name, uname, uremote, len(uremote))
		#			return True
		#		#elif uname == "":
		#		#	# The local channel is empty
		#		#	return True
		#		elif "unknown" in uname:
		#			# The local channel is unknown
		#			splog("SP compareChannels unknown", name, remote)
		#			return True

		return False
		
	def lookupChannelByReference(self, serviceref):
		if serviceref in ChannelsBase.channels:
			( name, alternatives ) = ChannelsBase.channels[serviceref]
			for altname, altuname in alternatives:
				if altname:
					splog("SP lookupChannelByReference", altname)
					return altname
			
		return False
	
	def lookupChannelByRemote(self, remote):
		uremote = unifyChannel(remote)	
		
		# Add remote to alternative channels
		for reference, namealternatives in ChannelsBase.channels.iteritems():
			name, alternatives = namealternatives
			if name == remote:
				splog("SP lookupChannel name remote", name, remote)
				return reference, name
			else:
				for altrem, alturem in alternatives:
					if remote == altrem or uremote == alturem:
						splog("SP lookupChannel remote, uremote alturem", remote, uremote, alturem)
						return reference, name
		return False
	
	def addChannel(self, ref, name, remote, uremote):
		splog("SP addChannel name remote uremote", name, remote, uremote)
		#if ref in ChannelsBase.channels:
		#	( ch_name, ch_alternatives ) = ChannelsBase.channels[ref]
		#	ch_alternatives.append( (remote, uremote) )
		#	ChannelsBase.channels[ref] = ( name, ch_alternatives )
		#else:
		ChannelsBase.channels[ref] = ( name, [(remote, uremote)] )
		ChannelsBase.channels_changed = True

	def removeChannel(self, ref):
		if ref in ChannelsBase.channels:
			del ChannelsBase.channels[ref]
			ChannelsBase.channels_changed = True

	#
	# I/O Functions
	#
	def loadXML(self):
		# Read xml config file
		root = self.readXML()
		if root:
			channels = {}
			
			# Parse Config
			def parse(root):
				channels = {}
				version = root.get("version", "1")
				if version.startswith("2"):
					if root:
						for element in root.findall("Channel"):
							name = element.get("name", "")
							reference = element.get("reference", "")
							if name and reference:
								#alternatives = []
								#alternatives = [(name, unifyChannel(name))]
								for alternative in element.findall("Alternative"):
									#alternatives.append( ( alternative.text , unifyChannel(alternative.text) ) )
									alternatives = [( alternative.text , unifyChannel(alternative.text) )]
								channels[reference] = (name, list(set(alternatives)))
				elif version.startswith("1"):
					splog("loadXML channels - Skip old file")
				return channels
			
			channels = parse( root )
			#splog("loadXML channels", channels)
			splog("SP loadXML channels", len(channels))
		else:
			channels = {}
		ChannelsBase.channels = channels

	def saveXML(self):
		if ChannelsBase.channels_changed:
			
			channels = ChannelsBase.channels
			
			# Generate List in RAM
			root = None
			#splog("saveXML channels", channels)
			splog("SP saveXML channels", len(channels))
			
			# Build Header
			from plugin import NAME, VERSION
			root = Element(NAME)
			root.set('version', VERSION)
			root.append(Comment(_("Don't edit this manually unless you really know what you are doing")))
			
			# Build Body
			def build(root, channels):
				if channels:
					for reference, namealternatives in channels.iteritems():
						name, alternatives = namealternatives
						# Add channel
						element = SubElement( root, "Channel", name = stringToXML(name), reference = stringToXML(reference) )
						# Add alternatives
						if alternatives:
							for name, uname in alternatives:
								#SubElement( element, "Alternative", identifier = stringToXML(NOTUSED) ).text = stringToXML(name)
								SubElement( element, "Alternative" ).text = stringToXML(name)
				return root
			
			root = build( root, channels )
			
			self.writeXML( root )
