import sys
import os
import time
import datetime
import logging

gaj_path = '/home/jendrik/projects/RedNotebook/ref/gnome-activity-journal/'
sys.path.insert(0, gaj_path)
sys.path.insert(0, os.path.join(gaj_path, 'src'))

import gtk

try:
	import zeitgeist
	from zeitgeist.client import ZeitgeistClient
	CLIENT = ZeitgeistClient()
	if CLIENT.get_version() < [0, 3, 1, 99]:
		logging.info('Zeitgeist version too old. You need at least 0.3.2')
		zeitgeist = None
	else:
		from zeitgeist.datamodel import Event, Subject, Interpretation, Manifestation, \
										ResultType, TimeRange
		from widgets import Item
except ImportError, e:
	logging.info('Zeitgeist not available')
	zeitgeist = None
except RuntimeError, e:
	logging.error("Unable to connect to Zeitgeist: %s" % e)
	zeitgeist = None
	

from daywidgets import DayWidget

class JournalZeitgeistWidget(DayWidget):
	def __init__(self, date):
		next_date = date + datetime.timedelta(days=1)
		# time.mktime coverts from date to secs since epoch
		day_start = time.mktime(date.timetuple())
		# day_end really is the start of the next day
		day_end = time.mktime(next_date.timetuple())
		DayWidget.__init__(self, day_start, day_end)
		
		day_part_widgets = self.view.get_children()
		day_part = day_part_widgets[1]
		day_part.get_events()
		print day_part.events
		
		#self.vbox.remove(self.daylabel)
		
		self.event_timerange = [day_start * 1000, day_end * 1000]
		self.event_templates = (
			Event.new_for_values(interpretation=Interpretation.VISIT_EVENT.uri),
			Event.new_for_values(interpretation=Interpretation.MODIFY_EVENT.uri),
			Event.new_for_values(interpretation=Interpretation.CREATE_EVENT.uri),
			Event.new_for_values(interpretation=Interpretation.OPEN_EVENT.uri),
		)
		
	
		CLIENT.install_monitor(self.event_timerange, self.event_templates,
			self.notify_insert_handler, self.notify_delete_handler)
			
		self.get_events()
		
	def set_events(self, events):
		print 'SETTING', events
		event = events[0]
		item = Item(event)
		self.view.pack_end(item)
			
	def get_events(self):#, *discard):
		if self.event_templates and len(self.event_templates) > 0:
			CLIENT.find_events_for_templates(self.event_templates,
				self.set_events, self.event_timerange, num_events=50000,
				result_type=ResultType.MostRecentSubjects)
		else:
			print 'No templates'
			#self.view.hide()

	def notify_insert_handler(self, time_range, events):
		# FIXME: Don't regenerate everything, we already get the
		# information we need
		print 'INCOMING', events
		self.get_events()

	def notify_delete_handler(self, time_range, event_ids):
		# FIXME: Same as above
		print 'OUTGOING', events
		self.get_events()


if __name__ == '__main__':
	win = gtk.Window()
		
	today = datetime.date.today() - datetime.timedelta(days=1)

	zg_day = JournalZeitgeistWidget(today)

	win.add(zg_day)
	win.show_all()
	win.connect("destroy", lambda w: gtk.main_quit())

	gtk.main()
