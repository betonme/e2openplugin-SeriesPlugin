# by betonme @2012

from Components.config import config

#class Logger(object):
#	def __init__(self):
#		pass

def splog(*args):
	strargs = ""
	for arg in args:
		if strargs: strargs += ", "
		strargs += str(arg)
	print strargs
	
	if config.plugins.seriesplugin.write_log.value:
		strargs += "\n"
		
		# Append to file
		f = None
		try:
			f = open(config.plugins.seriesplugin.log_file.value, 'a')
			f.write(strargs)
		except Exception, e:
			print "SeriesPlugin splog exception " + str(e)
		finally:
			if f:
				f.close()

# Adapted from CrashlogAutoSubmit
def sendLog(session):
	# Not possible yet - need a custom mail gateway
	try:
		from twisted.mail import smtp, relaymanager
		import MimeWriter, mimetools, StringIO
	except ImportError, e:
		splog( "[CrashlogAutoSubmit] Twisted-mail not available, not starting CrashlogAutoSubmitter", e)
		return
	
	def _gotMXRecord(mxRecord):
		return str(mxRecord.name)
	
	def getMailExchange(host):
		splog( "[SP sendLog] - getMailExchange" )
		return relaymanager.MXCalculator().getMX(host).addCallback(_gotMXRecord)
	
	def gotMXServer(mxServer):
		splog( "[SP sendLog] gotMXServer: ",mxServer )
		mxServerFound(mxServer)
	
	def handleMXError(error):
		splog( "[SP sendLog] - MX resolve ERROR:", error.getErrorMessage() )
	
	def mxServerFound(mxServer):
		splog( "[SP sendLog] - mxServerFound -->", mxServer )
		crashLogFilelist = []
		
		message = StringIO.StringIO()
		writer = MimeWriter.MimeWriter(message)
		mailFrom = "enigma2@crashlog.dream-multimedia-tv.de"
		#mailFrom = "enigma2@crashlog.dream-multimedia-tv.de"
		#mailFrom = str(config.plugins.seriesplugin.log_reply_mail.value)
		mailTo = "glaserfrank@gmail.com"
		subject = "SeriesPlugin Log"
		# Define the main body headers.
		#writer.addheader('To', "dream-multimedia-crashlogs <enigma2@crashlog.dream-multimedia-tv.de>")
		#writer.addheader('To', "glaserfrank@gmail.com")
		writer.addheader('To', mailTo)
		#writer.addheader('From', "CrashlogAutoSubmitter <enigma2@crashlog.dream-multimedia-tv.de>")
		writer.addheader('From', mailFrom)
		writer.addheader('Subject', str(subject))
		writer.addheader('Date', smtp.rfc822date())
		writer.addheader('MIME-Version', '1.0')
		
		writer.startmultipartbody('mixed')
		# start with a text/plain part
		part = writer.nextpart()
		body = part.startbody('text/plain')
		part.flushheaders()
		# Define the message body
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
		body.write(body_text)
		
		splog( "[SP sendLog] - send_mail" )
		logfile = config.plugins.seriesplugin.log_file.value
		filename = str(os.path.basename(logfile))
		subpart = writer.nextpart()
		subpart.addheader("Content-Transfer-Encoding", 'base64')
		subpart.addheader("Content-Disposition",'attachment; filename="%s"' % filename)
		subpart.addheader('Content-Description', 'Enigma2 crashlog')
		body = subpart.startbody("%s; name=%s" % ('application/octet-stream', filename))
		mimetools.encode(open(logfile, 'rb'), body, 'base64')
		writer.lastpart()
		
		sending = smtp.sendmail(str(mxServer), mailFrom, mailTo, message.getvalue())
		sending.addCallback(handleSuccess).addErrback(handleError)
	
	def handleError(error):
		from Screens.MessageBox import MessageBox
		splog( "[SP sendLog] - Message send Error -->", error.getErrorMessage() )
		session.open(
			MessageBox,
			"Message send Error\n"+str(error.getErrorMessage()),
			type = MessageBox.TYPE_ERROR
		)
	
	def handleSuccess(result):
		from Screens.MessageBox import MessageBox
		splog( "[SP sendLog] - Message sent successfully -->",result )
		session.open(
			MessageBox,
			"Message sent successfully\n"+str(result),
			type = MessageBox.TYPE_INFO
		)
	
	def confirmSend(self, confirmed):
		if confirmed:
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
				+ _("Have You already checked this problem list:\n") \
				+ _("Is the information available at Wunschliste.de / Fernsehserien.de? \n") \
				+ _("Does the start time match? \n") \
				+ _("Check the proxy: http://lima-status.de? \n") \
				+ _("Maybe the Cache is not yet uptodate, wait 24 hours and recheck? \n") \
	
	session.openWithCallback(
			confirmSend,
			MessageBox,
			MSG_TEXT,
			type = MessageBox.TYPE_YESNO,
			timeout = 15,
			default = False
		)
