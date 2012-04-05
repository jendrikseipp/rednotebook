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

from xml.sax.saxutils import escape

import gobject
import gtk

from rednotebook.gui.customwidgets import CustomComboBoxEntry, CustomListView
from rednotebook.util import dates


class SearchComboBox(CustomComboBoxEntry):
    def __init__(self, combo_box, main_window):
        CustomComboBoxEntry.__init__(self, combo_box)

        self.main_window = main_window
        self.journal = main_window.journal

        self.entry.set_icon_from_stock(1, gtk.STOCK_CLEAR)
        self.entry.connect('icon-press', lambda *args: self.set_active_text(''))

        self.entry.connect('changed', self.on_entry_changed)
        self.entry.connect('activate', self.on_entry_activated)

    def on_entry_changed(self, entry):
        """Called when the entry changes."""
        self.search(self.get_active_text())

    def on_entry_activated(self, entry):
        """Called when the user hits enter."""
        search_text = entry.get_text()
        self.add_entry(search_text)
        self.search(search_text)

    def search(self, search_text):
        tags = []
        queries = []
        for part in search_text.split():
            if part.startswith(u'#'):
                tags.append(part.lstrip(u'#').lower())
            else:
                queries.append(part)

        search_text = ' '.join(queries)

        # Highlight all occurences in the current day's text
        self.main_window.highlight_text(search_text)

        # Scroll to query.
        if search_text:
            gobject.idle_add(self.main_window.day_text_field.scroll_to_text,
                             search_text)

        self.main_window.search_tree_view.update_data(search_text, tags)


class SearchTreeView(CustomListView):
    def __init__(self, main_window):
        CustomListView.__init__(self, [(_('Date'), str), (_('Text'), str)])
        self.main_window = main_window
        self.journal = self.main_window.journal
        self.tree_store = self.get_model()

        self.connect('cursor_changed', self.on_cursor_changed)

    def update_data(self, search_text, tags):
        self.tree_store.clear()

        if not tags and not search_text:
            self.main_window.cloud.show()
            self.parent.hide()
            return
        self.main_window.cloud.hide()
        self.parent.show()

        for date_string, entries in self.journal.search(search_text, tags):
            for entry in entries:
                entry = escape(entry)
                entry = entry.replace('STARTBOLD', '<b>').replace('ENDBOLD', '</b>')
                self.tree_store.append([date_string, entry])

    def on_cursor_changed(self, treeview):
        """Move to the selected day when user clicks on it"""
        model, paths = self.get_selection().get_selected_rows()
        if not paths:
            return
        date_string = self.tree_store[paths[0]][0]
        new_date = dates.get_date_from_date_string(date_string)
        self.journal.change_date(new_date)
