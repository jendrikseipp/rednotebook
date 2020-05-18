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

import functools
import os

from gi.repository import Gtk

from rednotebook.gui import customwidgets
from rednotebook.util import dates, filesystem, urls


MENUITEMS_XML = """\
    <menuitem action="Picture"/>
    <menuitem action="File"/>
    <menuitem action="Link"/>
    <menuitem action="BulletList"/>
    <menu action="TitleMenu">
        <menuitem action="Title1"/>
        <menuitem action="Title2"/>
        <menuitem action="Title3"/>
        <menuitem action="Title4"/>
        <menuitem action="Title5"/>
    </menu>
    <menuitem action="Line"/>
    <menuitem action="Date"/>
    <menuitem action="LineBreak"/>
"""

TOOLBAR_XML = (
    """\
<ui>
<popup action="InsertMenu">
%s
</popup>
</ui>
"""
    % MENUITEMS_XML
)

MENUBAR_XML = (
    """\
<menu action="InsertMenuBar">
%s
</menu>
"""
    % MENUITEMS_XML
)


def get_image(name):
    image = Gtk.Image()
    file_name = os.path.join(filesystem.image_dir, name)
    image.set_from_file(file_name)
    return image


def insert_handler(callback_method):
    """
    Create text insertion/substitution hooks.

    If the wrapped method returns a single string, replace the selected text
    and place the editor cursor at the end of the selected text.

    If the wrapped method returns a triple <prefix, selected_text, postfix>,
    replace the selected text by "{prefix}{selected_text}{postfix}" and
    highlight selected_text in the editor.
    """

    @functools.wraps(callback_method)
    def insert_handler_wrapper(self, widget, *args, **kwargs):
        editor = self.main_window.day_text_field
        sel_text = editor.get_selected_text()
        repl = callback_method(self, sel_text, *args, **kwargs)
        if isinstance(repl, str):
            editor.replace_selection(repl)
        elif isinstance(repl, tuple):
            editor.replace_selection_and_highlight(*repl)
        else:
            assert repl is None, repl

    return insert_handler_wrapper


class InsertMenu:
    def __init__(self, main_window):
        self.main_window = main_window

        self.bullet_list = "\n- {}\n- {}\n  - {} ({})\n\n\n".format(
            _("First Item"),
            _("Second Item"),
            _("Indented Item"),
            _("Two blank lines close the list"),
        )

        self.setup()

    def setup(self):
        """
        See http://www.pyGtk.org/pygtk2tutorial/sec-UIManager.html for help
        A popup menu cannot show accelerators (HIG).
        """
        uimanager = self.main_window.uimanager

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.main_window.main_frame.add_accel_group(accelgroup)

        # Create an ActionGroup
        self.main_window.insert_actiongroup = Gtk.ActionGroup("InsertActionGroup")

        # Create actions
        actions = [
            (
                "Picture",
                Gtk.STOCK_ORIENTATION_PORTRAIT,
                _("Picture"),
                None,
                _("Insert an image from the harddisk"),
                self.on_insert_pic,
            ),
            (
                "File",
                Gtk.STOCK_FILE,
                _("File"),
                None,
                _("Insert a link to a file"),
                self.on_insert_file,
            ),
            # Translators: Noun
            (
                "Link",
                Gtk.STOCK_JUMP_TO,
                _("_Link"),
                "<Control>L",
                _("Insert a link to a website"),
                self.on_insert_link,
            ),
            (
                "BulletList",
                None,
                _("Bullet List"),
                None,
                None,
                self.on_insert_bullet_list,
            ),
            ("TitleMenu", None, _("Title")),
            (
                "Line",
                None,
                _("Line"),
                None,
                _("Insert a separator line"),
                self.on_insert_line,
            ),
            (
                "Date",
                None,
                _("Date/Time"),
                "<Ctrl>D",
                _("Insert the current date and time (edit format in preferences)"),
                self.on_insert_date_time,
            ),
            (
                "LineBreak",
                None,
                _("Line Break"),
                "<Ctrl>Return",
                _("Insert a manual line break"),
                self.on_insert_line_break,
            ),
            ("InsertMenuBar", None, _("_Insert")),
        ]

        # Create title submenu actions
        for level in range(1, 6):
            action_label = "{} {}".format(_("Level"), level)
            actions.append(
                (
                    "Title{}".format(level),
                    None,
                    action_label,
                    "<Control>{}".format(level),
                    None,
                    functools.partial(self.on_insert_title, level=level),
                )
            )

        self.main_window.insert_actiongroup.add_actions(actions)

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(self.main_window.insert_actiongroup, 0)

        # Add a UI description
        uimanager.add_ui_from_string(TOOLBAR_XML)

        # Create a Menu
        menu = uimanager.get_widget("/InsertMenu")

        image_items = "Picture Link BulletList Title Line Date LineBreak Table".split()

        for item in image_items:
            menu_item = uimanager.get_widget("/InsertMenu/" + item)
            filename = item.lower()
            # We may have disabled menu items
            if menu_item:
                menu_item.set_image(get_image(filename + ".png"))

        self.main_window.insert_button = customwidgets.ToolbarMenuButton(
            Gtk.STOCK_ADD, menu
        )
        self.main_window.insert_button.set_label(_("Insert"))
        self.main_window.insert_button.set_tooltip_text(
            _("Insert images, files, links and other content")
        )
        self.main_window.builder.get_object("edit_toolbar").insert(
            self.main_window.insert_button, -1
        )

    @insert_handler
    def on_insert_pic(self, sel_text):
        dirs = self.main_window.journal.dirs
        picture_chooser = self.main_window.builder.get_object("picture_chooser")
        picture_chooser.set_current_folder(dirs.last_pic_dir)

        # if no text is selected, we can support inserting multiple images
        picture_chooser.set_select_multiple(not sel_text)

        file_filter = Gtk.FileFilter()
        file_filter.set_name("Images")
        file_filter.add_mime_type("image/bmp")
        file_filter.add_mime_type("image/gif")
        file_filter.add_mime_type("image/jpeg")
        file_filter.add_mime_type("image/png")
        # SVG images aren't found by MIME type on Windows.
        file_filter.add_pattern("*.svg")

        # File filter hides all files on MacOS.
        if not filesystem.IS_MAC:
            picture_chooser.add_filter(file_filter)

        # Add box for inserting image width.
        box = Gtk.HBox()
        box.set_spacing(2)
        label = Gtk.Label(label=_("Width (optional):"))
        width_entry = Gtk.Entry()
        width_entry.set_max_length(6)
        width_entry.set_width_chars(6)
        box.pack_start(label, False, False, 0)
        box.pack_start(width_entry, False, False, 0)
        box.pack_start(Gtk.Label(_("pixels")), True, True, 0)
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
            width_text = ""
            width = width_entry.get_text()
            if width:
                try:
                    width = int(width)
                except ValueError:
                    self.main_window.journal.show_message(
                        _("Width must be an integer."), error=True
                    )
                    return
                width_text = "?%d" % width

            if sel_text:
                sel_text += " "

            # iterate through all selected images
            lines = []
            for filename in picture_chooser.get_filenames():
                base, ext = os.path.splitext(filename)

                # On windows firefox accepts absolute filenames only
                # with the file:// prefix
                base = urls.get_local_url(base)

                lines.append('[{}""{}""{}{}]'.format(sel_text, base, ext, width_text))

            return "\n".join(lines)

    @insert_handler
    def on_insert_file(self, sel_text):
        dirs = self.main_window.journal.dirs
        file_chooser = self.main_window.builder.get_object("file_chooser")
        file_chooser.set_current_folder(dirs.last_file_dir)

        response = file_chooser.run()
        file_chooser.hide()

        if response == Gtk.ResponseType.OK:
            folder = file_chooser.get_current_folder()
            # Folder is None if the file was chosen from the "recently used" section.
            if folder:
                dirs.last_file_dir = folder
            filename = file_chooser.get_filename()
            filename = urls.get_local_url(filename)
            sel_text = self.main_window.day_text_field.get_selected_text()
            _, tail = os.path.split(filename)
            # It is always safer to add the "file://" protocol and the ""s
            return '[{} ""{}""]'.format(sel_text or tail, filename)

    @insert_handler
    def on_insert_link(self, sel_text):
        link_creator = self.main_window.builder.get_object("link_creator")
        link_location_entry = self.main_window.builder.get_object("link_location_entry")
        link_name_entry = self.main_window.builder.get_object("link_name_entry")

        link_location_entry.set_text("http://")
        link_name_entry.set_text(sel_text)
        self.main_window.day_text_field.replace_selection("")

        def link_entered():
            return bool(link_location_entry.get_text())

        def on_link_changed(widget):
            # Only make the link submittable, if text has been entered.
            link_creator.set_response_sensitive(Gtk.ResponseType.OK, link_entered())

        link_location_entry.connect("changed", on_link_changed)

        # Let user finish by hitting ENTER.
        def respond(widget):
            if link_entered():
                link_creator.response(Gtk.ResponseType.OK)

        link_location_entry.connect("activate", respond)
        link_name_entry.connect("activate", respond)

        link_location_entry.grab_focus()

        response = link_creator.run()
        link_creator.hide()

        if response == Gtk.ResponseType.OK:
            link_location = link_location_entry.get_text()
            link_name = link_name_entry.get_text()

            if link_location and link_name:
                return '[{} ""{}""]'.format(link_name, link_location)
            elif link_location:
                return link_location
            else:
                self.main_window.journal.show_message(
                    _("No link location has been entered"), error=True
                )

    @insert_handler
    def on_insert_bullet_list(self, sel_text):
        if sel_text:
            return "\n".join("- %s" % row for row in sel_text.splitlines())
        return self.bullet_list

    @insert_handler
    def on_insert_title(self, sel_text, level):
        markup = "=" * level
        return markup + " ", sel_text, " " + markup

    @insert_handler
    def on_insert_line(self, sel_text):
        return "\n====================\n"

    @insert_handler
    def on_insert_date_time(self, sel_text):
        format_string = self.main_window.journal.config.read("dateTimeString")
        return dates.format_date(format_string)

    @insert_handler
    def on_insert_line_break(self, sel_text):
        return "\\\\\n"
