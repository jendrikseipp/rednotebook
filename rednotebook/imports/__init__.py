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
import logging
import re

import gtk
import gobject

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath("./../../"))

from rednotebook.redNotebook import Day, Month
#from rednotebook.imports.plaintext import PlainTextImporter
from rednotebook.util import filesystem

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
		
		self.header = None
		
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
		
		
class RadioButtonPage(AssistantPage):
	def __init__(self, *args, **kwargs):
		AssistantPage.__init__(self, *args, **kwargs)
		
		self.buttons = []
		
	def add_radio_option(self, label, tooltip, importer):
		bold_label = label
		#bold_label = gtk.Label()
		#bold_label.set_markup('<b>%s</b>' % label)
		group = self.buttons[0] if self.buttons else None
		button = gtk.RadioButton(group=group)
		button.set_tooltip_markup(tooltip)
		button.set_label(bold_label)
		button.importer = importer
		description = gtk.Label()
		description.set_alignment(0.0, 0.5)
		description.set_markup(tooltip)
		#hbox = gtk.HBox()
		#hbox.set_border_width(10)
		#hbox.pack_start(description, False, False)
		self.pack_start(button, False, False)
		self.pack_start(description, False, False)
		self.buttons.append(button)
		
	def get_selected_importer(self):
		for button in self.buttons:
			if button.get_active():
				return button.importer
				
				
class PathChooserPage(AssistantPage):
	def __init__(self, *args, **kwargs):
		AssistantPage.__init__(self, *args, **kwargs)
		
		self.last_path = os.path.expanduser('~')
		
		self.chooser = gtk.FileChooserWidget()
		
		self.pack_start(self.chooser)
		
	def _remove_filters(self):
		for filter in self.chooser.list_filters():
			self.chooser.remove_filter()
			
		
	def prepare(self, importer):
		self._remove_filters()
		
		path_type = importer.PATHTYPE
		path = importer.DEFAULTPATH
		extension = importer.EXTENSION
		helptext = importer.PATHTEXT
		
		if helptext:
			self.set_header(helptext)
		
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
			
		path = path or self.last_path
			
		if os.path.isdir(path):
			self.chooser.set_current_folder(path)
		else:
			self.chooser.set_filename(path)
		
	def get_selected_path(self):
		self.last_path = self.chooser.get_filename()
		return self.last_path
		

class SummaryPage(AssistantPage):
	def __init__(self, *args, **kwargs):
		AssistantPage.__init__(self, *args, **kwargs)
		
		scrolled_window = gtk.ScrolledWindow()
		self.board = gtk.TextView()
		self.board.set_editable(False)
		self.board.set_cursor_visible(False)
		self.board.set_wrap_mode(gtk.WRAP_WORD)
		scrolled_window.add(self.board)
		self.pack_start(scrolled_window)
		
		
	def prepare(self, type, path):
		text = 'You have selected to import <b>%s</b> from <b>%s</b>\n\n' \
				'The following contents will be imported:' % (type, path)
		self.set_header(text)
		self.clear()
		
	def add_day(self, day):
		day_text = '=== %s ===\n%s\n\n' % (day.date, day.text)
		self._append(day_text)
		# Wait for the text to be drawn
		while gtk.events_pending():
			gtk.main_iteration()
		
	def clear(self):
		self.board.get_buffer().set_text('')
		
	def _append(self, text):
		buffer = self.board.get_buffer()
		end_iter = buffer.get_end_iter()
		buffer.insert(end_iter, text)
		
				
		
		
class ImportAssistant(gtk.Assistant):
	def __init__(self, redNotebook, *args, **kwargs):
		gtk.Assistant.__init__(self, *args, **kwargs)
		
		self.redNotebook = redNotebook
		
		self.importers = get_importers()
		
		self.set_title('Import')
		self.set_size_request(1000, 700)
		
		self.page0 = self._get_page0()
		self.append_page(self.page0)
		self.set_page_title(self.page0, 'Welcome to the Import Assistant')
		self.set_page_type(self.page0, gtk.ASSISTANT_PAGE_INTRO)
		self.set_page_complete(self.page0, True)
		
		self.page1 = self._get_page1()
		self.append_page(self.page1)
		self.set_page_title(self.page1, 'Select what to import')
		self.set_page_complete(self.page1, True)
		
		self.page2 = self._get_page2()
		self.append_page(self.page2)
		self.set_page_title(self.page2, 'Select Import Path')
		
		self.page3 = self._get_page3()
		self.append_page(self.page3)
		self.set_page_title(self.page3, 'Summary')
		self.set_page_type(self.page3, gtk.ASSISTANT_PAGE_CONFIRM)
		
		self.importer = None
		self.path = None
		self.days = []
		
		self.connect('cancel', self._on_cancel)
		self.connect('close', self._on_close)
		self.connect('prepare', self._on_prepare)
	
	def run(self):
		self.show_all()
		
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
		self.redNotebook.merge_days(self.days)
		
	def _on_prepare(self, assistant, page):
		'''
		Called when a new page should be prepared, before it is shown
		'''
		#print 'preparing page', assistant.get_current_page()
		if page == self.page2:
			self.importer = self.page1.get_selected_importer()
			self.page2.prepare(self.importer)
			self.set_page_complete(self.page2, True)
		elif page == self.page3:
			self.path = self.page2.get_selected_path()
			self.set_page_complete(self.page3, False)
			self.page3.prepare(self.importer.NAME, self.path)
			
			# We want the page to be shown first and the days added then
			gobject.idle_add(self.add_days)
			
			
	def add_days(self):
		self.days = []
		for day in self.importer.get_days(self.path):
			#self.days.sort(key=lambda day: day.date)
			self.page3.add_day(day)
			self.days.append(day)
		self.set_page_complete(self.page3, True)
		
			
	def _get_page0(self):
		page = AssistantPage()
		label = gtk.Label()
		text = 'This Assistant will help you to import your notes from ' \
				'other applications.\nYou can check the results on the ' \
				'last page before any change is made to your journal.'
		label.set_markup(text)
		page.pack_start(label, True, True)
		return page
		
		
	def _get_page1(self):
		page = RadioButtonPage()
		for importer in self.importers:
			name = importer.NAME
			desc = importer.DESCRIPTION
			page.add_radio_option(name, desc, importer)
		return page
		
	def _get_page2(self):
		page = PathChooserPage()
		return page
		
	def _get_page3(self):
		page = SummaryPage()
		return page
		
		
		
class Importer(object):
	NAME = 'What do we import?'
	DESCRIPTION = 'Short description of what we import'
	REQUIREMENTS = [] #TODO
	PATHTEXT = 'Select the directory containing the sources to import'
	DEFAULTPATH = os.path.expanduser('~') #TODO
	PATHTYPE = 'DIR'
	EXTENSION = None
		


# Allow 2010-05-08[.txt] with different separators
sep = r'[:\._\-]?' # The separators :._-
date_exp = re.compile(r'(\d{4})%s(\d{2})%s(\d{2})(?:\.txt)?' % (sep, sep))
ref_date = datetime.date(2010, 5, 8)
for test in ['2010-05-08', '2010.05-08', '2010:05_08.TxT', '20100508.TXT']:
	match = date_exp.match(test)
	date = datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
	assert date == ref_date

		
class PlainTextImporter(Importer):
	NAME = 'Plain Text'
	DESCRIPTION = 'Import Text from plain textfiles'
	REQUIREMENTS = []
	PATHTEXT = 'Select a directory containing your data files'
	PATHTYPE = 'DIR'
	
	def get_days(self, dir):
		assert os.path.isdir(dir)
		files = os.listdir(dir)
		files.sort()
		days = []
		for file in files:
			match = date_exp.match(file)
			if match:
				year = int(match.group(1))
				month = int(match.group(2))
				day = int(match.group(3))
				
				import_day = ImportDay(year, month, day)
				
				path = os.path.join(dir, file)
				text = filesystem.read_file(path)
				import_day.text = text
				yield import_day
				#days.append(import_day)
				
		#return days
		
		
class TomboyImporter(Importer):
	NAME = 'Tomboy Notes'
	DESCRIPTION = 'Import your Tomboy notes'
	REQUIREMENTS = ['xml.etree']
	PATHTEXT = 'Select the directory containing your tomboy notes'
	DEFAULTPATH = os.getenv('XDG_DATA_HOME') or \
		os.path.join(os.path.expanduser('~'), '.local', 'share', 'tomboy')
	if sys.platform == 'win32':
		DEFAULTPATH = os.path.join(os.getenv('%APPDATA%'), 'Tomboy', 'notes')
	elif sys.platform == 'darwin':
		DEFAULTPATH = os.path.join(os.path.expanduser('~'), \
							'Library', 'Application Support', 'Tomboy')
	PATHTYPE = 'DIR'
	
	def get_days():
		day = ImportDay(2010, 5, 7)
		day.text = 'test text'
		day.add_category_entry('cat', 'dog')
		return [day]
		
		
def get_importers():
	importers = [cls for name, cls in globals().items() \
				if name.endswith('Importer') and not name == 'Importer']
	print importers
	
	supported_importers = importers[:]
	for importer in importers:
		for req in importer.REQUIREMENTS:
			print req
			try:
				__import__(req)
			except ImportError, err:
				print '%s could not be imported' % req
				# Importer cannot be used
				supported_importers.remove(importer)
				break
			
	print supported_importers
	supported_importers = [importer() for importer in supported_importers]
	
	return supported_importers
	#importers = map() 
		
		
		
if __name__ == '__main__':
	'''
	Run some tests
	'''
	
	assistant = ImportAssistant(None)
	assistant.set_position(gtk.WIN_POS_CENTER)
	assistant.run()
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
	a_tree = a.content.copy()
	
	a.merge(b)
	assert a_tree == a.content
	
	assert a.text == 'a_text\n\nb_text'
	assert a.tree == {'c1': {'e1': None}, 'c2': {'e2': None, 'e3':None}, \
			'c4': {'e5': None}, 'c3': {'e4': None},}, a.tree
			
	print 'ALL TESTS SUCCEEDED'
	

#plaintext_module = __import__('plaintext')
#print dir(plaintext_module)
#p = getattr(plaintext_module, 'aha')
#p = plaintext_module.PlainTextImporter()





	

		
	
