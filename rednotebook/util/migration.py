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
# with this program.  If not, see <https://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------

"""Convert journals and templates from txt2tags to Markdown once.

The markup of a journal is stored in its journal.cfg file (see
configuration.JournalConfig). Journals without this setting use txt2tags and
are converted when RedNotebook opens them. The setting lives next to the
data, so a journal that is synced between computers is only converted once.
The user configuration stores whether the templates have been converted.
"""

import datetime
import html
import logging
import os
import re
import zipfile

from rednotebook import storage
from rednotebook.util import filesystem
from rednotebook.util.t2t_to_markdown import convert_inline, convert_to_markdown


MARKUP = "markup"
MARKDOWN = "markdown"
TXT2TAGS = "txt2tags"
TEMPLATE_MARKUP = "templateMarkup"
BACKUP_PREFIX = "RedNotebook-Backup-before-Markdown"


def needs_conversion(config, key=MARKUP):
    """Return whether the configured markup is txt2tags, the old default."""
    markup = config.get(key, TXT2TAGS)
    if markup not in (TXT2TAGS, MARKDOWN):
        logging.warning(f"Unknown markup {markup!r}, leaving the text unchanged")
    return markup == TXT2TAGS


def _unescape(markdown):
    markdown = re.sub(r"\\([!-/:-@\[-`{-~])", r"\1", markdown)
    return html.unescape(markdown)


def _convert_name(text):
    """Convert a tag name or tag entry.

    Names identify tags in the cloud and in searches, so keep them unchanged
    unless their txt2tags formatting has to be translated.
    """
    markdown = convert_inline(text)
    return text if _unescape(markdown) == text else markdown


def convert_text(text):
    """Convert txt2tags text, keeping text without markup byte-identical."""
    markdown = convert_to_markdown(text)
    return text if markdown == text.strip() else markdown


def convert_day_content(content):
    """Return a copy of a day's content dictionary with Markdown markup."""
    converted = {}
    for key, value in content.items():
        if key == "text":
            converted[key] = convert_text(value or "")
            continue
        name = _convert_name(key)
        if value is None:
            converted.setdefault(name, None)
            continue
        entries = converted.get(name) or {}
        for entry, entry_value in value.items():
            entries[_convert_name(entry)] = entry_value
        converted[name] = entries
    return converted


def convert_months(months):
    """Convert all days in place and return the number of converted days."""
    converted_days = 0
    for month in months.values():
        for day in month.days.values():
            new_content = convert_day_content(day.content)
            if new_content != day.content:
                day.content = new_content
                month.edited = True
                converted_days += 1
    return converted_days


def backup_directory(directory, name):
    """Zip the files in directory and return the path of the archive."""
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    archive = os.path.join(directory, f"{name}-{stamp}.zip")
    files = [
        file
        for file in sorted(os.listdir(directory))
        if os.path.isfile(os.path.join(directory, file)) and BACKUP_PREFIX not in file
    ]
    with zipfile.ZipFile(archive, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            zip_file.write(os.path.join(directory, file), file)
    logging.info(f"Backed up {len(files)} files to {archive}")
    return archive


def convert_journal(months, data_dir, journal_config):
    """Convert and save a txt2tags journal and store its new markup.

    Return the path of the backup archive, or None for empty journals.
    """
    backup = None
    if any(not month.empty for month in months.values()):
        backup = backup_directory(data_dir, BACKUP_PREFIX)
        converted_days = convert_months(months)
        logging.info(f"Converted {converted_days} days to Markdown")
    # The entries in memory use Markdown now, so a later save stores the
    # setting, even if saving fails below.
    journal_config[MARKUP] = MARKDOWN
    if backup:
        storage.save_months_to_disk(months, data_dir)
    journal_config.save_to(data_dir)
    return backup


def convert_templates(template_dir, config):
    """Convert the template files once and return the number of changed files.

    config is the user configuration, which is saved afterwards.
    """
    if not needs_conversion(config, TEMPLATE_MARKUP):
        return 0
    templates = [
        os.path.join(template_dir, file)
        for file in os.listdir(template_dir)
        if file.endswith(".txt")
    ]
    changed = {}
    for path in templates:
        text = filesystem.read_file(path)
        markdown = convert_text(text)
        if markdown != text:
            changed[path] = markdown
    if changed:
        backup_directory(template_dir, f"{BACKUP_PREFIX}-Templates")
        for path, markdown in changed.items():
            filesystem.write_file(path, markdown)
        logging.info(f"Converted {len(changed)} templates to Markdown")
    config[TEMPLATE_MARKUP] = MARKDOWN
    # Save right away to avoid converting the templates again after a crash.
    config.save_to_disk()
    return len(changed)
