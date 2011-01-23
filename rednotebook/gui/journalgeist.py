# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2009  Jendrik Seipp
#
# RedNotebook is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# RedNotebook is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with RedNotebook; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# -----------------------------------------------------------------------

'''
Todo:
- Wait for delete methods to be fixed
'''

import sys
import os
import time
import datetime
import logging

gaj_path = '/home/jendrik/projects/RedNotebook/ref/gnome-activity-journal/'
sys.path.insert(0, gaj_path)
sys.path.insert(0, os.path.join(gaj_path, 'src'))

import gtk
import gobject

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
        from common import shade_gdk_color, combine_gdk_color, get_gtk_rgba
        from daywidgets import DayPartWidget
except ImportError, e:
    logging.info('Zeitgeist not available')
    zeitgeist = None
except RuntimeError, e:
    logging.error("Unable to connect to Zeitgeist: %s" % e)
    zeitgeist = None


from daywidgets import DayWidget

class ZeitgeistWidget(gtk.VBox):

    def __init__(self):
        super(ZeitgeistWidget, self).__init__()

        self._init_widgets()

        self.set_size_request(400, 400)
        self.show_all()

    def set_date(self, date):
        # time.mktime coverts from date to secs since epoch
        start = time.mktime(date.timetuple())

        hour = 60*60

        # 06-12: Morning
        # 12-18: Afternoon
        # 18-24: Evening
        # 00-06: Night
        self._periods = [
            (_("Morning"), start + 6*hour, start + 12*hour - 1),
            (_("Afternoon"), start + 12*hour, start + 18*hour - 1),
            (_("Evening"), start + 18*hour, start + 24*hour - 1),
            (_("Night"), start + 24*hour, start + (24+6)*hour - 1),
        ]
        self._init_events()

    def _init_widgets(self):
        self.vbox = gtk.VBox()
        self.pack_start(self.vbox)

        self.daylabel = None

        self._init_date_label()

        #label.modify_bg(gtk.STATE_SELECTED, style.bg[gtk.STATE_SELECTED])

        self.view = gtk.VBox()
        scroll = gtk.ScrolledWindow()
        scroll.set_shadow_type(gtk.SHADOW_NONE)

        evbox2 = gtk.EventBox()
        evbox2.add(self.view)
        self.view.set_border_width(6)

        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.add_with_viewport(evbox2)
        for w in scroll.get_children():
            w.set_shadow_type(gtk.SHADOW_NONE)
        self.vbox.pack_start(scroll)
        self.show_all()

        def change_style(widget, style):
            rc_style = self.style
            color = rc_style.bg[gtk.STATE_NORMAL]
            color = shade_gdk_color(color, 102/100.0)
            evbox2.modify_bg(gtk.STATE_NORMAL, color)

        self.connect("style-set", change_style)

    def _init_date_label(self):

        today = int(time.time() ) - 7*86400
        self.daylabel = gtk.Label()
        self.daylabel.set_markup('<b>' + _('Activities') + '</b>')
        self.daylabel.set_size_request(70, 30)
        hbox = gtk.HBox()
        hbox.pack_start(self.daylabel, False, False)
        #evbox = gtk.EventBox()
        #evbox.add(self.daylabel)
        #evbox.set_size_request(100, 30)
        self.vbox.pack_start(hbox, False, False)
        self.daylabel.show()

        def change_style(widget, style):
            rc_style = self.style
            color = rc_style.bg[gtk.STATE_NORMAL]
            evbox.modify_bg(gtk.STATE_NORMAL, color)
            self.daylabel.modify_bg(gtk.STATE_NORMAL, color)

        #self.connect("style-set", change_style)
        #self.connect("leave-notify-event", lambda x, y: evbox.window.set_cursor(None))

        self.vbox.reorder_child(self.daylabel, 0)

    def _init_events(self):
        for w in self.view:
            self.view.remove(w)
        for period in self._periods:
            part = DayPartWidget(period[0], period[1], period[2])
            self.view.pack_start(part, False, False)

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
        #self.view.pack_end(item)

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

    today = datetime.date.today()

    #zg_day = JournalZeitgeistWidget(today)
    zg_day = ZeitgeistWidget()
    zg_day.set_date(today)

    win.add(zg_day)
    win.show_all()
    win.connect("destroy", lambda w: gtk.main_quit())

    gtk.main()
