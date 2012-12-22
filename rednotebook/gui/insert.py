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

import gtk

from rednotebook.util import filesystem


XML = '''\
<ui>
<popup action="InsertMenu">
    <menuitem action="Picture"/>
    <menuitem action="File"/>
    <menuitem action="Link"/>
    <menuitem action="BulletList"/>
    %(numlist_ui)s
    <menuitem action="Title"/>
    <menuitem action="Line"/>
    %(table_ui)s
    %(formula_ui)s
    <menuitem action="Date"/>
    <menuitem action="LineBreak"/>
</popup>
</ui>'''


def get_image(name):
    image = gtk.Image()
    file_name = os.path.join(filesystem.image_dir, name)
    image.set_from_file(file_name)
    return image


class InsertMenu(object):
    def __init__(self, main_window):
        self.main_window = main_window
        
    def setup(self):
        '''
        See http://www.pygtk.org/pygtk2tutorial/sec-UIManager.html for help
        A popup menu cannot show accelerators (HIG).
        '''

        numlist_ui = '' #'<menuitem action="NumberedList"/>'
        table_ui = '' # '<menuitem action="Table"/>'
        formula_ui = '' #'<menuitem action="Formula"/>'

        insert_menu_xml = XML % locals()

        uimanager = self.main_window.uimanager

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.main_window.main_frame.add_accel_group(accelgroup)

        # Create an ActionGroup
        self.main_window.insert_actiongroup = gtk.ActionGroup('InsertActionGroup')

        line = '\n====================\n'

        item1 = _('First Item')
        item2 = _('Second Item')
        item3 = _('Indented Item')
        close = _('Two blank lines close the list')
        bullet_list = '\n- %s\n- %s\n  - %s (%s)\n\n\n' % (item1, item2, item3, close)
        numbered_list = bullet_list.replace('-', '+')

        title_text = _('Title text')
        title = '\n=== %s ===\n' % title_text

        table = ('\n|| Whitespace Left | Whitespace Right | Resulting Alignment |\n'
                   '| 1               | more than 1     | Align left   |\n'
                   '|     more than 1 |               1 |   Align right |\n'
                   '|   more than 1   |   more than 1   |   Center   |\n'
                   '|| Title rows | are always | centered |\n'
                   '|  Use two vertical  |  lines on the left  |  for title rows  |\n'
                   '|  Always use  |  at least  |  one whitespace  |\n')

        formula = '\\(\\sum_{i=1}^n i = \\frac{n(n+1)}{2}\\)'

        line_break = r'\\'

        def insert_date_time(widget):
            format_string = self.main_window.journal.config.read('dateTimeString', '%A, %x %X')
            date_string = dates.format_date(format_string)
            self.main_window.day_text_field.insert(date_string)

        def tmpl(letter):
            return ' (Ctrl+%s)' % letter

        # Create actions
        self.main_window.insert_actiongroup.add_actions([
            ('Picture', gtk.STOCK_ORIENTATION_PORTRAIT,
                _('Picture'),
                None, _('Insert an image from the harddisk'),
                self.on_insert_pic),
            ('File', gtk.STOCK_FILE, _('File'), None,
                _('Insert a link to a file'),
                self.on_insert_file),
            ### Translators: Noun
            ('Link', gtk.STOCK_JUMP_TO, _('_Link') + tmpl('L'), '<Control>L',
                _('Insert a link to a website'),
                self.on_insert_link),
            ('BulletList', None, _('Bullet List'), None, None,
                lambda widget: self.main_window.day_text_field.insert(bullet_list)),
            ('NumberedList', None, _('Numbered List'), None, None,
                lambda widget: self.main_window.day_text_field.insert(numbered_list)),
            ('Title', None, _('Title'), None, None,
                lambda widget: self.main_window.day_text_field.insert(title)),
            ('Line', None, _('Line'), None,
                _('Insert a separator line'),
                lambda widget: self.main_window.day_text_field.insert(line)),
            ('Table', None, _('Table'), None, None,
                lambda widget: self.main_window.day_text_field.insert(table)),
            ('Formula', None, _('Latex Formula'), None, None,
                lambda widget: self.main_window.day_text_field.insert(formula)),
            ('Date', None, _('Date/Time') + tmpl('D'), '<Ctrl>D',
                _('Insert the current date and time (edit format in preferences)'),
                insert_date_time),
            ('LineBreak', None, _('Line Break'), None,
                _('Insert a manual line break'),
                lambda widget: self.main_window.day_text_field.insert(line_break)),
            ])

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(self.main_window.insert_actiongroup, 0)

        # Add a UI description
        uimanager.add_ui_from_string(insert_menu_xml)

        # Create a Menu
        menu = uimanager.get_widget('/InsertMenu')

        image_items = 'Picture Link BulletList Title Line Date LineBreak Table'.split()

        for item in image_items:
            menu_item = uimanager.get_widget('/InsertMenu/'+ item)
            filename = item.lower()
            # We may have disabled menu items
            if menu_item:
                menu_item.set_image(get_image(filename + '.png'))

        self.main_window.single_menu_toolbutton = gtk.MenuToolButton(gtk.STOCK_ADD)
        self.main_window.single_menu_toolbutton.set_label(_('Insert'))

        self.main_window.single_menu_toolbutton.set_menu(menu)
        self.main_window.single_menu_toolbutton.connect('clicked', self.show_insert_menu)
        self.main_window.single_menu_toolbutton.set_tooltip_text(_('Insert images, files, links and other content'))
        edit_toolbar = self.main_window.builder.get_object('edit_toolbar')
        edit_toolbar.insert(self.main_window.single_menu_toolbutton, -1)
        self.main_window.single_menu_toolbutton.show()

    def show_insert_menu(self, button):
        '''
        Show the insert menu, when the Insert Button is clicked.

        A little hack for button and activate_time is needed as the "clicked" does
        not have an associated event parameter. Otherwise we would use event.button
        and event.time
        '''
        self.main_window.single_menu_toolbutton.get_menu().popup(parent_menu_shell=None,
                            parent_menu_item=None, func=None, button=0, activate_time=0, data=None)

    def on_insert_pic(self, widget):
        dirs = self.main_window.journal.dirs
        picture_chooser = self.main_window.builder.get_object('picture_chooser')
        picture_chooser.set_current_folder(dirs.last_pic_dir)

        filter = gtk.FileFilter()
        filter.set_name("Images")
        filter.add_mime_type("image/png")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/gif")
        filter.add_pattern("*.png")
        filter.add_pattern("*.jpg")
        filter.add_pattern("*.jpeg")
        filter.add_pattern("*.gif")
        filter.add_pattern("*.bmp")

        picture_chooser.add_filter(filter)

        # Add box for inserting image width.
        box = gtk.HBox()
        box.set_spacing(2)
        label = gtk.Label(_('Width (optional):'))
        width_entry = gtk.Entry(max=6)
        width_entry.set_width_chars(6)
        box.pack_start(label, False)
        box.pack_start(width_entry, False)
        box.pack_start(gtk.Label(_('pixels')), False)
        box.show_all()
        picture_chooser.set_extra_widget(box)

        response = picture_chooser.run()
        picture_chooser.hide()

        if response == gtk.RESPONSE_OK:
            dirs.last_pic_dir = picture_chooser.get_current_folder().decode('utf-8')
            base, ext = os.path.splitext(picture_chooser.get_filename().decode('utf-8'))

            # On windows firefox accepts absolute filenames only
            # with the file:/// prefix
            base = filesystem.get_local_url(base)

            width_text = ''
            width = width_entry.get_text().decode('utf-8')
            if width:
                try:
                    width = int(width)
                except ValueError:
                    self.main_window.journal.show_message(_('Width must be an integer.'), error=True)
                    return
                width_text = '?%d' % width

            self.main_window.day_text_field.insert('[""%s""%s%s]' % (base, ext, width_text))

    def on_insert_file(self, widget):
        dirs = self.main_window.journal.dirs
        file_chooser = self.main_window.builder.get_object('file_chooser')
        file_chooser.set_current_folder(dirs.last_file_dir)

        response = file_chooser.run()
        file_chooser.hide()

        if response == gtk.RESPONSE_OK:
            dirs.last_file_dir = file_chooser.get_current_folder().decode('utf-8')
            filename = file_chooser.get_filename().decode('utf-8')
            filename = filesystem.get_local_url(filename)
            head, tail = os.path.split(filename)
            # It is always safer to add the "file://" protocol and the ""s
            self.main_window.day_text_field.insert('[%s ""%s""]' % (tail, filename))

    def on_insert_link(self, widget):
        link_creator = self.main_window.builder.get_object('link_creator')
        link_location_entry = self.main_window.builder.get_object('link_location_entry')
        link_name_entry = self.main_window.builder.get_object('link_name_entry')

        link_location_entry.set_text('http://')
        link_name_entry.set_text('')

        def link_entered():
            return bool(link_location_entry.get_text())

        def on_link_changed(widget):
            # Only make the link submittable, if text has been entered.
            link_creator.set_response_sensitive(gtk.RESPONSE_OK, link_entered())

        link_location_entry.connect('changed', on_link_changed)

        # Let user finish by hitting ENTER.
        def respond(widget):
            if link_entered():
                link_creator.response(gtk.RESPONSE_OK)

        link_location_entry.connect('activate', respond)
        link_name_entry.connect('activate', respond)

        link_location_entry.grab_focus()

        response = link_creator.run()
        link_creator.hide()

        if response == gtk.RESPONSE_OK:
            link_location = link_location_entry.get_text()
            link_name = link_name_entry.get_text()

            if link_location and link_name:
                self.main_window.day_text_field.insert('[%s ""%s""]' % (link_name, link_location))
            elif link_location:
                self.main_window.day_text_field.insert(link_location)
            else:
                self.main_window.journal.show_message(_('No link location has been entered'), error=True)
