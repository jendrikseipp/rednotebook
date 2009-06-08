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

from rednotebook.util import markup

class ExportAssistant (object):
    
    _instance = None
    
    @staticmethod
    def get_instance (main_window):
        if ExportAssistant._instance is None :
            ExportAssistant._instance = ExportAssistant (main_window)
        return ExportAssistant._instance
    
    
    def __init__ (self, main_window):
                
        self.redNotebook = main_window.redNotebook
        self.main_window = main_window
        
        self.format_extension_map = {'Text': 'txt', 'HTML': 'html', \
									'Latex': 'tex', 'PDF' : 'pdf'}
        cache_wtree = self.main_window.wTree
        self.assistant = cache_wtree.get_widget('export_assistant')
        dic = {
               'on_quit': self.on_quit,
               'on_cancel': self.on_cancel,
               }
        
        cache_wtree.signal_autoconnect(dic)
        
        self.append_introduction_page()
        self.append_first_page()
        self.append_second_page()
        self.append_third_page()
        self.append_fourth_page()
        
        self.assistant.set_forward_page_func(self.prepare_next_page, None)
        self.assistant.set_title('Export Assistant')
    
    def run (self):
        self.refresh_categories_list()
        self.assistant.show()

    def append_introduction_page (self) :
        cache_wtree = self.main_window.wTree
        page0 = cache_wtree.get_widget('export_assistant_0')
        page0.show()        
        self.assistant.set_page_complete(page0, True)
    
    def append_first_page (self) :
        cache_wtree = self.main_window.wTree
        page1 = cache_wtree.get_widget('export_assistant_1')
        page1.show()

        self.assistant.set_page_complete(page1, True)

        self.text_button = cache_wtree.get_widget('text')
        self.html_button = cache_wtree.get_widget('html')
        self.latex_button = cache_wtree.get_widget('latex')
        self.pdf_button = cache_wtree.get_widget('pdf')
        if not self.is_pdf_supported() :
            self.pdf_button.hide()
        else :
            self.pdf_button.show()
            


    def append_second_page (self) :    
        cache_wtree = self.main_window.wTree
        dic = {'change_date_selector_status': self.change_date_selector_status}
        cache_wtree.signal_autoconnect(dic)
        
        page2 = cache_wtree.get_widget('export_assistant_2')
        page2.show()
        
        self.assistant.set_page_complete(page2, True)
        
        self.all_entries_button = cache_wtree.get_widget('all_entries')
        self.selected_range_button = cache_wtree.get_widget('selected_range')
        self.start_date = cache_wtree.get_widget('start_date')
        self.end_date = cache_wtree.get_widget('end_date')
        
        
        start_date_value = self.redNotebook.getEditDateOfEntryNumber(0)
        self.start_date.select_month(start_date_value.month - 1, start_date_value.year)
        self.start_date.select_day (start_date_value.day)

        end_date_value = self.redNotebook.getEditDateOfEntryNumber(-1)
        self.end_date.select_month(end_date_value.month - 1, end_date_value.year)
        self.end_date.select_day (end_date_value.day)
        
        self.change_date_selector_status(self.assistant)

    
    def append_third_page (self) :
        cache_wtree = self.main_window.wTree
        
        dic = {'select_category': self.select_category,
               'unselect_category': self.unselect_category,
               'change_categories_selector_status': self.change_categories_selector_status,
               'change_export_text_status': self.change_export_text_status,
               }
        cache_wtree.signal_autoconnect(dic)
        
        page3 = cache_wtree.get_widget('export_assistant_3')
        page3.show()
        
        self.assistant.set_page_complete(page3, True)

        self.nothing_exported_warning = cache_wtree.get_widget('nothing_exported_warning')

        self.export_text = cache_wtree.get_widget('export_text')
        
        self.no_categories = cache_wtree.get_widget('no_categories')
        self.all_categories = cache_wtree.get_widget('all_categories')
        self.selected_categories_radio = cache_wtree.get_widget('selected_categories_radio')
        self.hbox_categories = cache_wtree.get_widget('hbox_categories')
        
        
        self.available_categories = cache_wtree.get_widget('available_categories')
        
        column = gtk.TreeViewColumn('Available Categories')
        self.available_categories.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, 'text', 0)
                
        self.selected_categories = cache_wtree.get_widget('selected_categories')
        
        column = gtk.TreeViewColumn('Selected Categories')
        self.selected_categories.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, 'text', 0)
        
        self.change_categories_selector_status(self.assistant)   


    def append_fourth_page (self) :
        cache_wtree = self.main_window.wTree
        page4 = cache_wtree.get_widget('export_assistant_4')
        page4.show()
        
        self.assistant.set_page_complete(page4, True)

        self.filename_chooser = cache_wtree.get_widget('filename_chooser')
        
    
    def prepare_next_page (self, current_page, data):
        if current_page == 1 :
            proposedFileName = 'RedNotebook-Export_' + str(datetime.date.today()) + \
                                '.' + self.format_extension_map.get(self.get_selected_format())

            home = os.getenv('USERPROFILE') or os.getenv('HOME')
            self.filename_chooser.set_current_folder(home)
            self.filename_chooser.set_current_name (proposedFileName)
        return current_page + 1
    
    
    def on_quit (self, widget):
        self.filename = self.filename_chooser.get_filename()
        self.selected_categories_values = self.get_selected_categories_values()
        
        self.assistant.hide()
        self.export()
    
    def on_cancel (self, widget, other=None):
        self.redNotebook.showMessage('Cancelling export assistant.')
        self.assistant.hide()

    def change_date_selector_status (self, widget):
        if (self.is_all_entries_selected()) :
            self.start_date.set_sensitive(False)
            self.end_date.set_sensitive(False)
        else :
            self.start_date.set_sensitive(True)
            self.end_date.set_sensitive(True)

    def change_export_text_status (self, widget):
        if self.is_export_text_selected () :
            self.no_categories.set_sensitive(True)
        else :
            if self.is_no_categories_selected() :
                self.all_categories.set_active(True)
            self.no_categories.set_sensitive(False)
        self.check_exported_content_is_valid()



    def change_categories_selector_status (self, widget):
        if (self.is_all_categories_selected() or self.is_no_categories_selected()) :
            self.hbox_categories.set_sensitive(False)
        else :
            self.hbox_categories.set_sensitive(True)
        self.check_exported_content_is_valid()
    
    def select_category (self, widget):
        selection = self.available_categories.get_selection()
        nb_selected, selected_iter = selection.get_selected()
        
        if selected_iter != None :        
            model_available = self.available_categories.get_model()
            model_selected = self.selected_categories.get_model()
            
            row =  model_available[selected_iter]
            
            newRow = model_selected.insert(0)
            model_selected.set(newRow, 0, row[0])
            
            model_available.remove(selected_iter)
        self.check_exported_content_is_valid()

    def unselect_category (self, widget):
        selection = self.selected_categories.get_selection()
        nb_selected, selected_iter = selection.get_selected()
        
        if selected_iter != None :
            model_available = self.available_categories.get_model()
            model_selected = self.selected_categories.get_model()
            
            row =  model_selected[selected_iter]
            
            newRow = model_available.insert(0)
            model_available.set(newRow, 0, row[0])
            
            model_selected.remove(selected_iter)
        
        self.check_exported_content_is_valid()

    def check_exported_content_is_valid (self):
        current_page = self.assistant.get_nth_page(3) 
        
        if not self.is_export_text_selected() \
           and len (self.get_selected_categories_values()) == 0 :
            self.nothing_exported_warning.show()
            self.assistant.set_page_complete(current_page, False)
        else :
            self.nothing_exported_warning.hide()
            self.assistant.set_page_complete(current_page, True)
            
    
    def get_start_date (self):
        year, month, day = self.start_date.get_date()
        return datetime.date(year, month + 1, day)

    def get_end_date (self):
        year, month, day = self.end_date.get_date()
        return datetime.date(year, month + 1, day)
    
    def get_selected_format (self):
        if self.latex_button.get_active():
            return "Latex"
        if self.html_button.get_active():
            return "HTML"
        if self.pdf_button.get_active() :
            return "PDF"
        return "Text"
    
    def get_selected_categories_values (self):
        selected_categories = []
        
        if self.is_all_categories_selected() :
            selected_categories = self.main_window.redNotebook.nodeNames
        elif not self.is_no_categories_selected() :
            model_selected = self.selected_categories.get_model()
            
            for row in model_selected :
                selected_categories.append(row[0])
        
        return selected_categories
    
    def is_export_text_selected (self):
        if self.export_text.get_active() :
            return True
        return False
        
    def is_all_entries_selected (self):
        if self.all_entries_button.get_active():
            return True
        return False

    def is_all_categories_selected (self):
        if self.all_categories.get_active():
            return True
        return False

    def is_no_categories_selected (self):
        if self.no_categories.get_active():
            return True
        return False
    
    def refresh_categories_list (self):
        model_available = gtk.ListStore(gobject.TYPE_STRING)
        categories = self.main_window.redNotebook.nodeNames
        for category in categories :
            newRow = model_available.insert(0)
            model_available.set(newRow, 0, category)

        self.available_categories.set_model(model_available)
        model_selected = gtk.ListStore(gobject.TYPE_STRING)
        self.selected_categories.set_model(model_selected)

    
    
    def is_pdf_supported (self):
        #TODO: Implement that
        return False
    
    def export (self):
        #TODO: Add content page values management
        export_string = self.get_export_string(self.get_selected_format())
        
        try:
            export_file = codecs.open(self.filename, 'w', 'utf-8')
            export_file.write(export_string)
            export_file.flush()
            self.redNotebook.showMessage('Content exported to ' + self.filename)
        except:
            self.redNotebook.showMessage('Exporting to ' + self.filename + ' failed')

    def get_export_string(self, format):
        if self.is_all_entries_selected() :
            exportDays = self.redNotebook.sortedDays
        else:
            exportDays = self.redNotebook.getDaysInDateRange((self.get_start_date(), \
															self.get_end_date()))
            
        selected_categories = self.get_selected_categories_values()
        export_text = self.is_export_text_selected()
        
        markupStringsForEachDay = []
        for day in exportDays:
            default_export_date_format = '%A, %x'
            #date_format = self.redNotebook.config.read('exportDateFormat', \
		    #										default_export_date_format)
            date_format = default_export_date_format
            date_string = day.date.strftime(date_format)
            day_markup = markup.getMarkupForDay(day, with_text=export_text, \
											categories=selected_categories, \
											date=date_string)
            markupStringsForEachDay.append(day_markup)

        markupString = reduce(operator.add, markupStringsForEachDay)
        
        target = self.format_extension_map.get(self.get_selected_format())
        
        headers = ['RedNotebook', '', '']
        
        return markup.convert(markupString, target, headers)
    
    
