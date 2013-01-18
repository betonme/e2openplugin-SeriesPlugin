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

from Screens.MessageBox import MessageBox


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


## {{{ http://code.activestate.com/recipes/146306/ (r1)
import httplib, mimetypes

def post_multipart(host, selector, fields, files):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.
    """
    content_type, body = encode_multipart_formdata(fields, files)
    h = httplib.HTTPConnection(host)
    h.putrequest('POST', selector)
    h.putheader('content-type', content_type)
    h.putheader('content-length', str(len(body)))
    h.endheaders()
    h.send(body)
    return h.getresponse().read()

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
## end of http://code.activestate.com/recipes/146306/ }}}


class Logger(object):
	def sendLog(self):
		print "[SP sendLog]"
		
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
	#TODO
		if not not(
				(str(config.plugins.seriesplugin.log_reply_user.value) != "Dreambox User") or
				(str(config.plugins.seriesplugin.log_reply_mail.value) != "myemail@home.com")
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
					+ _("Does the start time match? \n") \
					+ _("Check the proxy status: http://lima-status.de? \n") \
					+ _("Maybe the Cache is not yet uptodate, wait 24 hours and recheck? \n") \
		
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
		
		logfile = config.plugins.seriesplugin.log_file.value
		filename = str(os.path.basename(logfile))
		
		user_name = str(config.plugins.seriesplugin.log_reply_user.value)
		user_email = str(config.plugins.seriesplugin.log_reply_mail.value)
		
		subject = 'Dreambox SeriesPlugin Auto Send Log'
		message = \
			"\nHello\n\nHere is a log for you.\n" + \
			"\n" + \
			"Supplied forum user name: " + user_name + "\n" + \
			"Supplied email address: " + user_email + "\n" + \
			"\n\nThis is an automatically generated email from the SeriesPlugin.\n\n\nHave a nice day.\n"
		
		response = post_multipart('betonme.lima-city.de', '/SeriesPlugin/mailer.php', [('replyname',user_name), ('replyto',user_email), ('subject',subject), ('message',message)], [('logfile', logfile, filename)] )
		
		splog( "[SP sendLog] - Message sent successfully --> \n", response )
		self.session.open(
			MessageBox,
			"Message sent successfully\n\n"+str(response),
			type = MessageBox.TYPE_INFO
		)
