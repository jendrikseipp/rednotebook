# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2012  Jendrik Seipp
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

from gi.repository import Gtk

from rednotebook.gui import customwidgets
from rednotebook.util import filesystem
from rednotebook.util import dates


MENUITEMS_XML = '''\
    <menuitem action="Picture"/>
    <menuitem action="File"/>
    <menuitem action="Link"/>
    <menuitem action="BulletList"/>
    <menuitem action="Title"/>
    <menuitem action="Line"/>
    <menuitem action="Date"/>
    <menuitem action="TimeInterval"/>
    <menuitem action="LineBreak"/>
'''

TOOLBAR_XML = '''\
<ui>
<popup action="InsertMenu">
%s
</popup>
</ui>
''' % MENUITEMS_XML

MENUBAR_XML = '''\
<menu action="InsertMenuBar">
%s
</menu>
''' % MENUITEMS_XML


def get_image(name):
    image = Gtk.Image()
    file_name = os.path.join(filesystem.image_dir, name)
    image.set_from_file(file_name)
    return image


class InsertMenu:
    def __init__(self, main_window):
        self.main_window = main_window

        self.bullet_list = (
            '\n- %s\n- %s\n  - %s (%s)\n\n\n' % (
                _('First Item'), _('Second Item'), _('Indented Item'),
                _('Two blank lines close the list')))

        self.setup()

    def setup(self):
        '''
        See http://www.pyGtk.org/pygtk2tutorial/sec-UIManager.html for help
        A popup menu cannot show accelerators (HIG).
        '''
        uimanager = self.main_window.uimanager

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.main_window.main_frame.add_accel_group(accelgroup)

        # Create an ActionGroup
        self.main_window.insert_actiongroup = Gtk.ActionGroup('InsertActionGroup')

        line = '\n====================\n'

        # table = ('\n|| Whitespace Left | Whitespace Right | Resulting Alignment |\n'
        #            '| 1               | more than 1     | Align left   |\n'
        #            '|     more than 1 |               1 |   Align right |\n'
        #            '|   more than 1   |   more than 1   |   Center   |\n'
        #            '|| Title rows | are always | centered |\n'
        #            '|  Use two vertical  |  lines on the left  |  for title rows  |\n'
        #            '|  Always use  |  at least  |  one whitespace  |\n')

        def tmpl(_letter):
            return ''  # return ' (Ctrl+%s)' % letter

        # Create actions
        self.main_window.insert_actiongroup.add_actions([
            ('Picture', Gtk.STOCK_ORIENTATION_PORTRAIT, _('Picture'),
                None, _('Insert an image from the harddisk'),
                self.get_insert_handler(self.on_insert_pic)),
            ('File', Gtk.STOCK_FILE, _('File'), None,
                _('Insert a link to a file'),
                self.get_insert_handler(self.on_insert_file)),
            # Translators: Noun
            ('Link', Gtk.STOCK_JUMP_TO, _('_Link') + tmpl('L'), '<Control>L',
                _('Insert a link to a website'),
                self.get_insert_handler(self.on_insert_link)),
            ('BulletList', None, _('Bullet List'), None, None,
                self.get_insert_handler(self.on_insert_bullet_list)),
            # ('NumberedList', None, _('Numbered List'), None, None,
            #     self.get_insert_handler(self.on_insert_numbered_list)),
            ('Title', None, _('Title'), None, None, self.on_insert_title),
            ('Line', None, _('Line'), None,
                _('Insert a separator line'),
                self.get_insert_handler(lambda sel_text: line)),
            # ('Table', None, _('Table'), None, None,
            #     self.get_insert_handler(lambda sel_text: table)),
            # ('Formula', None, _('Latex Formula'), None, None,
            #     self.get_insert_handler(self.on_insert_formula)),
            ('Date', None, _('Date/Time') + tmpl('D'), '<Ctrl>D',
                _('Insert the current date and time (edit format in preferences)'),
                self.get_insert_handler(self.on_insert_date_time)),
            ('TimeInterval', None, _('Time Interval'), '<Ctrl><Alt>D',
                _('Insert a time interval'),
                self.get_insert_handler(self.on_insert_time_interval)),
            ('LineBreak', None, _('Line Break'), '<Ctrl>Return',
                _('Insert a manual line break'),
                self.get_insert_handler(lambda sel_text: '\\\\\n')),
            ('InsertMenuBar', None, _('_Insert')),
        ])

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(self.main_window.insert_actiongroup, 0)

        # Add a UI description
        uimanager.add_ui_from_string(TOOLBAR_XML)

        # Create a Menu
        menu = uimanager.get_widget('/InsertMenu')

        image_items = 'Picture Link BulletList Title Line Date LineBreak Table'.split()

        for item in image_items:
            menu_item = uimanager.get_widget('/InsertMenu/' + item)
            filename = item.lower()
            # We may have disabled menu items
            if menu_item:
                menu_item.set_image(get_image(filename + '.png'))

        self.main_window.insert_button = customwidgets.ToolbarMenuButton(Gtk.STOCK_ADD, menu)
        self.main_window.insert_button.set_label(_('Insert'))
        self.main_window.insert_button.set_tooltip_text(_('Insert images, files, links and other content'))
        self.main_window.builder.get_object('edit_toolbar').insert(self.main_window.insert_button, -1)

    def get_insert_handler(self, func):
        def insert_handler(widget):
            editor = self.main_window.day_text_field
            sel_text = editor.get_selected_text()
            repl = func(sel_text)
            if isinstance(repl, str):
                editor.replace_selection(repl)
            elif isinstance(repl, tuple):
                editor.replace_selection_and_highlight(*repl)
            else:
                assert repl is None, repl
        return insert_handler

    def on_insert_pic(self, sel_text):
        dirs = self.main_window.journal.dirs
        picture_chooser = self.main_window.builder.get_object('picture_chooser')
        picture_chooser.set_current_folder(dirs.last_pic_dir)

        # if no text is selected, we can support inserting multiple images
        picture_chooser.set_select_multiple(not sel_text)

        filter = Gtk.FileFilter()
        filter.set_name("Images")
        filter.add_mime_type("image/bmp")
        filter.add_mime_type("image/gif")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/png")
        # SVG images aren't found by MIME type on Windows.
        filter.add_pattern("*.svg")

        # File filter hides all files on MacOS.
        if not filesystem.IS_MAC:
            picture_chooser.add_filter(filter)

        # Add box for inserting image width.
        box = Gtk.HBox()
        box.set_spacing(2)
        label = Gtk.Label(label=_('Width (optional):'))
        width_entry = Gtk.Entry()
        width_entry.set_max_length(6)
        width_entry.set_width_chars(6)
        box.pack_start(label, False, False, 0)
        box.pack_start(width_entry, False, False, 0)
        box.pack_start(Gtk.Label(_('pixels')), True, True, 0)
        box.show_all()
        picture_chooser.set_extra_widget(box)

        response = picture_chooser.run()
        picture_chooser.hide()

        if response == Gtk.ResponseType.OK:
            folder = picture_chooser.get_current_folder()
            # Folder is None if the file was chosen from the "recently used" section.
            if folder:
                dirs.last_pic_dir = folder

            # get requested width of image
            width_text = ''
            width = width_entry.get_text()
            if width:
                try:
                    width = int(width)
                except ValueError:
                    self.main_window.journal.show_message(_('Width must be an integer.'), error=True)
                    return
                width_text = '?%d' % width

            if sel_text:
                sel_text += ' '

            # iterate through all selected images
            lines = []
            for filename in picture_chooser.get_filenames():
                base, ext = os.path.splitext(filename)

                # On windows firefox accepts absolute filenames only
                # with the file:// prefix
                base = filesystem.get_local_url(base)

                lines.append('[%s""%s""%s%s]' % (sel_text, base, ext, width_text))

            return '\n'.join(lines)

    def on_insert_file(self, sel_text):
        dirs = self.main_window.journal.dirs
        file_chooser = self.main_window.builder.get_object('file_chooser')
        file_chooser.set_current_folder(dirs.last_file_dir)

        response = file_chooser.run()
        file_chooser.hide()

        if response == Gtk.ResponseType.OK:
            folder = file_chooser.get_current_folder()
            # Folder is None if the file was chosen from the "recently used" section.
            if folder:
                dirs.last_file_dir = folder
            filename = file_chooser.get_filename()
            filename = filesystem.get_local_url(filename)
            sel_text = self.main_window.day_text_field.get_selected_text()
            _, tail = os.path.split(filename)
            # It is always safer to add the "file://" protocol and the ""s
            return '[%s ""%s""]' % (sel_text or tail, filename)

    def on_insert_link(self, sel_text):
        link_creator = self.main_window.builder.get_object('link_creator')
        link_creator.set_transient_for(self.main_window.main_frame)
        link_location_entry = self.main_window.builder.get_object('link_location_entry')
        link_name_entry = self.main_window.builder.get_object('link_name_entry')

        link_location_entry.set_text('http://')
        link_name_entry.set_text(sel_text)
        self.main_window.day_text_field.replace_selection('')

        def link_entered():
            return bool(link_location_entry.get_text())

        def on_link_changed(widget):
            # Only make the link submittable, if text has been entered.
            link_creator.set_response_sensitive(Gtk.ResponseType.OK, link_entered())

        link_location_entry.connect('changed', on_link_changed)

        # Let user finish by hitting ENTER.
        def respond(widget):
            if link_entered():
                link_creator.response(Gtk.ResponseType.OK)

        link_location_entry.connect('activate', respond)
        link_name_entry.connect('activate', respond)

        link_location_entry.grab_focus()

        response = link_creator.run()
        link_creator.hide()

        if response == Gtk.ResponseType.OK:
            link_location = link_location_entry.get_text()
            link_name = link_name_entry.get_text()

            if link_location and link_name:
                return '[%s ""%s""]' % (link_name, link_location)
            elif link_location:
                return link_location
            else:
                self.main_window.journal.show_message(_('No link location has been entered'), error=True)

    def on_insert_bullet_list(self, sel_text):
        if sel_text:
            return '\n'.join('- %s' % row for row in sel_text.splitlines())
        return self.bullet_list

    # def on_insert_numbered_list(self, sel_text):
    #     if sel_text:
    #         return '\n'.join('+ %s' % row for row in sel_text.splitlines())
    #     return self.bullet_list.replace('-', '+')

    def on_insert_title(self, *args):
        self.main_window.day_text_field.apply_format('title')

    # def on_insert_formula(self, sel_text):
    #     formula = sel_text or '\\sum_{i=1}^n i = \\frac{n(n+1)}{2}'
    #     return '\\(', formula, '\\)'

    def on_insert_date_time(self, sel_text):
        format_string = self.main_window.journal.config.read('dateTimeString', '%A, %x %X')
        return dates.format_date(format_string)

    def on_insert_time_interval(self, sel_text):
        time_interval = self.main_window.builder.get_object('time_interval')
        time_interval.set_transient_for(self.main_window.main_frame)

        ti_start_hour = customwidgets.CustomComboBoxEntry(
            self.main_window.builder.get_object('ti_start_hour_combo_box'))
        ti_start_minute = customwidgets.CustomComboBoxEntry(
            self.main_window.builder.get_object('ti_start_minute_combo_box'))
        ti_end_hour = customwidgets.CustomComboBoxEntry(
            self.main_window.builder.get_object('ti_end_hour_combo_box'))
        ti_end_minute = customwidgets.CustomComboBoxEntry(
            self.main_window.builder.get_object('ti_end_minute_combo_box'))

        hours = [format(h, 'd') for h in range(24)]
        minutes = [format(m, '02d') for m in range(60)]

        ti_start_hour.set_entries(hours)
        ti_start_minute.set_entries(minutes)
        ti_end_hour.set_entries(hours)
        ti_end_minute.set_entries(minutes)

        # Set a default time interval
        ti_start_hour.set_active_text('8')
        ti_start_minute.set_active_text('00')
        ti_end_hour.set_active_text('9')
        ti_end_minute.set_active_text('00')

        def is_valid_time_interval():
            start_hour = int(ti_start_hour.get_active_text())
            start_minute = int(ti_start_minute.get_active_text())
            end_hour = int(ti_end_hour.get_active_text())
            end_minute = int(ti_end_minute.get_active_text())

            hour_interval = end_hour - start_hour
            minute_interval = end_minute - start_minute
            return hour_interval > 0 or hour_interval == 0 and minute_interval >= 0

        def correct_hour(entry):
            hour = entry.get_text().zfill(2)
            if not hour.isdigit() or int(hour) < 0:
                hour = '0'
            elif int(hour) > 23:
                hour = '23'

            entry.set_text(hour)
            return int(hour)

        def correct_minute(entry):
            minute = entry.get_text().zfill(2)
            if not minute.isdigit() or int(minute) < 0:
                minute = '00'
            elif int(minute) > 59:
                minute = '59'

            entry.set_text(minute)
            return minute

        def on_start_hour_changed(entry, event):
            # Set correct hour if it is out of range
            hour = correct_hour(entry)
            # Set a default interval of one hour
            if hour < 23:
                ti_end_hour.set_active_text(str(hour + 1))

        def on_start_minute_changed(entry, event):
            # Set correct minute if it is out of range
            minute = correct_minute(entry)
            # Set a default interval of one hour
            ti_end_minute.set_active_text(minute)

        def on_end_hour_changed(entry, event):
            # Set correct hour if it is out of range
            correct_hour(entry)

        def on_end_minute_changed(entry, event):
            # Set correct minute if it is out of range
            correct_minute(entry)

        def on_start_hour_key_pressed(entry, event):
            # Detect if Tab key is pressed
            if event.keyval == 65289:
                ti_start_minute.entry.grab_focus()

        def on_start_minute_key_pressed(entry, event):
            # Detect if Tab key is pressed
            if event.keyval == 65289:
                ti_end_hour.entry.grab_focus()

        def on_end_hour_key_pressed(entry, event):
            # Detect if Tab key is pressed
            if event.keyval == 65289:
                ti_end_minute.entry.grab_focus()

        ti_start_hour.entry.connect('key-press-event', on_start_hour_key_pressed)
        ti_start_minute.entry.connect('key-press-event', on_start_minute_key_pressed)
        ti_end_hour.entry.connect('key-press-event', on_end_hour_key_pressed)
        ti_start_hour.entry.connect('focus-out-event', on_start_hour_changed)
        ti_start_minute.entry.connect('focus-out-event', on_start_minute_changed)
        ti_end_hour.entry.connect('focus-out-event', on_end_hour_changed)
        ti_end_minute.entry.connect('focus-out-event', on_end_minute_changed)

        # Let user finish by hitting ENTER.
        def respond(widget):
            correct_minute(ti_end_minute.entry)
            time_interval.response(Gtk.ResponseType.OK)

        ti_end_minute.entry.connect('activate', respond)

        ti_start_hour.entry.grab_focus()

        response = time_interval.run()
        time_interval.hide()

        if response == Gtk.ResponseType.OK:
            start_hour = ti_start_hour.get_active_text()
            start_minute = ti_start_minute.get_active_text()
            end_hour = ti_end_hour.get_active_text()
            end_minute = ti_end_minute.get_active_text()

            if is_valid_time_interval():
                return '**Start time: %s:%s**\\\\\n\n**End time: %s:%s**' % (
                    start_hour, start_minute, end_hour, end_minute
                )
            else:
                self.main_window.journal.show_message(_('Time interval was negative'), error=True)
