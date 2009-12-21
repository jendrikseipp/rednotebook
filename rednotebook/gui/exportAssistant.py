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

import gtk
import gobject
import datetime
import os
import codecs
import operator
import logging

from rednotebook.util import markup
from rednotebook.gui import browser

class ExportAssistant(object):
	
	_instance = None
	
	@staticmethod
	def get_instance(main_window):
		if ExportAssistant._instance is None :
			ExportAssistant._instance = ExportAssistant(main_window)
		return ExportAssistant._instance
	
	
	def __init__(self, main_window):
				
		self.redNotebook = main_window.redNotebook
		self.main_window = main_window
		self.builder = main_window.builder
		
		self.format_extension_map = {'Text': 'txt', 'HTML': 'xhtml', \
									'Latex': 'tex', 'PDF' : 'pdf'}
		
		self.assistant = self.builder.get_object('export_assistant')
		
		self.append_introduction_page()
		self.append_first_page()
		self.append_second_page()
		self.append_third_page()
		self.append_fourth_page()
		
		self.assistant.set_forward_page_func(self.prepare_next_page, None)
		self.assistant.set_title(_('Export Assistant'))		
	
	def run(self):
		self.refresh_categories_list()
		self.assistant.show()

	def append_introduction_page(self):
		page0 = self.builder.get_object('export_assistant_0')
		page0.show()		
		self.assistant.set_page_complete(page0, True)
	
	def append_first_page(self):
		page1 = self.builder.get_object('export_assistant_1')
		page1.show()

		self.assistant.set_page_complete(page1, True)

		self.text_button = self.builder.get_object('text')
		self.html_button = self.builder.get_object('html')
		self.latex_button = self.builder.get_object('latex')
		self.pdf_button = self.builder.get_object('pdf')
		
		pdf_supported = self.is_pdf_supported()
		self.pdf_button.set_sensitive(pdf_supported)
		
		if not pdf_supported:
			tip1 = _('For direct PDF export, please install pywebkitgtk version 1.1.5 or later.')
			tip2 = _('Alternatively consult the help document for Latex to PDF conversion.')
			self.pdf_button.set_tooltip_text('%s\n%s' % (tip1, tip2))
		

	def append_second_page(self):	
		page2 = self.builder.get_object('export_assistant_2')
		page2.show()
		
		self.assistant.set_page_complete(page2, True)
		
		self.all_entries_button = self.builder.get_object('all_entries')
		self.selected_range_button = self.builder.get_object('selected_range')
		self.start_date = self.builder.get_object('start_date')
		self.end_date = self.builder.get_object('end_date')
		
		# The dates are set externally
		
		self.change_date_selector_status(self.assistant)
		
	def _set_date(self, calendar, date):
		# Avoid errors by setting the day to one that exists in every month first
		calendar.select_day(1)
		
		calendar.select_month(date.month - 1, date.year)
		calendar.select_day(date.day)
		
	def set_start_date(self, date):
		self._set_date(self.start_date, date)
		
	def set_end_date(self, date):
		self._set_date(self.end_date, date)
	
	def append_third_page(self):				
		page3 = self.builder.get_object('export_assistant_3')
		page3.show()
		
		self.assistant.set_page_complete(page3, True)

		self.nothing_exported_warning = self.builder.get_object('nothing_exported_warning')

		self.export_text = self.builder.get_object('export_text')
		
		self.no_categories = self.builder.get_object('no_categories')
		self.all_categories = self.builder.get_object('all_categories')
		self.selected_categories_radio = self.builder.get_object('selected_categories_radio')
		self.hbox_categories = self.builder.get_object('hbox_categories')
		
		
		self.available_categories = self.builder.get_object('available_categories')
		
		column = gtk.TreeViewColumn(_('Available Categories'))
		self.available_categories.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, True)
		column.add_attribute(cell, 'text', 0)
				
		self.selected_categories = self.builder.get_object('selected_categories')
		
		column = gtk.TreeViewColumn(_('Selected Categories'))
		self.selected_categories.append_column(column)
		cell = gtk.CellRendererText()
		column.pack_start(cell, True)
		column.add_attribute(cell, 'text', 0)
		
		self.change_categories_selector_status(self.assistant)   


	def append_fourth_page(self):
		page4 = self.builder.get_object('export_assistant_4')
		page4.show()
		
		self.assistant.set_page_complete(page4, True)

		self.filename_chooser = self.builder.get_object('filename_chooser')
		
	
	def prepare_next_page(self, current_page, data):
		if current_page == 1 :
			proposedFileName = 'RedNotebook-Export_' + str(datetime.date.today()) + \
								'.' + self.format_extension_map.get(self.get_selected_format())

			home = os.getenv('USERPROFILE') or os.getenv('HOME')
			self.filename_chooser.set_current_folder(home)
			self.filename_chooser.set_current_name(proposedFileName)
		return current_page + 1
	
	
	def on_quit(self, widget):
		self.filename = self.filename_chooser.get_filename()
		self.selected_categories_values = self.get_selected_categories_values()
		
		self.assistant.hide()
		self.export()
	
	def on_cancel(self, widget, other=None):
		self.redNotebook.showMessage(_('Cancelling export assistant.'))
		self.assistant.hide()

	def change_date_selector_status(self, widget):
		if (self.is_all_entries_selected()):
			self.start_date.set_sensitive(False)
			self.end_date.set_sensitive(False)
		else :
			self.start_date.set_sensitive(True)
			self.end_date.set_sensitive(True)

	def change_export_text_status(self, widget):
		if self.is_export_text_selected():
			self.no_categories.set_sensitive(True)
		else :
			if self.is_no_categories_selected():
				self.all_categories.set_active(True)
			self.no_categories.set_sensitive(False)
		self.check_exported_content_is_valid()



	def change_categories_selector_status(self, widget):
		if (self.is_all_categories_selected() or self.is_no_categories_selected()):
			self.hbox_categories.set_sensitive(False)
		else :
			self.hbox_categories.set_sensitive(True)
		self.check_exported_content_is_valid()
	
	def select_category(self, widget):
		selection = self.available_categories.get_selection()
		nb_selected, selected_iter = selection.get_selected()
		
		if selected_iter != None :		
			model_available = self.available_categories.get_model()
			model_selected = self.selected_categories.get_model()
			
			row = model_available[selected_iter]
			
			newRow = model_selected.insert(0)
			model_selected.set(newRow, 0, row[0])
			
			model_available.remove(selected_iter)
		self.check_exported_content_is_valid()

	def unselect_category(self, widget):
		selection = self.selected_categories.get_selection()
		nb_selected, selected_iter = selection.get_selected()
		
		if selected_iter != None :
			model_available = self.available_categories.get_model()
			model_selected = self.selected_categories.get_model()
			
			row = model_selected[selected_iter]
			
			newRow = model_available.insert(0)
			model_available.set(newRow, 0, row[0])
			
			model_selected.remove(selected_iter)
		
		self.check_exported_content_is_valid()

	def check_exported_content_is_valid(self):
		current_page = self.assistant.get_nth_page(3) 
		
		if not self.is_export_text_selected() \
		   and len(self.get_selected_categories_values()) == 0 :
			self.nothing_exported_warning.show()
			self.assistant.set_page_complete(current_page, False)
		else :
			self.nothing_exported_warning.hide()
			self.assistant.set_page_complete(current_page, True)
			
	
	def get_start_date(self):
		year, month, day = self.start_date.get_date()
		return datetime.date(year, month + 1, day)

	def get_end_date(self):
		year, month, day = self.end_date.get_date()
		return datetime.date(year, month + 1, day)
	
	def get_selected_format(self):
		if self.latex_button.get_active():
			return "Latex"
		if self.html_button.get_active():
			return "HTML"
		if self.pdf_button.get_active():
			return "PDF"
		return "Text"
	
	def get_selected_categories_values(self):
		selected_categories = []
		
		if self.is_all_categories_selected():
			selected_categories = self.main_window.redNotebook.nodeNames
		elif not self.is_no_categories_selected():
			model_selected = self.selected_categories.get_model()
			
			for row in model_selected :
				selected_categories.append(row[0])
		
		return selected_categories
	
	def is_export_text_selected(self):
		if self.export_text.get_active():
			return True
		return False
		
	def is_all_entries_selected(self):
		if self.all_entries_button.get_active():
			return True
		return False

	def is_all_categories_selected(self):
		if self.all_categories.get_active():
			return True
		return False

	def is_no_categories_selected(self):
		if self.no_categories.get_active():
			return True
		return False
	
	def refresh_categories_list(self):
		model_available = gtk.ListStore(gobject.TYPE_STRING)
		categories = self.main_window.redNotebook.nodeNames
		for category in categories :
			newRow = model_available.insert(0)
			model_available.set(newRow, 0, category)

		self.available_categories.set_model(model_available)
		model_selected = gtk.ListStore(gobject.TYPE_STRING)
		self.selected_categories.set_model(model_selected)

	
	
	def is_pdf_supported(self):
		return browser.can_print_pdf()
	
	def export(self):
		# Check sanity of dates
		#if not self.is_all_entries_selected():
		#	if not self.get_start_date() <= self.get_end_date():
		#		self.redNotebook.showMessage(_('The start date is later than the end date'), \
		#										error=True)
		#		return
		
		#TODO: Add content page values management
		format = self.get_selected_format()
		
		if format == 'PDF':
			self.export_pdf()
			return
		
		export_string = self.get_export_string(format)
		
		try:
			export_file = codecs.open(self.filename, 'w', 'utf-8')
			export_file.write(export_string)
			export_file.flush()
			self.redNotebook.showMessage(_('Content exported to %s') % self.filename)
		except IOError:
			self.redNotebook.showMessage(_('Exporting to %s failed') % self.filename)
			
	def export_pdf(self):
		logging.info('Exporting to PDF')
		html = self.get_export_string('HTML')
		browser.print_pdf(html, self.filename)

	def get_export_string(self, format):
		if self.is_all_entries_selected():
			exportDays = self.redNotebook.sortedDays
		else:
			start, end = sorted([self.get_start_date(),	self.get_end_date()])
			exportDays = self.redNotebook.getDaysInDateRange((start, end))
			
		selected_categories = self.get_selected_categories_values()
		logging.debug('Selected Categories for Export: %s' % selected_categories)
		export_text = self.is_export_text_selected()
		
		markupStringsForEachDay = []
		for day in exportDays:
			default_export_date_format = '%A, %x'
			# probably no one needs to configure this as i18n already exists
			#date_format = self.redNotebook.config.read('exportDateFormat', \
			#										default_export_date_format)
			date_format = default_export_date_format
			date_string = day.date.strftime(date_format)
			day_markup = markup.getMarkupForDay(day, with_text=export_text, \
											categories=selected_categories, \
											date=date_string)
			markupStringsForEachDay.append(day_markup)

		markupString = ''.join(markupStringsForEachDay)
		
		target = self.format_extension_map.get(format)
		
		headers = ['RedNotebook', '', '']
		
		options = {'toc': 0}
		
		return markup.convert(markupString, target, headers=headers, \
								options=options)
	
	
