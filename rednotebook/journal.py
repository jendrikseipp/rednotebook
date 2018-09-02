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

from collections import defaultdict
import datetime
import itertools
import locale
import logging
import os
import sys
import time


# Use basic stdout logging before we can initialize logging correctly.
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)-8s %(message)s',
    stream=sys.stdout)

try:
    import gi
except ImportError as err:
    logging.error(
        'pygobject could not be imported: "{}". Please install it (python3-gi).'.format(err))
    sys.exit(1)

gi.require_version("Gtk", "3.0")
gi.require_version('GtkSource', '3.0')

if hasattr(sys, "frozen"):
    base_dir = sys._MEIPASS
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(app_dir)

print('Adding {} to sys.path'.format(base_dir))
sys.path.insert(0, base_dir)

from rednotebook.util import filesystem


# ---------------------- Enable i18n -------------------------------

from rednotebook.external import elibintl

LOCALE_PATH = filesystem.locale_dir

GETTEXT_DOMAIN = 'rednotebook'

"""
On Windows, translations currently only work with a hack. We need to
translate

  1) Strings in source code.
  2) GTK stock items.
  3) Strings in the Glade file.

1) works fine. For 3) we need a workaround in main_window.py. If we
initialize libintl with elibintl, the translations for 2) stop working.
Without the workaround we need to initalize libintl to avoid UTF-8
encoding errors.

When the problem is fixed upstream, we can pass libintl='libintl-8.dll'
to elibintl. See also

https://bugzilla.gnome.org/show_bug.cgi?id=574520
https://bugzilla.gnome.org/show_bug.cgi?id=753991
https://github.com/tobias47n9e/pygobject-locale
https://sourceforge.net/p/pygobjectwin32/tickets/27/

"""

elibintl.install(GETTEXT_DOMAIN, LOCALE_PATH, libintl=None)

# ------------------- end Enable i18n -------------------------------


from rednotebook.util import utils
from rednotebook.util import markup
from rednotebook.help import example_content
from rednotebook import info
from rednotebook import configuration
from rednotebook import data


args = info.get_commandline_parser().parse_args()

# ---------------------- Enable logging -------------------------------


def setup_logging(log_file):
    file_logging_stream = open(log_file, 'w')

    # We want to have all stdout and stderr messages in the logfile.
    # In the frozen version we cannot log to sys.stderr because it's
    # broken on windows. Stdout doesn't work either it seems.
    stderr_streams = [file_logging_stream]
    stdout_streams = [file_logging_stream]
    if not filesystem.main_is_frozen():
        stderr_streams.append(sys.__stderr__)
        stdout_streams.append(sys.__stdout__)
    sys.stderr = utils.StreamDuplicator(stderr_streams)
    sys.stdout = utils.StreamDuplicator(stdout_streams)

    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.DEBUG)

    # Python adds a default handler if some log is generated before here
    # Remove all handlers that have been added automatically
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

    # define a Handler which writes messages to sys.stdout
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    root_logger.addHandler(console)

    logging.info('Writing log to file "%s"' % log_file)


default_config_file = os.path.join(filesystem.app_dir, 'files', 'default.cfg')
default_config = configuration.Config(default_config_file)

dirs = filesystem.Filenames(default_config)
setup_logging(dirs.log_file)

# ------------------ end Enable logging -------------------------------

logging.info('System encoding: %s' % filesystem.ENCODING)
logging.info('Language code: %s' % filesystem.LANGUAGE)

try:
    from gi.repository import Gtk
    from gi.repository import GObject
except (ImportError, AssertionError) as e:
    logging.error(e)
    logging.error('GTK+ not found. Please install it (gir1.2-gtk-3.0).')
    sys.exit(1)

GObject.threads_init()


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

        self.month = None
        self.date = None
        self.months = {}

        # The dir name is the title
        self.title = ''

        # show instructions at first start
        self.is_first_start = self.config.read('firstStart')
        self.config['firstStart'] = 0
        logging.info('First Start: %s' % bool(self.is_first_start))

        logging.info('RedNotebook version: %s' % info.version)
        logging.info(filesystem.get_platform_info())

        self.actual_date = self.get_start_date()

        # Let components check if the MainWindow has been created
        self.frame = None
        self.frame = MainWindow(self)

        journal_path = self.get_journal_path()
        if not self.dirs.is_valid_journal_path(journal_path):
            logging.error('Invalid directory: %s. Using default journal.' % journal_path)
            self.show_message(_('You cannot use this directory for your journal:') +
                              ' %s' % journal_path + '. ' + _('Opening default journal.'),
                              error=True)
            journal_path = self.dirs.default_data_dir
        self.open_journal(journal_path)

        self.archiver = backup.Archiver(self)
        GObject.idle_add(self.archiver.check_last_backup_date)

        # Check for a new version
        if self.config.read('checkForNewVersion') == 1:
            utils.check_new_version(self, info.version, startup=True)

        # Automatically save the content after a period of time
        GObject.timeout_add_seconds(600, self.save_to_disk)

    def get_journal_path(self):
        '''
        Retrieve the path from optional args or return standard value if args
        not present
        '''
        if not args.journal:
            data_dir = self.config.read('dataDir', self.dirs.data_dir)
            if not os.path.isabs(data_dir):
                data_dir = os.path.join(self.dirs.app_dir, data_dir)
                data_dir = os.path.normpath(data_dir)
            return data_dir

        # path_arg can be e.g. data (under .rednotebook), data (elsewhere),
        # or an absolute path /home/username/myjournal
        # Try to find the journal under the standard location or at the given
        # absolute or relative location
        path_arg = args.journal

        logging.debug('Trying to find journal "%s"' % path_arg)

        paths_to_check = [path_arg, os.path.join(self.dirs.journal_user_dir, path_arg)]

        for path in paths_to_check:
            if os.path.exists(path):
                if os.path.isdir(path):
                    return path
                else:
                    logging.warning('To open a journal you must specify a '
                                    'directory, not a file.')

        logging.error('The path "%s" is not a valid journal directory. '
                      'Execute "rednotebook -h" for instructions' % path_arg)
        sys.exit(2)

    def get_start_date(self):
        '''
        Retrieve the date from optional args or otherwise return 'today'
        '''
        if not args.start_date:
            return datetime.date.today()

        try:
            return dates.get_date_from_date_string(args.start_date)
        except ValueError:
            logging.error('Invalid date: %s (required format: YYYY-MM-DD).' % args.start_date)
            sys.exit(2)

    def exit(self):
        self.frame.add_values_to_config()

        # Make it possible to stop the program from exiting
        # e.g. if the journal could not be saved
        self.is_allowed_to_exit = True
        self.save_to_disk(exit_imminent=True)

        if self.is_allowed_to_exit:
            logging.info('Goodbye!')
            # Informs the logging system to perform an orderly shutdown by
            # flushing and closing all handlers.
            logging.shutdown()
            Gtk.main_quit()

    def convert(self, text, target, headers=None, options=None):
        options = options or {}
        options['font'] = self.config.read('previewFont')
        return markup.convert(text, target, self.dirs.data_dir, headers=headers, options=options)

    def save_to_disk(self, exit_imminent=False, changing_journal=False, saveas=False):
        self.save_old_day()

        try:
            filesystem.make_directory(self.dirs.data_dir)
        except (OSError, IOError) as err:
            logging.error('Creating journal directory failed: {}'.format(err))
            self.frame.show_save_error_dialog(exit_imminent)
            return True

        try:
            something_saved = storage.save_months_to_disk(
                self.months, self.dirs.data_dir, exit_imminent, saveas)
        except (IOError, OSError) as err:
            logging.error('Saving month files failed: {}'.format(err))
            self.frame.show_save_error_dialog(exit_imminent)
            something_saved = None

        if something_saved:
            self.show_message(_('The content has been saved to %s') % self.dirs.data_dir, error=False)
            logging.info('The content has been saved to %r' % self.dirs.data_dir)
        elif something_saved is None:
            # Don't display this as an error, because we already show a dialog.
            self.show_message(_('The journal could not be saved'), error=False)
        else:
            self.show_message(_('Nothing to save'), error=False)

        self.config.save_to_disk()

        if not (exit_imminent or changing_journal) and something_saved:
            # Update cloud.
            self.frame.cloud.update(force_update=True)
            for tag in self.get_escaped_tags():
                self.frame.search_box.add_entry(tag)

        # tell gobject to keep saving the content in regular intervals
        return True

    def open_journal(self, data_dir):
        if not os.path.exists(data_dir):
            logging.warning('The dir %s does not exist. Select a different dir.'
                            % data_dir)
            return

        if self.months:
            self.save_to_disk(changing_journal=True)

        logging.info('Opening journal at %r' % data_dir)
        self.dirs.data_dir = data_dir

        self.month = None
        self.months.clear()
        self.frame.search_box.clear()

        self.months = storage.load_all_months_from_disk(data_dir)

        # Nothing to save before first day change
        self.load_day(self.actual_date)

        if self.is_first_start and not os.listdir(data_dir) and not self.days:
            self.add_instruction_content()

        self.stats = Statistics(self)

        self.frame.cloud.update(force_update=True)

        self.frame.categories_tree_view.categories = self.categories
        self.frame.search_box.set_entries(self.get_escaped_tags())

        self.title = filesystem.get_journal_title(data_dir)

        # Set frame title
        self.set_frame_title()

        # Save the folder for next start
        if not self.dirs.portable:
            self.config['dataDir'] = data_dir
        else:
            rel_data_dir = filesystem.get_relative_path(self.dirs.app_dir, data_dir)
            self.config['dataDir'] = rel_data_dir

    def set_frame_title(self):
        parts = ['RedNotebook']
        if self.title != 'data':
            parts.append(self.title)
        parts.append(dates.format_date(self.config.read('exportDateFormat'), self.date))
        self.frame.main_frame.set_title(' - '.join(parts))

    def get_month(self, date):
        '''
        Returns the corresponding month if it has previously been visited,
        otherwise a new month is created and returned
        '''

        year_and_month = dates.get_year_and_month_from_date(date)

        # Selected month has not been loaded or created yet
        if year_and_month not in self.months:
            self.months[year_and_month] = Month(date.year, date.month)

        return self.months[year_and_month]

    def get_day(self, date):
        return self.get_month(date).get_day(date.day)

    def get_escaped_tags(self):
        return ['#%s' % data.escape_tag(tag) for tag in self.categories]

    def save_old_day(self):
        '''Order is important'''
        old_content = self.day.content
        new_content = self.frame.categories_tree_view.get_day_content()
        new_content['text'] = self.frame.get_day_text()
        self.day.content = new_content

        content_changed = (old_content != new_content)
        if content_changed:
            self.month.edited = True

        self.frame.calendar.set_day_edited(self.date.day, not self.day.empty)

    def load_day(self, new_date):
        old_date = self.date
        self.date = new_date

        if not dates.same_month(new_date, old_date) or self.month is None:
            self.month = self.get_month(self.date)

        self.frame.set_date(self.month, self.date, self.day)

        self.set_frame_title()

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
        if new_date < datetime.date(1900, 1, 1):
            self.show_message('Only dates after 1900 are supported.',
                              title='Too Early', error=True)
            return

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

    def show_message(self, msg, title=None, error=False):
        if error and not title:
            title = _('Error')

        if error:
            msg_type = Gtk.MessageType.ERROR
            log_level = logging.ERROR
        else:
            msg_type = Gtk.MessageType.INFO
            log_level = logging.INFO

        self.frame.show_message(title, msg, msg_type)
        logging.log(log_level, '%s. %s' % (title, msg) if title else msg)

    @property
    def categories(self):
        return list(sorted(set(itertools.chain.from_iterable(
            day.categories for day in self.days)), key=locale.strxfrm))

    def get_entries(self, category):
        entries = set()
        for day in self.days:
            entries |= set(day.get_entries(category))
        return sorted(entries)

    def search(self, text, tags):
        results = []
        for day in reversed(self.get_days_with_tags(tags)):
            results.append(day.search(text, tags))
        return results

    def get_days_with_tags(self, tags):
        if not tags:
            return self.days
        days = []
        for day in self.days:
            day_tags = set(data.escape_tag(tag) for tag in day.categories)
            if all(tag in day_tags for tag in tags):
                days.append(day)
        return days

    def get_word_count_dict(self):
        """
        Return a dictionary mapping the words to their number of appearance.
        """
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
            # Filter out days without content.
            days_in_month = [day for day in month.days.values() if not day.empty]
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

        for example_day in example_content:
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
        Gtk.main()
    except KeyboardInterrupt:
        pass

    try:
        logging.info("Peak memory: {} KiB".format(filesystem.get_peak_memory_in_kb()))
    except Warning:
        pass


if __name__ == '__main__':
    main()
