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

import logging
import datetime
import os

import gtk
import gobject


class ActionButton(gtk.Button):
    def __init__(self, text, action):
        gtk.Button.__init__(self, text)
        self.connect('clicked', action)


class UrlButton(ActionButton):
    def __init__(self, text, url):
        import webbrowser
        action = lambda x: webbrowser.open(url)
        ActionButton.__init__(self, text, action)


class CustomComboBoxEntry(object):
    def __init__(self, combo_box):
        self.combo_box = combo_box

        self.liststore = gtk.ListStore(gobject.TYPE_STRING)
        self.combo_box.set_model(self.liststore)
        #self.combo_box.set_wrap_width(5)
        self.combo_box.set_text_column(0)
        self.entry = self.combo_box.get_child()

        # Autocompletion
        self.entry_completion = gtk.EntryCompletion()
        self.entry_completion.set_model(self.liststore)
        self.entry_completion.set_minimum_key_length(1)
        self.entry_completion.set_text_column(0)
        self.entry.set_completion(self.entry_completion)

    def add_entry(self, entry):
        self.liststore.append([entry])

    def set_entries(self, value_list):
        self.clear()
        self.combo_box.set_model(None)
        for entry in value_list:
            self.add_entry(entry)
        self.combo_box.set_model(self.liststore)

    def get_active_text(self):
        return self.entry.get_text().decode('utf-8')

    def set_active_text(self, text):
        return self.entry.set_text(text)

    def clear(self):
        self.combo_box.set_model(None)
        if self.liststore:
            self.liststore.clear()
        self.set_active_text('')
        self.combo_box.set_model(self.liststore)

    def connect(self, *args, **kargs):
        self.combo_box.connect(*args, **kargs)

    def set_editable(self, editable):
        self.entry.set_editable(editable)


class CustomListView(gtk.TreeView):
    def __init__(self, columns):
        """
        *columns* must be a list of (header, type) pairs e.g. [('title', str)].
        """
        gtk.TreeView.__init__(self)
        headers, types = zip(*columns)
        # create a TreeStore with columns to use as the model
        self.set_model(gtk.ListStore(*types))

        columns = [gtk.TreeViewColumn(header) for header in headers]

        # add tvcolumns to tree_view
        for index, column in enumerate(columns):
            self.append_column(column)

            # create a CellRendererText to render the data
            cell_renderer = gtk.CellRendererText()

            # add the cell to the tvcolumn and allow it to expand
            column.pack_start(cell_renderer, True)

            # Get markup for column, not text
            column.set_attributes(cell_renderer, markup=index)

            # Allow sorting on the column
            column.set_sort_column_id(index)

        # make it searchable
        self.set_search_column(1)


class Calendar(gtk.Calendar):
    def __init__(self, week_numbers=False):
        gtk.Calendar.__init__(self)
        if week_numbers:
            self.set_property('show-week-numbers', True)

    def set_date(self, date):
        '''
        A date check makes no sense here since it is normal that a new month is
        set here that will contain the day
        '''
        # We need to set the day temporarily to a day that is present in all months
        self.select_day(1)

        # PyGTK calendars show months in range [0,11]
        self.select_month(date.month-1, date.year)

        # Select the day after the month and year have been set
        self.select_day(date.day)

    def get_date(self):
        year, month, day = gtk.Calendar.get_date(self)
        return datetime.date(year, month+1, day)


# ------------------------- Assistant Pages ------------------------------------

class AssistantPage(gtk.VBox):
    def __init__(self, *args, **kwargs):
        gtk.VBox.__init__(self, *args, **kwargs)

        self.set_spacing(5)
        self.set_border_width(10)

        self.header = None
        self.show_all()

    def _add_header(self):
        self.header = gtk.Label()
        self.header.set_markup('Unset')
        self.header.set_alignment(0.0, 0.5)
        self.pack_start(self.header, False, False)
        self.separator = gtk.HSeparator()
        self.pack_start(self.separator, False, False)
        self.reorder_child(self.header, 0)
        self.reorder_child(self.separator, 1)
        self.show_all()

    def set_header(self, text):
        if not self.header:
            self._add_header()
        self.header.set_markup(text)



class IntroductionPage(AssistantPage):
    def __init__(self, text, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)

        label = gtk.Label(text)

        self.pack_start(label)



class RadioButtonPage(AssistantPage):
    def __init__(self, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)

        self.buttons = []


    def add_radio_option(self, object, label, tooltip=''):
        sensitive = object.is_available()

        group = self.buttons[0] if self.buttons else None
        button = gtk.RadioButton(group=group)
        button.set_tooltip_markup(tooltip)
        button.set_label(label)
        button.object = object
        button.set_sensitive(sensitive)
        self.pack_start(button, False, False)
        self.buttons.append(button)

        if tooltip:
            description = gtk.Label()
            description.set_alignment(0.0, 0.5)
            description.set_markup(' '*5 + tooltip)
            description.set_sensitive(sensitive)
            self.pack_start(description, False, False)


    def get_selected_object(self):
        for button in self.buttons:
            if button.get_active():
                return button.object



class PathChooserPage(AssistantPage):
    def __init__(self, assistant, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)

        self.assistant = assistant

        self.last_path = None

        self.chooser = gtk.FileChooserWidget()
        self.chooser.connect('selection-changed', self.on_path_changed)

        self.pack_start(self.chooser)


    def _remove_filters(self):
        for filter in self.chooser.list_filters():
            self.chooser.remove_filter(filter)


    def prepare(self, porter):
        self._remove_filters()

        self.path_type = porter.PATHTYPE.upper()
        path = porter.DEFAULTPATH
        extension = porter.EXTENSION
        helptext = porter.PATHTEXT

        if helptext:
            self.set_header(helptext)

        if self.path_type == 'DIR':
            self.chooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        elif self.path_type == 'FILE':
            self.chooser.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        elif self.path_type == 'NEWFILE':
            self.chooser.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
        else:
            logging.error('Wrong path_type "%s"' % self.path_type)

        if self.path_type in ['FILE', 'NEWFILE'] and extension:
            filter = gtk.FileFilter()
            filter.set_name(extension)
            filter.add_pattern('*.' + extension)
            self.chooser.add_filter(filter)

        if self.last_path and os.path.exists(self.last_path):
            path = self.last_path

        if os.path.isdir(path):
            self.chooser.set_current_folder(path)
        else:
            dirname, basename = os.path.split(path)
            filename, old_ext = os.path.splitext(basename)
            self.chooser.set_current_folder(dirname)
            self.chooser.set_current_name(filename + '.' + extension)


    def get_selected_path(self):
        self.last_path = self.chooser.get_filename().decode('utf-8')
        return self.last_path


    def on_path_changed(self, widget):
        return



class Assistant(gtk.Assistant):
    def __init__(self, journal, *args, **kwargs):
        gtk.Assistant.__init__(self, *args, **kwargs)

        self.journal = journal

        self.set_size_request(1000, 500)

        self.connect('cancel', self._on_cancel)
        self.connect('close', self._on_close)
        self.connect('prepare', self._on_prepare)

    def run(self):
        '''
        Show assistant
        '''

    def _on_cancel(self, assistant):
        '''
        Cancelled -> Hide assistant
        '''
        self.hide()

    def _on_close(self, assistant):
        '''
        Do the action
        '''

    def _on_prepare(self, assistant, page):
        '''
        Called when a new page should be prepared, before it is shown
        '''

    def _add_intro_page(self, text):
        page = IntroductionPage(text)
        self.append_page(page)
        self.set_page_title(page, _('Introduction'))
        self.set_page_type(page, gtk.ASSISTANT_PAGE_INTRO)
        self.set_page_complete(page, True)
