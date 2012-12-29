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

import gtk

from rednotebook.util import filesystem
from rednotebook.util import dates


WEEKDAYS = (_('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'),
            _('Friday'), _('Saturday'), _('Sunday'))


example_text = '''\
=== This is an example template ===

It has been created to show you what can be put into a template. \
To edit it, click the arrow right of "Template" \
and select the template under "Edit Template".

Templates can contain any formatting or content that is also \
allowed in normal entries.

Your text can be:

- **bold**
- //italic//
- __underlined__
- --strikethrough--
- or some **//__combination__//**


You can add images to your template:

**Images:** [""/path/to/your/picture"".jpg]

You can link to almost everything:

- **links to files on your computer:** [filename.txt ""/path/to/filename.txt""]
- **links to directories:** [directory name ""/path/to/directory/""]
- **links to websites:** [RedNotebook Homepage ""http://rednotebook.sourceforge.net""]


As you see, **bullet lists** are also available. As always you have to add two \
empty lines to end a list.

Additionally you can have **titles** and **horizontal lines**:

= Title level 1 =
(The dates in the export will use this level, so it is recommended to use lower
levels in your entries)
== Title level 2 ==
=== Title level 3 ===
etc.

====================

% Commentary text can be put on lines starting with a percent sign.
% Those lines will not show up in the preview and the export.

**Macros**:

When a template is inserted, every occurence of "$date$" is converted to \
the current date. You can set the date format in the preferences.

There is even more markup that you can put into your templates. Have a look at
the inline help (Ctrl+H) for information.
'''

help_text = '''\
Besides templates for weekdays you can also have arbitrary named templates.
For example you might want to have a template for "Meeting" or "Journey".
All templates must reside in the directory "%s".

The template button gives you the options to create a new template or to \
visit the templates directory.
'''

meeting = _('''\
=== Meeting ===

Purpose, date, and place

**Present:**
+
+
+


**Agenda:**
+
+
+


**Discussion, Decisions, Assignments:**
+
+
+
==================================
''')

journey = _('''\
=== Journey ===
**Date:**

**Location:**

**Participants:**

**The trip:**
First we went to xxxxx then we got to yyyyy ...

**Pictures:** [Image folder ""/path/to/the/images/""]
''')

call = _('''\
==================================
=== Phone Call ===
- **Person:**
- **Time:**
- **Topic:**
- **Outcome and Follow up:**
==================================
''')

personal = _('''\
=====================================
=== Personal ===

+
+
+
========================

**How was the Day?**


========================
**What needs to be changed?**
+
+
+
=====================================
''')


class TemplateManager(object):
    def __init__(self, main_window):
        self.main_window = main_window

        self.main_window.template_bar.save_insert_button.connect('clicked', self.on_save_insert)
        self.main_window.template_bar.save_button.connect('clicked', self.on_save)
        self.main_window.template_bar.close_button.connect('clicked', self.on_close)

        self.dirs = main_window.journal.dirs

        self.merge_id = None
        self.actiongroup = None
        self.tmp_title = None
        self.tmp_parts = None

    def set_template_menu_sensitive(self, sensitive):
        if self.tmp_title:
            sensitive = False
        self.actiongroup.set_sensitive(sensitive)
        self.main_window.template_menu_button.set_sensitive(sensitive)

    def _set_widgets_sensitive(self, sensitive):
        self.main_window.calendar.calendar.set_sensitive(sensitive)
        journal_menu_item = self.main_window.uimanager.get_widget('/MainMenuBar/Journal')
        for child in journal_menu_item.get_submenu().get_children():
            if isinstance(child, gtk.MenuItem):
                action = child.get_action()
                if action:
                    action.set_sensitive(sensitive)
        self.set_template_menu_sensitive(sensitive)
        for widget in [
                self.main_window.back_one_day_button,
                self.main_window.today_button,
                self.main_window.forward_one_day_button,
                self.main_window.search_tree_view,
                self.main_window.search_box.entry,
                self.main_window.cloud,
                self.main_window.uimanager.get_widget('/MainMenuBar/Edit/Find').get_action(),
                ]:
            widget.set_sensitive(sensitive)

    def enter_template_mode(self, title, parts):
        # Save the templates title and the day's text.
        self.tmp_title = title
        self.tmp_parts = parts
        self.main_window.template_bar.show()
        if title == 'Weekday':
            text = self.get_weekday_text()
        else:
            text = self.get_text(title)
        self.main_window.undo_redo_manager.set_stack(title)
        self.main_window.day_text_field.set_text(text, undoing=True)
        self._set_widgets_sensitive(False)

    def exit_template_mode(self):
        self.tmp_title = None
        self.tmp_parts = None
        self.main_window.template_bar.hide()
        if self.main_window.preview_mode:
            self.main_window.change_mode(preview=False)
        self.main_window.day_text_field.day_text_view.grab_focus()
        self._set_widgets_sensitive(True)

    def _reset_undo_stack(self):
        self.main_window.undo_redo_manager.set_stack(self.main_window.day.date)

    def on_insert(self, action):
        # Convert to unicode and strip 'Insert'.
        title = unicode(action.get_name())[6:]
        parts = self.main_window.day_text_field.get_text_parts()
        self.enter_template_mode(title, parts)

    def on_save_insert(self, button):
        template = self.main_window.day_text_field.get_text()
        p1, p2, p3 = self.tmp_parts
        self._reset_undo_stack()
        # Force addition of an undo item.
        self.main_window.day_text_field.set_text(p1 + p2 + p3, undoing=True)
        self.main_window.day_text_field.set_text(p1 + template + p3)
        self.exit_template_mode()

    def on_save(self, button):
        template = self.main_window.day_text_field.get_text()
        filename = self.titles_to_files.get(self.tmp_title)
        assert filename is not None
        filesystem.write_file(filename, template)

    def on_close(self, button):
        template = self.main_window.day_text_field.get_text()
        p1, p2, p3 = self.tmp_parts
        self._reset_undo_stack()
        self.main_window.day_text_field.set_text(p1 + p2 + p3, undoing=True)
        self.exit_template_mode()

    def on_new_template(self, action):
        dialog = gtk.Dialog(_('Choose Template Name'))
        dialog.set_transient_for(self.main_window.main_frame)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

        entry = gtk.Entry()
        entry.set_size_request(300, -1)
        dialog.get_content_area().pack_start(entry)
        dialog.show_all()
        response = dialog.run()
        dialog.hide()

        if response == gtk.RESPONSE_OK:
            title = entry.get_text()
            if not title.lower().endswith('.txt'):
                title += '.txt'
            filename = os.path.join(self.dirs.template_dir, title)

            filesystem.make_file(filename, example_text)

            filesystem.open_url(filename)

    def on_open_template_dir(self):
        filesystem.open_url(self.dirs.template_dir)

    def get_template_file(self, basename):
        return os.path.join(self.dirs.template_dir, str(basename) + '.txt')

    def get_text(self, title):
        filename = self.titles_to_files.get(title, None)
        if not filename:
            return ''

        text = filesystem.read_file(filename)

        # An Error occured
        if not text:
            text = ('This template contains no text or has unreadable content. To edit it, '
                    'click the arrow right of "Template" '
                    'and select the template under "Edit Template".')

        # convert every "$date$" to the current date
        config = self.main_window.journal.config
        format_string = config.read('dateTimeString', '%A, %x %X')
        date_string = dates.format_date(format_string)

        template_text = text.replace(u'$date$', date_string)
        return template_text

    def get_weekday_text(self, date=None):
        if date is None:
            date = self.main_window.journal.date
        week_day_number = date.weekday() + 1
        return self.get_text(str(week_day_number))

    def get_available_template_files(self):
        dir = self.dirs.template_dir
        files = os.listdir(dir)
        files = map(lambda basename: os.path.join(dir, basename), files)

        # No directories allowed
        files = filter(lambda file:os.path.isfile(file), files)

        # No tempfiles
        files = filter(lambda file: not file.endswith('~'), files)
        return files

    def get_menu(self):
        '''
        See http://www.pygtk.org/pygtk2tutorial/sec-UIManager.html for help
        A popup menu cannot show accelerators (HIG).
        '''
        # complete paths
        files = self.get_available_template_files()

        def escape_name(name):
            """Remove special xml chars for GUI display."""
            for char in '&<>\'"':
                name = name.replace(char, '')
            return name

        # 1, 2, 3
        self.titles_to_files = {}
        for file in files:
            root, ext = os.path.splitext(file)
            title = os.path.basename(root)
            self.titles_to_files[escape_name(title)] = file

        sorted_titles = sorted(self.titles_to_files.keys())

        menu_xml = '''\
        <ui>
        <popup action="TemplateMenu">'''

        insert_menu_xml = '''
                <menuitem action="InsertWeekday"/>
                <separator name="sep4"/>'''
        for title in sorted_titles:
            if title not in map(str, range(1, 8)):
                insert_menu_xml += '''
                <menuitem action="Insert%s"/>''' % title

        menu_xml += insert_menu_xml

        menu_xml += '''
            <separator name="sep5"/>
            <menuitem action="NewTemplate"/>'''

        menu_xml +='''
            <menuitem action="OpenTemplateDirectory"/>
        </popup>
        </ui>'''

        uimanager = self.main_window.uimanager

        if self.actiongroup:
            uimanager.remove_action_group(self.actiongroup)

        # Create an ActionGroup
        self.actiongroup = gtk.ActionGroup('TemplateActionGroup')

        # Create actions
        actions = []

        for title in sorted_titles:
            insert_action = ('Insert' + title, None, title, None, None,
                             self.on_insert)
            actions.append(insert_action)

        actions.append(('InsertWeekday', gtk.STOCK_HOME,
                        _("This Weekday's Template"), None, None,
                        self.on_insert))

        actions.append(('NewTemplate', gtk.STOCK_NEW, _('Create New Template'),
                        None, None, lambda widget: self.on_new_template(widget)))

        actions.append(('OpenTemplateDirectory', gtk.STOCK_DIRECTORY,
                        _('Open Template Directory'), None, None,
                        lambda widget: self.on_open_template_dir()))

        self.actiongroup.add_actions(actions)

        # Remove the previous ui descriptions
        if self.merge_id:
            uimanager.remove_ui(self.merge_id)

        # Add a UI description
        self.merge_id = uimanager.add_ui_from_string(menu_xml)

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(self.actiongroup, 0)

        # Create a Menu
        menu = uimanager.get_widget('/TemplateMenu')
        return menu

    def make_empty_template_files(self):
        global help_text

        files = []
        for day_number in range(1, 8):
            weekday = WEEKDAYS[day_number - 1]
            files.append((self.get_template_file(day_number),
                          example_text.replace('template ===',
                                               'template for %s ===' % weekday)))

        help_text %= (self.dirs.template_dir)

        files.append((self.get_template_file('Help'), help_text))

        # Only add the example templates the first time and just restore
        # the day templates everytime
        if self.main_window.journal.is_first_start:
            files.append((self.get_template_file('Meeting'), meeting))
            files.append((self.get_template_file('Journey'), journey))
            files.append((self.get_template_file('Call'), call))
            files.append((self.get_template_file('Personal'), personal))

        filesystem.make_files(files)
