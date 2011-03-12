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

from __future__ import with_statement

import sys
import datetime
import os
import operator
import collections
import time
import logging
from optparse import OptionParser, OptionValueError


# Use basic stdout logging before we can initialize logging correctly
logging.basicConfig(level=logging.INFO,
                    format='%(levelname)-8s %(message)s',
                    stream=sys.stdout)


# Allow importing from rednotebook package
if hasattr(sys, "frozen"):
    from rednotebook.util import filesystem
else:
    from util import filesystem

base_dir = os.path.abspath(os.path.join(filesystem.app_dir, '../'))
if base_dir not in sys.path:
    # Adding BaseDir to sys.path
    sys.path.insert(0, base_dir)

#from rednotebook.util import filesystem # creates a copy of filesystem module
#import rednotebook.util.filesystem      # imports the original filesystem module


## ---------------------- Enable i18n -------------------------------

# We need to translate 3 different types of strings:
# * sourcecode strings
# * gtkbuilder strings
# * gtk stock names

# set the locale for all categories to the user’s default setting
# (typically specified in the LANG environment variable)
import locale
lang = os.environ.get('LANG', None)
logging.info('LANG: %s' % lang)
default_locale = locale.getdefaultlocale()[0]
logging.info('Default locale: %s' % default_locale)
try:
    locale.setlocale(locale.LC_ALL, '')
    logging.info('Set default locale: "%s"' % default_locale)
except locale.Error, err:
    # unsupported locale setting
    logging.error('Locale "%s" could not be set: "%s"' % (default_locale, err))
    logging.error('Probably you have to install the appropriate language packs')

# If the default locale could be determined and the LANG env variable
# has not been set externally, set LANG to the default locale
# This is necessary only for windows where program strings are not
# shown in the system language, but in English
if default_locale and not lang:
    logging.info('Setting LANG to %s' % default_locale)
    # sourcecode strings
    os.environ['LANG'] = default_locale

LOCALE_PATH = os.path.join(filesystem.app_dir, 'i18n')

# the name of the gettext domain. because we have our translation files
# not in a global folder this doesn't really matter, setting it to the
# application name is a good idea tough.
GETTEXT_DOMAIN = 'rednotebook'

# set up the gettext system
import gettext

# Adding locale to the list of modules translates gtkbuilder strings
modules = [#gettext,
            locale]

# Sometimes this doesn't work though,
# so we try to call gtk.glade's function as well if glade is present
try:
    import gtk.glade
    modules.append(gtk.glade)
    logging.info('Module glade found')
except ImportError, err:
    logging.info('Module glade not found: %s' % err)

for module in modules:
    try:
        # locale.bintextdomain and locale textdomain not available on win
        module.bindtextdomain(GETTEXT_DOMAIN, LOCALE_PATH)
        module.textdomain(GETTEXT_DOMAIN)
    except AttributeError, err:
        logging.info(err)

# register the gettext function for the whole interpreter as "_"
gettext.install(GETTEXT_DOMAIN, LOCALE_PATH, unicode=1)

## ------------------- end Enable i18n -------------------------------


from rednotebook.util import utils
from rednotebook import info
from rednotebook import configuration



def parse_options():
    parser = OptionParser(usage="usage: %prog [options] [journal-path]",
                          description=info.command_line_help,
                          version="RedNotebook %s" % info.version,
                          formatter=utils.IndentedHelpFormatterWithNL(),
                          )

    parser.add_option('-d', '--debug', dest='debug', default=False,
                      action='store_true', help='Output debugging messages'
                      ' (default: False)')

    parser.add_option('-m', '--minimized', dest='minimized', default=False,
                      action='store_true', help='Start mimimized to system tray'
                      ' (default: False)')

    options, args = parser.parse_args()

    return options, args

options, args = parse_options()



## ---------------------- Enable logging -------------------------------

def setup_logging(log_file):
    #logging_levels = {'debug': logging.DEBUG,
    #               'info': logging.INFO,
    #               'warning': logging.WARNING,
    #               'error': logging.ERROR,
    #               'critical': logging.CRITICAL}

    # File logging
    if sys.platform == 'win32' and hasattr(sys, "frozen"):
        utils.redirect_output_to_file(log_file)

    file_logging_stream = open(log_file, 'w')

    # We want to have the error messages in the logfile
    sys.stderr = utils.StreamDuplicator(sys.__stderr__, [file_logging_stream])

    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.DEBUG)

    # Python adds a default handler if some log is generated before here
    # Remove all handlers that have been added automatically
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

    # define a Handler which writes DEBUG messages or higher to the logfile
    filelog = logging.StreamHandler(file_logging_stream)
    filelog.setLevel(logging.DEBUG)
    filelog_formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    # tell the handler to use this format
    filelog.setFormatter(filelog_formatter)
    # add the handler to the root logger
    root_logger.addHandler(filelog)

    level = logging.INFO
    if options.debug:
        level = logging.DEBUG

    # define a Handler which writes INFO messages or higher to sys.stdout
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    root_logger.addHandler(console)

    logging.debug('sys.stdout logging level: %s' % level)
    logging.info('Writing log to file "%s"' % log_file)


default_config_file = os.path.join(filesystem.app_dir, 'files', 'default.cfg')
default_config = configuration.Config(default_config_file)

dirs = filesystem.Filenames(default_config)
setup_logging(dirs.log_file)

## ------------------ end Enable logging -------------------------------


try:
    import pygtk
    if not sys.platform == 'win32':
        pygtk.require("2.0")
except ImportError:
    logging.error('pygtk not found. Please install PyGTK (python-gtk2)')
    sys.exit(1)

try:
    import gtk
    import gobject
    # Some notes on threads_init:
    # only gtk.gdk.threads_init(): pdf export works, but gui hangs afterwards
    # only gobject.threads_init(): pdf export works, gui works
    # both: pdf export works, gui hangs afterwards
    gobject.threads_init() # only initializes threading in the glib/gobject module
    #gtk.gdk.threads_init() # also initializes the gdk threads
except (ImportError, AssertionError), e:
    logging.error(e)
    logging.error('gtk not found. Please install PyGTK (python-gtk2)')
    sys.exit(1)


# This version of import is needed for win32 to work
from rednotebook.util import dates
from rednotebook import backup

from rednotebook.util.statistics import Statistics
from rednotebook.gui.main_window import MainWindow
from rednotebook import storage
from rednotebook.data import Month


class Journal:
    def __init__(self):
        self.dirs = dirs

        user_config = configuration.Config(self.dirs.config_file)
        # Apply defaults where no custom values have been set
        for key, value in default_config.items():
            if key not in user_config:
                user_config[key] = value
        self.config = user_config
        self.config.save_state()

        logging.info('Running in portable mode: %s' % self.dirs.portable)

        self.testing = False
        if options.debug:
            self.testing = True
            logging.debug('Debug Mode is on')

        # Allow starting minimized to tray
        # When we start minimized we have to set the tray icon visible
        self.start_minimized = options.minimized
        if self.start_minimized:
            self.config['closeToTray'] = 1

        self.month = None
        self.date = None
        self.months = {}

        # The dir name is the title
        self.title = ''

        # show instructions at first start
        logging.info('First Start: %s' % self.dirs.is_first_start)

        logging.info('RedNotebook version: %s' % info.version)
        logging.info(filesystem.get_platform_info())

        utils.set_environment_variables(self.config)

        self.actual_date = datetime.date.today()

        # Let components check if the MainWindow has been created
        self.frame = None
        self.frame = MainWindow(self)

        self.open_journal(self.get_journal_path())

        self.archiver = backup.Archiver(self)

        # Check for a new version
        if self.config.read('checkForNewVersion', default=0) == 1:
            utils.check_new_version(self, info.version, startup=True)

        # Automatically save the content after a period of time
        if not self.testing:
            gobject.timeout_add_seconds(600, self.save_to_disk)


    def get_journal_path(self):
        '''
        Retrieve the path from optional args or return standard value if args
        not present
        '''
        if not args:
            data_dir = self.config.read('dataDir', self.dirs.data_dir)
            if not os.path.isabs(data_dir):
                data_dir = os.path.join(self.dirs.app_dir, data_dir)
                data_dir = os.path.normpath(data_dir)
            return data_dir

        # path_arg can be e.g. data (under .rednotebook), data (elsewhere),
        # or an absolute path /home/username/myjournal
        # Try to find the journal under the standard location or at the given
        # absolute or relative location
        path_arg = args[0]

        logging.debug('Trying to find journal "%s"' % path_arg)

        paths_to_check = [path_arg, os.path.join(self.dirs.journal_user_dir, path_arg)]

        for path in paths_to_check:
            if os.path.exists(path):
                if os.path.isdir(path):
                    return path
                else:
                    logging.warning('To open a journal you must specify a '
                                'directory, not a file.')

        logging.error('The path "%s" is no valid journal directory. '
                    'Execute "rednotebook -h" for instructions' % path_arg)
        sys.exit(1)


    def backup_contents(self, backup_file):
        self.save_to_disk()

        if backup_file:
            self.archiver.backup(backup_file)


    def exit(self):
        self.frame.add_values_to_config()

        # Make it possible to stop the program from exiting
        # e.g. if the journal could not be saved
        self.is_allowed_to_exit = True
        self.save_to_disk(exit_imminent=True)

        if self.is_allowed_to_exit:
            logging.info('Goodbye!')
            gtk.main_quit()


    def save_to_disk(self, exit_imminent=False, changing_journal=False, saveas=False):
        #logging.info('Trying to save the journal')

        self.save_old_day()

        try:
            filesystem.make_directory(self.dirs.data_dir)
        except OSError, err:
            self.frame.show_save_error_dialog(exit_imminent)
            return True

        if not os.path.exists(self.dirs.data_dir):
            logging.error('Save path does not exist')
            self.frame.show_save_error_dialog(exit_imminent)
            return True


        something_saved = storage.save_months_to_disk(self.months,
            self.dirs.data_dir, self.frame, exit_imminent, changing_journal, saveas)

        if something_saved:
            self.show_message(_('The content has been saved to %s') % self.dirs.data_dir, error=False)
            logging.info('The content has been saved to %s' % self.dirs.data_dir)
        else:
            self.show_message(_('Nothing to save'), error=False)
            #logging.info('Nothing to save')

        if self.config.changed():
            try:
                filesystem.make_directory(self.dirs.journal_user_dir)
                self.config.save_to_disk()
            except IOError, err:
                self.show_message(_('Configuration could not be saved. Please check your permissions'))
                logging.error('Configuration could not be saved. Please check your permissions')

        if not (exit_imminent or changing_journal) and something_saved:
            # Update cloud
            self.frame.cloud.update(force_update=True)

        # tell gobject to keep saving the content in regular intervals
        return True


    def open_journal(self, data_dir, load_files=True):

        if self.months:
            self.save_to_disk(changing_journal=True)

        # Password Protection
        #password = self.config.read('password', '')

        logging.info('Opening journal at %s' % data_dir)

        if not os.path.exists(data_dir):
            logging.warning('The data dir %s does not exist. Select a different dir.'
                        % data_dir)

            self.frame.show_dir_chooser('open', dir_not_found=True)
            return

        data_dir_empty = not os.listdir(data_dir)

        if not load_files and not data_dir_empty:
            msg_part1 = _('The selected folder is not empty.')
            msg_part2 = _('To prevent you from overwriting data, the folder content has been imported into the new journal.')
            self.show_message('%s %s' % (msg_part1, msg_part2), error=False)
        elif load_files and data_dir_empty:
            self.show_message(_('The selected folder is empty. A new journal has been created.'),
                                error=False)

        self.dirs.data_dir = data_dir

        self.month = None
        self.months.clear()

        # We always want to load all files
        if load_files or True:
            self.months = storage.load_all_months_from_disk(data_dir)

        # Nothing to save before first day change
        self.load_day(self.actual_date)

        self.stats = Statistics(self)

        sorted_categories = sorted(self.node_names, key=lambda category: str(category).lower())
        self.frame.categories_tree_view.categories = sorted_categories

        if self.dirs.is_first_start and data_dir_empty:
            logging.info('Adding example content')
            self.add_instruction_content()

        # Notebook is only on page 1 here, if we are opening a journal the second time
        old_page = self.frame.search_notebook.get_current_page()
        new_page = self.config.read('cloudTabActive', 1)
        # 0 -> 0: search is cleared later
        # 0 -> 1: change to cloud, update automatically
        # 1 -> 0: change to search
        # 1 -> 1: update cloud

        # At tab change, cloud is updated automatically
        self.frame.search_notebook.set_current_page(new_page)
        if new_page == old_page:
            # Without tab change, force update
            self.frame.cloud.update(force_update=True)

        # Reset Search
        self.frame.search_box.clear()

        self.title = filesystem.get_journal_title(data_dir)

        # Set frame title
        if self.title == 'data':
            frame_title = 'RedNotebook'
        else:
            frame_title = 'RedNotebook - ' + self.title
        self.frame.main_frame.set_title(frame_title)

        # Save the folder for next start
        if not self.dirs.portable:
            self.config['dataDir'] = data_dir
        else:
            rel_data_dir = filesystem.get_relative_path(self.dirs.app_dir, data_dir)
            self.config['dataDir'] = rel_data_dir


    def get_month(self, date):
        '''
        Returns the corresponding month if it has previously been visited,
        otherwise a new month is created and returned
        '''

        year_and_month = dates.get_year_and_month_from_date(date)

        # Selected month has not been loaded or created yet
        if not year_and_month in self.months:
            self.months[year_and_month] = Month(date.year, date.month)

        return self.months[year_and_month]


    def save_old_day(self):
        '''Order is important'''
        old_content = self.day.content
        self.day.content = self.frame.categories_tree_view.get_day_content()
        self.day.text = self.frame.get_day_text()

        content_changed = not (old_content == self.day.content)
        if content_changed:
            self.month.edited = True

        self.frame.calendar.set_day_edited(self.date.day, not self.day.empty)


    def load_day(self, new_date):
        old_date = self.date
        self.date = new_date

        if not Month.same_month(new_date, old_date) or self.month is None:
            self.month = self.get_month(self.date)
            #self.month.visited = True

        self.frame.set_date(self.month, self.date, self.day)


    def merge_days(self, days):
        '''
        Method used by importers
        '''
        self.save_old_day()
        for new_day in days:
            date = new_day.date
            month = self.get_month(date)
            old_day = month.get_day(date.day)
            old_day.merge(new_day)
            month.edited = True


    def _get_current_day(self):
        return self.month.get_day(self.date.day)
    day = property(_get_current_day)


    def change_date(self, new_date):
        if new_date == self.date:
            return

        self.save_old_day()
        self.load_day(new_date)


    def go_to_next_day(self):
        self.change_date(self.date + dates.one_day)


    def go_to_prev_day(self):
        self.change_date(self.date - dates.one_day)


    def show_message(self, message_text, error=False, countdown=True):
        self.frame.statusbar.show_text(message_text, error, countdown)


    @property
    def node_names(self):
        node_names = set([])
        for month in self.months.values():
            node_names |= set(month.node_names)
        return list(node_names)


    @property
    def tags(self):
        tags = set([])
        for month in self.months.values():
            tags |= set(month.tags)
        return list(tags)


    def search(self, text=None, category=None, tag=None):
        results = []
        for day in self.days:
            result = None
            if text:
                result = day.search_text(text)
            elif category:
                result = day.search_category(category)
            elif tag:
                result = day.search_tag(tag)

            if result:
                if category:
                    results.extend(result)
                else:
                    results.append(result)

        return results


    @property
    def days(self):
        '''
        Returns all edited days ordered by their date
        '''
        # The day being edited counts too
        if self.frame:
            self.save_old_day()

        days = []
        for month in self.months.values():
            days_in_month = month.days.values()

            # Filter out days without content
            days_in_month = [day for day in days_in_month if not day.empty]
            days.extend(days_in_month)

        # Sort days
        days = sorted(days, key=lambda day: day.date)
        return days


    def get_word_count_dict(self, type):
        '''
        Returns a dictionary mapping the words to their number of appearance
        '''
        word_dict = collections.defaultdict(int)
        for day in self.days:
            if type == 'word':
                words = day.words
            if type == 'category':
                words = day.node_names
            if type == 'tag':
                words = day.tags

            for word in words:
                word_dict[word.lower()] += 1
        return word_dict


    def get_days_in_date_range(self, range):
        start_date, end_date = range
        assert start_date <= end_date

        sorted_days = self.days
        days_in_date_range = []
        for day in sorted_days:
            if day.date < start_date:
                continue
            elif day.date >= start_date and day.date <= end_date:
                days_in_date_range.append(day)
            elif day.date > end_date:
                break
        return days_in_date_range


    def get_edit_date_of_entry_number(self, entry_number):
        sorted_days = self.days
        if len(sorted_days) == 0:
            return datetime.date.today()
        return sorted_days[entry_number % len(sorted_days)].date


    def go_to_first_empty_day(self):
        if len(self.days) == 0:
            return datetime.date.today()

        last_edited_day = self.days[-1]
        first_empty_date = last_edited_day.date + dates.one_day
        self.change_date(first_empty_date)


    def add_instruction_content(self):
        self.go_to_first_empty_day()
        current_date = self.date

        for example_day in info.example_content:
            self.day.content = example_day
            self.frame.set_date(self.month, self.date, self.day)
            self.go_to_next_day()

        self.change_date(current_date)



def main():
    start_time = time.time()
    journal = Journal()
    utils.setup_signal_handlers(journal)
    end_time = time.time()
    logging.debug('Start took %s seconds' % (end_time - start_time))

    try:
        logging.debug('Trying to enter the gtk main loop')
        gtk.main()
        #logging.debug('Closing logfile')
        #file_logging_stream.close()
    except KeyboardInterrupt:
        # 'Interrupt'
        #journal.save_to_disk()
        sys.exit()


if __name__ == '__main__':
    main()

