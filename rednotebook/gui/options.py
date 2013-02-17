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

import os
import sys
import logging
import platform

import gtk

from rednotebook.gui.customwidgets import UrlButton, CustomComboBoxEntry
from rednotebook.gui.customwidgets import ActionButton
from rednotebook.util import filesystem, utils, dates
from rednotebook import info


class Option(gtk.HBox):
    def __init__(self, text, option_name, tooltip=''):
        gtk.HBox.__init__(self)

        self.text = text
        self.option_name = option_name

        self.set_spacing(5)

        self.label = gtk.Label(self.text)
        self.pack_start(self.label, False, False)

        if tooltip:
            self.set_tooltip_text(tooltip)

    def get_value(self):
        raise NotImplementedError

    def get_string_value(self):
        return unicode(self.get_value())


class TickOption(Option):
    def __init__(self, text, name, value=None, default_value=0, tooltip=''):
        Option.__init__(self, '', name, tooltip=tooltip)

        self.check_button = gtk.CheckButton(text)

        if value is None:
            self.check_button.set_active(Option.config.read(name, default_value) == 1)
        else:
            self.check_button.set_active(value)

        self.pack_start(self.check_button, False)

    def get_value(self):
        return self.check_button.get_active()

    def get_string_value(self):
        '''
        We use 0 and 1 internally for bool options
        '''
        return int(self.get_value())


class AutostartOption(TickOption):
    def __init__(self):
        home_dir = os.path.expanduser('~')
        autostart_dir = os.path.join(home_dir, '.config/autostart/')
        self.autostart_file = os.path.join(autostart_dir, 'rednotebook.desktop')
        autostart_file_exists = os.path.exists(self.autostart_file)
        TickOption.__init__(self, _('Load RedNotebook at startup'), None,
                            value=autostart_file_exists)

    def get_value(self):
        return self.check_button.get_active()

    def set(self):
        '''Apply the current setting'''
        selected = self.get_value()

        if selected:
            # Add autostart file if it is not present
            filesystem.make_file_with_dir(self.autostart_file, info.desktop_file)
        else:
            # Remove autostart file
            if os.path.exists(self.autostart_file):
                os.remove(self.autostart_file)


#class TextOption(Option):
#   def __init__(self, text, name):
#       self.entry = gtk.Entry(30)
#       self.entry.set_text(Option.config.read(name, ''))
#
#       Option.__init__(self, text, name, self.entry)
#
#   def get_value(self):
#       return self.entry.get_text()

class CsvTextOption(Option):
    def __init__(self, text, option_name, **kwargs):
        Option.__init__(self, text, option_name, **kwargs)

        # directly read the string, not the list
        values_string = Option.config.read(option_name, '')

        # Ensure that we have a string here
        values_string = unicode(values_string)

        self.entry = gtk.Entry()
        self.entry.set_text(values_string)

        self.pack_start(self.entry, True)

    def get_value(self):
        return self.entry.get_text().decode('utf-8')


#class TextAndButtonOption(TextOption):
#   def __init__(self, text, name, button):
#       TextOption.__init__(self, text, name)

#       self.widget.pack_end(button, False, False)


class ComboBoxOption(Option):
    def __init__(self, text, name, entries):
        Option.__init__(self, text, name)

        self.combo = CustomComboBoxEntry(gtk.ComboBoxEntry())
        self.combo.set_entries(entries)

        self.pack_start(self.combo.combo_box, False)

    def get_value(self):
        return self.combo.get_active_text()


class DateFormatOption(ComboBoxOption):
    def __init__(self, text, name):
        date_formats = ['%A, %x %X', _('%A, %x, Day %j'), '%H:%M', _('Week %W of Year %Y'),
                        '%y-%m-%d', _('Day %j'), '%A', '%B']

        ComboBoxOption.__init__(self, text, name, date_formats)

        date_url = 'http://docs.python.org/library/time.html#time.strftime'
        date_format_help_button = UrlButton(_('Help'), date_url)

        self.preview = gtk.Label()
        self.pack_start(self.preview, False)

        self.pack_end(date_format_help_button, False)

        # Set default format if not present
        format = Option.config.read(name, '%A, %x %X')
        format = unicode(format)
        self.combo.set_active_text(format)

        self.combo.connect('changed', self.on_format_changed)

        # Update the preview
        self.on_format_changed(None)

    def on_format_changed(self, widget):
        format_string = self.get_value()
        date_string = dates.format_date(format_string)
        ### Translators: Noun
        label_text = u'%s %s' % (_('Preview:'), date_string)
        self.preview.set_text(label_text)


class FontSizeOption(ComboBoxOption):
    def __init__(self, text, name):
        sizes = range(6, 15) + range(16, 29, 2) + [32, 36, 40, 48, 56, 64, 72]
        sizes = ['default'] + map(str, sizes)

        ComboBoxOption.__init__(self, text, name, sizes)

        # Set default size if not present
        size = Option.config.read(name, -1)

        if size == -1:
            self.combo.set_active_text('default')
        else:
            self.combo.set_active_text(str(size))

        self.combo.set_editable(False)
        self.combo.combo_box.set_wrap_width(3)

        self.combo.connect('changed', self.on_combo_changed)

    def on_combo_changed(self, widget):
        '''Live update'''
        size = self.get_string_value()
        Option.main_window.set_font_size(size)

    def get_string_value(self):
        '''We use 0 and 1 internally for size options'''
        size = self.combo.get_active_text()
        if size == 'default':
            return -1
        try:
            return int(size)
        except ValueError:
            return -1


#class SpinOption(LabelAndWidgetOption):
#   def __init__(self, text, name):
#
#       adj = gtk.Adjustment(10.0, 6.0, 72.0, 1.0, 10.0, 0.0)
#       self.spin = gtk.SpinButton(adj)#, climb_rate=1.0)
#       self.spin.set_numeric(True)
#       self.spin.set_range(6,72)
#       self.spin.set_sensitive(True)
#       value = Option.config.read(name, -1)
#       if value >= 0:
#           self.spin.set_value(value)
#
#       LabelAndWidgetOption.__init__(self, text, name, self.spin)
#
#   def get_value(self):
#       return self.spin.get_value()
#
#   def get_string_value(self):
#       value = int(self.get_value())
#       return value


class OptionsDialog(object):
    def __init__(self, dialog):
        self.dialog = dialog
        self.categories = {}

    def __getattr__(self, attr):
        '''Wrap the dialog'''
        return getattr(self.dialog, attr)

    def add_option(self, category, option):
        self.categories[category].pack_start(option, False)
        option.show_all()

    def add_category(self, name, vbox):
        self.categories[name] = vbox

    def clear(self):
        for category, vbox in self.categories.items():
            for option in vbox.get_children():
                vbox.remove(option)


class OptionsManager(object):
    def __init__(self, main_window):
        self.main_window = main_window
        self.builder = main_window.builder
        self.journal = main_window.journal
        self.config = self.journal.config

        self.dialog = OptionsDialog(self.builder.get_object('options_dialog'))
        self.dialog.set_transient_for(self.main_window.main_frame)
        self.dialog.set_default_size(600, 300)
        self.dialog.add_category('general', self.builder.get_object('general_vbox'))

    def on_options_dialog(self):
        self.dialog.clear()

        # Make the config globally available
        Option.config = self.config
        Option.main_window = self.main_window

        self.options = []

        if platform.system() == 'Linux' and os.path.exists('/usr/bin/rednotebook'):
            logging.debug('Running on Linux. Is installed. Adding autostart option')
            self.options.insert(0, AutostartOption())

        # Most modern Linux distributions do not have a systray anymore.
        # If this option is activated on a system without a systray, the
        # application keeps on running in the background after it has been
        # closed. The option can still be activated in the configuration file.
        if sys.platform.startswith('win'):
            self.options.append(TickOption(_('Close to system tray'), 'closeToTray',
                tooltip=_('Closing the window will send RedNotebook to the tray')))

        # Automatic switching between preview and edit mode.
        self.options.append(TickOption(_('Switch between edit and preview mode automatically'),
                                       'autoSwitchMode', default_value=0))

        # Check for new version
        check_version_option = TickOption(_('Check for new version at startup'), 'checkForNewVersion')

        def check_version_action(widget):
            utils.check_new_version(self.main_window.journal, info.version)
            # Apply changes from dialog to options window
            check = bool(self.journal.config.get('checkForNewVersion'))
            check_version_option.check_button.set_active(check)

        check_version_button = ActionButton(_('Check now'), check_version_action)
        check_version_option.pack_start(check_version_button, False, False)
        self.options.append(check_version_option)

        self.options.extend([
            FontSizeOption(_('Font Size'), 'mainFontSize'),
            DateFormatOption(_('Date/Time format'), 'dateTimeString'),
            CsvTextOption(_('Exclude from cloud'), 'cloudIgnoreList',
                          tooltip=_('Do not show these comma separated words in the word cloud')),
            CsvTextOption(_('Include small words in cloud'), 'cloudIncludeList',
                          tooltip=_('Allow these words with 4 letters or less')),
        ])


        self.add_all_options()

        response = self.dialog.run()

        if response == gtk.RESPONSE_OK:
            self.save_options()

            # Apply some options
            self.main_window.cloud.update_lists()
            self.main_window.cloud.update(force_update=True)

            visible = (self.config.read('closeToTray', 0) == 1)
            self.main_window.tray_icon.set_visible(visible)
        else:
            # Reset some options
            self.main_window.set_font_size(self.config.read('mainFontSize', -1))

        self.dialog.hide()

    def add_all_options(self):
        for option in self.options:
            self.dialog.add_option('general', option)

    def save_options(self):
        logging.debug('Saving Options')
        for option in self.options:
            value = option.get_string_value()
            if option.option_name is not None:
                logging.debug('Setting %s = %s' % (option.option_name, repr(value)))
                self.config[option.option_name] = value
            else:
                # We don't save the autostart setting in the config file
                option.set()
