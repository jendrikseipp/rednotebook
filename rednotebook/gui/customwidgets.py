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
        
        #self.liststore = self.combo_box.get_model()
        #if self.liststore is None:
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
        for entry in value_list:
            self.add_entry(entry)
        
        if len(value_list) > 0:
            self.combo_box.set_active(0)
            self.set_active_text(value_list[0])
            self.combo_box.queue_draw()
    
    def get_active_text(self):
        return self.entry.get_text().decode('utf-8')
    
    def set_active_text(self, text):
        return self.entry.set_text(text)
    
    def clear(self):
        if self.liststore:
            self.liststore.clear()
        self.set_active_text('')
    
    def connect(self, *args, **kargs):
        self.combo_box.connect(*args, **kargs)
        
    def set_editable(self, editable):
        self.entry.set_editable(editable)
        

class CustomListView(gtk.TreeView):
    def __init__(self):
        gtk.TreeView.__init__(self)
        # create a TreeStore with two string columns to use as the model
        self.set_model(gtk.ListStore(str, str))

        columns = [gtk.TreeViewColumn('1'), gtk.TreeViewColumn('2')]

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
        

class EntryDialog(gtk.MessageDialog):
    # base this on a message dialog
    def __init__(self, title, value_name, subtitle=''):
        gtk.MessageDialog.__init__(self, None,
                                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                gtk.MESSAGE_QUESTION,
                                gtk.BUTTONS_OK,
                                None)
        self.set_markup(title)
        
        # create the text input field
        self.entry = gtk.Entry()
        
        # allow the user to press enter to do ok
        def response_to_dialog(entry, response):
            self.response(response)
        self.entry.connect("activate", response_to_dialog, gtk.RESPONSE_OK)
        
        # create a horizontal box to pack the entry and a label
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(value_name), False, 5, 5)
        hbox.pack_end(self.entry)
        
        if subtitle:
            # some secondary text
            self.format_secondary_markup(subtitle)
        
        # add it and show it
        self.vbox.pack_end(hbox, True, True, 0)
        self.show_all()
        
    def get_value(self):
        return self.entry.get_text()
    
    
class RedNotebookTrayIcon(gtk.StatusIcon):
    def __init__(self):
        gtk.StatusIcon.__init__(self)
        
                
class NewVersionDialog(gtk.MessageDialog):
    def __init__(self):
        gtk.MessageDialog.__init__(parent=None, flags=gtk.DIALOG_MODAL, \
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_YES_NO, message_format=None)
