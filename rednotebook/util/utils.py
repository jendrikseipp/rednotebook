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

from __future__ import with_statement, division

import sys
import signal
import os
import re
from urllib2 import urlopen, URLError
import webbrowser
import logging
from optparse import IndentedHelpFormatter
import textwrap
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


def redirect_output_to_file(logfile_path):
    """
    Changes stdout and stderr to a file.
    Disables both streams if logfile_path is None or cannot be opened.

    This is necessary to suppress the error messages on Windows when closing
    the application.
    """
    assert sys.platform == 'win32'

    if logfile_path is None:
        logfile = None
    else:
        try:
            logfile = open(logfile_path, 'w')
        except IOError:
            logging.info('logfile %s could not be found, disabling output' % logfile_path)
            logfile = None

    sys.stdout = logfile
    sys.stderr = logfile


def setup_signal_handlers(journal):
    """
    Catch abnormal exits of the program and save content to disk
    Look in signal man page for signal names

    SIGKILL cannot be caught
    SIGINT is caught again by KeyboardInterrupt
    """

    signals = []

    try:
        signals.append(signal.SIGHUP)  #Terminal closed, Parent process dead
    except AttributeError:
        pass
    try:
        signals.append(signal.SIGINT)  #Interrupt from keyboard (CTRL-C)
    except AttributeError:
        pass
    try:
        signals.append(signal.SIGQUIT) #Quit from keyboard
    except AttributeError:
        pass
    try:
        signals.append(signal.SIGABRT) #Abort signal from abort(3)
    except AttributeError:
        pass
    try:
        signals.append(signal.SIGTERM) #Termination signal
    except AttributeError:
        pass
    try:
        signals.append(signal.SIGTSTP) #Stop typed at tty
    except AttributeError:
        pass


    def signal_handler(signum, frame):
        logging.info('Program was abnormally aborted with signal %s' % signum)
        journal.exit()


    msg = 'Connected Signals: '

    for signal_number in signals:
        try:
            msg += str(signal_number) + ' '
            signal.signal(signal_number, signal_handler)
        except RuntimeError:
            msg += '\n_false Signal Number: ' + signal_number

    logging.info(msg)


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
    except URLError:
        return None


def check_new_version(journal, current_version, startup=False):
    new_version = get_new_version_number()

    if new_version:
        new_version = StrictVersion(new_version)
    else:
        logging.error('New version info could not be read')
        new_version = 'unknown'

    current_version = StrictVersion(current_version)
    # Only compare versions if new version could be read
    newer_version_available = ((new_version > current_version)
                    if isinstance(new_version, StrictVersion) else True)
    logging.info('A newer version is available: %s' % newer_version_available)

    if newer_version_available or not startup:
        dialog = gtk.MessageDialog(parent=None, flags=gtk.DIALOG_MODAL,
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_YES_NO, message_format=None)
        dialog.set_transient_for(journal.frame.main_frame)
        primary_text = (_('You have version <b>%s</b>.') % current_version +
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
    def __init__(self, default, duplicates):
        if not type(duplicates) == list:
            duplicates = [duplicates]
        self.duplicates = duplicates
        self.default = default

    @property
    def streams(self):
        return [self.default] + self.duplicates

    def write(self, str):
        for stream in self.streams:
            stream.write(str)

    def flush(self):
        for stream in self.streams:
            stream.flush()

    #def close(self):
    #   for stream in self.streams():
    #       self.stream.close()



class IndentedHelpFormatterWithNL(IndentedHelpFormatter):
    """
    Code taken from "Dan"
    http://groups.google.com/group/comp.lang.python/browse_frm/thread/e72deee779d9989b/

    This class preserves newlines in the optparse help
    """
    def format_description(self, description):
        if not description: return ""
        desc_width = self.width - self.current_indent
        indent = " "*self.current_indent
        # the above is still the same
        bits = description.split('\n')
        formatted_bits = [
            textwrap.fill(bit,
                desc_width,
                initial_indent=indent,
                subsequent_indent=indent)
            for bit in bits]
        result = "\n".join(formatted_bits) + "\n"
        return result

    def format_option(self, option):
        # The help for each option consists of two parts:
        #    * the opt strings and metavars
        #    eg. ("-x", or "-f FILENAME, --file=FILENAME")
        #    * the user-supplied help string
        #    eg. ("turn on expert mode", "read data from FILENAME")
        #
        # If possible, we write both of these on the same line:
        #    -x     turn on expert mode
        #
        # But if the opt string list is too long, we put the help
        # string on a second line, indented to the same column it would
        # start in if it fit on the first line.
        #    -f FILENAME, --file=FILENAME
        #            read data from FILENAME
        result = []
        opts = self.option_strings[option]
        opt_width = self.help_position - self.current_indent - 2
        if len(opts) > opt_width:
            opts = "%*s%s\n" % (self.current_indent, "", opts)
            indent_first = self.help_position
        else: # start help on same line as opts
            opts = "%*s%-*s " % (self.current_indent, "", opt_width, opts)
            indent_first = 0
        result.append(opts)
        if option.help:
            help_text = option.help
            # Everything is the same up through here
            help_lines = []
            help_text = "\n".join([x.strip() for x in
                                help_text.split("\n")])
            for para in help_text.split("\n\n"):
                help_lines.extend(textwrap.wrap(para, self.help_width))
                if len(help_lines):
                    # for each paragraph, keep the double newlines..
                    help_lines[-1] += "\n"
                    # Everything is the same after here
            result.append("%*s%s\n" % (
                indent_first, "", help_lines[0]))
            result.extend(["%*s%s\n" % (self.help_position, "", line)
                for line in help_lines[1:]])
        elif opts[-1] != "\n":
            result.append("\n")
        return "".join(result)
