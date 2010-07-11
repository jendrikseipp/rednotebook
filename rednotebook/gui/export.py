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
    logging.basicConfig(level=logging.DEBUG)


from rednotebook.data import Day, Month
#from rednotebook.imports.plaintext import PlainTextImporter
from rednotebook.util import filesystem
from rednotebook.storage import Storage
from rednotebook.util import markup
from rednotebook.gui import customwidgets
from rednotebook.journal import Journal

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
        self.show_all()
        
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
        
class IntroductionPage(AssistantPage):
    def __init__(self, text, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)
        
        label = gtk.Label(text)
        
        self.pack_start(label)
        
        
class DatePage(AssistantPage):
    def __init__(self, journal, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)
        
        self.journal = journal 
        
        self.start_date = self.journal.get_edit_date_of_entry_number(0)
        self.end_date = self.journal.get_edit_date_of_entry_number(-1)
        
        self.all_days_button = gtk.RadioButton(label='All days')
        self.sel_days_button = gtk.RadioButton(label='Only the days in the selected time range',
                                            group=self.all_days_button)
                                            
        self.pack_start(self.all_days_button, False)
        self.pack_start(self.sel_days_button, False)
        
        hbox = gtk.HBox()
        self.calendar1 = customwidgets.Calendar()
        self.calendar1.set_date(self.start_date)
        self.calendar2 = customwidgets.Calendar()
        self.calendar2.set_date(self.end_date)
        hbox.pack_start(self.calendar1)
        hbox.pack_start(self.calendar2)
        self.pack_start(hbox)
        
        self.sel_days_button.connect('toggled', self._on_select_days_toggled)
        
        self.select_days = False
        self._set_select_days(False)
        
    def _on_select_days_toggled(self, button):
        select = self.sel_days_button.get_active()
        self._set_select_days(select)
        
    def _set_select_days(self, sensitive):
        self.calendar1.set_sensitive(sensitive)
        self.calendar2.set_sensitive(sensitive)
        self.select_days = sensitive
        
    def get_date_range(self):
        if self.select_days:
            return (self.calendar1.get_date(), self.calendar2.get_date())
        return (self.start_date, self.end_date)
        
        
        
class ContentsPage(AssistantPage):
    def __init__(self, journal, assistant, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)
        
        self.journal = journal
        self.assistant = assistant
        
        self.text_button = gtk.CheckButton(label='Export text')
        self.all_categories_button = gtk.RadioButton(label='Export all categories')
        self.no_categories_button = gtk.RadioButton(label='Do not export categories',
                                            group=self.all_categories_button)
        self.sel_categories_button = gtk.RadioButton(label='Export only the selected categories',
                                            group=self.all_categories_button)
                                            
        self.pack_start(self.text_button, False)
        self.pack_start(self.all_categories_button, False)
        self.pack_start(self.no_categories_button, False)
        self.pack_start(self.sel_categories_button, False)
        
        self.available_categories = gtk.TreeView()
        
        column = gtk.TreeViewColumn(_('Available Categories'))
        self.available_categories.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, 'text', 0)
                
        self.selected_categories = gtk.TreeView()
        
        column = gtk.TreeViewColumn(_('Selected Categories'))
        self.selected_categories.append_column(column)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, 'text', 0)
        
        select_button = gtk.Button('Select' + ' >>')
        unselect_button = gtk.Button('<< ' + 'Unselect')
        
        select_button.connect('clicked', self.on_select_category)
        unselect_button.connect('clicked', self.on_unselect_category)
        
        centered_vbox = gtk.VBox()
        centered_vbox.pack_start(select_button, True, False)
        centered_vbox.pack_start(unselect_button, True, False)
        
        vbox = gtk.VBox()
        vbox.pack_start(centered_vbox, True, False)
        
        hbox = gtk.HBox()
        hbox.pack_start(self.available_categories)
        hbox.pack_start(vbox, False)
        hbox.pack_start(self.selected_categories)
        self.pack_start(hbox)
        
        self.error_text = gtk.Label('')
        self.error_text.set_alignment(0.0, 0.5)
        
        self.pack_end(self.error_text, False, False)
        
        self.refresh_categories_list()
        self.text_button.set_active(True)
        
        self.text_button.connect('toggled', self.check_selection)
        self.all_categories_button.connect('toggled', self.check_selection)
        self.no_categories_button.connect('toggled', self.check_selection)
        self.sel_categories_button.connect('toggled', self.check_selection)
        
        
    def refresh_categories_list(self):
        model_available = gtk.ListStore(gobject.TYPE_STRING)
        categories = self.journal.node_names
        for category in categories:
            new_row = model_available.insert(0)
            model_available.set(new_row, 0, category)
        self.available_categories.set_model(model_available)
        
        model_selected = gtk.ListStore(gobject.TYPE_STRING)
        self.selected_categories.set_model(model_selected)
        
        
    def on_select_category(self, widget):
        selection = self.available_categories.get_selection()
        nb_selected, selected_iter = selection.get_selected()
        
        if selected_iter != None :      
            model_available = self.available_categories.get_model()
            model_selected = self.selected_categories.get_model()
            
            row = model_available[selected_iter]
            
            new_row = model_selected.insert(0)
            model_selected.set(new_row, 0, row[0])
            
            model_available.remove(selected_iter)
            
        self.check_selection()
        

    def on_unselect_category(self, widget):
        selection = self.selected_categories.get_selection()
        nb_selected, selected_iter = selection.get_selected()
        
        if selected_iter != None :
            model_available = self.available_categories.get_model()
            model_selected = self.selected_categories.get_model()
            
            row = model_selected[selected_iter]
            
            new_row = model_available.insert(0)
            model_available.set(new_row, 0, row[0])
            
            model_selected.remove(selected_iter)
        
        self.check_selection()
        
        
    def set_error_text(self, text):
        self.error_text.set_markup('<b>' + text + '</b>')
        
        
    def is_text_exported(self):
        return self.text_button.get_active()
        
        
    def get_categories(self):
        if self.all_categories_button.get_active():
            return self.journal.node_names
        elif self.no_categories_button.get_active():
            return []
        else:
            selected_categories = []
            model_selected = self.selected_categories.get_model()
            
            for row in model_selected:
                selected_categories.append(row[0])
        
            return selected_categories
            
            
    def check_selection(self, *args):
        if not self.is_text_exported() and not self.get_categories():
            error = 'If export text is not selected, you have to select at least one category.'
            self.set_error_text(error)
            correct = False
        else:
            self.set_error_text('')
            correct = True
            
        self.assistant.set_page_complete(self.assistant.page3, correct)
        
        
        
class RadioButtonPage(AssistantPage):
    def __init__(self, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)
        
        self.buttons = []
        
    def add_radio_option(self, object, label, tooltip=''):
        bold_label = label
        #bold_label = gtk.Label()
        #bold_label.set_markup('<b>%s</b>' % label)
        group = self.buttons[0] if self.buttons else None
        button = gtk.RadioButton(group=group)
        button.set_tooltip_markup(tooltip)
        button.set_label(bold_label)
        button.object = object
        description = gtk.Label()
        description.set_alignment(0.0, 0.5)
        description.set_markup(tooltip)
        #hbox = gtk.HBox()
        #hbox.set_border_width(10)
        #hbox.pack_start(description, False, False)
        self.pack_start(button, False, False)
        self.pack_start(description, False, False)
        self.buttons.append(button)
        
        # For testing purposes
        button.set_active(True)
        
    def get_selected_object(self):
        for button in self.buttons:
            if button.get_active():
                return button.object
                
                
class PathChooserPage(AssistantPage):
    def __init__(self, assistant, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)
        
        self.assistant = assistant
        
        self.last_path = None
        
        self.chooser = gtk.FileChooserWidget()
        self.chooser.connect('selection-changed', self.on_path_changed)
        
        self.pack_start(self.chooser)
        
        
    def _remove_filters(self):
        for filter in self.chooser.list_filters():
            self.chooser.remove_filter(filter)
            
        
    def prepare(self, porter):
        self._remove_filters()
        
        self.path_type = porter.PATHTYPE.upper()
        path = porter.DEFAULTPATH
        extension = porter.EXTENSION
        helptext = porter.PATHTEXT
        
        if helptext:
            self.set_header(helptext)
        
        if self.path_type == 'DIR':
            self.chooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        elif self.path_type == 'FILE':
            self.chooser.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        elif self.path_type == 'NEWFILE':
            self.chooser.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
        else:
            logging.error('Wrong path_type "%s"' % path_type)
            
        if self.path_type in ['FILE', 'NEWFILE'] and extension:
            filter = gtk.FileFilter()
            filter.set_name(extension)
            filter.add_pattern('*.' + extension)
            self.chooser.add_filter(filter)
            
        path = self.last_path or path
                    
        if os.path.isdir(path):
            self.chooser.set_current_folder(path)
        else:
            if os.path.exists(path):
                # Method is for existing files
                self.chooser.set_filename(path)
            else:
                self.chooser.set_current_folder(os.path.dirname(path))
                self.chooser.set_current_name(os.path.basename(path))            
        
        
    def get_selected_path(self):
        self.last_path = self.chooser.get_filename()
        return self.last_path
        
        
    def on_path_changed(self, widget):
        # TODO: Try to make this smarter
        self.assistant.set_page_complete(self.assistant.page4, True)
        return
        
        correct = False
        path = self.chooser.get_filename()
        if path is None:
            correct = False
        elif self.path_type == 'DIR':
            correct = os.path.isdir(path)
        elif self.path_type == 'FILE':
            correct = os.path.isfile(path)
        elif self.path_type == 'NEWFILE':
            correct = os.path.isfile(path)
            
        self.assistant.set_page_complete(self.assistant.page4, correct)
        
        

class SummaryPage(AssistantPage):
    def __init__(self, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)
        
        self.settings = []
        
    def prepare(self):
        text = 'You have selected the following settings:'
        self.set_header(text)
        self.clear()
        
    def add_setting(self, setting, value):
        label = gtk.Label()
        label.set_markup('<b>%s:</b> %s' % (setting, value))
        label.set_alignment(0.0, 0.5)
        label.show()
        self.pack_start(label, False)
        self.settings.append(label)
        
    def clear(self):
        for setting in self.settings:
            self.remove(setting)
        self.settings = []
        
                
        
        
class ImportAssistant(gtk.Assistant):
    def __init__(self, journal, *args, **kwargs):
        gtk.Assistant.__init__(self, *args, **kwargs)
        
        self.journal = journal
        
        self.exporters = get_exporters()
        
        self.set_title('Export Assistant')
        self.set_size_request(1000, 700)
        
        texts = ['Welcome to the Export Assistant.',
                'This wizard will help you to export your journal to various formats.',
                'You can select the days you want to export and where the output will be saved.']
        text = '\n'.join(texts)
        self._add_intro_page(text)#self._get_page0()
        
        self.page1 = RadioButtonPage()
        for exporter in self.exporters:
            name = exporter.NAME
            desc = exporter.DESCRIPTION
            self.page1.add_radio_option(exporter, name, desc)
        self.append_page(self.page1)
        self.set_page_title(self.page1, 'Select Export Format' + ' (1/4)')
        self.set_page_complete(self.page1, True)
        
        self.page2 = DatePage(self.journal)
        self.append_page(self.page2)
        self.set_page_title(self.page2, 'Select Date Range' + ' (2/4)')
        self.set_page_complete(self.page2, True)
        
        self.page3 = ContentsPage(self.journal, self)
        self.append_page(self.page3)
        self.set_page_title(self.page3, 'Select Contents' + ' (3/4)')
        self.set_page_complete(self.page3, True)
        
        self.page4 = PathChooserPage(self)
        self.append_page(self.page4)
        self.set_page_title(self.page4, 'Select Export Path' + ' (4/4)')
        
        self.page5 = SummaryPage()
        self.append_page(self.page5)
        self.set_page_title(self.page5, 'Summary')
        self.set_page_type(self.page5, gtk.ASSISTANT_PAGE_CONFIRM)
        self.set_page_complete(self.page5, True)
        
        self.exporter = None
        self.path = None
        
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
        #self.journal.merge_days(self.days)
        
    def _on_prepare(self, assistant, page):
        '''
        Called when a new page should be prepared, before it is shown
        '''
        if page == self.page2:
            self.exporter = self.page1.get_selected_object()
        elif page == self.page3:
            pass
            #self.set_page_complete(self.page3, False)
            #self.page3.prepare(self.importer.NAME, self.path)
            
            # We want the page to be shown first and the days added then
            #gobject.idle_add(self.add_days)
        elif page == self.page4:
            self.page4.prepare(self.exporter)
        elif page == self.page5:
            self.path = self.page4.get_selected_path()
            self.page5.prepare()
            format = self.exporter.NAME
            self.start_date, self.end_date = self.page2.get_date_range()
            self.is_text_exported = self.page3.is_text_exported()
            self.exported_categories = self.page3.get_categories()
            self.page5.add_setting('Format', format)
            self.page5.add_setting('Start date', self.start_date)
            self.page5.add_setting('End date', self.end_date)
            is_text_exported = 'Yes' if self.is_text_exported else 'No'
            self.page5.add_setting('Export text', is_text_exported)
            self.page5.add_setting('Exported categories', ', '.join(self.exported_categories))
            self.page5.add_setting('Export path', self.path)
        
            
    def _add_intro_page(self, text):
        page = IntroductionPage(text)
        self.append_page(page)
        self.set_page_title(page, 'Introduction')
        self.set_page_type(page, gtk.ASSISTANT_PAGE_INTRO)
        self.set_page_complete(page, True)
        
        
        
class Exporter(object):
    NAME = 'Which format do we use?'
    # Short description of how we export
    DESCRIPTION = ''
    PATHTEXT = 'Select the export destination'
    PATHTYPE = 'DIR'
    EXTENSION = None
    
    @classmethod
    def _check_modules(cls, modules):
        for module in modules:
            try:
                __import__(module)
            except ImportError, err:
                logging.info('"%s" could not be imported. ' \
                    'You will not be able to import %s' % (module, cls.NAME))
                # Importer cannot be used
                return False
        return True
    
    @classmethod
    def is_available(cls):
        '''
        This function should be implemented by the subclasses that may
        not be available
        
        If their requirements are not met, they return False
        '''
        return True
        
    
    def export(self):
        '''
        This function has to be implemented by all subclasses
        
        It should *yield* ImportDay objects
        '''
        
    @property
    def DEFAULTPATH(self):
        return os.path.join(os.path.expanduser('~'), 'RedNotebook-Export_%s.%s' % \
                                (datetime.date.today(), self.EXTENSION))




        
class PlainTextExporter(Exporter):
    NAME = 'Plain Text'
    DESCRIPTION = 'Export journal to a plain textfile'
    PATHTYPE = 'NEWFILE'
    EXTENSION = 'txt'
    
class HtmlExporter(Exporter):
    NAME = 'HTML'
    DESCRIPTION = 'Export journal to HTML'
    PATHTYPE = 'NEWFILE'
    EXTENSION = 'html'
        

        
        
def get_exporters():
    exporters = [cls for name, cls in globals().items() \
                if name.endswith('Exporter') and not name == 'Exporter']
    
    exporters = filter(lambda exporter: exporter.is_available(), exporters)
    
    # Instantiate importers
    exporters = map(lambda exporter: exporter(), exporters)
    return exporters
        
        
        
if __name__ == '__main__':
    '''
    Run some tests
    '''
    
    assistant = ImportAssistant(Journal())
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





    

        
    
