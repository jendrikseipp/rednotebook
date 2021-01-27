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

from gi.repository import Gtk

from rednotebook.util import dates, filesystem


WEEKDAYS = (
    _("Monday"),
    _("Tuesday"),
    _("Wednesday"),
    _("Thursday"),
    _("Friday"),
    _("Saturday"),
    _("Sunday"),
)


MENU_XML = """\
<ui>
<popup action="TemplateMenu">
    <menuitem action="EditWeekday"/>
    <separator name="sep4"/>
    %s
    <separator name="sep5"/>
    <menuitem action="NewTemplate"/>
</popup>
</ui>"""


example_text = """\
=== This is an example template ===

It has been created to show you what can be put into a template. \
You can edit and save it with the buttons above.

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
- **links to websites:** [RedNotebook Homepage ""https://rednotebook.app""]


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

When a template is inserted, every occurence of $date$ is converted to \
the current date. You can set the date format in the preferences.

There is even more markup that you can put into your templates. Have a look at
the inline help (Ctrl+H) for information.
"""

help_text = """\
Besides templates for weekdays you can also have arbitrary named templates.
For example you might want to have a template for "Meeting" or "Journey".
All templates must reside in the directory "%s".

The template button gives you the options to create a new template or to \
visit the templates directory.
"""

meeting = _(
    """\
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
"""
)

journey = _(
    """\
=== Journey ===
**Date:**

**Location:**

**Participants:**

**The trip:**
First we went to xxxxx then we got to yyyyy ...

**Pictures:** [Image folder ""/path/to/the/images/""]
"""
)

call = _(
    """\
==================================
=== Phone Call ===
- **Person:**
- **Time:**
- **Topic:**
- **Outcome and Follow up:**
==================================
"""
)

personal = _(
    """\
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
"""
)


class TemplateInfo(Gtk.InfoBar):
    def __init__(self):
        Gtk.InfoBar.__init__(self)
        self.set_message_type(Gtk.MessageType.INFO)

        title_label = Gtk.Label()
        title_label.set_markup("<b>{}</b>".format(_("Template mode")))
        title_label.set_alignment(0.0, 0.5)

        msg_label = Gtk.Label()
        msg_label.set_markup(_("You are currently editing a template."))
        msg_label.set_alignment(0.0, 0.5)

        vbox = Gtk.VBox(spacing=5)
        vbox.pack_start(title_label, False, False, 0)
        vbox.pack_start(msg_label, False, False, 0)

        image = Gtk.Image.new_from_stock(Gtk.STOCK_DIALOG_INFO, Gtk.IconSize.DIALOG)

        content = self.get_content_area()
        content.pack_start(image, False, False, 0)
        content.pack_start(vbox, False, False, 0)

        self.show_all()


class TemplateManager:
    def __init__(self, main_window):
        self.main_window = main_window

        self.main_window.template_bar.save_insert_button.connect(
            "clicked", self.on_save_insert
        )
        self.main_window.template_bar.save_button.connect("clicked", self.on_save)
        self.main_window.template_bar.close_button.connect("clicked", self.on_close)

        self.dirs = main_window.journal.dirs

        self.merge_id = None
        self.actiongroup = None
        self.tmp_title = None
        self.selection_to_replace = None

        self._template_mode_info_bar = TemplateInfo()
        self._template_mode_info_bar.hide()
        self.main_window.text_vbox.pack_start(
            self._template_mode_info_bar, False, False, 0
        )
        self.main_window.text_vbox.reorder_child(self._template_mode_info_bar, 1)

    def set_template_menu_sensitive(self, sensitive):
        if self.tmp_title:
            sensitive = False
        self.actiongroup.set_sensitive(sensitive)
        self.main_window.template_button.set_sensitive(sensitive)

    def _set_widgets_sensitive(self, sensitive):
        self.main_window.calendar.calendar.set_sensitive(sensitive)
        journal_menu_item = self.main_window.uimanager.get_widget(
            "/MainMenuBar/Journal"
        )
        for child in journal_menu_item.get_submenu().get_children():
            if isinstance(child, Gtk.MenuItem):
                child.set_sensitive(sensitive)
        self.set_template_menu_sensitive(sensitive)
        for widget in [
            self.main_window.back_one_day_button,
            self.main_window.today_button,
            self.main_window.forward_one_day_button,
            self.main_window.search_tree_view,
            self.main_window.search_box.entry,
            self.main_window.cloud,
            self.main_window.uimanager.get_widget("/MainMenuBar/Edit/Find"),
        ]:
            widget.set_sensitive(sensitive)

    def enter_template_mode(self, title, selection):
        # Save the templates title and the day's text.
        self.tmp_title = title
        self.selection_to_replace = selection
        self.main_window.template_bar.show()
        text = self.get_text(title)
        self.main_window.day_text_field.show_template(title, text)
        self._template_mode_info_bar.show()
        self._set_widgets_sensitive(False)

    def exit_template_mode(self):
        self.tmp_title = None
        self.selection_to_replace = None
        self.main_window.template_bar.hide()
        if self.main_window.preview_mode:
            self.main_window.change_mode(preview=False)
        self.main_window.day_text_field.day_text_view.grab_focus()
        self._template_mode_info_bar.hide()
        self._set_widgets_sensitive(True)

    def edit(self, title):
        selection = self.main_window.day_text_field.get_selection_bounds()
        self.enter_template_mode(title, selection)

    def _replace_macros(self, text):
        # convert every "$date$" to the current date
        config = self.main_window.journal.config
        format_string = config.read("dateTimeString")
        date_string = dates.format_date(format_string)
        text = text.replace("$date$", date_string)
        return text

    def on_save_insert(self, button):
        self.on_save(None)
        template = self.main_window.day_text_field.get_text()
        template = self._replace_macros(template)

        self.main_window.day_text_field.show_day(self.main_window.day)
        buf = self.main_window.day_text_field.day_text_buffer
        buf.begin_user_action()
        buf.select_range(*self.selection_to_replace)
        buf.delete_selection(interactive=False, default_editable=True)
        buf.insert_at_cursor(template)
        buf.end_user_action()
        self.exit_template_mode()

    def on_save(self, button):
        template = self.main_window.day_text_field.get_text()
        filesystem.write_file(self.get_path(self.tmp_title), template)

    def on_close(self, button):
        self.main_window.day_text_field.show_day(self.main_window.day)
        self.exit_template_mode()

    def on_new_template(self, action):
        dialog = Gtk.Dialog(_("Choose Template Name"))
        dialog.set_transient_for(self.main_window.main_frame)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dialog.set_response_sensitive(Gtk.ResponseType.OK, False)

        # Let user finish by hitting ENTER.
        def respond(widget):
            dialog.response(Gtk.ResponseType.OK)

        def on_text_changed(entry):
            dialog.set_response_sensitive(Gtk.ResponseType.OK, bool(entry.get_text()))

        entry = Gtk.Entry()
        entry.connect("activate", respond)
        # Only allow closing dialog when text is entered.
        entry.connect("changed", on_text_changed)
        entry.set_size_request(300, -1)
        dialog.get_content_area().pack_start(entry, True, True, 0)
        dialog.show_all()
        response = dialog.run()
        dialog.hide()

        if response == Gtk.ResponseType.OK:
            title = entry.get_text()
            selection = self.main_window.day_text_field.get_selection_bounds()
            path = self.get_path(title)
            filesystem.make_file(path, example_text)
            self.enter_template_mode(title, selection)

    def _get_weekday_number(self):
        return self.main_window.journal.date.isoweekday()

    def get_path(self, title):
        return os.path.join(self.dirs.template_dir, title + ".txt")

    def get_text(self, title):
        text = filesystem.read_file(self.get_path(title))

        # An Error occured
        if not text:
            text = _("This template file contains no text or has unreadable content.")
        return text

    def get_available_template_files(self):
        path = self.dirs.template_dir
        return [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".txt")]

    def _escape_template_name(self, name):
        """Remove special xml chars for GUI display."""
        for char in "&<>'\"":
            name = name.replace(char, "")
        return name

    def get_menu(self):
        """
        See http://www.pyGtk.org/pygtk2tutorial/sec-UIManager.html for help
        A popup menu cannot show accelerators (HIG).
        """
        files = self.get_available_template_files()

        titles = []
        for file in files:
            root, ext = os.path.splitext(file)
            title = os.path.basename(root)
            titles.append(title)

        actions_xml = "".join(
            '<menuitem action="Edit%s"/>' % self._escape_template_name(title)
            for title in sorted(titles)
            if title not in "1234567"
        )

        uimanager = self.main_window.uimanager

        if self.actiongroup:
            uimanager.remove_action_group(self.actiongroup)

        # Create an ActionGroup
        self.actiongroup = Gtk.ActionGroup("TemplateActionGroup")

        # Create actions
        actions = []

        for title in sorted(titles):
            # Define inline to force early binding.
            def get_edit_function(title):
                return lambda button: self.edit(title)

            edit_action = (
                "Edit" + self._escape_template_name(title),
                None,
                title,
                None,
                None,
                get_edit_function(title),
            )
            actions.append(edit_action)

        actions.append(
            (
                "EditWeekday",
                Gtk.STOCK_HOME,
                _("This Weekday's Template"),
                None,
                None,
                lambda button: self.edit(str(self._get_weekday_number())),
            )
        )

        actions.append(
            (
                "NewTemplate",
                Gtk.STOCK_NEW,
                _("Create New Template"),
                None,
                None,
                self.on_new_template,
            )
        )

        self.actiongroup.add_actions(actions)

        # Remove the previous ui descriptions
        if self.merge_id:
            uimanager.remove_ui(self.merge_id)

        # Add a UI description
        self.merge_id = uimanager.add_ui_from_string(MENU_XML % actions_xml)

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(self.actiongroup, 0)

        # Create a Menu
        menu = uimanager.get_widget("/TemplateMenu")
        return menu

    def make_empty_template_files(self):
        global help_text

        files = []
        for day_number in range(1, 8):
            weekday = WEEKDAYS[day_number - 1]
            files.append(
                (
                    self.get_path(str(day_number)),
                    example_text.replace(
                        "template ===", "template for %s ===" % weekday
                    ),
                )
            )

        help_text %= self.dirs.template_dir

        files.append((self.get_path("Help"), help_text))

        # Only add the example templates the first time and just restore
        # the day templates everytime
        if self.main_window.journal.is_first_start:
            files.append((self.get_path("Meeting"), meeting))
            files.append((self.get_path("Journey"), journey))
            files.append((self.get_path("Call"), call))
            files.append((self.get_path("Personal"), personal))

        filesystem.make_files(files)
