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

import codecs
import logging
import os
import re
import shutil
import stat
import sys


try:
    import yaml
except ImportError:
    logging.error('PyYAML not found. Please install it (python-yaml).')
    sys.exit(1)

# The presence of the yaml module has been checked
try:
    from yaml import CLoader as Loader
    from yaml import CSafeDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
    logging.info('Using pyyaml for loading and dumping')

from rednotebook.data import Month


def format_year_and_month(year, month):
    return '%04d-%02d' % (year, month)


def get_journal_files(data_dir):
    # Format: 2010-05.txt
    date_exp = re.compile(r'(\d{4})-(\d{2})\.txt$')

    for file in sorted(os.listdir(data_dir)):
        match = date_exp.match(file)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            assert month in range(1, 12 + 1)
            path = os.path.join(data_dir, file)
            yield (path, year, month)
        else:
            logging.debug('%s is not a valid month filename' % file)


def _load_month_from_disk(path, year_number, month_number):
    '''
    Load the month file at path and return a month object

    If an error occurs, return None
    '''
    try:
        # Try to read the contents of the file.
        with codecs.open(path, 'rb', encoding='utf-8') as month_file:
            logging.debug('Loading file "%s"' % path)
            month_contents = yaml.load(month_file, Loader=Loader)
            month = Month(year_number, month_number, month_contents, os.path.getmtime(path))
            return month
    except yaml.YAMLError, exc:
        logging.error('Error in file %s:\n%s' % (path, exc))
    except IOError:
        # If that fails, there is nothing to load, so just display an error message.
        logging.error('Error: The file %s could not be read' % path)
    except Exception:
        logging.error('An error occured while reading %s:' % path)
        raise
    # If we continued here, the possibly corrupted file would be overwritten.
    sys.exit(1)


def load_all_months_from_disk(data_dir):
    '''
    Load all months and return a directory mapping year-month values
    to month objects.
    '''
    months = {}

    logging.debug('Starting to load files in dir "%s"' % data_dir)
    for path, year_number, month_number in get_journal_files(data_dir):
        month = _load_month_from_disk(path, year_number, month_number)
        if month:
            months[format_year_and_month(year_number, month_number)] = month

    logging.debug('Finished loading files in dir "%s"' % data_dir)
    return months


def _save_month_to_disk(month, journal_dir):
    """
    When overwriting 2014-12.txt:
        write new content to 2014-12.new.txt
        cp 2014-12.txt 2014-12.old.txt
        mv 2014-12.new.txt 2014-12.txt
        rm 2014-12.old.txt
    """
    content = {}
    for day_number, day in month.days.iteritems():
        if not day.empty:
            content[day_number] = day.content

    def get_filename(infix):
        year_and_month = format_year_and_month(month.year_number, month.month_number)
        return os.path.join(journal_dir, '%s%s.txt' % (year_and_month, infix))

    old = get_filename('.old')
    new = get_filename('.new')
    filename = get_filename('')

    # Do not save empty month files.
    if not content and not os.path.exists(filename):
        return False

    with codecs.open(new, 'wb', encoding='utf-8') as f:
        # Write readable unicode and no Python directives.
        yaml.dump(content, f, Dumper=Dumper, allow_unicode=True)

    if os.path.exists(filename):
        mtime = os.path.getmtime(filename)
        if mtime != month.mtime:
            conflict = get_filename('.CONFLICT_BACKUP' + str(mtime))
            logging.debug('Last edit time of %s conflicts with edit time at file load\n'
                          '--> Backing up to %s' % (filename, conflict))
            shutil.copy2(filename, conflict)
        shutil.copy2(filename, old)
    shutil.move(new, filename)
    if os.path.exists(old):
        os.remove(old)

    try:
        # Make file readable and writable only by the owner.
        os.chmod(filename, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass

    month.edited = False
    month.mtime = os.path.getmtime(filename)
    logging.info('Wrote file %s' % filename)
    return True


def save_months_to_disk(months, journal_dir, exit_imminent=False, saveas=False):
    '''
    Update the journal on disk and return if something had to be written.
    '''
    something_saved = False
    for year_and_month, month in months.items():
        # We always need to save everything when we are "saving as".
        if month.edited or saveas:
            something_saved |= _save_month_to_disk(month, journal_dir)

    return something_saved
