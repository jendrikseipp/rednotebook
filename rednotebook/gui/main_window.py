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

import sys
import os
import datetime
import logging

import gtk
import gobject


from rednotebook.gui.menu import MainMenuBar
from rednotebook.gui.options import OptionsManager
from rednotebook.gui import customwidgets
from rednotebook.gui.customwidgets import CustomComboBoxEntry, CustomListView
from rednotebook.util import filesystem
from rednotebook import templates
from rednotebook.util import markup
from rednotebook.util import dates
from rednotebook import undo
from rednotebook.gui import categories
from rednotebook.gui.exports import ExportAssistant
from rednotebook.gui import browser
from rednotebook.gui import search
from rednotebook.gui.editor import Editor
from rednotebook.gui.clouds import Cloud
from rednotebook.gui import insert_menu
from rednotebook.gui import format_menu


class MainWindow(object):
    '''
    Class that holds the reference to the main glade file and handles
    all actions
    '''
    def __init__(self, journal):

        self.journal = journal

        # Set the Glade file
        self.gladefile = os.path.join(filesystem.files_dir, 'main_window.glade')
        self.builder = gtk.Builder()
        self.builder.set_translation_domain('rednotebook')
        try:
            self.builder.add_from_file(self.gladefile)
        except gobject.GError, err:
            logging.error('An error occured while loading the GUI: %s' % err)
            logging.error('RedNotebook requires at least gtk+ 2.14. '
                          'If you cannot update gtk, you might want to try an '
                          'older version of RedNotebook.')
            sys.exit(1)


        # Get the main window and set the icon
        self.main_frame = self.builder.get_object('main_frame')
        self.main_frame.set_title('RedNotebook')
        try:
            icon = gtk.gdk.pixbuf_new_from_file(os.path.join(filesystem.frame_icon_dir,
                                                             'rednotebook.svg'))
        except gobject.GError:
            icon = gtk.gdk.pixbuf_new_from_file(os.path.join(filesystem.frame_icon_dir,
                                                             'rn-192.png'))
        self.main_frame.set_icon(icon)

        self.is_fullscreen = False

        self.uimanager = gtk.UIManager()

        # Before fetching the menubar, add all menus and actiongroups.
        # Setup the toolbar items first to avoid warnings for missing actions.
        insert_menu.InsertMenu(self)
        format_menu.FormatMenu(self)
        self.menubar_manager = MainMenuBar(self)
        self.menubar = self.menubar_manager.get_menu_bar()
        main_vbox = self.builder.get_object('vbox3')
        main_vbox.pack_start(self.menubar, False)
        main_vbox.reorder_child(self.menubar, 0)

        self.undo_redo_manager = undo.UndoRedoManager(self)

        self.calendar = Calendar(self.journal, self.builder.get_object('calendar'))
        self.day_text_field = DayEditor(self.builder.get_object('day_text_view'),
                                        self.undo_redo_manager)
        self.day_text_field.day_text_view.grab_focus()
        can_spell_check = self.day_text_field.can_spell_check()
        spell_check_enabled = bool(self.journal.config.read('spellcheck', 0))
        for actiongroup in self.menubar_manager.uimanager.get_action_groups():
            if actiongroup.get_name() == 'MainMenuActionGroup':
                for action in actiongroup.list_actions():
                    if action.get_name() == 'CheckSpelling':
                        action.set_sensitive(can_spell_check)
                        action.set_active(spell_check_enabled and can_spell_check)
        self.day_text_field.enable_spell_check(spell_check_enabled)

        self.statusbar = Statusbar(self.builder.get_object('statusbar'))

        self.new_entry_dialog = NewEntryDialog(self)

        self.categories_tree_view = categories.CategoriesTreeView(
            self.builder.get_object('categories_tree_view'), self)

        self.new_entry_dialog.categories_tree_view = self.categories_tree_view

        self.back_one_day_button = self.builder.get_object('back_one_day_button')
        self.today_button = self.builder.get_object('today_button')
        self.forward_one_day_button = self.builder.get_object('forward_one_day_button')

        self.edit_pane = self.builder.get_object('edit_pane')

        self.html_editor = Preview(self.journal)
        self.html_editor.webview.connect('button-press-event', self.on_browser_clicked)
        self.html_editor.webview.connect('navigation-requested', self.on_browser_navigate)

        self.text_vbox = self.builder.get_object('text_vbox')
        self.text_vbox.pack_start(self.html_editor)
        self.html_editor.hide()
        self.html_editor.set_editable(False)
        self.preview_mode = False

        # Let the edit_paned respect its childs size requests
        self.edit_pane.child_set_property(self.text_vbox, 'shrink', False)

        # Add InfoBar.
        if customwidgets.Info:
            self.infobar = customwidgets.Info()
            self.text_vbox.pack_start(self.infobar, False, False)
            self.text_vbox.reorder_child(self.infobar, 1)
        else:
            self.infobar = self.statusbar

        # Add TemplateBar.
        self.template_bar = customwidgets.TemplateBar()
        self.text_vbox.pack_start(self.template_bar, False, False)
        self.text_vbox.reorder_child(self.template_bar, 1)
        self.template_bar.hide()

        self.load_values_from_config()

        if not self.journal.start_minimized:
            self.main_frame.show()

        self.options_manager = OptionsManager(self)
        self.export_assistant = ExportAssistant(self.journal)
        self.export_assistant.set_transient_for(self.main_frame)

        self.setup_clouds()
        self.setup_search()

        # Create an event->method dictionary and connect it to the widgets
        dic = {
            'on_back_one_day_button_clicked': self.on_back_one_day_button_clicked,
            'on_today_button_clicked': self.on_today_button_clicked,
            'on_forward_one_day_button_clicked': self.on_forward_one_day_button_clicked,

            'on_preview_button_clicked': self.on_preview_button_clicked,
            'on_edit_button_clicked': self.on_edit_button_clicked,

            'on_main_frame_configure_event': self.on_main_frame_configure_event,
            'on_main_frame_window_state_event': self.on_main_frame_window_state_event,

            'on_add_new_entry_button_clicked': self.on_add_new_entry_button_clicked,

            'on_main_frame_delete_event': self.on_main_frame_delete_event,

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

    def set_tooltips(self):
        '''
        Little work-around:
        Tooltips are not shown for menuitems that have been created with uimanager.
        We have to do it manually.
        '''
        groups = self.uimanager.get_action_groups()
        for group in groups:
            actions = group.list_actions()
            for action in actions:
                widgets = action.get_proxies()
                tooltip = action.get_property('tooltip')
                if tooltip:
                    for widget in widgets:
                        widget.set_tooltip_markup(tooltip)

    def set_shortcuts(self):
        '''
        This method actually is not responsible for the Ctrl-C etc. actions
        '''
        self.accel_group = self.builder.get_object('accelgroup1')  # gtk.AccelGroup()
        #self.accel_group = gtk.AccelGroup()
        self.main_frame.add_accel_group(self.accel_group)
        #self.main_frame.add_accel_group()
        #for key, signal in [('C', 'copy_clipboard'), ('V', 'paste_clipboard'),
        #                   ('X', 'cut_clipboard')]:
        #   self.day_text_field.day_text_view.add_accelerator(signal, self.accel_group,
        #                   ord(key), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        shortcuts = [
            (self.back_one_day_button, 'clicked', '<Ctrl>Page_Up'),
            (self.today_button, 'clicked', '<Alt>Home'),
            (self.forward_one_day_button, 'clicked', '<Ctrl>Page_Down'),
            #(self.builder.get_object('undo_menuitem'), 'activate', '<Ctrl>z'),
            #(self.builder.get_object('redo_menuitem'), 'activate', '<Ctrl>y'),
            #(self.builder.get_object('options_menuitem'), 'activate', '<Ctrl><Alt>p'),
        ]

        for button, signal, shortcut in shortcuts:
            (keyval, mod) = gtk.accelerator_parse(shortcut)
            button.add_accelerator(signal, self.accel_group,
                                   keyval, mod, gtk.ACCEL_VISIBLE)


    # TRAY-ICON / CLOSE --------------------------------------------------------

    def setup_tray_icon(self):
        self.tray_icon = gtk.StatusIcon()
        visible = (self.journal.config.read('closeToTray', 0) == 1)
        self.tray_icon.set_visible(visible)
        logging.debug('Tray icon visible: %s' % visible)

        self.tray_icon.set_tooltip('RedNotebook')
        # TODO: Try using the svg here as well.
        icon_file = os.path.join(self.journal.dirs.frame_icon_dir, 'rn-32.png')
        self.tray_icon.set_from_file(icon_file)

        self.tray_icon.connect('activate', self.on_tray_icon_activated)
        self.tray_icon.connect('popup-menu', self.on_tray_popup_menu)

    def on_tray_icon_activated(self, tray_icon):
        if self.main_frame.get_property('visible'):
            self.hide()
        else:
            self.show()

    def on_tray_popup_menu(self, status_icon, button, activate_time):
        '''
        Called when the user right-clicks the tray icon
        '''

        tray_menu_xml = '''
        <ui>
        <popup action="TrayMenu">
            <menuitem action="Show"/>
            <menuitem action="Quit"/>
        </popup>
        </ui>'''

        # Create an ActionGroup
        actiongroup = gtk.ActionGroup('TrayActionGroup')

        # Create actions
        actiongroup.add_actions([
            ('Show', gtk.STOCK_MEDIA_PLAY, _('Show RedNotebook'),
                None, None, lambda widget: self.show()),
            ('Quit', gtk.STOCK_QUIT, None, None, None, self.on_quit_activate),
        ])

        # Add the actiongroup to the uimanager
        self.uimanager.insert_action_group(actiongroup, 0)

        # Add a UI description
        self.uimanager.add_ui_from_string(tray_menu_xml)

        # Create a Menu
        menu = self.uimanager.get_widget('/TrayMenu')

        menu.popup(None, None, gtk.status_icon_position_menu,
                button, activate_time, status_icon)

    def show(self):
        self.main_frame.show()
        self.load_values_from_config()

    def hide(self):
        self.add_values_to_config()
        self.journal.save_to_disk()
        self.main_frame.hide()

    def on_main_frame_delete_event(self, widget, event):
        '''
        Exit if not close_to_tray
        '''
        logging.debug('Main frame destroyed')

        if self.journal.config.read('closeToTray', 0):
            self.hide()
        else:
            self.journal.exit()

        # We never call the default handler. Otherwise, the window would be
        # destroyed, but we might no actually want to exit.
        return True

    def on_quit_activate(self, widget):
        '''
        User selected quit from the menu -> exit unconditionally
        '''
        self.journal.exit()

    # -------------------------------------------------------- TRAY-ICON / CLOSE


    def setup_stats_dialog(self):
        self.stats_dialog = self.builder.get_object('stats_dialog')
        self.stats_dialog.set_transient_for(self.main_frame)
        overall_box = self.builder.get_object('overall_box')
        day_box = self.builder.get_object('day_stats_box')
        columns = [('1', str), ('2', str)]
        overall_list = CustomListView(columns)
        day_list = CustomListView(columns)
        overall_box.pack_start(overall_list, True, True)
        day_box.pack_start(day_list, True, True)
        setattr(self.stats_dialog, 'overall_list', overall_list)
        setattr(self.stats_dialog, 'day_list', day_list)
        for list in [overall_list, day_list]:
            list.set_headers_visible(False)


    # MODE-SWITCHING -----------------------------------------------------------

    def change_mode(self, preview):
        edit_scroll = self.builder.get_object('text_scrolledwindow')
        edit_button = self.builder.get_object('edit_button')
        preview_button = self.builder.get_object('preview_button')

        size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        size_group.add_widget(edit_button)
        size_group.add_widget(preview_button)

        # Do not forget to update the text in editor and preview respectively
        if preview:
            # Enter preview mode
            edit_scroll.hide()
            self.html_editor.show()

            edit_button.show()
            preview_button.hide()
        else:
            # Enter edit mode
            edit_scroll.show()
            self.html_editor.hide()

            preview_button.show()
            edit_button.hide()

        self.template_manager.set_template_menu_sensitive(not preview)
        # Disable insert shortcuts in preview mode.
        self.insert_actiongroup.set_sensitive(not preview)
        self.format_actiongroup.set_sensitive(not preview)
        self.insert_button.set_sensitive(not preview)
        self.format_button.set_sensitive(not preview)

        self.preview_mode = preview

    def on_edit_button_clicked(self, button):
        # The day's text is already in the editor.
        self.change_mode(preview=False)
        # Select (not only highlight) previously selected text by giving focus
        # to the day editor.
        gobject.idle_add(self.day_text_field.day_text_view.grab_focus)

    def on_preview_button_clicked(self, button):
        self.journal.save_old_day()
        self.html_editor.show_day(self.day)
        self.change_mode(preview=True)

    def on_browser_clicked(self, webview, event):
        # Double-click -> Change to edit mode.
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.change_mode(preview=False)
            # Stop processing that event
            return True

    # ----------------------------------------------------------- MODE-SWITCHING


    def setup_search(self):
        self.search_tree_view = search.SearchTreeView(self)
        self.search_tree_view.show()
        scroll = gtk.ScrolledWindow()
        scroll.add(self.search_tree_view)
        self.builder.get_object('search_container').pack_start(scroll)
        self.search_box = search.SearchComboBox(
            self.builder.get_object('search_box'), self)

    def setup_clouds(self):
        self.cloud = Cloud(self.journal)
        self.builder.get_object('search_container').pack_start(self.cloud)

    def on_main_frame_configure_event(self, widget, event):
        '''
        Is called when the frame size is changed. Unfortunately this is
        the way to go as asking for frame.get_size() at program termination
        gives strange results.
        '''
        main_frame_width, main_frame_height = self.main_frame.get_size()
        self.journal.config['mainFrameWidth'] = main_frame_width
        self.journal.config['mainFrameHeight'] = main_frame_height

    def on_main_frame_window_state_event(self, widget, event):
        '''
        The "window-state-event" signal is emitted when window state
        of widget changes. For example, for a toplevel window this
        event is signaled when the window is iconified, deiconified,
        minimized, maximized, made sticky, made not sticky, shaded or
        unshaded.
        '''
        if event.changed_mask & gtk.gdk.WINDOW_STATE_MAXIMIZED:
            maximized = bool(event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED)
            self.journal.config['mainFrameMaximized'] = int(maximized)

        # Does not work correctly -> Track fullscreen state in program
        #self.is_fullscreen = bool(state and gtk.gdk.WINDOW_STATE_FULLSCREEN)

    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.main_frame.unfullscreen()
            self.menubar.show()
            self.is_fullscreen = False
        else:
            self.main_frame.fullscreen()
            self.menubar.hide()
            self.is_fullscreen = True

    def on_back_one_day_button_clicked(self, widget):
        self.journal.go_to_prev_day()

    def on_today_button_clicked(self, widget):
        actual_date = datetime.date.today()
        self.journal.change_date(actual_date)

    def on_forward_one_day_button_clicked(self, widget):
        self.journal.go_to_next_day()


    def on_browser_navigate(self, webview, frame, request):
        '''
        We want to load files and links externally
        '''
        if self.html_editor.loading_html:
            # Keep processing
            return False

        uri = request.get_uri()
        logging.info('Clicked URI "%s"' % uri)
        filesystem.open_url(uri)

        # Stop processing that event
        return True


    def get_new_journal_dir(self, title, message):
        dir_chooser = self.builder.get_object('dir_chooser')
        dir_chooser.set_transient_for(self.main_frame)
        label = self.builder.get_object('dir_chooser_label')

        label.set_markup('<b>' + message + '</b>')
        dir_chooser.set_current_folder(self.journal.dirs.data_dir)

        response = dir_chooser.run()
        # Retrieve the dir now, because it will be cleared by the call to hide().
        new_dir = dir_chooser.get_filename()
        dir_chooser.hide()

        if response == gtk.RESPONSE_OK:
            if new_dir is None:
                self.journal.show_message(_('No directory selected.'), error=True)
                return None
            return new_dir.decode('utf-8')
        return None


    def show_save_error_dialog(self, exit_imminent):
        dialog = self.builder.get_object('save_error_dialog')
        dialog.set_transient_for(self.main_frame)

        exit_without_save_button = self.builder.get_object('exit_without_save_button')
        if exit_imminent:
            exit_without_save_button.show()
        else:
            exit_without_save_button.hide()

        answer = dialog.run()
        dialog.hide()

        if answer == gtk.RESPONSE_OK:
            # Even if the user aborts the Save-As dialog, we don't want to exit.
            self.journal.is_allowed_to_exit = False
            # Let the user select a new directory. Nothing has been saved yet.
            self.menubar_manager.on_save_as_menu_item_activate(None)
        elif answer == gtk.RESPONSE_CANCEL and exit_imminent:
            self.journal.is_allowed_to_exit = False
        # Do nothing if user wants to exit without saving


    def add_values_to_config(self):
        config = self.journal.config

        left_div = self.builder.get_object('main_pane').get_position()
        config['leftDividerPosition'] = left_div

        right_div = self.edit_pane.get_position()
        config['rightDividerPosition'] = right_div

        # Remember if window was maximized in separate method

        # Remember window position
        config['mainFrameX'], config['mainFrameY'] = self.main_frame.get_position()

        # Actually this is unnecessary as the list gets saved when it changes
        # so we use it to sort the list ;)
        config.write_list('cloudIgnoreList', sorted(self.cloud.ignore_list))
        config.write_list('cloudIncludeList', sorted(self.cloud.include_list))


    def load_values_from_config(self):
        config = self.journal.config
        main_frame_width = config.read('mainFrameWidth', 1024)
        main_frame_height = config.read('mainFrameHeight', 700)

        screen_width = gtk.gdk.screen_width()
        screen_height = gtk.gdk.screen_height()

        main_frame_width = min(main_frame_width, screen_width)
        main_frame_height = min(main_frame_height, screen_height)

        self.main_frame.resize(main_frame_width, main_frame_height)

        if config.read('mainFrameMaximized', 0):
            self.main_frame.maximize()
        else:
            # If window is not maximized, restore last position
            x = config.read('mainFrameX', None)
            y = config.read('mainFrameY', None)
            try:
                x, y = int(x), int(y)
                # Set to 0 if value is below 0
                if 0 <= x <= screen_width and 0 <= y <= screen_height:
                    self.main_frame.move(x, y)
                else:
                    self.main_frame.set_position(gtk.WIN_POS_CENTER)
            except (ValueError, TypeError):
                # Values have not been set or are not valid integers
                self.main_frame.set_position(gtk.WIN_POS_CENTER)

        self.builder.get_object('main_pane').set_position(config.read('leftDividerPosition', 250))
        # By default do not show tags pane.
        self.edit_pane.set_position(config.read('rightDividerPosition', main_frame_width))

        # A font size of -1 applies the standard font size
        main_font_size = config.read('mainFontSize', -1)

        self.set_font_size(main_font_size)

    def set_font_size(self, main_font_size):
        # -1 sets the default font size on Linux
        # -1 does not work on windows, 0 means invisible
        if sys.platform == 'win32' and main_font_size <= 0:
            main_font_size = 10

        self.day_text_field.set_font_size(main_font_size)
        self.html_editor.set_font_size(main_font_size)

    def setup_template_menu(self):
        def update_menu(button):
            self.template_button.set_menu(self.template_manager.get_menu())

        self.template_button = customwidgets.ToolbarMenuButton(gtk.STOCK_PASTE,
                                        self.template_manager.get_menu())
        self.template_button.set_label(_('Template'))
        self.template_button.connect('show-menu', update_menu)
        self.template_button.set_tooltip_text(_("Insert this weekday's template. "
                        "Click the arrow on the right for more options"))
        self.builder.get_object('edit_toolbar').insert(self.template_button, 2)

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
        if self.journal.config.get('autoSwitchMode', 1):
            if day.has_text and not self.preview_mode:
                self.change_mode(preview=True)
            elif not day.has_text and self.preview_mode:
                self.change_mode(preview=False)

        if self.preview_mode:
            # Converting markup to html takes time, so only do it when necessary
            self.html_editor.show_day(day)

        self.categories_tree_view.set_day_content(day)
        self.undo_redo_manager.set_stack(new_date)

    def get_day_text(self):
        return self.day_text_field.get_text()

    def highlight_text(self, search_text):
        self.html_editor.highlight(search_text)
        self.day_text_field.highlight(search_text)

    def show_message(self, title, msg, msg_type):
        if msg_type == gtk.MESSAGE_ERROR:
            self.infobar.show_message(title, msg, msg_type)
        else:
            self.statusbar.show_message(title, msg, msg_type)


class Preview(browser.HtmlView):
    def __init__(self, journal, *args, **kwargs):
        browser.HtmlView.__init__(self, *args, **kwargs)
        self.journal = journal
        self.day = None

    def show_day(self, new_day):
        # Save the position in the preview pane for the old day
        if self.day:
            self.day.last_preview_pos = (self.get_hscrollbar().get_value(),
                                         self.get_vscrollbar().get_value())

        # Show new day
        self.day = new_day
        html = markup.convert(self.day.text, 'xhtml', self.journal.dirs.data_dir)
        self.load_html(html)

        if self.day.last_preview_pos is not None:
            x, y = self.day.last_preview_pos
            gobject.idle_add(self.get_hscrollbar().set_value, x)
            gobject.idle_add(self.get_vscrollbar().set_value, y)


class DayEditor(Editor):
    def __init__(self, *args, **kwargs):
        Editor.__init__(self, *args, **kwargs)
        self.day = None
        self.scrolled_win = self.day_text_view.get_parent()

    def show_day(self, new_day):
        # Save the position in the edit pane for the old day
        if self.day:
            cursor_pos = self.day_text_buffer.get_property('cursor-position')
            # If there is a selection we save it, else we save the cursor position
            selection = self.day_text_buffer.get_selection_bounds()
            if selection:
                selection = [it.get_offset() for it in selection]
            else:
                selection = [cursor_pos, cursor_pos]
            self.day.last_edit_pos = (self.scrolled_win.get_hscrollbar().get_value(),
                                      self.scrolled_win.get_vscrollbar().get_value(),
                                      selection)

        # Show new day
        self.day = new_day
        self.set_text(self.day.text, undoing=True)

        if self.search_text:
            # If a search is currently made, scroll to the text and return.
            gobject.idle_add(self.scroll_to_text, self.search_text)
            return

        if self.day.last_edit_pos is not None:
            x, y, selection = self.day.last_edit_pos
            gobject.idle_add(self.scrolled_win.get_hscrollbar().set_value, x)
            gobject.idle_add(self.scrolled_win.get_vscrollbar().set_value, y)
            gobject.idle_add(self._restore_selection, selection)

    def _restore_selection(self, selection):
        iters = [self.day_text_buffer.get_iter_at_offset(offset)
                 for offset in selection]
        self.day_text_buffer.select_range(*iters)
        self.day_text_view.grab_focus()


class NewEntryDialog(object):
    def __init__(self, main_frame):
        dialog = main_frame.builder.get_object('new_entry_dialog')
        self.dialog = dialog
        dialog.set_transient_for(main_frame.main_frame)

        self.main_frame = main_frame
        self.journal = self.main_frame.journal
        self.categories_combo_box = CustomComboBoxEntry(main_frame.builder.get_object('categories_combo_box'))
        self.new_entry_combo_box = CustomComboBoxEntry(main_frame.builder.get_object('entry_combo_box'))

        # Let the user finish a new category entry by hitting ENTER
        def respond(widget):
            if self._text_entered():
                self.dialog.response(gtk.RESPONSE_OK)
        self.new_entry_combo_box.entry.connect('activate', respond)
        self.categories_combo_box.entry.connect('activate', respond)

        self.categories_combo_box.connect('changed', self.on_category_changed)

    def on_category_changed(self, widget):
        '''Show old entries in ComboBox when a new category is selected'''
        category = self.categories_combo_box.get_active_text()
        old_entries = self.journal.get_entries(category)
        self.new_entry_combo_box.set_entries(old_entries)

        # only make the entry submittable, if text has been entered
        self.dialog.set_response_sensitive(gtk.RESPONSE_OK, self._text_entered())

    def _text_entered(self):
        return bool(self.categories_combo_box.get_active_text())

    def show_dialog(self, category=''):
        # Use last used category.
        last_category = self.categories_tree_view.last_category

        # Has to be first, because it may be populated later
        self.new_entry_combo_box.clear()

        # Show the list of categories
        self.categories_combo_box.set_entries(self.categories_tree_view.categories)

        self.categories_combo_box.set_active_text(category or last_category or '')

        if category:
            # We already know the category so let's get the entry
            self.new_entry_combo_box.combo_box.grab_focus()
        else:
            self.categories_combo_box.combo_box.grab_focus()

        response = self.dialog.run()
        self.dialog.hide()

        if not response == gtk.RESPONSE_OK:
            return

        category_name = self.categories_combo_box.get_active_text()
        if not self.categories_tree_view.check_category(category_name):
            return

        entry_text = self.new_entry_combo_box.get_active_text()

        self.categories_tree_view.add_entry(category_name, entry_text)

        # Update cloud
        self.main_frame.cloud.update()


class Statusbar(object):
    def __init__(self, statusbar):
        self.statusbar = statusbar
        self.context_id = self.statusbar.get_context_id('RedNotebook')
        self.last_message_id = None
        self.timespan = 10

    def remove_message(self):
        if hasattr(self.statusbar, 'remove_message'):
            self.statusbar.remove_message(self.context_id, self.last_message_id)
        else:
            # Deprecated
            self.statusbar.remove(self.context_id, self.last_message_id)

    def _show_text(self, text, countdown=True):
        if self.last_message_id is not None:
            self.remove_message()
        self.last_message_id = self.statusbar.push(self.context_id, text)
        if countdown:
            self.start_countdown()

    def show_message(self, title, msg, msg_type):
        if title and msg:
            text = '%s: %s' % (title, msg)
        else:
            text = title or msg
        self._show_text(text)

    def start_countdown(self):
        self.time_left = self.timespan
        self.countdown = gobject.timeout_add(1000, self.count_down)

    def count_down(self):
        self.time_left -= 1
        if self.time_left <= 0:
            gobject.source_remove(self.countdown)
            self._show_text('', countdown=False)
        return True


class Calendar(object):
    def __init__(self, journal, calendar):
        self.journal = journal
        self.calendar = calendar

        week_numbers = self.journal.config.read('weekNumbers', 0)
        if week_numbers:
            calendar.set_property('show-week-numbers', True)

        self.date_listener = self.calendar.connect('day-selected', self.on_day_selected)

    def on_day_selected(self, cal):
        self.journal.change_date(self.get_date())

    def set_date(self, date):
        '''
        A date check makes no sense here since it is normal that a new month is
        set here that will contain the day
        '''
        # Probably useless
        if date == self.get_date():
            return

        # We do not want to listen to this programmatic date change
        self.calendar.handler_block(self.date_listener)

        # We need to set the day temporarily to a day that is present in all months
        self.calendar.select_day(1)

        # PyGTK calendars show months in range [0,11]
        self.calendar.select_month(date.month - 1, date.year)

        # Select the day after the month and year have been set
        self.calendar.select_day(date.day)

        # We want to listen to manual date changes
        self.calendar.handler_unblock(self.date_listener)

    def get_date(self):
        year, month, day = self.calendar.get_date()
        return datetime.date(year, month + 1, day)

    def set_day_edited(self, day_number, edited):
        '''
        It may happen that we try to mark a day that is non-existent in this month
        if we switch by clicking on the calendar e.g. from Aug 31 to Sep 1.
        The month has already changed and there is no Sep 31.
        Still save_old_day tries to mark the 31st.
        '''
        if not self._check_date(day_number):
            return

        if edited:
            self.calendar.mark_day(day_number)
        else:
            self.calendar.unmark_day(day_number)

    def set_month(self, month):
        #month_days = dates.get_number_of_days(month.year_number, month.month_number)
        #for day_number in range(1, month_days + 1):
        #   self.set_day_edited(day_number, False)
        self.calendar.clear_marks()
        for day_number, day in month.days.items():
            self.set_day_edited(day_number, not day.empty)

    def _check_date(self, day_number):
        '''
        E.g. It may happen that text is edited on the 31.7. and then the month
        is changed to June. There is no 31st in June, so we don't mark anything
        in the calendar. This behaviour is necessary since we use the calendar
        both for navigating and showing the current date.
        '''
        cal_year, cal_month, cal_day = self.calendar.get_date()
        cal_month += 1
        if not day_number in range(1, dates.get_number_of_days(cal_year, cal_month) + 1):
            logging.debug('Non-existent date in calendar: %s.%s.%s' %
                        (day_number, cal_month, cal_year))
            return False
        return True
