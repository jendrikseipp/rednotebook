# -----------------------------------------------------------------------
# Copyright (c) 2008-2024 Jendrik Seipp
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

from rednotebook.data import Month


try:
    import yaml
except ImportError:
    logging.error("PyYAML not found. Please install it (python3-yaml).")
    sys.exit(1)

try:
    from yaml import CLoader as Loader
    from yaml import CSafeDumper as Dumper

    logging.info("Using LibYAML")
except ImportError:
    from yaml import Dumper, Loader

    logging.info("Using PyYAML")


def format_year_and_month(year, month):
    return f"{year:04d}-{month:02d}"


def get_journal_files(data_dir):
    # Format: 2010-05.txt
    date_exp = re.compile(r"(\d{4})-(\d{2})\.txt$")

    for file in sorted(os.listdir(data_dir)):
        if match := date_exp.match(file):
            year = int(match[1])
            month = int(match[2])
            assert month in range(1, 12 + 1)
            path = os.path.join(data_dir, file)
            yield (path, year, month)
        else:
            logging.debug(f"{file} is not a valid month filename")


def _load_month_from_disk(path, year_number, month_number):
    """
    Load the month file at path and return a month object

    If an error occurs, return None
    """
    try:
        # Try to read the contents of the file.
        with codecs.open(path, "rb", encoding="utf-8") as month_file:
            logging.debug(f'Loading file "{path}"')
            month_contents = yaml.load(month_file, Loader=Loader)
            return Month(
                year_number,
                month_number,
                month_contents,
                os.path.getmtime(path),
            )
    except yaml.YAMLError as exc:
        logging.error(f"Error in file {path}:\n{exc}")
    except OSError:
        # If that fails, there is nothing to load, so just display an error message.
        logging.error(f"Error: The file {path} could not be read")
    except Exception:
        logging.error(f"An error occurred while reading {path}:")
        raise
    # If we continued here, the possibly corrupted file would be overwritten.
    sys.exit(1)


def load_all_months_from_disk(data_dir):
    """
    Load all months and return a directory mapping year-month values
    to month objects.
    """
    months = {}

    logging.debug(f'Starting to load files in dir "{data_dir}"')
    for path, year_number, month_number in get_journal_files(data_dir):
        if month := _load_month_from_disk(path, year_number, month_number):
            months[format_year_and_month(year_number, month_number)] = month

    logging.debug(f'Finished loading files in dir "{data_dir}"')
    return months


def _get_dict(month):
    return {day_number: day.content for day_number, day in month.days.items() if not day.empty}


def _save_month_to_disk(month, journal_dir):
    """
    Return whether data was written to disk.

    When overwriting 2014-12.txt:
        write new content to 2014-12.new.txt
        check that new file is valid month file
        cp 2014-12.txt 2014-12.old.txt
        mv 2014-12.new.txt 2014-12.txt
        rm 2014-12.old.txt
    """
    content = _get_dict(month)

    def get_filename(infix):
        year_and_month = format_year_and_month(month.year_number, month.month_number)
        return os.path.join(journal_dir, f"{year_and_month}{infix}.txt")

    old = get_filename(".old")
    new = get_filename(".new")
    filename = get_filename("")

    # Do not save empty month files.
    if not content and not os.path.exists(filename):
        return False

    with codecs.open(new, "wb", encoding="utf-8") as f:
        # Write readable unicode and no Python directives.
        yaml.dump(content, f, Dumper=Dumper, allow_unicode=True)

    # Check that month file was written to disk successfully.
    written_month = _load_month_from_disk(new, month.year_number, month.month_number)
    if _get_dict(written_month) != content:
        try:
            os.remove(new)
        except OSError:
            pass
        raise OSError("writing month file to disk failed")

    if os.path.exists(filename):
        mtime = os.path.getmtime(filename)
        if mtime != month.mtime:
            conflict = get_filename(f".CONFLICT_BACKUP{mtime}")
            logging.debug(
                f"Last edit time of {filename} conflicts with edit time at file load\n"
                f"--> Backing up to {conflict}"
            )
            shutil.copy2(filename, conflict)
        shutil.copy2(filename, old)
    # Prevent save failures on network and cloud drives.
    if os.path.exists(filename):
        os.remove(filename)
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
    logging.info(f"Wrote file {filename}")
    return True


def save_months_to_disk(months, journal_dir, exit_imminent=False, saveas=False):
    """
    Update the journal on disk and return if something had to be written.
    """
    something_saved = False
    for month in months.values():
        # We always need to save everything when we are "saving as".
        if month.edited or saveas:
            something_saved |= _save_month_to_disk(month, journal_dir)

    return something_saved
