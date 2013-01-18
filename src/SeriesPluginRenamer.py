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

# for localized messages
from . import _

# Config
from Components.config import *

from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup

from Tools.BoundFunction import boundFunction

from enigma import eServiceCenter, iServiceInformation, eServiceReference
from ServiceReference import ServiceReference

# Plugin internal
from SeriesPlugin import getInstance, refactorTitle, refactorDescription


# Adapted from MovieRetitle setTitleDescr
def renameSeries(service, title, descr):
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
			if not title and title != "":
				title = oldtitle
			if not descr and descr != "":
				descr = olddescr
			metafile = open(meta_file, "w")
			metafile.write("%s%s\n%s\n%s" % (sid, title, descr, rest))
			metafile.close()
	except Exception, e:
		print e

def renameFile(service, new_name):
	try:
		path = os.path.dirname(service.getPath())
		file_name = os.path.basename(os.path.splitext(service.getPath())[0])
		src = os.path.join(path, file_name)
		dst = os.path.join(path, new_name)
		import glob
		for f in glob.glob(os.path.join(path, src + "*")):
			os.rename(f, f.replace(src, dst))
	except Exception, e:
		print e


class SeriesPluginService(object):
	def __init__(self, service, callback):
		self.callback = callback
		self.seriesPlugin = getInstance()
		self.serviceHandler = eServiceCenter.getInstance()
		
		if isinstance(service, eServiceReference):
			ref = service
		elif isinstance(service, ServiceReference):
			ref = service.ref
		else:
			print _("SeriesPluginRenamer: Wrong instance")
			return self.callback(service)
		self.ref = ref
		
		if not os.path.exists( ref.getPath() ):
			print _("SeriesPluginRenamer: File not exists: ") + ref.getPath()
			return self.callback(service)
		
		info = self.serviceHandler.info(ref)
		if not info:
			print _("SeriesPluginRenamer: No info available: ") + ref.getPath()
			return self.callback(service)
		
		self.name = name = ref.getName() or info.getName(ref) or ""
		print "name", name
		
		begin = info.getInfo(ref, iServiceInformation.sTimeCreate) or -1
		if begin != -1:
			end = begin + (info.getLength(ref) or 0)
		else:
			end = os.path.getmtime(ref.getPath())
			begin = end - (info.getLength(ref) or 0)
			#MAYBE we could also try to parse the filename
		self.begin = begin
		#self.end
		
		rec_ref_str = info.getInfoString(service, iServiceInformation.sServiceref)
		self.channel = channel = ServiceReference(rec_ref_str).getServiceName()
		print channel
		
		event = info.getEvent(ref)
		self.short = short = event and event.getShortDescription() or ""
		
		self.seriesPlugin.getEpisode(
				self.serviceCallback, 
				name, begin, end, channel, elapsed=True
			)

	def serviceCallback(self, data=None):
		print "SeriesPluginTimer serviceCallback"
		print data
		
		if data:
			# Episode data available
			print data
			name = refactorTitle(self.name, data)
			short = refactorDescription(self.short, data)
			print name
			print short
			
			#MAYBE Check if it is already renamed?
			try:
				# Before renaming change content
				renameSeries(self.ref, name, short)
				renameFile(self.ref, name)
				return self.callback()
			except:
				pass
		self.callback(self.ref)


#######################################################
# Rename movies
class SeriesPluginRenamer(object):
	def __init__(self, session, services, *args, **kwargs):
		self.services = services
		
		self.failed = []
		self.returned = 0
		
		session.openWithCallback(
			self.confirm,
			MessageBox,
			_("Do You want to start background renaming?"),
			MessageBox.TYPE_YESNO,
			timeout = 15,
			default = False
		)

	def confirm(self, confirmed):
		if confirmed:
			for service in self.services:
				SeriesPluginService(service, self.renamerCallback)

	def renamerCallback(self, service=None):
		self.returned += 1
		if service:
			#Maybe later self.failed.append( name + " " + begin.strftime('%y.%m.%d %H-%M') + " " + channel )
			self.failed.append( service.getPath() )
		
		if self.returned == len(self.services):
			if self.failed:
				AddPopup(
					_("Movie rename has been finished with %d errors:\n%s") % (len(self.failed), "\n".join(self.failed)),
					MessageBox.TYPE_ERROR,
					0,
					'SP_PopUp_ID_RenameFinished'
				)
			else:
				AddPopup(
					_("Movie rename has been finished successfully"),
					MessageBox.TYPE_INFO,
					10,
					'SP_PopUp_ID_RenameFinished'
				)

