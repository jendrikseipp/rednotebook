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

from widgets import UrlButton, CustomComboBox

class Option(object):
	pass


class TickOption(Option):
	def __init__(self, text, name):
		self.text = text
		self.name = name
		self.widget = gtk.CheckButton(self.text)
		if Option.config.read(name, 0):
			self.widget.set_active(True)
		
	def get_value(self):
		return self.widget.get_active()
		
	def get_string_value(self):
		value = str(int(self.get_value()))
		return value
	
	
class TextOption(Option):
	def __init__(self, text, name):
		self.text = text
		self.name = name
		
		self.widget = gtk.HBox()
		self.widget.set_spacing(5)
		
		self.entry = gtk.Entry(20)
		self.entry.set_text(Option.config.read(name, ''))
		self.label = gtk.Label(self.text)
		self.widget.pack_start(self.label, False, False)
		self.widget.pack_start(self.entry, False, False)
		
	def get_value(self):
		return self.entry.get_text()
		
	def get_string_value(self):
		return str(self.get_value()).strip()
	
	
class TextAndButtonOption(TextOption):
	def __init__(self, text, name, button):
		TextOption.__init__(self, text, name)
		
		self.widget.pack_end(button, False, False)
		
		
class ComboBoxAndButtonOption(TextAndButtonOption):
	def __init__(self, text, name, entries, button):
		TextAndButtonOption.__init__(self, text, name, button)
		
		self.combo = CustomComboBox(gtk.ComboBoxEntry(gtk.ListStore(gobject.TYPE_STRING)))
		self.combo.set_entries(entries)
		self.combo.set_active_text(Option.config.read(name, ''))
		self.widget.remove(self.entry)
		self.widget.pack_start(self.combo.comboBox, False, False)
		
	def get_value(self):
		return self.combo.get_active_text()
	
class DateFormatOption(ComboBoxAndButtonOption):
	def __init__(self, text, name, button):
		date_formats = ['%A, %x %X', '%A, %x, Day %j', '%H:%M', 'Week %W of Year %Y', \
						'%y-%m-%d', 'Day %j', '%A', '%B']
		ComboBoxAndButtonOption.__init__(self, text, name, date_formats, button)
		
		self.preview = gtk.Label()
		self.widget.pack_start(self.preview, False, False)
		
		self.combo.connect('changed', self.on_format_changed)
		
		# Update the preview
		self.on_format_changed(None)
		
	def on_format_changed(self, widget):
		import time
		self.preview.set_text('Result: %s' % time.strftime(self.combo.get_active_text()))
	

class OptionsDialog(object):
	def __init__(self, dialog):
		self.dialog = dialog
		self.categories = {}
		
	def __getattr__(self, attr):
		'''Wrap the dialog'''
		return getattr(self.dialog, attr)
	
	def add_option(self, category, option):
		self.categories[category].pack_start(option.widget, False)
		option.widget.show_all()
		
	def add_category(self, name, vbox):
		self.categories[name] = vbox
		
	def clear(self):
		for category, vbox in self.categories.items():
			for option in vbox.get_children():
				vbox.remove(option)
		

class OptionsManager(object):
	def __init__(self, main_window):
		self.xml = main_window.wTree
		self.redNotebook = main_window.redNotebook
		self.config = self.redNotebook.config
		
		self.dialog = OptionsDialog(self.xml.get_widget('options_dialog'))
		self.dialog.add_category('general', self.xml.get_widget('general_vbox'))
		
	def on_options_dialog(self):
		self.dialog.clear()
		
		date_url = 'http://docs.python.org/library/time.html#time.strftime'
		date_format_help_button = UrlButton('Help', date_url)
		
		# Make the config globally available
		Option.config = self.config
		self.options = [
				TickOption('Check for new versions at startup', 'checkForNewVersion'),
				DateFormatOption('Date/Time format', 'dateTimeString', \
									date_format_help_button)
				]
		
		self.add_all_options()
		
		response = self.dialog.run()
		
		if response == gtk.RESPONSE_OK:
			self.save_options()
			
		self.dialog.hide()
		
	def add_all_options(self):
		for option in self.options:
			self.dialog.add_option('general', option)
			
	def save_options(self):
		logging.debug('Saving Options')
		for option in self.options:
			value = option.get_string_value()
			logging.debug('Setting %s = %s' % (option.name, value))
			self.config[option.name] = value