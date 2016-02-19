# -*- coding: utf-8 -*-
# by betonme @2015

# for localized messages
from . import _

from Components.config import *

from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup

# Plugin internal
from SeriesPluginTimer import SeriesPluginTimer
from Logger import log


loop_data = []
loop_counter = 0


def bareGetSeasonEpisode(service_ref, name, begin, end, description, path, future=True, today=False, elapsed=False):
	result = _("SeriesPlugin is deactivated")
	if config.plugins.seriesplugin.enabled.value:
		
		log.start()
		
		log.info("Bare:", service_ref, name, begin, end, description, path, future, today, elapsed)
		
		from SeriesPlugin import getInstance, refactorTitle, refactorDescription, refactorDirectory
		seriesPlugin = getInstance()
		data = seriesPlugin.getEpisodeBlocking(
			name, begin, end, service_ref, future, today, elapsed
		)
		
		global loop_counter
		loop_counter += 1
		
		if data and isinstance(data, dict):
			name = str(refactorTitle(name, data))
			description = str(refactorDescription(description, data))
			path = refactorDirectory(path, data)
			log.info("Bare: Success", name, description, path)
			return (name, description, path, log.get())
		
		elif data and isinstance(data, basestring):
			global loop_data
			msg = _("Failed: %s." % ( str( data ) ))
			log.debug(msg)
			loop_data.append( name + ": " + msg )
		
		else:
			global loop_data
			msg = _("No data available")
			log.debug(msg)
			loop_data.append( name + ": " + msg )
		
		log.info("Bare: Failed", str(data))
		return str(data)
	
	return result

def bareShowResult():
	global loop_data, loop_counter
	
	if loop_data and config.plugins.seriesplugin.timer_popups.value:
		AddPopup(
			"SeriesPlugin:\n" + _("SP has been finished with errors:\n") +"\n" +"\n".join(loop_data),
			MessageBox.TYPE_ERROR,
			int(config.plugins.seriesplugin.timer_popups_timeout.value),
			'SP_PopUp_ID_Finished'
		)
	elif not loop_data and config.plugins.seriesplugin.timer_popups_success.value:
		AddPopup(
			"SeriesPlugin:\n" + _("%d timer renamed successfully") % (loop_counter),
			MessageBox.TYPE_INFO,
			int(config.plugins.seriesplugin.timer_popups_timeout.value),
			'SP_PopUp_ID_Finished'
		)
	
	loop_data = []
	loop_counter = 0
