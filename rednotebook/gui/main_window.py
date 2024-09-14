# -----------------------------------------------------------------------
# Copyright (c) 2008-2024 Jendrik Seipp
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

from collections import OrderedDict
import datetime
import logging
import os
from unittest import mock
import urllib.parse

from gi.repository import Gdk, GdkPixbuf, GObject, Gtk, GtkSource, Pango

from rednotebook.gui.options import OptionsManager
from rednotebook import info, templates
from rednotebook.gui import (
    browser,
    browser_cef,
    categories,
    customwidgets,
    editor,
    format_menu,
    insert_menu,
    search,
)
from rednotebook.gui.customwidgets import CustomComboBoxEntry, CustomListView
from rednotebook.gui.exports import ExportAssistant
from rednotebook.gui.menu import MainMenuBar
from rednotebook.util import dates, filesystem, markup, urls, utils


class MainWindow:
    """
    Class that holds the reference to the main glade file and handles
    all actions
    """

    def __init__(self, journal):
        self.journal = journal

        # Load Glade file.
        # TODO: Remove workaround for Windows once it is no longer needed.
        self.gladefile = os.path.join(filesystem.files_dir, "main_window.glade")
        self.builder = Gtk.Builder()
        # Register GtkSourceView so builder can use it when loading the file
        # https://stackoverflow.com/q/10524196/434217
        GObject.type_register(GtkSource.View)
        if filesystem.IS_WIN:
            from xml.etree import ElementTree as ET

            tree = ET.parse(self.gladefile)
            for node in tree.iter():
                if "translatable" in node.attrib:
                    node.text = _(node.text)
            xml_text = ET.tostring(tree.getroot(), encoding="unicode")
            self.builder = Gtk.Builder.new_from_string(xml_text, len(xml_text))
        else:
            self.builder.set_translation_domain("rednotebook")
            self.builder.add_from_file(self.gladefile)

        self.main_frame = self.builder.get_object("main_frame")
        self.main_frame.set_application(journal)
        self.main_frame.set_title("RedNotebook")
        icon = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(filesystem.frame_icon_dir, "rn-128.png")
        )
        self.main_frame.set_icon(icon)

        self.is_fullscreen = False

        self.uimanager = Gtk.UIManager()

        # Before fetching the menubar, add all menus and actiongroups.
        # Setup the toolbar items first to avoid warnings for missing actions.
        insert_menu.InsertMenu(self)
        format_menu.FormatMenu(self)
        self.menubar_manager = MainMenuBar(self)
        self.menubar = self.menubar_manager.get_menu_bar()
        main_vbox = self.builder.get_object("vbox3")
        main_vbox.pack_start(self.menubar, False, False, 0)
        main_vbox.reorder_child(self.menubar, 0)

        self.undo_action = self.uimanager.get_action("/MainMenuBar/Edit/Undo")
        self.redo_action = self.uimanager.get_action("/MainMenuBar/Edit/Redo")

        self.calendar = MainCalendar(self.journal, self.builder.get_object("calendar"))
        self.day_text_field = DayEditor(self.builder.get_object("day_text_view"))
        self.day_text_field.connect(
            "can-undo-redo-changed", self.update_undo_redo_buttons
        )
        self.update_undo_redo_buttons()
        self.day_text_field.day_text_view.grab_focus()
        can_spell_check = self.day_text_field.can_spell_check()
        spell_check_enabled = bool(self.journal.config.read("spellcheck"))
        for actiongroup in self.menubar_manager.uimanager.get_action_groups():
            if actiongroup.get_name() == "MainMenuActionGroup":
                for action in actiongroup.list_actions():
                    if action.get_name() == "CheckSpelling":
                        action.set_sensitive(can_spell_check)
                        action.set_active(spell_check_enabled and can_spell_check)
        self.day_text_field.enable_spell_check(spell_check_enabled)

        self.statusbar = Statusbar(self.builder.get_object("statusbar"))

        self.new_entry_dialog = NewEntryDialog(self)

        self.categories_tree_view = categories.CategoriesTreeView(
            self.builder.get_object("categories_tree_view"), self
        )

        self.new_entry_dialog.categories_tree_view = self.categories_tree_view

        self.back_one_day_button = self.builder.get_object("back_one_day_button")
        self.today_button = self.builder.get_object("today_button")
        self.forward_one_day_button = self.builder.get_object("forward_one_day_button")

        self.edit_pane = self.builder.get_object("edit_pane")
        self.text_vbox = self.builder.get_object("text_vbox")

        use_internal_preview = self.journal.config.read("useInternalPreview", 1)
        if use_internal_preview and browser.WebKit2:

            class Preview(browser.HtmlView):
                def __init__(self, journal):
                    browser.HtmlView.__init__(self)
                    self.journal = journal
                    self.internal = True

                def show_day(self, new_day):
                    html = self.journal.convert(
                        new_day.text, "xhtml", use_gtk_theme=True
                    )
                    self.load_html(html)

                def shutdown(self):
                    pass

            self.html_editor = Preview(self.journal)
            self.html_editor.connect("button-press-event", self.on_browser_clicked)
            self.html_editor.connect("decide-policy", self.on_browser_decide_policy)
            self.text_vbox.pack_start(self.html_editor, True, True, 0)
            self.html_editor.set_editable(False)
        elif use_internal_preview and browser_cef.get_html_view_class():
            HtmlView = browser_cef.get_html_view_class()

            class Preview(HtmlView):
                def __init__(self, journal):
                    super().__init__()
                    self.journal = journal
                    self.internal = True

                def show_day(self, new_day):
                    html = self.journal.convert(
                        new_day.text, "xhtml", use_gtk_theme=True
                    )
                    self.load_html(html)

                def highlight(self, text):
                    pass

            self.html_editor = Preview(self.journal)
            self.html_editor.connect(
                "on-url-clicked", lambda _, url: self.navigate_to_uri(url)
            )
            self.text_vbox.pack_start(self.html_editor, True, True, 0)
        else:
            self.html_editor = mock.MagicMock()
            self.html_editor.internal = False
            preview_button = self.builder.get_object("preview_button")
            preview_button.set_label(_("Preview in Browser"))

        self.html_editor.hide()

        self.preview_mode = False

        # Let the edit_paned respect its childs size requests
        self.edit_pane.child_set_property(self.text_vbox, "shrink", False)

        # Add InfoBar.
        self.infobar = customwidgets.Info()
        self.text_vbox.pack_start(self.infobar, False, False, 0)
        self.text_vbox.reorder_child(self.infobar, 1)

        # Add TemplateBar.
        self.template_bar = customwidgets.TemplateBar()
        self.text_vbox.pack_start(self.template_bar, False, False, 0)
        self.text_vbox.reorder_child(self.template_bar, 1)
        self.template_bar.hide()

        self.load_values_from_config()

        self.main_frame.show()

        self.options_manager = OptionsManager(self)
        self.export_assistant = ExportAssistant(self.journal)
        self.export_assistant.set_transient_for(self.main_frame)

        self.setup_clouds()
        self.setup_search()

        # Create an event->method dictionary and connect it to the widgets
        dic = {
            "on_back_one_day_button_clicked": self.on_back_one_day_button_clicked,
            "on_today_button_clicked": self.on_today_button_clicked,
            "on_forward_one_day_button_clicked": self.on_forward_one_day_button_clicked,
            "on_preview_button_clicked": self.on_preview_button_clicked,
            "on_edit_button_clicked": self.on_edit_button_clicked,
            "on_main_frame_configure_event": self.on_main_frame_configure_event,
            "on_main_frame_window_state_event": self.on_main_frame_window_state_event,
            "on_add_new_entry_button_clicked": self.on_add_new_entry_button_clicked,
            "on_main_frame_delete_event": self.on_main_frame_delete_event,
            # connect_signals can only be called once, it seems
            # Otherwise RuntimeWarnings are raised: RuntimeWarning: missing handler '...'
        }
        self.builder.connect_signals(dic)

        self.set_shortcuts()
        self.setup_stats_dialog()

        self.template_manager = templates.TemplateManager(self)
        self.template_manager.make_empty_template_files()
        self.setup_template_menu()

        self.set_tooltips()
        self.setup_tray_icon()

        # Show/hide the "tags" panel on the right.
        self.builder.get_object("annotations_pane").set_visible(
            self.journal.config.read("showTagsPane")
        )

    def set_tooltips(self):
        """
        Little work-around:
        Tooltips are not shown for menuitems that have been created with uimanager.
        We have to do it manually.
        """
        groups = self.uimanager.get_action_groups()
        for group in groups:
            actions = group.list_actions()
            for action in actions:
                widgets = action.get_proxies()
                if tooltip := action.get_property("tooltip"):
                    for widget in widgets:
                        widget.set_tooltip_markup(tooltip)

    def set_shortcuts(self):
        """
        This method actually is not responsible for the Ctrl-C etc. actions
        """
        self.accel_group = self.builder.get_object("accelgroup1")
        self.main_frame.add_accel_group(self.accel_group)

        self.main_frame.connect("key-press-event", self._on_key_press_event)

        shortcuts = [
            (self.back_one_day_button, "clicked", "<Ctrl>Page_Up"),
            (self.today_button, "clicked", "<Alt>Home"),
            (self.forward_one_day_button, "clicked", "<Ctrl>Page_Down"),
        ]
        for button, signal, shortcut in shortcuts:
            (keyval, mod) = Gtk.accelerator_parse(shortcut)
            button.add_accelerator(
                signal, self.accel_group, keyval, mod, Gtk.AccelFlags.VISIBLE
            )

    def _on_key_press_event(self, widget, event):
        # Exit fullscreen mode with ESC.
        if event.keyval == Gdk.KEY_Escape and self.is_fullscreen:
            self.toggle_fullscreen()

    # TRAY-ICON / CLOSE --------------------------------------------------------

    def setup_tray_icon(self):
        self.tray_icon = Gtk.StatusIcon()
        self.tray_icon.set_name("RedNotebook")
        visible = self.journal.config.read("closeToTray") == 1
        self.tray_icon.set_visible(visible)
        logging.debug(f"Tray icon visible: {visible}")

        self.tray_icon.set_tooltip_text("RedNotebook")
        icon_file = os.path.join(self.journal.dirs.frame_icon_dir, "rn-32.png")
        self.tray_icon.set_from_file(icon_file)

        self.tray_icon.connect("activate", self.on_tray_icon_activated)
        self.tray_icon.connect("popup-menu", self.on_tray_popup_menu)

    def on_tray_icon_activated(self, tray_icon):
        if self.main_frame.get_property("visible"):
            self.hide()
        else:
            self.show()

    def on_tray_popup_menu(self, _status_icon, button, activate_time):
        """
        Called when the user right-clicks the tray icon
        """

        tray_menu_xml = """
        <ui>
        <popup action="TrayMenu">
            <menuitem action="Show"/>
            <menuitem action="Quit"/>
        </popup>
        </ui>"""

        # Create an ActionGroup
        actiongroup = Gtk.ActionGroup("TrayActionGroup")

        # Create actions
        actiongroup.add_actions(
            [
                (
                    "Show",
                    None,
                    _("Show RedNotebook"),
                    None,
                    None,
                    lambda widget: self.show(),
                ),
                ("Quit", None, None, None, None, self.on_quit_activate),
            ]
        )

        # Add the actiongroup to the uimanager
        self.uimanager.insert_action_group(actiongroup, 0)

        # Add a UI description
        self.uimanager.add_ui_from_string(tray_menu_xml)

        # Create a Menu
        menu = self.uimanager.get_widget("/TrayMenu")

        menu.popup(None, None, None, None, button, activate_time)

    def show(self):
        self.main_frame.show()
        self.load_values_from_config()

    def hide(self):
        self.add_values_to_config()
        self.journal.save_to_disk()
        self.main_frame.hide()

    def on_main_frame_delete_event(self, widget, event):
        """
        Exit if not close_to_tray
        """
        logging.debug("Main frame destroyed")

        if self.journal.config.read("closeToTray"):
            self.hide()
        else:
            self.html_editor.shutdown()
            self.journal.exit()

        # We never call the default handler. Otherwise, the window would be
        # destroyed, but we might no actually want to exit.
        return True

    def on_quit_activate(self, widget):
        """
        User selected quit from the menu -> exit unconditionally
        """
        self.journal.exit()

    # -------------------------------------------------------- TRAY-ICON / CLOSE

    def setup_stats_dialog(self):
        self.stats_dialog = self.builder.get_object("stats_dialog")
        self.stats_dialog.set_transient_for(self.main_frame)
        overall_box = self.builder.get_object("overall_box")
        day_box = self.builder.get_object("day_stats_box")
        columns = [("1", str), ("2", str)]
        overall_list = CustomListView(columns)
        day_list = CustomListView(columns)
        overall_box.pack_start(overall_list, True, True, 0)
        day_box.pack_start(day_list, True, True, 0)
        self.stats_dialog.overall_list = overall_list
        self.stats_dialog.day_list = day_list
        for list in [overall_list, day_list]:
            list.set_headers_visible(False)

    # MODE-SWITCHING -----------------------------------------------------------

    def change_mode(self, preview):
        edit_scroll = self.builder.get_object("text_scrolledwindow")
        edit_button = self.builder.get_object("edit_button")
        preview_button = self.builder.get_object("preview_button")

        size_group = Gtk.SizeGroup(Gtk.SizeGroupMode.HORIZONTAL)
        size_group.add_widget(edit_button)
        size_group.add_widget(preview_button)

        if preview:
            # Enter preview mode
            edit_scroll.hide()
            self.html_editor.show()

            edit_button.show()
            preview_button.hide()

            self.disable_undo_redo_buttons()
        else:
            # Enter edit mode
            edit_scroll.show()
            self.html_editor.hide()

            preview_button.show()
            edit_button.hide()

            self.update_undo_redo_buttons()

        # Interacting with the CEF browser makes the main window inactive, so
        # we make it active again.
        self.main_frame.present()

        self.template_manager.set_template_menu_sensitive(not preview)
        self.insert_actiongroup.set_sensitive(not preview)
        self.format_actiongroup.set_sensitive(not preview)
        self.insert_button.set_sensitive(not preview)
        self.format_button.set_sensitive(not preview)
        for action in ["Cut", "Paste"]:
            self.uimanager.get_widget(f"/MainMenuBar/Edit/{action}").set_sensitive(
                not preview
            )

        self.preview_mode = preview

    def on_edit_button_clicked(self, button):
        # The day's text is already in the editor.
        self.change_mode(preview=False)
        # Select (not only highlight) previously selected text by giving focus
        # to the day editor.
        GObject.idle_add(self.day_text_field.day_text_view.grab_focus)

    def on_preview_button_clicked(self, button):
        self.journal.save_old_day()
        if self.html_editor.internal:
            self.html_editor.show_day(self.day)
            self.change_mode(preview=True)
        else:
            date_format = self.journal.config.read("exportDateFormat")
            date_string = dates.format_date(date_format, self.day.date)
            markup_string = markup.get_markup_for_day(self.day, "xhtml")
            html = self.journal.convert(
                markup_string,
                "xhtml",
                headers=[f"{date_string} - RedNotebook", "", ""],
                options={"toc": 0},
            )
            utils.show_html_in_browser(
                html, os.path.join(self.journal.dirs.temp_dir, "day.html")
            )

    def on_browser_clicked(self, webview, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            # Double-click -> Change to edit mode.
            self.change_mode(preview=False)
            # Stop processing this event.
            return True
        elif event.button == 3:
            # Right-click -> don't show context menu.
            return True

    # ----------------------------------------------------------- MODE-SWITCHING

    def setup_search(self):
        always_show_results = not browser.WebKit2
        self.search_tree_view = search.SearchTreeView(self, always_show_results)
        self.search_tree_view.show()
        self.search_scroll = Gtk.ScrolledWindow()
        if always_show_results:
            self.search_scroll.show()
        self.search_scroll.add(self.search_tree_view)
        self.search_box = search.SearchComboBox(Gtk.ComboBox.new_with_entry(), self)
        self.search_box.combo_box.show()
        self.replace_box = search.ReplaceBox(self)
        search_container = self.builder.get_object("search_container")
        search_container.pack_start(self.search_box.combo_box, False, False, 0)
        search_container.pack_start(self.replace_box, False, True, 0)
        search_container.pack_start(self.search_scroll, True, True, 0)

    def setup_clouds(self):
        if browser.WebKit2:
            from rednotebook.gui import clouds

            self.cloud = clouds.Cloud(self.journal)
            self.builder.get_object("search_container").pack_end(
                self.cloud, True, True, 0
            )
        else:
            self.cloud = mock.MagicMock()

    def on_main_frame_configure_event(self, widget, event):
        """
        Is called when the frame size is changed. Unfortunately this is
        the way to go as asking for frame.get_size() at program termination
        gives strange results.
        """
        main_frame_width, main_frame_height = self.main_frame.get_size()
        self.journal.config["mainFrameWidth"] = main_frame_width
        self.journal.config["mainFrameHeight"] = main_frame_height

    def on_main_frame_window_state_event(self, widget, event):
        """
        The "window-state-event" signal is emitted when window state
        of widget changes. For example, for a toplevel window this
        event is signaled when the window is iconified, deiconified,
        minimized, maximized, made sticky, made not sticky, shaded or
        unshaded.
        """
        if event.changed_mask & Gdk.WindowState.MAXIMIZED:
            maximized = bool(event.new_window_state & Gdk.WindowState.MAXIMIZED)
            self.journal.config["mainFrameMaximized"] = int(maximized)

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.main_frame.unfullscreen()
            self.is_fullscreen = False
        else:
            self.main_frame.fullscreen()
            self.is_fullscreen = True

    def on_back_one_day_button_clicked(self, widget):
        self.journal.go_to_prev_day()

    def on_today_button_clicked(self, widget):
        actual_date = datetime.date.today()
        self.journal.change_date(actual_date)

    def on_forward_one_day_button_clicked(self, widget):
        self.journal.go_to_next_day()

    def on_browser_decide_policy(self, webview, decision, decision_type):
        """
        We want to load files and links externally.
        """
        if decision_type == browser.WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            action = decision.get_navigation_action()
            if action.is_user_gesture():
                uri = action.get_request().get_uri()
                self.navigate_to_uri(uri)
                decision.ignore()

        # Stop processing this event.
        return True

    def navigate_to_uri(self, uri):
        logging.info(f'Navigating to URI "{uri}"')
        if urls.is_entry_reference_uri(uri):
            self.navigate_to_referenced_entry(uri)
        else:
            urls.open_url(uri)

    def navigate_to_referenced_entry(self, entry_reference_uri):
        entry_reference_uri = urllib.parse.urlparse(entry_reference_uri)
        date = dates.get_date_from_date_string(entry_reference_uri.fragment)
        self.journal.change_date(date)

    def get_new_journal_dir(self, title, message):
        dir_chooser = self.builder.get_object("dir_chooser")
        dir_chooser.set_transient_for(self.main_frame)
        label = self.builder.get_object("dir_chooser_label")

        label.set_markup(f"<b>{message}</b>")
        dir_chooser.set_current_folder(os.path.dirname(self.journal.dirs.data_dir))

        response = dir_chooser.run()
        # Retrieve the dir now, because it will be cleared by the call to hide().
        new_dir = dir_chooser.get_filename()
        dir_chooser.hide()

        if response == Gtk.ResponseType.OK:
            if new_dir is None:
                self.journal.show_message(_("No directory selected."), error=True)
                return None
            return new_dir
        return None

    def show_save_error_dialog(self, exit_imminent):
        dialog = self.builder.get_object("save_error_dialog")
        dialog.set_transient_for(self.main_frame)

        exit_without_save_button = self.builder.get_object("exit_without_save_button")
        if exit_imminent:
            exit_without_save_button.show()
        else:
            exit_without_save_button.hide()

        answer = dialog.run()
        dialog.hide()

        if answer == Gtk.ResponseType.OK:
            # Even if the user aborts the Save-As dialog, we don't want to exit.
            self.journal.is_allowed_to_exit = False
            # Let the user select a new directory. Nothing has been saved yet.
            self.menubar_manager.on_save_as_menu_item_activate(None)
        elif answer == Gtk.ResponseType.CANCEL and exit_imminent:
            self.journal.is_allowed_to_exit = False
        # Do nothing if user wants to exit without saving

    def add_values_to_config(self):
        config = self.journal.config

        left_div = self.builder.get_object("main_pane").get_position()
        config["leftDividerPosition"] = left_div

        right_div = self.edit_pane.get_position()
        config["rightDividerPosition"] = right_div

        # Remember if window was maximized in separate method

        # Remember window position
        config["mainFrameX"], config["mainFrameY"] = self.main_frame.get_position()

    def load_values_from_config(self):
        config = self.journal.config
        main_frame_width = config.read("mainFrameWidth")
        main_frame_height = config.read("mainFrameHeight")

        screen_width = Gdk.Screen.width()
        screen_height = Gdk.Screen.height()

        main_frame_width = min(main_frame_width, screen_width)
        main_frame_height = min(main_frame_height, screen_height)

        self.main_frame.resize(main_frame_width, main_frame_height)

        if config.read("mainFrameMaximized"):
            self.main_frame.maximize()
        else:
            # If window is not maximized, restore last position
            x = config.read("mainFrameX")
            y = config.read("mainFrameY")
            try:
                x, y = int(x), int(y)
                # Set to 0 if value is below 0
                if 0 <= x <= screen_width and 0 <= y <= screen_height:
                    self.main_frame.move(x, y)
                else:
                    self.main_frame.set_position(Gtk.WindowPosition.CENTER)
            except (ValueError, TypeError):
                # Values have not been set or are not valid integers
                self.main_frame.set_position(Gtk.WindowPosition.CENTER)

        self.builder.get_object("main_pane").set_position(
            config.read("leftDividerPosition")
        )
        # By default do not show tags pane.
        self.edit_pane.set_position(
            config.read("rightDividerPosition", main_frame_width)
        )

        self.set_font(config.read("mainFont", editor.DEFAULT_FONT))
        
        self.set_auto_indent()
        
    def set_auto_indent(self):
        auto_indent = self.journal.config.read("autoIndent") == 1
        self.day_text_field.day_text_view.set_auto_indent(auto_indent)

    def set_font(self, font_name):
        self.day_text_field.set_font(font_name)
        self.html_editor.set_font_size(
            Pango.FontDescription(font_name).get_size() / Pango.SCALE
        )

    def setup_template_menu(self):
        def update_menu(button):
            self.template_button.set_menu(self.template_manager.get_menu())

        self.template_button = customwidgets.ToolbarMenuButton(
            "edit-paste", self.template_manager.get_menu()
        )
        self.template_button.set_label(_("Template"))
        self.template_button.connect("clicked", update_menu)
        self.template_button.set_tooltip_text(
            _(
                "Insert this weekday's template. "
                "Click the arrow on the right for more options"
            )
        )
        self.builder.get_object("edit_toolbar").insert(self.template_button, 2)

    def on_add_new_entry_button_clicked(self, widget):
        self.categories_tree_view._on_add_entry_clicked(None)

    def set_date(self, new_month, new_date, day):
        """
        Notes: When switching days in edit mode almost all processing
        time is used for highlighting the markup (searching regexes).
        """
        self.day = day
        self.categories_tree_view.clear()

        self.calendar.set_date(new_date)
        self.calendar.set_month(new_month)

        # Regardless of the mode, we always keep the editor updated, to be able
        # to always save the day.
        self.day_text_field.show_day(day)

        # Only switch mode automatically if set in preferences.
        if self.journal.config.read("autoSwitchMode") and self.html_editor.internal:
            if day.has_text and not self.preview_mode:
                self.change_mode(preview=True)
            elif not day.has_text and self.preview_mode:
                self.change_mode(preview=False)

        if self.preview_mode:
            # Converting markup to html takes time, so only do it when necessary
            self.html_editor.show_day(day)

        self.categories_tree_view.set_day_content(day)

    def set_day_text(self, new_text):
        self.day_text_field.set_text(new_text)

    def get_day_text(self):
        return self.day_text_field.get_text()

    def highlight_text(self, search_text):
        self.html_editor.highlight(search_text)
        self.day_text_field.highlight(search_text)

    def show_message(self, title, msg, msg_type):
        if msg_type == Gtk.MessageType.ERROR:
            self.infobar.show_message(title, msg, msg_type)
        else:
            self.statusbar.show_message(title, msg, msg_type)

    def disable_undo_redo_buttons(self):
        self.undo_action.set_sensitive(False)
        self.redo_action.set_sensitive(False)

    def update_undo_redo_buttons(self, _gobject=None):
        """Enable/disable undo+redo actions according to the current text buffer

        The _gobject parameter is unused, but it's necessary for the method
        to be connected to a GObject signal.
        """
        can_undo = self.day_text_field.day_text_buffer.can_undo()
        self.undo_action.set_sensitive(can_undo)
        can_redo = self.day_text_field.day_text_buffer.can_redo()
        self.redo_action.set_sensitive(can_redo)


class DayEditor(editor.Editor):
    n_recent_buffers = 10  # How many recent buffers to store
    _t2t_highlighting = None
    _style_scheme = None

    def __init__(self, *args, **kwargs):
        editor.Editor.__init__(self, *args, **kwargs)
        self.day = None
        # Store buffers for recently edited days - these preserve undo history
        # and cursor position. Once a buffer drops out of this, it needs to be
        # recreated: at this point, the cursor and undo are lost.
        self.recent_buffers = OrderedDict()

    def _get_t2t_highlighting(self):
        if self._t2t_highlighting is None:
            # Load our own copy of t2t syntax highlighting
            lm = GtkSource.LanguageManager.get_default()
            search_path = lm.get_search_path()
            if filesystem.files_dir not in search_path:
                search_path.insert(0, filesystem.files_dir)
                lm.set_search_path(search_path)
            self._t2t_highlighting = lm.get_language("t2t")
        return self._t2t_highlighting

    def _get_style_scheme(self):
        if self._style_scheme is None:
            # Load our customised variant of the Tango scheme
            sm = GtkSource.StyleSchemeManager.get_default()
            if filesystem.files_dir not in sm.get_search_path():
                sm.prepend_search_path(filesystem.files_dir)
            self._style_scheme = sm.get_scheme("rednotebook")
        return self._style_scheme

    def _get_buffer(self, key, text):
        """Get an editing buffer for a given item

        If key is in our cache of recently used buffers, its buffer is retrieved
        and text is ignored. Otherwise, a new buffer is constructed with text.
        """
        if key in self.recent_buffers:
            self.recent_buffers.move_to_end(key)
            return self.recent_buffers[key]

        buf = self.recent_buffers[key] = GtkSource.Buffer.new()
        buf.set_style_scheme(self._get_style_scheme())
        buf.set_language(self._get_t2t_highlighting())
        # Use butter1 (yellow) from Tango theme for highlighting.
        # I couldn't find a way to take the background color from the theme directly.
        buf.create_tag("highlighter", background="#fce94f")
        buf.begin_not_undoable_action()
        buf.set_text(text)
        buf.end_not_undoable_action()

        if len(self.recent_buffers) > self.n_recent_buffers:
            self.recent_buffers.popitem(last=False)

        # Only one buffer is added at a time, so the 'if' above should always
        # keep us at most n_recent_buffers. If code is added to add to the list
        # elsewhere, it should check the maximum length as well.
        assert len(self.recent_buffers) <= self.n_recent_buffers

        return buf

    def _get_buffer_for_day(self, day):
        return self._get_buffer(day.date, day.text)

    def show_day(self, new_day):
        # Show new day
        self.day = new_day
        buf = self._get_buffer_for_day(new_day)
        self.replace_buffer(buf)
        self.day_text_view.grab_focus()

        if self.search_text:
            # If a search is currently made, scroll to the text and return.
            GObject.idle_add(self.scroll_to_text, self.search_text)
            GObject.idle_add(self.highlight, self.search_text)
            return

    def show_template(self, title, text):
        buf = self._get_buffer(("template", title), text)
        self.replace_buffer(buf)
        self.day_text_view.grab_focus()

    def clear_buffers(self):
        self.recent_buffers.clear()


class NewEntryDialog:
    def __init__(self, main_frame):
        dialog = main_frame.builder.get_object("new_entry_dialog")
        self.dialog = dialog
        dialog.set_transient_for(main_frame.main_frame)

        self.main_frame = main_frame
        self.journal = self.main_frame.journal
        self.categories_combo_box = CustomComboBoxEntry(
            main_frame.builder.get_object("categories_combo_box")
        )
        self.new_entry_combo_box = CustomComboBoxEntry(
            main_frame.builder.get_object("entry_combo_box")
        )

        # Let the user finish a new category entry by hitting ENTER
        def respond(widget):
            if self._text_entered():
                self.dialog.response(Gtk.ResponseType.OK)

        self.new_entry_combo_box.entry.connect("activate", respond)
        self.categories_combo_box.entry.connect("activate", respond)

        self.categories_combo_box.combo_box.connect("changed", self.on_category_changed)

    def on_category_changed(self, widget):
        """Show old entries in ComboBox when a new category is selected"""
        category = self.categories_combo_box.get_active_text()
        old_entries = self.journal.get_entries(category)
        self.new_entry_combo_box.set_entries(old_entries)

        # only make the entry submittable, if text has been entered
        self.dialog.set_response_sensitive(Gtk.ResponseType.OK, self._text_entered())

    def _text_entered(self):
        return bool(self.categories_combo_box.get_active_text())

    def show_dialog(self, category=""):
        # Use last used category.
        last_category = self.categories_tree_view.last_category

        # Has to be first, because it may be populated later
        self.new_entry_combo_box.clear()

        # Show the list of categories
        self.categories_combo_box.set_entries(self.categories_tree_view.categories)

        self.categories_combo_box.set_active_text(category or last_category or "")

        if category:
            # We already know the category so let's get the entry
            self.new_entry_combo_box.combo_box.grab_focus()
        else:
            self.categories_combo_box.combo_box.grab_focus()

        response = self.dialog.run()
        self.dialog.hide()

        if response != Gtk.ResponseType.OK:
            return

        category_name = self.categories_combo_box.get_active_text()
        if not self.categories_tree_view.check_category(category_name):
            return

        entry_text = self.new_entry_combo_box.get_active_text()

        self.categories_tree_view.add_entry(category_name, entry_text)

        # Update cloud
        self.main_frame.cloud.update()


class Statusbar:
    def __init__(self, statusbar):
        self.statusbar = statusbar
        self.context_id = self.statusbar.get_context_id(info.program_name)
        self.last_message_id = None
        self.timespan = 10

    def remove_message(self):
        self.statusbar.remove(self.context_id, self.last_message_id)

    def _show_text(self, text, countdown=True):
        if self.last_message_id is not None:
            self.remove_message()
        self.last_message_id = self.statusbar.push(self.context_id, text)
        if countdown:
            self.start_countdown()

    def show_message(self, title, msg, msg_type):
        text = f"{title}: {msg}" if title and msg else title or msg
        self._show_text(text)

    def start_countdown(self):
        self.time_left = self.timespan
        self.countdown = GObject.timeout_add(1000, self.count_down)

    def count_down(self):
        self.time_left -= 1
        if self.time_left <= 0:
            GObject.source_remove(self.countdown)
            self._show_text("", countdown=False)
        return True


class MainCalendar:
    def __init__(self, journal, calendar):
        self.journal = journal
        self.calendar = calendar

        if self.journal.config.read("weekNumbers"):
            calendar.set_property("show-week-numbers", True)

        self.date_listener = self.calendar.connect("day-selected", self.on_day_selected)

    def on_day_selected(self, _cal):
        self.journal.change_date(self.get_date())

    def set_date(self, date):
        if date == self.get_date():
            return

        # We do not want to listen to programmatic date changes.
        self.calendar.handler_block(self.date_listener)

        # We need to set the day temporarily to a day that is present in all months.
        self.calendar.select_day(1)

        # GTK shows months in range [0,11].
        self.calendar.select_month(date.month - 1, date.year)

        # Select the day after the month and year have been set.
        self.calendar.select_day(date.day)

        # We want to listen to manual date changes.
        self.calendar.handler_unblock(self.date_listener)

    def get_date(self):
        year, month, day = self.calendar.get_date()
        return datetime.date(year, month + 1, day)

    def set_day_edited(self, day_number, edited):
        """
        It may happen that we try to mark a day that is non-existent in this month
        if we switch by clicking on the calendar e.g. from Aug 31 to Sep 1.
        The month has already changed and there is no Sep 31.
        Still save_old_day tries to mark the 31st.
        """
        if not self._check_date(day_number):
            return

        if edited:
            self.calendar.mark_day(day_number)
        else:
            self.calendar.unmark_day(day_number)

    def set_month(self, month):
        self.calendar.clear_marks()
        for day_number, day in month.days.items():
            self.set_day_edited(day_number, not day.empty)

    def _check_date(self, day_number):
        """
        E.g. It may happen that text is edited on the 31.7. and then the month
        is changed to June. There is no 31st in June, so we don't mark anything
        in the calendar. This behaviour is necessary since we use the calendar
        both for navigating and showing the current date.
        """
        cal_year, cal_month, _cal_day = self.calendar.get_date()
        cal_month += 1
        if day_number not in range(
            1, dates.get_number_of_days(cal_year, cal_month) + 1
        ):
            logging.debug(
                f"Non-existent date in calendar: {day_number}.{cal_month}.{cal_year}"
            )
            return False
        return True
