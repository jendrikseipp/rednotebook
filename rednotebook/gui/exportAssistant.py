# -*- coding: utf-8 -*-

import gtk
import gobject
import datetime
import os
import codecs
import operator

from rednotebook.util import markup

class ExportAssistant (object):
    def __init__ (self, mainWindow):
                
        self.redNotebook = mainWindow.redNotebook
        self.mainWindow = mainWindow
        
        self.format_extension_map = {'Text': 'txt', 'HTML': 'html', 'Latex': 'tex', 'PDF' : 'pdf'}
        cache_wtree = self.mainWindow.wTree
        self.assistant = cache_wtree.get_widget('export_assistant')
        dic = {
               'on_quit': self.on_quit,
               'on_cancel': self.on_cancel,
               }
        
        cache_wtree.signal_autoconnect(dic)
        
        self.append_first_page()
        self.append_second_page()
        self.append_third_page()
        self.append_fourth_page()
        
        self.assistant.set_forward_page_func(self.prepare_next_page, None)
        
        self.assistant.show()

    def append_first_page (self) :
        cache_wtree = self.mainWindow.wTree
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
        cache_wtree = self.mainWindow.wTree
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
        cache_wtree = self.mainWindow.wTree
        
        dic = {'select_category': self.select_category,
               'unselect_category': self.unselect_category,
               'change_categories_selector_status': self.change_categories_selector_status,
               }
        cache_wtree.signal_autoconnect(dic)
        
        page3 = cache_wtree.get_widget('export_assistant_3')
        page3.show()
        
        self.assistant.set_page_complete(page3, True)
        
        self.all_categories = cache_wtree.get_widget('all_categories')
        self.selected_categories_radio = cache_wtree.get_widget('selected_categories_radio')
        self.hbox_categories = cache_wtree.get_widget('hbox_categories')
        
        
        self.available_categories = cache_wtree.get_widget('available_categories')
        model_available = gtk.ListStore(gobject.TYPE_STRING)
        self.available_categories.set_model(model_available)
        
        existing_columns = self.available_categories.get_columns()
        for column in existing_columns :
            self.available_categories.remove_column(column)
        
        column = gtk.TreeViewColumn('Available Categories')
        self.available_categories.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, 'text', 0)
        
        categories = self.mainWindow.redNotebook.nodeNames
        for category in categories :
            newRow = model_available.insert(0)
            model_available.set(newRow, 0, category)
        
        self.selected_categories = cache_wtree.get_widget('selected_categories')
        model_selected = gtk.ListStore(gobject.TYPE_STRING)
        self.selected_categories.set_model(model_selected)

        existing_columns = self.selected_categories.get_columns()
        for column in existing_columns :
            self.selected_categories.remove_column(column)

        column = gtk.TreeViewColumn('Selected Categories')
        self.selected_categories.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, 'text', 0)
        
        self.change_categories_selector_status(self.assistant)   


    def append_fourth_page (self) :
        cache_wtree = self.mainWindow.wTree
        page4 = cache_wtree.get_widget('export_assistant_4')
        page4.show()
        
        self.assistant.set_page_complete(page4, True)

        self.filename_chooser = cache_wtree.get_widget('filename_chooser')
        
    
    def prepare_next_page (self, currentPage, data):
        if currentPage == 0 :
            proposedFileName = 'RedNotebook-Export_' + str(datetime.date.today()) + \
                                '.' + self.format_extension_map.get(self.get_selected_format())

            home = os.getenv('USERPROFILE') or os.getenv('HOME')
            self.filename_chooser.set_current_folder(home)
            self.filename_chooser.set_current_name (proposedFileName)
            
        return currentPage + 1
    
    
    def on_quit (self, widget):
        self.fileName = self.filename_chooser.get_filename()
        self.selected_categories_values = self.get_selected_categories_values()
        
        self.assistant.hide()
        self.export()
    
    def on_cancel (self, widget, other=None):
        self.redNotebook.showMessage('Cancelling export assistant.')
        self.assistant.hide()

    def change_date_selector_status (self, widget):
        if (self.all_entries_button.get_active()) :
            self.start_date.set_sensitive(False)
            self.end_date.set_sensitive(False)
        else :
            self.start_date.set_sensitive(True)
            self.end_date.set_sensitive(True)

    def change_categories_selector_status (self, widget):
        if (self.all_categories.get_active()) :
            self.hbox_categories.set_sensitive(False)
        else :
            self.hbox_categories.set_sensitive(True)
    
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
            selected_categories = self.mainWindow.redNotebook.nodeNames
        else :
            model_selected = self.selected_categories.get_model()
            
            for row in model_selected :
                selected_categories.append(row[0])
        
        return selected_categories
    
    def is_all_entries_selected (self):
        if self.all_entries_button.get_active():
            return True
        return False

    def is_all_categories_selected (self):
        if self.all_categories.get_active():
            return True
        return False
        
    def is_pdf_supported (self):
        #TODO: Implement that
        return False
    
    def export (self):
        #TODO: Implement that
        exportString = self.get_export_string(self.get_selected_format())
        
        try:
            exportFile = codecs.open(self.fileName, 'w', 'utf-8')
            exportFile.write(exportString)
            exportFile.flush()
            self.redNotebook.showMessage('Content exported to ' + self.fileName)
        except:
            self.redNotebook.showMessage('Exporting to ' + self.fileName + ' failed')

    def get_export_string(self, format):
        if self.is_all_entries_selected() :
            exportDays = self.redNotebook.sortedDays
        else:
            exportDays = self.redNotebook.getDaysInDateRange((self.get_start_date(), self.get_end_date()))

        markupStringHeader = 'RedNotebook'
        markupStringsForEachDay = map(markup.getMarkupForDay, exportDays)
        markupString = reduce(operator.add, markupStringsForEachDay)
        
        target = self.format_extension_map.get(self.get_selected_format())
        
        return markup.convertMarkupToTarget(markupString, target, markupStringHeader)
    
    
