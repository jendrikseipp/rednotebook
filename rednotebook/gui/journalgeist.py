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
	client = ZeitgeistClient()
	if client.get_version() < [0, 3, 1, 99]:
		logging.info('Zeitgeist version too old. You need at least 0.3.2')
		zeitgeist = None
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
		
		#self.vbox.remove(self.daylabel)


if __name__ == '__main__':
	win = gtk.Window()
		
	today = datetime.date.today() - datetime.timedelta(days=1)

	zg_day = JournalZeitgeistWidget(today)

	win.add(zg_day)
	win.show_all()
	win.connect("destroy", lambda w: gtk.main_quit())

	gtk.main()
