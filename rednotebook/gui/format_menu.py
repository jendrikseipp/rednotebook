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

from gi.repository import Gtk

from rednotebook.gui import customwidgets


MENUITEMS_XML = """\
    <menuitem action="Bold"/>
    <menuitem action="Italic"/>
    <menuitem action="Monospace"/>
    <menuitem action="Underline"/>
    <menuitem action="Strikethrough"/>
    <menuitem action="Clear"/>
"""

TOOLBAR_XML = (
    """\
<ui>
<popup action="FormatMenu">
%s
</popup>
</ui>"""
    % MENUITEMS_XML
)

MENUBAR_XML = (
    """\
<menu action="FormatMenuBar">
%s
</menu>
"""
    % MENUITEMS_XML
)


class FormatMenu:
    FORMAT_TO_MARKUP = {
        "bold": "**",
        "italic": "//",
        "monospace": "``",
        "underline": "__",
        "strikethrough": "--",
    }

    def __init__(self, main_window):
        self.main_window = main_window
        self.setup()

    def setup(self):
        uimanager = self.main_window.uimanager

        # Create an ActionGroup
        actiongroup = Gtk.ActionGroup("FormatActionGroup")

        def apply_format(action):
            format_ = action.get_name().lower()
            iter_ = self.main_window.categories_tree_view.get_selected_node()
            if iter_:
                markup = self.FORMAT_TO_MARKUP[format_]
                text = self.main_window.categories_tree_view.get_iter_value(iter_)
                text = "{}{}{}".format(markup, text, markup)
                self.main_window.categories_tree_view.set_iter_value(iter_, text)
            else:
                self.main_window.day_text_field.apply_format(format_)

        def shortcut(char):
            # Translators: The Control (Ctrl) key
            return ""  # return ' (%s+%s)' % (_('Ctrl'), char)

        # Create actions
        actions = [
            (
                "Bold",
                Gtk.STOCK_BOLD,
                _("Bold") + shortcut("B"),
                "<Control>B",
                None,
                apply_format,
            ),
            (
                "Italic",
                Gtk.STOCK_ITALIC,
                _("Italic") + shortcut("I"),
                "<Control>I",
                None,
                apply_format,
            ),
            (
                "Monospace",
                None,
                _("Monospace") + shortcut("M"),
                "<Control>M",
                None,
                apply_format,
            ),
            (
                "Underline",
                Gtk.STOCK_UNDERLINE,
                _("Underline") + shortcut("U"),
                "<Control>U",
                None,
                apply_format,
            ),
            (
                "Strikethrough",
                Gtk.STOCK_STRIKETHROUGH,
                _("Strikethrough") + shortcut("K"),
                "<Control>K",
                None,
                apply_format,
            ),
            (
                "Clear",
                Gtk.STOCK_CLEAR,
                _("Clear format") + shortcut("R"),
                "<Control>R",
                None,
                self.on_clear_format,
            ),
            # Translators: Noun
            ("FormatMenuBar", None, _("_Format")),
        ]

        actiongroup.add_actions(actions)

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)

        # Add a UI description
        uimanager.add_ui_from_string(TOOLBAR_XML)

        # Create a Menu
        menu = uimanager.get_widget("/FormatMenu")

        self.main_window.format_button = customwidgets.ToolbarMenuButton(
            Gtk.STOCK_BOLD, menu
        )
        # Translators: Noun
        self.main_window.format_button.set_label(_("Format"))
        tip = _("Format the selected text or tag")
        self.main_window.format_button.set_tooltip_text(tip)
        self.main_window.builder.get_object("edit_toolbar").insert(
            self.main_window.format_button, -1
        )
        self.main_window.format_actiongroup = actiongroup

    def on_clear_format(self, action):
        editor = self.main_window.day_text_field
        sel_text = editor.get_selected_text()
        for markup in list(self.FORMAT_TO_MARKUP.values()) + ["=== ", " ==="]:
            sel_text = sel_text.replace(markup, "")
        editor.replace_selection(sel_text)
