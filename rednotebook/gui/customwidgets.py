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

import datetime
import logging
import os
import webbrowser

from gi.repository import GObject, Gtk


class ActionButton(Gtk.Button):
    def __init__(self, text, action):
        Gtk.Button.__init__(self, text)
        self.connect("clicked", action)


class UrlButton(ActionButton):
    def __init__(self, text, url):
        ActionButton.__init__(self, text, lambda _: webbrowser.open(url))


class CustomComboBoxEntry:
    def __init__(self, combo_box):
        self.combo_box = combo_box

        self.liststore = Gtk.ListStore(GObject.TYPE_STRING)
        self.entries = set()
        self.combo_box.set_model(self.liststore)
        self.combo_box.set_entry_text_column(0)
        self.entry = self.combo_box.get_child()

        # Autocompletion
        entry_completion = Gtk.EntryCompletion()
        entry_completion.set_model(self.liststore)
        entry_completion.set_minimum_key_length(1)
        entry_completion.set_text_column(0)
        self.entry.set_completion(entry_completion)

    def add_entry(self, entry):
        if entry not in self.entries:
            self.liststore.append([entry])
            self.entries.add(entry)

    def set_entries(self, value_list):
        self.clear()
        for entry in value_list:
            self.add_entry(entry)
        self.combo_box.set_model(self.liststore)

    def get_active_text(self):
        return self.entry.get_text()

    def set_active_text(self, text):
        return self.entry.set_text(text)

    def clear(self):
        self.combo_box.set_model(None)
        self.liststore.clear()
        self.entries.clear()
        self.set_active_text("")
        self.combo_box.set_model(self.liststore)


class CustomListView(Gtk.TreeView):
    def __init__(self, columns):
        """
        *columns* must be a list of (header, type) pairs e.g. [('title', str)].
        """
        Gtk.TreeView.__init__(self)
        headers, types = list(zip(*columns))
        # create a TreeStore with columns to use as the model
        self.set_model(Gtk.ListStore(*types))

        columns = [Gtk.TreeViewColumn(header) for header in headers]

        # add tvcolumns to tree_view
        for index, column in enumerate(columns):
            self.append_column(column)

            # create a CellRendererText to render the data
            cell_renderer = Gtk.CellRendererText()

            # add the cell to the tvcolumn and allow it to expand
            column.pack_start(cell_renderer, True)

            # Get markup for column, not text
            column.set_attributes(cell_renderer, markup=index)

            # Allow sorting on the column
            column.set_sort_column_id(index)

        # make it searchable
        self.set_search_column(1)


class Calendar(Gtk.Calendar):
    def __init__(self, week_numbers=False):
        Gtk.Calendar.__init__(self)
        self.set_property("show-week-numbers", week_numbers)

    def set_date(self, date):
        # Set the day temporarily to a day that is present in all months.
        self.select_day(1)

        # Gtk.Calendar show months in range [0,11].
        self.select_month(date.month - 1, date.year)

        # Select the day after the month and year have been set
        self.select_day(date.day)

    def get_date(self):
        year, month, day = Gtk.Calendar.get_date(self)
        return datetime.date(year, month + 1, day)


class Info(Gtk.InfoBar):
    icons = {Gtk.MessageType.ERROR: Gtk.STOCK_DIALOG_ERROR}

    def __init__(self):
        Gtk.InfoBar.__init__(self)
        self.title_label = Gtk.Label()
        self.msg_label = Gtk.Label()
        self.title_label.set_alignment(0.0, 0.5)
        self.msg_label.set_alignment(0.0, 0.5)

        vbox = Gtk.VBox(spacing=5)
        vbox.pack_start(self.title_label, False, False, 0)
        vbox.pack_start(self.msg_label, False, False, 0)

        self.image = Gtk.Image()

        content = self.get_content_area()
        content.pack_start(self.image, False, False, 0)
        content.pack_start(vbox, False, False, 0)

        self.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        self.connect("close", lambda x: self.hide())
        self.connect("response", self.on_response)

    def on_response(self, infobar, response_id):
        if response_id == Gtk.ResponseType.CLOSE:
            self.hide()

    def show_message(self, title, msg, msg_type):
        if not title:
            title = msg
            msg = ""
        self.title_label.set_markup("<b>%s</b>" % title)
        self.msg_label.set_markup(msg)
        self.set_message_type(msg_type)
        self.image.set_from_stock(
            self.icons.get(msg_type, Gtk.STOCK_DIALOG_INFO), Gtk.IconSize.DIALOG
        )
        self.show_all()


# ------------------------- Assistant Pages ------------------------------------


class AssistantPage(Gtk.VBox):
    def __init__(self, *args, **kwargs):
        GObject.GObject.__init__(self, *args, **kwargs)

        self.set_spacing(5)
        self.set_border_width(10)

        self.header = None
        self.show_all()

    def _add_header(self):
        self.header = Gtk.Label()
        self.header.set_markup("Unset")
        self.header.set_alignment(0.0, 0.5)
        self.pack_start(self.header, False, False, 0)
        self.separator = Gtk.HSeparator()
        self.pack_start(self.separator, False, False, 0)
        self.reorder_child(self.header, 0)
        self.reorder_child(self.separator, 1)
        self.show_all()

    def set_header(self, text):
        if not self.header:
            self._add_header()
        self.header.set_markup(text)


class RadioButtonPage(AssistantPage):
    def __init__(self, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)

        self.buttons = []

    def add_radio_option(self, object, label, tooltip=""):
        sensitive = object.is_available()

        group = self.buttons[0] if self.buttons else None
        button = Gtk.RadioButton(group=group)
        button.set_tooltip_markup(tooltip)
        button.set_label(label)
        button.object = object
        button.set_sensitive(sensitive)
        self.pack_start(button, False, False, 0)
        self.buttons.append(button)

        if tooltip:
            description = Gtk.Label()
            description.set_alignment(0.0, 0.5)
            description.set_markup(" " * 10 + tooltip)
            description.set_sensitive(sensitive)
            self.pack_start(description, False, False, 0)

    def get_selected_object(self):
        for button in self.buttons:
            if button.get_active():
                return button.object


class PathChooserPage(AssistantPage):
    def __init__(self, assistant, *args, **kwargs):
        AssistantPage.__init__(self, *args, **kwargs)

        self.assistant = assistant

        self.last_path = None

        self.chooser = Gtk.FileChooserWidget()
        self.chooser.connect("selection-changed", self.on_path_changed)

        self.pack_start(self.chooser, True, True, 0)

    def _remove_filters(self):
        for filter in self.chooser.list_filters():
            self.chooser.remove_filter(filter)

    def prepare(self, porter):
        self._remove_filters()

        self.path_type = porter.PATHTYPE.upper()
        path = porter.DEFAULTPATH
        extension = porter.EXTENSION
        helptext = porter.PATHTEXT

        if helptext:
            self.set_header(helptext)

        if self.path_type == "DIR":
            self.chooser.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        elif self.path_type == "FILE":
            self.chooser.set_action(Gtk.FileChooserAction.OPEN)
        elif self.path_type == "NEWFILE":
            self.chooser.set_action(Gtk.FileChooserAction.SAVE)
        else:
            logging.error('Wrong path_type "%s"' % self.path_type)

        if self.path_type in ["FILE", "NEWFILE"] and extension:
            filter = Gtk.FileFilter()
            filter.set_name(extension)
            filter.add_pattern("*." + extension)
            self.chooser.add_filter(filter)

        if self.last_path and os.path.exists(self.last_path):
            path = self.last_path

        if os.path.isdir(path):
            self.chooser.set_current_folder(path)
        else:
            dirname, basename = os.path.split(path)
            filename, _ = os.path.splitext(basename)
            self.chooser.set_current_folder(dirname)
            self.chooser.set_current_name(filename + "." + extension)

    def get_selected_path(self):
        self.last_path = self.chooser.get_filename()
        return self.last_path

    def on_path_changed(self, widget):
        return


class Assistant(Gtk.Assistant):
    def __init__(self, journal, *args, **kwargs):
        GObject.GObject.__init__(self, *args, **kwargs)

        self.journal = journal

        self.set_size_request(1000, 500)

        self.connect("cancel", self._on_cancel)
        self.connect("close", self._on_close)
        self.connect("prepare", self._on_prepare)

    def run(self):
        """
        Show assistant
        """

    def _on_cancel(self, assistant):
        """
        Cancelled -> Hide assistant
        """
        self.hide()

    def _on_close(self, assistant):
        """
        Do the action
        """

    def _on_prepare(self, assistant, page):
        """
        Called when a new page should be prepared, before it is shown
        """


class TemplateBar(Gtk.HBox):
    def __init__(self):
        GObject.GObject.__init__(self)
        self.set_spacing(2)
        label = Gtk.Label(label="<b>%s</b>:" % _("Template"))
        label.set_use_markup(True)
        self.pack_start(label, False, False, 0)
        self.save_insert_button = Gtk.Button(_("Save and insert"))
        self.pack_start(self.save_insert_button, False, False, 0)
        self.save_button = Gtk.Button(stock=Gtk.STOCK_SAVE)
        self.pack_start(self.save_button, False, False, 0)
        self.close_button = Gtk.Button(stock=Gtk.STOCK_CLOSE)
        self.pack_start(self.close_button, False, False, 0)
        self.show_all()


class ToolbarMenuButton(Gtk.ToolButton):
    def __init__(self, stock_id, menu):
        Gtk.ToolButton.__init__(self)
        self.set_stock_id(stock_id)
        self._menu = menu
        self.connect("clicked", self._on_clicked)
        self.show_all()

    def _on_clicked(self, button):
        self._menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())

    def set_menu(self, menu):
        self._menu = menu
