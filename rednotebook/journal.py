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
import time
import itertools
import logging
import locale
from optparse import OptionParser
from collections import defaultdict


# Use basic stdout logging before we can initialize logging correctly
logging.basicConfig(level=logging.INFO,
                    format='%(levelname)-8s %(message)s',
                    stream=sys.stdout)


# Allow importing from rednotebook package
if hasattr(sys, "frozen"):
    from rednotebook.util import filesystem
else:
    from util import filesystem

# Add base directory to sys.path
base_dir = os.path.abspath(os.path.join(filesystem.app_dir, '../'))
sys.path.insert(0, base_dir)

#from rednotebook.util import filesystem # creates a copy of filesystem module
#import rednotebook.util.filesystem      # imports the original filesystem module
from rednotebook.external import elibintl


## ---------------------- Enable i18n -------------------------------

# We need to translate 3 different types of strings:
# * sourcecode strings
# * gtkbuilder strings
# * gtk stock names

LOCALE_PATH = filesystem.get_utf8_path(filesystem.locale_dir)

# the name of the gettext domain. because we have our translation files
# not in a global folder this doesn't really matter, setting it to the
# application name is a good idea tough.
GETTEXT_DOMAIN = 'rednotebook'

# Register _() as a global translation function and set up the translation
try:
    elibintl.install(GETTEXT_DOMAIN, LOCALE_PATH)
except locale.Error, err:
    # unsupported locale setting
    logging.error('Locale could not be set: "%s"' %  err)
    logging.error('Probably you have to install the appropriate language packs')

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
        self.is_first_start = self.config.read('firstStart', 1)
        self.config['firstStart'] = 0
        logging.info('First Start: %s' % bool(self.is_first_start))

        logging.info('RedNotebook version: %s' % info.version)
        logging.info(filesystem.get_platform_info())

        utils.set_environment_variables(self.config)

        self.actual_date = datetime.date.today()

        # Let components check if the MainWindow has been created
        self.frame = None
        self.frame = MainWindow(self)

        self.open_journal(self.get_journal_path())

        self.archiver = backup.Archiver(self)
        #self.archiver.check_last_backup_date()

        # Check for a new version
        if self.config.read('checkForNewVersion', 0) == 1:
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


    def exit(self):
        self.frame.add_values_to_config()

        self.config['running'] = 0

        # Make it possible to stop the program from exiting
        # e.g. if the journal could not be saved
        self.is_allowed_to_exit = True
        self.save_to_disk(exit_imminent=True)

        if self.is_allowed_to_exit:
            logging.info('Goodbye!')
            # Informs the logging system to perform an orderly shutdown by
            # flushing and closing all handlers.
            logging.shutdown()
            gtk.main_quit()


    def save_to_disk(self, exit_imminent=False, changing_journal=False, saveas=False):
        #logging.info('Trying to save the journal')

        self.save_old_day()

        try:
            filesystem.make_directory(self.dirs.data_dir)
        except OSError:
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

        self.config.save_to_disk()

        if not (exit_imminent or changing_journal) and something_saved:
            # Update cloud
            self.frame.cloud.update(force_update=True)

        # tell gobject to keep saving the content in regular intervals
        return True


    def open_journal(self, data_dir):

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

        if data_dir_empty:
            self.show_message(_('The selected folder is empty. A new journal has been created.'),
                                error=False)

        self.dirs.data_dir = data_dir

        self.month = None
        self.months.clear()

        self.months = storage.load_all_months_from_disk(data_dir)

        # Nothing to save before first day change
        self.load_day(self.actual_date)

        self.stats = Statistics(self)

        self.frame.categories_tree_view.categories = self.categories

        if self.is_first_start and data_dir_empty and len(self.days) == 0:
            self.add_instruction_content()

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


    @property
    def day(self):
        return self.month.get_day(self.date.day)


    def change_date(self, new_date):
        if new_date == self.date:
            return

        self.save_old_day()
        self.load_day(new_date)


    def go_to_next_day(self):
        next_date = self.date + dates.one_day
        following_edited_days = self.get_days_in_date_range(start_date=next_date)
        if following_edited_days:
            next_date = following_edited_days[0].date
        self.change_date(next_date)


    def go_to_prev_day(self):
        prev_date = self.date - dates.one_day
        previous_edited_days = self.get_days_in_date_range(end_date=prev_date)
        if previous_edited_days:
            prev_date = previous_edited_days[-1].date
        self.change_date(prev_date)


    def show_message(self, message_text, error=False, countdown=True):
        self.frame.statusbar.show_text(message_text, error, countdown)


    @property
    def categories(self):
        return list(sorted(set(itertools.chain.from_iterable(
                                        day.categories for day in self.days)),
                           key=utils.sort_asc))


    def get_entries(self, category):
        entries = set()
        for day in self.days:
            entries |= set(day.get_entries(category))
        return sorted(entries)


    def search(self, text, categories_only=False):
        results = []
        for day in reversed(self.days):
            results.append(day.search(text, categories_only=categories_only))
        return results


    def get_word_count_dict(self):
        '''
        Returns a dictionary mapping the words to their number of appearance
        '''
        word_dict = defaultdict(int)
        for day in self.days:
            words = day.get_words()
            for word in words:
                word_dict[word.lower()] += 1
        return word_dict


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


    def get_days_in_date_range(self, start_date=None, end_date=None):
        if not start_date:
            start_date = datetime.date.min
        if not end_date:
            end_date = datetime.date.max

        start_date, end_date = sorted([start_date, end_date])
        assert start_date <= end_date

        days_in_date_range = []
        for day in self.days:
            if day.date < start_date:
                continue
            elif start_date <= day.date <= end_date:
                days_in_date_range.append(day)
            elif day.date > end_date:
                break
        return days_in_date_range


    def add_instruction_content(self):
        self.change_date(datetime.date.today())
        current_date = self.date

        logging.info('Adding example content on %s' % current_date)

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
    except KeyboardInterrupt:
        # 'Interrupt'
        #journal.save_to_disk()
        sys.exit()


if __name__ == '__main__':
    main()

