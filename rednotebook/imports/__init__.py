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

import sys
import os
import datetime

import gtk

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath("./../../"))

from rednotebook.redNotebook import Day, Month

class ImportDay(Day):
	'''
	text is set and retrieved with the property "text"
	'''
	def __init__(self, year, month, day):
		import_month = Month(year, month)
		Day.__init__(self, import_month, day)
		
		
class AssistantPage(gtk.VBox):
	def __init__(self, *args, **kwargs):
		gtk.VBox.__init__(self, *args, **kwargs)
		
		self.set_spacing(5)
		self.set_border_width(10)
		
		
class RadioButtonPage(AssistantPage):
	def __init__(self, *args, **kwargs):
		AssistantPage.__init__(self, *args, **kwargs)
		
		self.buttons = []
		
	def add_radio_option(self, label, tooltip, source):
		bold_label = label
		#bold_label = gtk.Label()
		#bold_label.set_markup('<b>%s</b>' % label)
		group = self.buttons[0] if self.buttons else None
		button = gtk.RadioButton(group=group)
		button.set_tooltip_markup(tooltip)
		button.set_label(bold_label)
		button.source = source
		description = gtk.Label()
		description.set_alignment(0.0, 0.5)
		description.set_markup(tooltip)
		#hbox = gtk.HBox()
		#hbox.set_border_width(10)
		#hbox.pack_start(description, False, False)
		self.pack_start(button, False, False)
		self.pack_start(description, False, False)
		self.buttons.append(button)
		
	def get_selected_source(self):
		for button in self.buttons:
			if button.get_active():
				return button.source
				
				
class PathChooserPage(AssistantPage):
	def __init__(self, *args, **kwargs):
		AssistantPage.__init__(self, *args, **kwargs)
		
		self.last_path = os.path.expanduser('~')
		
		self.chooser = gtk.FileChooserWidget()
		
		self.pack_start(self.chooser)
		
	def _remove_filters(self):
		for filter in self.chooser.list_filters():
			self.chooser.remove_filter()
			
		
	def prepare_chooser(self, path_type, extension=None):
		self._remove_filters()
		
		if path_type.upper() == 'DIR':
			self.chooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
		elif path_type.upper() == 'FILE':
			self.chooser.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
			if extension:
				filter = gtk.FileFilter()
				filter.set_name(extension)
				filter.add_pattern("*.extension")
				self.chooser.add_filter(filter)
		else:
			logging.error('Wrong path_type "%s"' % path_type)
			
		if self.last_path:
			self.chooser.set_filename(self.last_path)
		
	def get_selected_path(self):
		self.last_path = self.chooser.get_filename()
		return self.last_path
		

class SummaryPage(AssistantPage):
	def __init__(self, *args, **kwargs):
		AssistantPage.__init__(self, *args, **kwargs)
		self._add_header()
		
	def _add_header(self):
		header = gtk.Label()
		header.set_markup('<b>You have selected:</b>')
		header.set_alignment(0.0, 0.5)
		self.pack_start(header, False, False)
		self.pack_start(gtk.HSeparator(), False, False)
		self.show_all()
		
	def add_line(self, key, value):
		label = gtk.Label()
		text = '<b>%s</b>: %s' % (key, value)
		label.set_markup(text)
		label.set_alignment(0.0, 0.5)
		self.pack_start(label, False, False)
		label.show()
		
	def clear(self):
		for child in self.get_children():
			self.remove(child)
		self._add_header()
		
				
		
		
class ImportAssistant(gtk.Assistant):
	def __init__(self, *args, **kwargs):
		gtk.Assistant.__init__(self, *args, **kwargs)
		
		self.set_title('Import')
		self.set_size_request(1000, 700)
		
		self.page0 = self._get_page0()
		self.append_page(self.page0)
		self.set_page_title(self.page0, 'Welcome to the Import Assistant')
		self.set_page_type(self.page0, gtk.ASSISTANT_PAGE_INTRO)
		self.set_page_complete(self.page0, True)
		
		self.page1 = self._get_page1()
		self.append_page(self.page1)
		self.set_page_title(self.page1, 'Select Import Source')
		self.set_page_complete(self.page1, True)
		
		self.page2 = self._get_page2()
		self.append_page(self.page2)
		self.set_page_title(self.page2, 'Select Import Path')
		self.set_page_complete(self.page2, True)
		
		self.page3 = self._get_page3()
		self.append_page(self.page3)
		self.set_page_title(self.page3, 'Summary')
		self.set_page_type(self.page3, gtk.ASSISTANT_PAGE_CONFIRM)
		self.set_page_complete(self.page3, True)
		
		self.source = None
		self.path = None
		
		self.connect('cancel', self._on_cancel)
		self.connect('close', self._on_close)
		self.connect('prepare', self._on_prepare)
		#self.set_forward_page_func(self._on_page_change, None)
		
	#def _on_page_change(self, current_page, user_data):
	#	print current_page
	#	
	#	if current_page == 1:
	#		self.source = self.page1.get_selected_source()
	#		print 'SOURCE', self.source
	#		
	#		self.page2.prepare_chooser('DIR')
	#	elif current_page == 2:
	#		self.path = self.page2.get_selected_path()
	#		print self.path
	#		self.page3.add_line('Import type', self.source)
	#		self.page3.add_line('Import path', self.path)
	#	return current_page + 1
		
	def _on_cancel(self, assistant):
		'''
		Cancelled -> Hide assistant
		'''
		self.hide()
		
	def _on_close(self, assistant):
		'''
		Do the import
		'''
		self.hide()
		print 'CLOSE', self.source, self.path
		#days = self.source.get_days()
		#self.redNotebook.merge_days(days)
		
	def _on_prepare(self, assistant, page):
		#print page
		if page == self.page2:
			self.source = self.page1.get_selected_source()
			#print 'SOURCE', self.source	
			self.page2.prepare_chooser('DIR')
		elif page == self.page3:
			#print 'Aha'
			self.path = self.page2.get_selected_path()
			#print self.path
			self.page3.clear()
			self.page3.add_line('Import type', self.source)
			self.page3.add_line('Import path', self.path)
		
			
	def _get_page0(self):
		page = AssistantPage()
		label = gtk.Label()
		text = 'This Assistant will help you to import your notes \nfrom '\
				'other applications.'
		label.set_markup(text)
		page.pack_start(label, True, True)
		return page
		
		
	def _get_page1(self):
		page = RadioButtonPage()
		page.add_radio_option('Plain Text', 'Aha', 'plaintext')
		page.add_radio_option('Text', 'Uhu', 'tomboy')
		return page
		
	def _get_page2(self):
		page = PathChooserPage()
		return page
		
	def _get_page3(self):
		page = SummaryPage()
		return page
		
		
	def get_days(self):
		pass
		
		
	def _get_path(self):
		pass
		
	def _get_file(self):
		pass
		
		
		
if __name__ == '__main__':
	'''
	Run some tests
	'''
	
	assistant = ImportAssistant()
	assistant.set_position(gtk.WIN_POS_CENTER)
	assistant.show_all()
	gtk.main()
	
	a = ImportDay(2010,5,7)
	a.text = 'a_text'
	a.add_category_entry('c1', 'e1')
	a.add_category_entry('c2', 'e2')
	a.add_category_entry('c4', 'e5')

	print a.content
	
	b = ImportDay(2010,5,7)
	b.text = 'b_text'
	b.add_category_entry('c1', 'e1')
	b.add_category_entry('c2', 'e3')
	b.add_category_entry('c3', 'e4')
	
	a.merge(b)
	
	assert a.text == 'a_text\n\nb_text'
	assert a.tree == {'c1': {'e1': None}, 'c2': {'e2': None, 'e3':None}, \
			'c4': {'e5': None}, 'c3': {'e4': None},}, a.tree
			
	print 'ALL TESTS SUCCEEDED'
	

#plaintext_module = __import__('plaintext')
#print dir(plaintext_module)
#p = getattr(plaintext_module, 'aha')
#p = plaintext_module.PlainTextImporter()


	

		
	
