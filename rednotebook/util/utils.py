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

import signal
import os
import re
import httplib
from urllib2 import urlopen
import webbrowser
import logging
from distutils.version import StrictVersion

import gtk

from rednotebook import info
import filesystem


def sort_asc(string):
    return str(string).lower()


def set_environment_variables(config):
    variables = {}

    for variable, value in variables.iteritems():
        if not variable in os.environ:
            # Only add environment variable if it does not exist yet
            os.environ[variable] = config.read(variable, default=value)
            logging.info('%s set to %s' % (variable, value))

    for variable in variables.keys():
        if variable in os.environ:
            logging.info('The environment variable %s has value %s' % (variable, os.environ.get(variable)))
        else:
            logging.info('There is no environment variable called %s' % variable)


def setup_signal_handlers(journal):
    """
    Catch abnormal exits of the program and save content to disk
    Look in signal man page for signal names

    SIGKILL cannot be caught
    SIGINT is caught again by KeyboardInterrupt
    """
    signals = []
    signal_names = [
        'SIGHUP',   # Terminal closed, Parent process dead
        'SIGINT',   # Interrupt from keyboard (CTRL-C)
        'SIGQUIT',  # Quit from keyboard
        'SIGABRT',  # Abort signal from abort(3)
        'SIGTERM',  # Termination signal
        'SIGTSTP',  # Stop typed at tty
    ]

    def signal_handler(signum, frame):
        logging.info('Program was abnormally aborted with signal %s' % signum)
        journal.exit()

    for signal_name in signal_names:
        signal_number = getattr(signal, signal_name, None)
        if signal_number is not None:
            try:
                signal.signal(signal_number, signal_handler)
                signals.append(signal_number)
            except RuntimeError:
                logging.info('Could not connect signal number %d' % signal_number)

    logging.info('Connected Signals: %s' % signals)


def get_new_version_number():
    """
    Reads version number from website and returns None if it cannot be read
    """
    version_pattern = re.compile(r'<span id="download-version">(.+)</span>')

    try:
        project_xml = urlopen('http://rednotebook.sourceforge.net/index.html').read()
        match = version_pattern.search(project_xml)
        if not match:
            return None
        new_version = match.group(1)
        logging.info('%s is the latest version' % new_version)
        return new_version
    except (IOError, httplib.HTTPException):
        return None


def check_new_version(journal, current_version, startup=False):
    new_version = get_new_version_number()

    if new_version:
        new_version = StrictVersion(new_version)
    else:
        logging.error('New version info could not be read')
        new_version = _('unknown')

    current_version = StrictVersion(current_version)
    # Only compare versions if new version could be read
    newer_version_available = True
    if isinstance(new_version, StrictVersion):
        newer_version_available = new_version > current_version
    logging.info('A newer version is available: %s' % newer_version_available)

    if newer_version_available or not startup:
        dialog = gtk.MessageDialog(parent=None, flags=gtk.DIALOG_MODAL,
                                   type=gtk.MESSAGE_INFO,
                                   buttons=gtk.BUTTONS_YES_NO,
                                   message_format=None)
        dialog.set_transient_for(journal.frame.main_frame)
        primary_text = (_('You have version <b>%s</b>.') % current_version + ' ' +
                        _('The latest version is <b>%s</b>.') % new_version)
        secondary_text = _('Do you want to visit the RedNotebook homepage?')
        dialog.set_markup(primary_text)
        dialog.format_secondary_text(secondary_text)

        # Let user disable checks
        if startup:
            # Add button on the left side
            dialog.add_button(_('Do not ask again'), 30)
            settings = gtk.settings_get_default()
            settings.set_property('gtk-alternative-button-order', True)

            dialog.set_alternative_button_order([30, gtk.RESPONSE_NO,
                                                 gtk.RESPONSE_YES])

        response = dialog.run()
        dialog.hide()

        if response == gtk.RESPONSE_YES:
            webbrowser.open(info.url)
        elif response == 30:
            logging.info('Checks for new versions disabled')
            journal.config['checkForNewVersion'] = 0


def show_html_in_browser(html, filename):
    filesystem.write_file(filename, html)

    html_file = os.path.abspath(filename)
    html_file = 'file://' + html_file
    webbrowser.open(html_file)


class StreamDuplicator(object):
    def __init__(self, streams):
        self.streams = streams

    def write(self, buf):
        for stream in self.streams:
            stream.write(buf)
            # If we don't flush here, stderr messages are printed late.
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()

    def close(self):
        for stream in self.streams():
            self.stream.close()
