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
import glob

# for localized messages
from . import _

# Config
from Components.config import config

from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup

from Tools.BoundFunction import boundFunction
from Tools.ASCIItranslit import ASCIItranslit

from enigma import eServiceCenter, iServiceInformation, eServiceReference
from ServiceReference import ServiceReference

# Plugin internal
from SeriesPlugin import getInstance, refactorTitle, refactorDescription
from Logger import splog


# By Bin4ry
def newLegacyEncode(string):
	string2 = ""
	for z, char in enumerate(string.decode("utf-8")):
		i = ord(char)
		if i < 33:
			string2 += " "
		elif i in ASCIItranslit:
			# There is a bug in the E2 ASCIItranslit some (not all) german-umlaut(a) -> AE
			if char.islower():
				string2 += ASCIItranslit[i].lower()
			else:
				string2 += ASCIItranslit[i]
				
		else:
			try:
				string2 += char.encode('ascii', 'strict')
			except:
				string2 += " "
	return string2

def rename(service, name, short, data):
	# Episode data available
	splog(data)
	
	#MAYBE Check if it is already renamed?
	try:
		# Before renaming change content
		renameMeta(service, data)
		if config.plugins.seriesplugin.pattern_title.value and not config.plugins.seriesplugin.pattern_title.value == "Off":
			if config.plugins.seriesplugin.rename_file.value == True:
				renameFile(service, name, data)
		return True
	except:
		#pass
		raise
	return False

# Adapted from MovieRetitle setTitleDescr
def renameMeta(service, data):
	try:
		#TODO Use MetaSupport EitSupport classes from EMC ?
		if service.getPath().endswith(".ts"):
			meta_file = service.getPath() + ".meta"
		else:
			meta_file = service.getPath() + ".ts.meta"
		
		# Create new meta for ts files
		if not os.path.exists(meta_file):
			if os.path.isfile(service.getPath()):
				_title = os.path.basename(os.path.splitext(service.getPath())[0])
			else:
				_title = service.getName()
			_sid = ""
			_descr = ""
			_time = ""
			_tags = ""
			metafile = open(meta_file, "w")
			metafile.write("%s\n%s\n%s\n%s\n%s" % (_sid, _title, _descr, _time, _tags))
			metafile.close()
		
		if os.path.exists(meta_file):
			metafile = open(meta_file, "r")
			sid = metafile.readline()
			oldtitle = metafile.readline().rstrip()
			olddescr = metafile.readline().rstrip()
			rest = metafile.read()
			metafile.close()
			
			if config.plugins.seriesplugin.pattern_title.value and not config.plugins.seriesplugin.pattern_title.value == "Off":
				title = refactorTitle(oldtitle, data)
			else:
				title = oldtitle
			splog(title)
			if config.plugins.seriesplugin.pattern_description.value and not config.plugins.seriesplugin.pattern_description.value == "Off":
				descr = refactorDescription(olddescr, data)
			else:
				descr = olddescr
			splog(descr)
			
			metafile = open(meta_file, "w")
			metafile.write("%s%s\n%s\n%s" % (sid, title, descr, rest))
			metafile.close()
	except Exception as e:
		splog(e)

def renameFile(service, name, data):
	try:
		path = os.path.dirname(service.getPath())
		file_name = os.path.basename(os.path.splitext(service.getPath())[0])
		
		# Refactor title
		if config.plugins.seriesplugin.tidy_rename.value:
			name = refactorTitle(name, data)
		else:
			name = refactorTitle(file_name, data)
		name = newLegacyEncode(name)
		
		src = os.path.join(path, file_name)
		dst = os.path.join(path, name)

		for f in glob.glob(os.path.join(path, src + "*")):
			os.rename(f, f.replace(src, dst))
	except Exception as e:
		splog(e)


class SeriesPluginRenameService(object):
	def __init__(self, service, callback=None):
		self.callback = callback
		
		splog("SeriesPluginRenamer")
		self.seriesPlugin = getInstance()
		self.serviceHandler = eServiceCenter.getInstance()
		
		if isinstance(service, eServiceReference):
			self.service = service
		elif isinstance(service, ServiceReference):
			self.service = service.ref
		else:
			splog(_("SeriesPluginRenamer: Wrong instance"))
			return self.callback(service)
		
		if not os.path.exists( service.getPath() ):
			splog(_("SeriesPluginRenamer: File not exists: ") + service.getPath())
			return self.callback(service)
		
		info = self.serviceHandler.info(service)
		if not info:
			splog(_("SeriesPluginRenamer: No info available: ") + service.getPath())
			return self.callback(service)
		
		self.name = service.getName() or info.getName(service) or ""
		splog("name", self.name)
		
		self.short = ""
		begin = None
		
		event = info.getEvent(service)
		if event:
			self.short = event.getShortDescription()
			begin = event.getBeginTime()
			duration = event.getDuration() or 0
			end = begin + duration or 0
			# We got the exact start times, no need for margin handling
		
		if not begin:
			begin = info.getInfo(service, iServiceInformation.sTimeCreate) or -1
			if begin != -1:
				end = begin + (info.getLength(service) or 0)
			else:
				end = os.path.getmtime(service.getPath())
				begin = end - (info.getLength(service) or 0)
			#MAYBE we could also try to parse the filename
			# We don't know the exact margins, we will assume the E2 default margins
			begin + (int(config.recording.margin_before.value) * 60)
			end - (int(config.recording.margin_after.value) * 60)
		
		rec_ref_str = info.getInfoString(service, iServiceInformation.sServiceref)
		#channel = ServiceReference(rec_ref_str).getServiceName()
		
		self.seriesPlugin.getEpisode(
				self.serviceCallback, 
				#self.name, begin, end, channel, elapsed=True
				#self.name, begin, end, eServiceReference(rec_ref_str), elapsed=True
				self.name, begin, end, rec_ref_str, elapsed=True
			)

	def serviceCallback(self, data=None):
		splog("SeriesPluginRenamer serviceCallback")
		splog(data)
		
		result = None
		
		if data and len(data) == 4:
			if rename(self.service, self.name, self.short, data):
				# Rename was successfully
				result = None
		elif data:
			result = self.service.getPath() + " : " + str( data )
		else:
			result = self.service.getPath()
		
		if callable(self.callback):
			self.callback( result )


#######################################################
# Rename movies
class SeriesPluginRenamer(object):
	def __init__(self, session, services, *args, **kwargs):
		
		if services and not isinstance(services, list):
			services = [services]	
		
		self.services = services
		
		self.failed = []
		self.returned = 0
		
		session.openWithCallback(
			self.confirm,
			MessageBox,
			_("Do You want to start renaming?\nThis will block Your Dreambox until all records are renamed!"),
			MessageBox.TYPE_YESNO,
			timeout = 15,
			default = True
		)

	def confirm(self, confirmed):
		if confirmed and self.services:
			for service in self.services:
				SeriesPluginRenameService(service, self.renamerCallback)

	def renamerCallback(self, result=None):
		self.returned += 1
		if result and isinstance(result, basestring):
			#Maybe later self.failed.append( name + " " + begin.strftime('%y.%m.%d %H-%M') + " " + channel )
			self.failed.append( result )

#TBD Because of E2 Update 05.2013
		#from threading import currentThread
		#if currentThread().getName() == 'MainThread':
#		if self.returned == len(self.services):
#			if self.failed:
#				AddPopup(
#					_("Movie rename has been finished with %d errors:\n") % (len(self.failed)) + "\n".join(self.failed),
#					MessageBox.TYPE_ERROR,
#					0,
#					'SP_PopUp_ID_RenameFinished'
#				)
#			else:
#				AddPopup(
#					_("Movie rename has been finished successfully"),
#					MessageBox.TYPE_INFO,
#					0,
#					'SP_PopUp_ID_RenameFinished'
#				)
