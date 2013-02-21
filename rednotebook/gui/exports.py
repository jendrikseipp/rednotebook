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
import logging
import datetime

import gtk
import gobject

if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath("./../../"))
    logging.basicConfig(level=logging.DEBUG)
    from rednotebook.journal import Journal


from rednotebook.util import filesystem
from rednotebook.util import markup
from rednotebook.util import dates
from rednotebook.gui import customwidgets
from rednotebook.gui.customwidgets import Calendar, AssistantPage, \
    RadioButtonPage, PathChooserPage, Assistant
from rednotebook.gui import browser
from rednotebook.gui import options



class DatePage(AssistantPage):
    def __init__(self, journal, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)

        self.journal = journal

        self.all_days_button = gtk.RadioButton(label=_('Export all days'))
        self.selected_text_button = gtk.RadioButton(
            label=_('Export currently selected text'),
            group=self.all_days_button)
        self.one_day_button = gtk.RadioButton(
            label=_('Export currently visible day'),
            group=self.all_days_button)
        self.sel_days_button = gtk.RadioButton(
            label=_('Export days in the selected time range'),
            group=self.all_days_button)

        self.pack_start(self.all_days_button, False)
        self.pack_start(self.one_day_button, False)
        self.pack_start(self.selected_text_button, False)
        self.pack_start(self.sel_days_button, False)

        label1 = gtk.Label()
        label1.set_markup('<b>' + _('From:') + '</b>')
        label2 = gtk.Label()
        label2.set_markup('<b>' + _('To:') + '</b>')

        self.calendar1 = Calendar()
        self.calendar2 = Calendar()

        vbox1 = gtk.VBox()
        vbox2 = gtk.VBox()
        vbox1.pack_start(label1, False)
        vbox1.pack_start(self.calendar1)
        vbox2.pack_start(label2, False)
        vbox2.pack_start(self.calendar2)

        hbox = gtk.HBox()
        hbox.pack_start(vbox1)
        hbox.pack_start(vbox2)
        self.pack_start(hbox)

        self.sel_days_button.connect('toggled', self._on_select_days_toggled)

        self.all_days_button.set_active(True)
        self._set_select_days(False)


    def _on_select_days_toggled(self, button):
        select = self.sel_days_button.get_active()
        self._set_select_days(select)


    def _set_select_days(self, sensitive):
        self.calendar1.set_sensitive(sensitive)
        self.calendar2.set_sensitive(sensitive)
        self.select_days = sensitive


    def export_all_days(self):
        return self.all_days_button.get_active()


    def export_selected_text(self):
        return self.selected_text_button.get_active()


    def get_date_range(self):
        if self.select_days:
            return (self.calendar1.get_date(), self.calendar2.get_date())
        return (self.journal.day.date,) * 2


    def refresh_dates(self):
        self.calendar1.set_date(datetime.date.today())
        self.calendar2.set_date(datetime.date.today())



class ContentsPage(AssistantPage):
    def __init__(self, journal, assistant, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)

        self.journal = journal
        self.assistant = assistant

        # Make the config available for the date format option
        options.Option.config = journal.config
        # Set default date format string
        options.Option.config['exportDateFormat'] = '%A, %x'
        self.date_format = options.DateFormatOption(_('Date format'), 'exportDateFormat')
        self.date_format.combo.combo_box.set_tooltip_text(_('Leave blank to omit dates in export'))

        self.text_and_tags_button = gtk.RadioButton(label=_('Export text and tags'))
        self.text_only_button = gtk.RadioButton(label=_('Export text only'),
                                                group=self.text_and_tags_button)
        self.tags_only_button = gtk.RadioButton(label=_('Export tags only'),
                                                group=self.text_and_tags_button)
        self.filter_tags_button = gtk.CheckButton(label=_('Filter days by tags'))

        self.pack_start(self.date_format, False)
        self.pack_start(self.text_and_tags_button, False)
        self.pack_start(self.text_only_button, False)
        self.pack_start(self.tags_only_button, False)
        self.pack_start(gtk.HSeparator(), False)
        self.pack_start(self.filter_tags_button, False)

        self.available_categories = customwidgets.CustomListView([(_('Available tags'), str)])
        self.selected_categories = customwidgets.CustomListView([(_('Selected tags'), str)])

        left_scroll = gtk.ScrolledWindow()
        left_scroll.add(self.available_categories)

        right_scroll = gtk.ScrolledWindow()
        right_scroll.add(self.selected_categories)

        self.select_button = gtk.Button(_('Select') + ' >>')
        self.deselect_button = gtk.Button('<< ' + _('Deselect'))

        self.select_button.connect('clicked', self.on_select_category)
        self.deselect_button.connect('clicked', self.on_deselect_category)

        centered_vbox = gtk.VBox()
        centered_vbox.pack_start(self.select_button, True, False)
        centered_vbox.pack_start(self.deselect_button, True, False)

        vbox = gtk.VBox()
        vbox.pack_start(centered_vbox, True, False)

        hbox = gtk.HBox()
        hbox.pack_start(left_scroll)
        hbox.pack_start(vbox, False)
        hbox.pack_start(right_scroll)
        self.pack_start(hbox)

        self.error_text = gtk.Label('')
        self.error_text.set_alignment(0.0, 0.5)

        self.pack_end(self.error_text, False, False)

        self.text_and_tags_button.set_active(True)
        self.filter_tags_button.connect('toggled', self.check_selection)

    def refresh_categories_list(self):
        model_available = gtk.ListStore(gobject.TYPE_STRING)
        for category in self.journal.categories:
            model_available.append([category])
        self.available_categories.set_model(model_available)

        model_selected = gtk.ListStore(gobject.TYPE_STRING)
        self.selected_categories.set_model(model_selected)

    def on_select_category(self, widget):
        selection = self.available_categories.get_selection()
        nb_selected, selected_iter = selection.get_selected()

        if selected_iter is not None:
            model_available = self.available_categories.get_model()
            model_selected = self.selected_categories.get_model()

            row = model_available[selected_iter]

            new_row = model_selected.insert(0)
            model_selected.set(new_row, 0, row[0])

            model_available.remove(selected_iter)

        self.check_selection()

    def on_deselect_category(self, widget):
        selection = self.selected_categories.get_selection()
        nb_selected, selected_iter = selection.get_selected()

        if selected_iter is not None:
            model_available = self.available_categories.get_model()
            model_selected = self.selected_categories.get_model()

            row = model_selected[selected_iter]

            new_row = model_available.insert(0)
            model_available.set(new_row, 0, row[0])

            model_selected.remove(selected_iter)

        self.check_selection()

    def set_error_text(self, text):
        self.error_text.set_markup('<b>' + text + '</b>')

    def is_text_included(self):
        return self.text_only_button.get_active() or self.text_and_tags_button.get_active()

    def is_tags_included(self):
        return self.tags_only_button.get_active() or self.text_and_tags_button.get_active()

    def is_filtered(self):
        return self.filter_tags_button.get_active()

    def get_categories(self):
        if not self.filter_tags_button.get_active():
            return self.journal.categories
        else:
            selected_categories = []
            model_selected = self.selected_categories.get_model()

            for row in model_selected:
                selected_categories.append(row[0])

            return selected_categories

    def check_selection(self, *args):
        if self.is_filtered() and not self.get_categories():
            error = _('When filtering by tags, you have to select at least one tag.')
            self.set_error_text(error)
            correct = False
        else:
            self.set_error_text('')
            correct = True

        select = self.filter_tags_button.get_active()
        self.available_categories.set_sensitive(select)
        self.selected_categories.set_sensitive(select)
        self.select_button.set_sensitive(select)
        self.deselect_button.set_sensitive(select)

        self.assistant.set_page_complete(self.assistant.page3, correct)



class SummaryPage(AssistantPage):
    def __init__(self, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)

        self.settings = []

    def prepare(self):
        text = _('You have selected the following settings:')
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



class ExportAssistant(Assistant):
    def __init__(self, *args, **kwargs):
        Assistant.__init__(self, *args, **kwargs)

        self.exporters = get_exporters()

        self.set_title(_('Export Assistant'))

        texts = [_('Welcome to the Export Assistant.'),
                _('This wizard will help you to export your journal to various formats.'),
                _('You can select the days you want to export and where the output will be saved.')]
        text = '\n'.join(texts)
        self._add_intro_page(text)

        self.page1 = RadioButtonPage()
        for exporter in self.exporters:
            name = exporter.NAME
            desc = exporter.DESCRIPTION
            self.page1.add_radio_option(exporter, name, desc)
        self.append_page(self.page1)
        self.set_page_title(self.page1, _('Select Export Format') + ' (1/5)')
        self.set_page_complete(self.page1, True)

        self.page2 = DatePage(self.journal)
        self.append_page(self.page2)
        self.set_page_title(self.page2, _('Select Date Range') + ' (2/5)')
        self.set_page_complete(self.page2, True)

        self.page3 = ContentsPage(self.journal, self)
        self.append_page(self.page3)
        self.set_page_title(self.page3, _('Select Contents') + ' (3/5)')
        self.set_page_complete(self.page3, True)
        self.page3.check_selection()

        self.page4 = PathChooserPage(self)
        self.append_page(self.page4)
        self.set_page_title(self.page4, _('Select Export Path') + ' (4/5)')
        self.set_page_complete(self.page4, True)

        self.page5 = SummaryPage()
        self.append_page(self.page5)
        self.set_page_title(self.page5, _('Summary') + ' (5/5)')
        self.set_page_type(self.page5, gtk.ASSISTANT_PAGE_CONFIRM)
        self.set_page_complete(self.page5, True)

        self.exporter = None
        self.path = None
        self.set_forward_page_func(self.pageforward)

    def pageforward(self, page):
        if page == 2 and self.page2.export_selected_text():
            return 4
        else:
            return page + 1

    def run(self, selected_text):
        self.selected_text = selected_text
        self.page2.refresh_dates()
        self.page3.refresh_categories_list()
        self.show_all()

    def _on_close(self, assistant):
        '''
        Do the export
        '''
        self.hide()
        self.export()

    def _on_prepare(self, assistant, page):
        '''
        Called when a new page should be prepared, before it is shown
        '''
        if page == self.page2:
            # Date Range
            self.exporter = self.page1.get_selected_object()
        elif page == self.page3:
            # Categories
            start_date, end_date = self.page2.get_date_range()
            if not self.page2.export_all_days() and start_date == end_date:
                self.page3.filter_tags_button.set_active(False)
                self.page3.filter_tags_button.set_sensitive(False)
            else:
                self.page3.filter_tags_button.set_sensitive(True)
        elif page == self.page4:
            # Path
            self.page4.prepare(self.exporter)
        elif page == self.page5:
            # Summary
            self.path = self.page4.get_selected_path()
            self.page5.prepare()
            self.export_all_days = self.page2.export_all_days()
            self.export_selected_text = self.page2.export_selected_text()
            self.is_filtered = self.page3.is_filtered()
            self.exported_categories = self.page3.get_categories()

            self.page5.add_setting(_('Format'), self.exporter.NAME)
            self.page5.add_setting(_('Export all days'), self.yes_no(self.export_all_days))
            if not self.export_all_days:
                start_date, end_date = self.page2.get_date_range()
                if start_date == end_date:
                    self.page5.add_setting(_('Date'), start_date)
                    self.page5.add_setting(_('Export selected text only'), self.yes_no(self.export_selected_text))
                else:
                    self.page5.add_setting(_('Start date'), start_date)
                    self.page5.add_setting(_('End date'), end_date)
            if self.export_selected_text:
                self.exported_categories = []
            else:
                self.page5.add_setting(_('Include text'), self.yes_no(self.page3.is_text_included()))
                self.page5.add_setting(_('Include tags'), self.yes_no(self.page3.is_tags_included()))
            if self.is_filtered:
                self.page5.add_setting(_('Filtered by tags'), ', '.join(self.exported_categories))
            self.page5.add_setting(_('Export path'), self.path)

    def yes_no(self, value):
        return _('Yes') if value else _('No')

    def get_export_string(self, format):
        if self.export_selected_text and self.selected_text:
            markup_string = self.selected_text
        else:
            if self.export_all_days:
                export_days = self.journal.days
            else:
                export_days = self.journal.get_days_in_date_range(*self.page2.get_date_range())

            selected_categories = self.exported_categories
            logging.debug('Selected Categories for Inclusion: %s' % selected_categories)

            # Save selected date format
            date_format = self.page3.date_format.get_value()
            self.journal.config['exportDateFormat'] = date_format

            markup_strings_for_each_day = []
            for day in export_days:
                include_day = True
                if self.is_filtered:
                    include_day = False
                    catagory_pairs = day.get_category_content_pairs()
                    for category in selected_categories:
                        if category in catagory_pairs:
                            include_day = True
                if include_day:
                    date_string = dates.format_date(date_format, day.date)
                    day_markup = markup.get_markup_for_day(day, with_text=self.page3.is_text_included(),
                                                           with_tags=self.page3.is_tags_included(),
                                                           categories=selected_categories,
                                                           date=date_string)
                    markup_strings_for_each_day.append(day_markup)

            markup_string = ''.join(markup_strings_for_each_day)

        return markup.convert(markup_string, format, self.journal.dirs.data_dir,
                              options={'toc': 0})

    def export(self):
        format = self.exporter.FORMAT

        if format == 'pdf':
            self.export_pdf()
            return

        export_string = self.get_export_string(format)

        filesystem.write_file(self.path, export_string)
        self.journal.show_message(_('Content exported to %s') % self.path)


    def export_pdf(self):
        logging.info('Exporting to PDF')
        browser.print_pdf(self.get_export_string('xhtml'), self.path)
        self.journal.show_message(_('Content exported to %s') % self.path)



class Exporter(object):
    NAME = 'Which format do we use?'
    # Short description of how we export
    DESCRIPTION = ''
    # Export destination
    PATHTEXT = ''
    PATHTYPE = 'NEWFILE'
    EXTENSION = None

    @classmethod
    def _check_modules(cls, modules):
        for module in modules:
            try:
                __import__(module)
            except ImportError:
                logging.info('"%s" could not be imported. '
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
        return os.path.join(os.path.expanduser('~'),
            'RedNotebook-Export_%s.%s' % (datetime.date.today(), self.EXTENSION))


class PlainTextExporter(Exporter):
    NAME = _('Plain Text')
    #DESCRIPTION = 'Export journal to a plain textfile'
    EXTENSION = 'txt'
    FORMAT = 'txt'


class HtmlExporter(Exporter):
    NAME = 'HTML'
    #DESCRIPTION = 'Export journal to HTML'
    EXTENSION = 'html'
    FORMAT = 'xhtml'


class LatexExporter(Exporter):
    NAME = 'Latex'
    #DESCRIPTION = 'Create a tex file'
    EXTENSION = 'tex'
    FORMAT = 'tex'


class PdfExporter(Exporter):
    NAME = 'PDF'
    #DESCRIPTION = 'Create a PDF file'
    EXTENSION = 'pdf'
    FORMAT = 'pdf'

    @property
    def DESCRIPTION(self):
        if self.is_available():
            return ''
        else:
            return '(' + _('requires pywebkitgtk') + ')'

    @classmethod
    def is_available(cls):
        return browser.can_print_pdf()




def get_exporters():
    exporters = [PlainTextExporter, HtmlExporter, LatexExporter, PdfExporter]

    # Instantiate importers
    exporters = map(lambda exporter: exporter(), exporters)
    return exporters



if __name__ == '__main__':
    '''
    Run some tests
    '''
    assistant = ExportAssistant(Journal())
    assistant.set_position(gtk.WIN_POS_CENTER)
    assistant.run()
    gtk.main()
