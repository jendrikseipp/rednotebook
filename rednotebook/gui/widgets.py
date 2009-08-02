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
	def __init__(self, comboBox):
		self.comboBox = comboBox
		self.liststore = self.comboBox.get_model()
		#self.comboBox.set_wrap_width(5)
		self.entry = self.comboBox.get_child()
		
	def add_entry(self, entry):
		self.liststore.append([entry])
	
	def set_entries(self, value_list):
		self.clear()
		for entry in value_list:
			self.add_entry(entry)
		
		if len(value_list) > 0:
			self.comboBox.set_active(0)
	
	def _get_active_text(self):
		model = self.comboBox.get_model()
		index = self.comboBox.get_active()
		if index > -1:
			return model[index][0]
		else:
			return ''
		
	def get_active_text(self):
		return self.entry.get_text().decode('utf-8')
	
	def set_active_text(self, text):
		return self.entry.set_text(text)
	
	def clear(self):
		if self.liststore:
			self.liststore.clear()
		self.set_active_text('')
	
	def connect(self, *args, **kargs):
		self.comboBox.connect(*args, **kargs)
		
	def set_editable(self, editable):
		self.entry.set_editable(editable)
		

class CustomListView(gtk.TreeView):
	def __init__(self):
		gtk.TreeView.__init__(self)
		'create a TreeStore with two string columns to use as the model'
		self.set_model(gtk.ListStore(str, str))

		columns = [gtk.TreeViewColumn('1'), gtk.TreeViewColumn('2')]

		'add tvcolumns to treeView'
		for index, column in enumerate(columns):
			self.append_column(column)

			'create a CellRendererText to render the data'
			cellRenderer = gtk.CellRendererText()

			'add the cell to the tvcolumn and allow it to expand'
			column.pack_start(cellRenderer, True)

			'Get markup for column, not text'
			column.set_attributes(cellRenderer, markup=index)
			
			'Allow sorting on the column'
			column.set_sort_column_id(index)

		'make it searchable'
		self.set_search_column(1)
		