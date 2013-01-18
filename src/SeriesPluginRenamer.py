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
from thread import start_new_thread

# for localized messages
from . import _

# Config
from Components.config import *

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel

from Tools.BoundFunction import boundFunction

from enigma import eServiceCenter, iServiceInformation, eServiceReference
from ServiceReference import ServiceReference

# Plugin internal
from SeriesPlugin import getInstance


#######################################################
# Configuration screen
class SeriesPluginRenamer(Screen):
	def __init__(self, session, service, services=None, *args, **kwargs):
		Screen.__init__(self, session)
		self.skinName = ["SeriesPluginRenamer", "Console"]
		
		self["text"] = ScrollLabel("")
		self["actions"] = ActionMap(["WizardActions", "DirectionActions"], 
		{
			"ok":    self.cancel,
			"back":  self.cancel,
			"up":    self["text"].pageUp,
			"down":  self["text"].pageDown
		}, -1)
		
		#self.regexp_seriesepisodes = re.compile('(.*)[ _][Ss]{,1}\d{1,2}[EeXx]\d{1,2}.*')  #Only for S01E01 01x01
		
		#self.parent = session.current_dialog
		#print "SeriesPluginRenamer"
		#print self.parent
		
		self.serviceHandler = eServiceCenter.getInstance()
		
		if services:
			if not isinstance(services, list):
				services = [services]	
		else:
			services = [service]
		
		self.services = services
		self.goal = len(services)
		self.progress = 0
		
		self.seriesPlugin = getInstance()
		
		self.onLayoutFinish.append( self.layoutFinished )

	def layoutFinished(self):
		
		self.setTitle( _("SeriesPlugin Renamer") + ' %d/%d' % (self.progress, self.goal) )
		start_new_thread(self.renameNext, ())

	def renameNext(self):
		
		for service in self.services:
		#if self.services:
		#	service = self.services.pop()
			if isinstance(service, eServiceReference):
				ref = service
				print "SeriesPluginRenamer eServiceReference" + str(ref)
			elif isinstance(service, ServiceReference):
				ref = service.ref
				print "SeriesPluginRenamer ServiceReference" + str(ref)
			else:
				print _("SeriesPluginRenamer: No instance of eServiceReference")
				return #self.renameNext()
			
			if not os.path.exists( ref.getPath() ):
				self.progress += 1
				self.setTitle( _("SeriesPlugin Renamer") + ' %d/%d' % (self.progress, self.goal) )
				self.appendText( _("File does not exist: ") + name )
				return #self.renameNext()
			
			#print ref.getServiceName()
			
			name = ref.getName() or "" #info and info.getName(ref)
			print "name", name
			
			# Remove Series Episode naming
			#MAYBE read SeriesPlugin config and parse it ??
			#m = self.regexp_seriesepisodes.match(name)
			#if m:
			#	print m.group(0)       # The entire match
			#	print m.group(1)       # The first parenthesized subgroup.
			#	name = m.group(1)
			
			
			description = "TODO"
			
			
			info = self.serviceHandler.info(ref)
			if not info:
				print _("SeriesPluginRenamer: No info available")
				return
			
			channel = "TODO"
			#rec_ref_str = info.getInfoString(service, iServiceInformation.sServiceref)
			#channel = ServiceReference(rec_ref_str).getServiceName()
			
			#channel = info and info.getName(ref)
			#print "channel", channel
			
			#channel = ServiceReference(ref).getServiceName()
			#print "channel", channel
			
			
			begin = info and info.getInfo(ref, iServiceInformation.sTimeCreate) or -1
			if begin != -1:
				end = begin + (info.getLength(ref) or 0)
			else:
				end = os.path.getmtime(ref.getPath())
				begin = end - (info.getLength(ref) or 0)
				#MAYBE we could also try to parse the filename
			print begin
			print end
			
			short = "TODO"
			
			self.appendText( _("Search: ") + name )
			
			self.seriesPlugin.getEpisode(
					boundFunction(self.episodeCallback, ref, name, short, description), 
					name, short, description, begin, end, channel, elapsed=True
				)

	def episodeCallback(self, ref, name, short, description, data=None):
		try:
			self.progress += 1
			self.setTitle( _("SeriesPlugin Renamer") + ' %d/%d' % (self.progress, self.goal) )
		except:
			pass
		
		if data:
			# Episode data available
			print data
			
			name = self.seriesPlugin.refactorTitle(name, data)
			description = self.seriesPlugin.refactorDescription(description, data)
			
			print name
			print description
			
			#MAYBE Check if it is already renamed?
			
			self.renameSeries(ref, name, description)
			self.renameFile(ref, name)
			
			try:
				self.appendText( _("Finished: ") + name )
			except:
				pass
		else:
			try:
				self.appendText( _("Failed: ") + name )
			except:
				pass
		
		#self.renameNext()

	# Adapted from MovieRetitle setTitleDescr
	def renameSeries(self, service, title, descr):
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

	def renameFile(self, service, new_name):
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

	def appendText(self, text):
		self["text"].setText( self["text"].getText() + text + '\n')

	def cancel(self):
		self.services = []
		self.seriesPlugin.cancel()
		self.close()

	def close(self):
		if self.seriesPlugin:
			print "SeriesPluginRenamer cancel"
			self.seriesPlugin.cancel()
		Screen.close(self)
