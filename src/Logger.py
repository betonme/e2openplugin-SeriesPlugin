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

import os, sys, traceback

from Components.config import config

#class Logger(object):
#	def __init__(self):
#		pass

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
		except Exception, e:
			print "SeriesPlugin splog exception " + str(e)
		finally:
			if f:
				f.close()
	
	if sys.exc_info()[0]:
		print "Unexpected error:", sys.exc_info()[0]
		traceback.print_exc(file=sys.stdout)

def sendLog(session):
	print "[SP sendLog] - send_mail"
	logfile = config.plugins.seriesplugin.log_file.value
	filename = str(os.path.basename(logfile))
	
	body_text1 = "\nHello\n\nHere is a log for you.\n"
	if str(config.plugins.seriesplugin.log_reply_user.value) ==  "Dreambox User":
		user_name = ""
	else:
		user_name = "\n\nOptional supplied name: " + str(config.plugins.seriesplugin.log_reply_user.value)
	if str(config.plugins.seriesplugin.log_reply_mail.value) == "myemail@home.com":
		user_email = ""
	else:
		user_email = "\nUser supplied email address: " + str(config.plugins.seriesplugin.log_reply_mail.value)
	body_text2 = "\n\nThis is an automatically generated email from the SeriesPlugin.\n\n\nHave a nice day.\n"
	body_text = body_text1 + user_name + user_email + body_text2
		
	
def handleSuccess(result):
	from Screens.MessageBox import MessageBox
	splog( "[SP sendLog] - Message sent successfully -->",result )
	session.open(
		MessageBox,
		"Message sent successfully\n"+str(result),
		type = MessageBox.TYPE_INFO
	)

def confirmSend(self, confirmed):
	if not confirmed:
		return
	
	# Check preconditions
	if not config.plugins.seriesplugin.write_log.value:
		session.open(
			MessageBox,
			_("Enable Logging"),
			type = MessageBox.TYPE_ERROR
		)
		return
	if not config.plugins.seriesplugin.log_file.value:
		session.open(
			MessageBox,
			_("Specify log file"),
			type = MessageBox.TYPE_ERROR
		)
		return
	if not(
			(str(config.plugins.seriesplugin.log_reply_user.value) !=  "Dreambox User") or
			(str(config.plugins.seriesplugin.log_reply_mail.value) != "myemail@home.com")
		):
		session.open(
			MessageBox,
			_("Enter user name or user mail"),
			type = MessageBox.TYPE_ERROR
		)
		return
	
	import os
	if not os.path.exists(config.plugins.seriesplugin.log_file.value):
		session.open(
			MessageBox,
			_("No log file found"),
			type = MessageBox.TYPE_ERROR
		)
		return
	
	# Get server and send mail
	getMailExchange('crashlog.dream-multimedia-tv.de').addCallback(gotMXServer).addErrback(handleMXError)
	
	MSG_TEXT = "Please consider:\n" \
				+ _("I've to spend my free time for this support!\n\n") \
				+ _("Have You already checked the problem list:\n") \
				+ _("Is the information available at Wunschliste.de / Fernsehserien.de? \n") \
				+ _("Does the start time match? \n") \
				+ _("Check the proxy status: http://lima-status.de? \n") \
				+ _("Maybe the Cache is not yet uptodate, wait 24 hours and recheck? \n") \
	
	session.openWithCallback(
			confirmSend,
			MessageBox,
			MSG_TEXT,
			type = MessageBox.TYPE_YESNO,
			timeout = 60,
			default = False
		)
