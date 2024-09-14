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

import logging
import os

from rednotebook.util import filesystem


def delete_comment(line):
    return "" if line.startswith("#") else line


class Config(dict):
    defaults = {
        # mingliu and MS Mincho are required for displaying Asian fonts
        # in preview mode on Windows.
        "previewFont": "Ubuntu, mingliu, MS Mincho, sans-serif",
        "autoSwitchMode": 0,
        "closeToTray": 0,
        "checkForNewVersion": 0,
        "dateTimeString": "%A, %x %X",
        "exportDateFormat": "%A, %x",
        "showTagsPane": 0,
        "weekNumbers": 0,
        "portable": 0,
        "userDir": "",
        "firstStart": 1,
        "instantSearch": 1,
        "spellcheck": 0,
        "mainFrameWidth": 1024,
        "mainFrameHeight": 700,
        "mainFrameMaximized": 0,
        "mainFrameX": None,
        "mainFrameY": None,
        "leftDividerPosition": 260,
        "rightDividerPosition": None,
        "cloudMaxTags": 1000,
        "autoIndent": 1,
    }

    obsolete_keys = {
        "useGTKMozembed",
        "useWebkit",
        "LD_LIBRARY_PATH",
        "MOZILLA_FIVE_HOME",
        "cloudTabActive",
        "mainFontSize",
        "running",
    }

    # Allow changing the value of portable only in default.cfg.
    suppressed_keys = {"portable", "user_dir"}

    def __init__(self, config_file):
        dict.__init__(self)

        self.filename = config_file

        self.update(self._read_file(self.filename))
        self.save_state()

    def save_state(self):
        """Save a copy of the dir to check for changes later"""
        self.old_config = self.copy()

    def _read_file(self, filename):
        content = filesystem.read_file(filename)

        # Delete comments and whitespace.
        lines = [delete_comment(line.strip()) for line in content.splitlines()]

        dictionary = {}

        for line in lines:
            if "=" not in line:
                continue
            pair = line.partition("=")[::2]
            key, value = (s.strip() for s in pair)
            # Skip obsolete keys to prevent rewriting them to disk.
            if key in self.obsolete_keys:
                continue

            try:
                value = int(value)
            except ValueError:
                pass

            dictionary[key] = value

        return dictionary

    def read(self, key, default=None):
        """
        Get the stored value for the given key.

        If *default* is omitted, there must be a default for *key* in
        Config.defaults. If *default* is given and there is no value
        stored for *key*, set the stored value to *default*.
        """
        if default is None:
            default = self.defaults[key]
        return self.setdefault(key, default)

    def read_list(self, key, default):
        """
        Read the string corresponding to key and convert it to a list.

        alpha,beta gamma;delta -> ['alpha', 'beta', 'gamma', 'delta']

        default should be of the form 'alpha,beta gamma;delta'
        """
        string = str(self.read(key, default))

        separators = [",", ";"]
        for separator in separators:
            string = string.replace(separator, " ")

        strings = [s.strip() for s in string.split()]
        return [s for s in strings if s]

    def write_list(self, key, list):
        self[key] = ", ".join(list)

    def changed(self):
        return self != self.old_config

    def save_to_disk(self):
        if not self.changed():
            return

        lines = [
            f"{key}={value}"
            for key, value in sorted(self.items())
            if key not in self.suppressed_keys
        ]
        try:
            filesystem.make_directory(os.path.dirname(self.filename))
            filesystem.write_file(self.filename, "\n".join(lines))
        except OSError:
            logging.error(
                "Configuration could not be saved. Please check " "your permissions"
            )
        else:
            logging.info(f"Configuration has been saved to {self.filename}")
            self.save_state()
