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

import gtk

from rednotebook.gui.customwidgets import CustomComboBoxEntry
from rednotebook.util import markup
from rednotebook.util import dates


class SearchComboBox(CustomComboBoxEntry):
    def __init__(self, combo_box, main_window):
        CustomComboBoxEntry.__init__(self, combo_box)

        self.main_window = main_window
        self.journal = main_window.journal

        self.set_active_text(_('Search ...'))

        self.entry.connect('changed', self.on_entry_changed)
        self.entry.connect('activate', self.on_entry_activated)

        self.recent_searches = []
        self.search_type = 0

    def set_search_type(self, search_type):
        self.main_window.search_tree_view.set_search_type(search_type)

        if search_type == 0:
            # Search for text
            self.set_entries(self.recent_searches)
        if search_type == 1:
            # Search for category
            categories = self.main_window.categories_tree_view.categories
            self.set_entries(categories)
        if search_type == 2:
            # Search for tags
            self.set_entries(self.journal.tags)

        self.search_type = search_type

    def on_entry_changed(self, entry):
        """Called when the entry changes."""
        self.search(self.get_active_text())

    def on_entry_activated(self, entry):
        """Called when the user hits enter."""
        search_text = entry.get_text()

        if self.search_type == 0:
            # Search for text
            self.recent_searches.append(search_text)
            self.recent_searches = self.recent_searches[-20:]
            self.add_entry(search_text)

        self.search(self.get_active_text())

    def search(self, search_text):
        if self.search_type == 0:
            # Tell the webview which text to highlight after the html is loaded
            self.main_window.html_editor.search_text = search_text

            # Highlight all occurences in the current day's text
            self.main_window.highlight_text(search_text)

        self.main_window.search_tree_view.update_data(search_text)


class SearchTreeView(object):
    def __init__(self, tree_view, main_window):
        self.tree_view = tree_view
        self.main_window = main_window
        self.journal = self.main_window.journal
        self.search_type = 0

        # Normally unneeded, but just to be sure everything works fine
        self.searched_text = ''

        # create a TreeStore with two string columns to use as the model
        self.tree_store = gtk.ListStore(str, str)

        # create the TreeView using tree_store
        self.tree_view.set_model(self.tree_store)

        # create the TreeViewColumns to display the data
        self.date_column = gtk.TreeViewColumn(_('Date'))
        self.matching_column = gtk.TreeViewColumn(_('Text'))

        columns = [self.date_column,self.matching_column, ]
                        #self.category_column, self.entry_column]

        # add tvcolumns to tree_view
        for index, column in enumerate(columns):
            self.tree_view.append_column(column)

            # create a CellRendererText to render the data
            cell_renderer = gtk.CellRendererText()

            # add the cell to the tvcolumn and allow it to expand
            column.pack_start(cell_renderer, True)

            # Get markup for column, not text
            column.set_attributes(cell_renderer, markup=index)

            # Allow sorting on the column
            column.set_sort_column_id(index)

        self.update_data()

        # make it searchable
        self.tree_view.set_search_column(1)

        #self.tree_view.connect('row_activated', self.on_row_activated)
        self.tree_view.connect('cursor_changed', self.on_cursor_changed)

    def update_data(self, search_text=''):
        self.tree_store.clear()
        rows = None

        if not search_text:
            return

        # Save the search text for highlighting
        self.searched_text = search_text

        if self.search_type == 0:
            # Search for text
            self.matching_column.set_title(_('Text'))
            rows = self.journal.search(text=search_text)
        if self.search_type == 1:
            # Search for category
            self.matching_column.set_title(_('Entry'))
            rows = self.journal.search(category=search_text)
        if self.search_type == 2:
            # Search for tags
            self.matching_column.set_title(_('Text'))
            rows = self.journal.search(tag=search_text)

        if rows:
            for date_string, entry in rows:
                if self.search_type == 1:
                    # We want **done** to be bold in the list,
                    # but the text should only be bold where the search text occurs
                    entry = markup.convert_to_pango(entry)
                else:
                    entry = escape(entry)
                    entry = entry.replace('STARTBOLD', '<b>').replace('ENDBOLD', '</b>')
                self.tree_store.append([date_string, entry])

    def on_cursor_changed(self, treeview):
        """Move to the selected day when user clicks on it"""
        selection = self.tree_view.get_selection()
        model, paths = selection.get_selected_rows()
        if not paths:
            return
        date_string = self.tree_store[paths[0]][0]
        new_date = dates.get_date_from_date_string(date_string)
        self.journal.change_date(new_date)

        if self.search_type == 0:
            self.main_window.highlight_text(self.searched_text)

    def set_search_type(self, search_type):
        self.search_type = search_type
