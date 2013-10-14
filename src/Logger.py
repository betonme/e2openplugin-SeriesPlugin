﻿#######################################################################
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

from . import _

import os, sys, traceback

from Components.config import config

from Screens.MessageBox import MessageBox

import requests


def splog(*args):
	strargs = ""
	for arg in args:
		if strargs: strargs += " "
		strargs += str(arg)
	print strargs
	
	if config.plugins.seriesplugin.write_log.value:
		strargs += "\n"
		
		# Append to file
		f = None
		try:
			f = open(config.plugins.seriesplugin.log_file.value, 'a')
			f.write(strargs)
			if sys.exc_info()[0]:
				print "Unexpected error:", sys.exc_info()[0]
				traceback.print_exc(file=f)
		except Exception as e:
			print "SeriesPlugin splog exception " + str(e)
		finally:
			if f:
				f.close()
	
	if sys.exc_info()[0]:
		print "Unexpected error:", sys.exc_info()[0]
		traceback.print_exc(file=sys.stdout)
	
	sys.exc_clear()

def post(url, fields, files):
	from plugin import VERSION
	
	headers = {
			'user-agent'     : 'Enigma2-SeriesPlugin/'+VERSION
		}
	
	for (key, filename, value) in files:
		
		# TODO Actually only for one file
		rfiles = {key: open(filename, 'r')}
		r = requests.post(url, headers=headers, params=fields, files=rfiles )
		
		splog("HTTP Response:", r.status_code, r.text)
		return r.text


class Logger(object):
	def sendLog(self):
		print "[SP sendLog]"
		
		return
		
		#LATER
		
		# Check preconditions
		if not config.plugins.seriesplugin.write_log.value:
			self.session.open(
				MessageBox,
				_("Enable Logging"),
				type = MessageBox.TYPE_ERROR
			)
			return
		if not config.plugins.seriesplugin.log_file.value:
			self.session.open(
				MessageBox,
				_("Specify log file"),
				type = MessageBox.TYPE_ERROR
			)
			return
		
		# Avoid "Dreambox User" and "myemail@home.com"
		if not(
				( str(config.plugins.seriesplugin.log_reply_user.value) != str(config.plugins.seriesplugin.log_reply_user.default) ) or
				( str(config.plugins.seriesplugin.log_reply_mail.value) != str(config.plugins.seriesplugin.log_reply_mail.default) )
			):
			self.session.open(
				MessageBox,
				_("Enter user name or user mail"),
				type = MessageBox.TYPE_ERROR
			)
			return
		
		if not os.path.exists(config.plugins.seriesplugin.log_file.value):
			self.session.open(
				MessageBox,
				_("No log file found"),
				type = MessageBox.TYPE_ERROR
			)
			return
		
		MSG_TEXT = "Please consider:\n" \
					+ _("I've to spend my free time for this support!\n\n") \
					+ _("Have You already checked the problem list:\n") \
					+ _("Is the information available at Wunschliste.de / Fernsehserien.de? \n") \
					+ _("Does the start time match? \n")
		
		self.session.openWithCallback(
				self.confirmSend,
				MessageBox,
				MSG_TEXT,
				type = MessageBox.TYPE_YESNO,
				timeout = 60,
				default = False
			)

	def confirmSend(self, confirmed):
		if not confirmed:
			return
		
		#LATER
		#import zipfile
		#logfile = "/tmp/seriesplugin_log.zip"
		#print 'creating archive'
		#zf = zipfile.ZipFile(logfile, mode='w')
		#try:
		#	print 'adding README.txt'
		#	zf.write(config.plugins.seriesplugin.log_file.value)
		#finally:
		#	print 'closing'
		#	zf.close()
		
		logfile = config.plugins.seriesplugin.log_file.value
		filename = str(os.path.basename(logfile))
		
		user_name = str(config.plugins.seriesplugin.log_reply_user.value)
		user_email = str(config.plugins.seriesplugin.log_reply_mail.value)
		
		subject = _('Dreambox SeriesPlugin Auto Send Log')
		message = \
			_("Hello,") + "\n" + \
			_("this is an email from the SeriesPlugin.\n") + "\n" + \
			"\n" + \
			_("Supplied forum user name: ") + user_name + "\n" + \
			_("Supplied email address: ") + user_email + "\n" + \
			_("Have a nice day.") + "\n" + \
			_("Good bye")
		try:
			response = post(
							'http://betonme.lima-city.de/SeriesPlugin/mailer.php', 
							#'http://betonme.my3gb.com/SeriesPlugin/mailer.php',
							#'http://betonme.funpic.de/mailer.php',
							{'replyname':user_name, 'replyto':user_email, 'subject':subject, 'message':message},
							[('File', logfile, filename)]
						)
		except Exception as e:
			response = "Failed, " + str(e)
		
		splog( "[SP sendLog] - Server response:\n", response )
		self.session.open(
			MessageBox,
			_("Server response:") + "\n\n" + str(response),
			type = MessageBox.TYPE_INFO
		)
