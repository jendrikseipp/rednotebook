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

# For testing
import __builtin__
if not hasattr(__builtin__, '_'):
    __builtin__._ = lambda x: x

if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath("./../../"))
    logging.basicConfig(level=logging.DEBUG)



from rednotebook.data import Day, Month
from rednotebook.util import filesystem
from rednotebook import storage
from rednotebook.util import markup
from rednotebook.gui.customwidgets import AssistantPage, RadioButtonPage, \
    PathChooserPage, Assistant

class ImportDay(Day):
    '''
    text is set and retrieved with the property "text"
    '''
    def __init__(self, year, month, day):
        import_month = Month(year, month)
        Day.__init__(self, import_month, day)



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
        parts = [
            _('Import type:') + ' <b>' + type + '</b>\n',
            _('Path:') + ' <b>' + path + '</b>\n\n',
            _('The following contents will be imported:')]
        self.set_header(''.join(parts))
        self.clear()


    def add_day(self, day):
        day_text = '====== %s ======\n%s\n\n' % (day.date, day.text)
        categories = day.get_category_content_pairs()
        if categories:
            day_text += markup.convert_categories_to_markup(categories, False)
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



class ImportAssistant(Assistant):
    def __init__(self, *args, **kwargs):
        Assistant.__init__(self, *args, **kwargs)

        self.importers = get_importers()

        self.set_title(_('Import Assistant'))

        texts = [_('This Assistant lets you import notes from other applications.'),
                _('You can check the results on the last page before any change is made.')]
        self.page0 = self._add_intro_page('\n'.join(texts))

        self.page1 = self._get_page1()
        self.append_page(self.page1)
        self.set_page_title(self.page1, _('Select what to import') + ' (1/3)')
        self.set_page_complete(self.page1, True)

        self.page2 = PathChooserPage(self.journal)
        self.append_page(self.page2)
        self.set_page_title(self.page2, _('Select Import Path') + ' (2/3)')

        self.page3 = SummaryPage()
        self.append_page(self.page3)
        self.set_page_title(self.page3, _('Summary') + ' (3/3)')
        self.set_page_type(self.page3, gtk.ASSISTANT_PAGE_CONFIRM)

        self.importer = None
        self.path = None
        self.days = []


    def run(self):
        self.show_all()


    def _on_close(self, assistant):
        '''
        Do the import
        '''
        self.hide()
        self.journal.merge_days(self.days)

        # We want to see the new contents of the currently loaded day
        # so reload current day
        self.journal.load_day(self.journal.date)


    def _on_prepare(self, assistant, page):
        '''
        Called when a new page should be prepared, before it is shown
        '''
        if page == self.page2:
            self.importer = self.page1.get_selected_object()
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
            self.page3.add_day(day)
            self.days.append(day)
        self.set_page_complete(self.page3, True)


    def _get_page1(self):
        page = RadioButtonPage()
        for importer in self.importers:
            name = importer.NAME
            desc = importer.DESCRIPTION
            page.add_radio_option(importer, name, desc)
        return page




class Importer(object):
    NAME = 'What do we import?'
    DESCRIPTION = 'Short description of what we import'
    PATHTEXT = _('Select the directory containing the sources to import')
    DEFAULTPATH = os.path.expanduser('~')
    PATHTYPE = 'DIR'
    EXTENSION = None

    @classmethod
    def _check_modules(cls, modules):
        for module in modules:
            try:
                __import__(module)
            except ImportError, err:
                logging.info('"%s" could not be imported: %s\nYou will not be '
                             'able to import %s' % (module, err, cls.NAME))
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


    def get_days(self):
        '''
        This function has to be implemented by all subclasses

        It should *yield* ImportDay objects
        '''


    def _get_files(self, dir):
        '''
        Convenience function that can be used by Importers that operate
        on files in a directory

        returns a sorted list of all files in dir without the path
        '''
        assert os.path.isdir(dir)
        files = os.listdir(dir)
        files.sort()
        return files





class PlainTextImporter(Importer):
    NAME = 'Plain Text'
    DESCRIPTION = _('Import Text from plain textfiles')
    PATHTEXT = _('Select a directory containing your data files')
    PATHTYPE = 'DIR'

    # Allow 2010-05-08[.txt] with different or no separators
    sep = r'[:\._\-]?'  # The separators :._-
    date_exp = re.compile(r'(\d{4})%s(\d{2})%s(\d{2})(?:\.txt)?' % (sep, sep))

    def get_days(self, dir):
        for file in self._get_files(dir):
            match = self.date_exp.match(file)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))

                import_day = ImportDay(year, month, day)

                path = os.path.join(dir, file)
                text = filesystem.read_file(path)
                import_day.text = text
                yield import_day


class RedNotebookImporter(Importer):
    NAME = _('RedNotebook Journal')
    DESCRIPTION = _('Import data from a different RedNotebook journal')
    PATHTEXT = _('Select a directory containing RedNotebook data files')
    PATHTYPE = 'DIR'

    def get_days(self, dir):
        assert os.path.isdir(dir)
        months = storage.load_all_months_from_disk(dir)
        for month in sorted(months.values()):
            for day in sorted(month.days.values()):
                yield day


class RedNotebookBackupImporter(RedNotebookImporter):
    NAME = _('RedNotebook Zip Backup')
    DESCRIPTION = _('Import a RedNotebook backup zip archive')
    PATHTEXT = _('Select a backup zipfile')
    PATHTYPE = 'FILE'
    EXTENSION = 'zip'

    @classmethod
    def is_available(cls):
        import zipfile
        can_extractall = hasattr(zipfile.ZipFile, 'extractall')
        return can_extractall

    def get_days(self, file):
        assert os.path.isfile(file)

        import zipfile
        import tempfile
        import shutil

        zip_archive = zipfile.ZipFile(file, 'r')

        tempdir = tempfile.mkdtemp()

        logging.info('Extracting backup zipfile to %s' % tempdir)
        zip_archive.extractall(tempdir)

        for day in RedNotebookImporter.get_days(self, tempdir):
            yield day

        # Cleanup
        logging.info('Remove tempdir')
        shutil.rmtree(tempdir)
        zip_archive.close()


class TomboyImporter(Importer):
    NAME = _('Tomboy Notes')
    DESCRIPTION = _('Import your Tomboy notes')
    PATHTEXT = _('Select the directory containing your tomboy notes')
    DEFAULTPATH = (os.getenv('XDG_DATA_HOME') or
        os.path.join(os.path.expanduser('~'), '.local', 'share', 'tomboy'))
    if sys.platform == 'win32':
        appdata = os.getenv('APPDATA')
        DEFAULTPATH = os.path.join(appdata, 'Tomboy', 'notes')
    elif sys.platform == 'darwin':
        DEFAULTPATH = os.path.join(os.path.expanduser('~'),
                            'Library', 'Application Support', 'Tomboy')
    PATHTYPE = 'DIR'

    def get_days(self, dir):
        '''
        We do not check if there are multiple notes for one day
        explicitly as they will just be concatted anyway
        '''
        import xml.etree.ElementTree as ET

        xmlns = '{http://beatniksoftware.com/tomboy}'

        # date has format 2010-05-07T12:41:37.1619220+02:00
        date_format = '%Y-%m-%d'

        files = self._get_files(dir)
        files = filter(lambda file: file.endswith('.note'), files)

        for file in files:
            path = os.path.join(dir, file)

            tree = ET.parse(path)

            date_string = tree.findtext(xmlns + 'create-date')
            short_date_string = date_string.split('T')[0]
            date = datetime.datetime.strptime(short_date_string, date_format)

            title = tree.findtext(xmlns + 'title')

            text = tree.findtext(xmlns + 'text/' + xmlns + 'note-content')

            day = ImportDay(date.year, date.month, date.day)
            day.text = '=== %s ===\n%s' % (title, text)
            yield day


def get_importers():
    importers = [cls for name, cls in globals().items()
                if name.endswith('Importer') and not name == 'Importer']

    # Filter and instantiate importers.
    return [imp() for imp in importers if imp.is_available()]



if __name__ == '__main__':
    '''
    Run some tests
    '''

    assistant = ImportAssistant(None)
    assistant.set_position(gtk.WIN_POS_CENTER)
    assistant.run()
    gtk.main()

    a = ImportDay(2010, 5, 7)
    a.text = 'a_text'
    a.add_category_entry('c1', 'e1')
    a.add_category_entry('c2', 'e2')
    a.add_category_entry('c4', 'e5')

    print a.content

    b = ImportDay(2010, 5, 7)
    b.text = 'b_text'
    b.add_category_entry('c1', 'e1')
    b.add_category_entry('c2', 'e3')
    b.add_category_entry('c3', 'e4')

    a.merge(b)
    a_tree = a.content.copy()

    a.merge(b)
    assert a_tree == a.content

    assert a.text == 'a_text\n\nb_text'
    assert a.tree == {'c1': {'e1': None}, 'c2': {'e2': None, 'e3': None},
            'c4': {'e5': None}, 'c3': {'e4': None}}, a.tree

    print 'ALL TESTS SUCCEEDED'


#plaintext_module = __import__('plaintext')
#print dir(plaintext_module)
#p = getattr(plaintext_module, 'aha')
#p = plaintext_module.PlainTextImporter()
