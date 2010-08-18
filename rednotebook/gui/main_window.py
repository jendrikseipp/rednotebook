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
import time
import urllib
import urlparse
import webbrowser
import logging

import gtk
import gobject
import pango

# try to import gtkspell
try:
    import gtkspell
except ImportError:
    gtkspell = None


# Initialize the gtk thread engine
#gobject.threads_init()

from rednotebook.util import utils
import rednotebook.util.unicode

from rednotebook.gui.menu import MainMenuBar
from rednotebook.external.htmltextview import HtmlWindow
from rednotebook.gui.options import OptionsManager
from rednotebook.gui import customwidgets
from rednotebook.gui.customwidgets import CustomComboBoxEntry, CustomListView, \
                                            get_button_width
from rednotebook.gui.richtext import HtmlEditor
from rednotebook.util import filesystem
from rednotebook import info
from rednotebook import templates
from rednotebook.util import markup
from rednotebook.util import dates
from rednotebook import undo

from rednotebook.gui.exports import ExportAssistant
from rednotebook.gui import categories
from rednotebook.gui import t2t_highlight
from rednotebook.gui import browser

test_zeitgeist = False
if test_zeitgeist:
    from rednotebook.gui import journalgeist


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
        icons = [gtk.gdk.pixbuf_new_from_file(file) for file in filesystem.get_icons()]
        self.main_frame.set_icon_list(*map(lambda file: gtk.gdk.pixbuf_new_from_file(file), \
                                filesystem.get_icons()))
        
        self.uimanager = gtk.UIManager()
        
        self.menubar_manager = MainMenuBar(self)
        self.menubar = self.menubar_manager.get_menu_bar()
        main_vbox = self.builder.get_object('vbox3')
        main_vbox.pack_start(self.menubar, False)
        main_vbox.reorder_child(self.menubar, 0)
        
        self.undo_redo_manager = undo.UndoRedoManager(self)
        
        
        self.calendar = Calendar(self.journal, self.builder.get_object('calendar'))
        self.day_text_field = DayTextField(self.builder.get_object('day_text_view'), \
                                        self.undo_redo_manager)
        self.day_text_field.day_text_view.grab_focus()
        spell_check_enabled = self.journal.config.read('spellcheck', 0)
        self.day_text_field.enable_spell_check(spell_check_enabled)
        
        self.statusbar = Statusbar(self.builder.get_object('statusbar'))
        
        self.new_entry_dialog = NewEntryDialog(self)
        
        self.categories_tree_view = categories.CategoriesTreeView(self.builder.get_object(\
                                    'categories_tree_view'), self)
        
        self.new_entry_dialog.categories_tree_view = self.categories_tree_view
        
        self.back_one_day_button = self.builder.get_object('back_one_day_button')
        self.forward_one_day_button = self.builder.get_object('forward_one_day_button')
        
        self.edit_pane = self.builder.get_object('edit_pane')
        
        # Only add the config variable if webkit is available
        # Use webkit by default if it is available
        self.use_webkit = bool(browser.webkit)# and self.journal.config.read('useWebkit', 1)
        
        logging.info('Using webkit for previews: %s' % self.use_webkit)
        
        if self.use_webkit:
            self.html_editor = browser.HtmlView()
        else:
            self.html_editor = HtmlEditor()
            
        self.text_vbox = self.builder.get_object('text_vbox')
        self.text_vbox.pack_start(self.html_editor)
        self.html_editor.hide()
        self.html_editor.set_editable(False)
        self.preview_mode = False
        self.preview_button = self.builder.get_object('preview_button')
        
        # Let the preview button always have the same size        
        preview_button = self.preview_button
        preview_button.realize()
        width_edit = get_button_width(preview_button, _('Edit'))
        width_preview = get_button_width(preview_button, _('Preview'))
        width = max([width_edit, width_preview])
        if sys.platform == 'win32':
            # Calculation does not work on windows
            width += 30
        preview_button.set_size_request(width, -1)
        
        self.load_values_from_config()
        
        if not self.journal.start_minimized:
            self.main_frame.show()
        
        self.options_manager = OptionsManager(self)
        self.export_assistant = ExportAssistant(self.journal)
        
        self.setup_search()
        self.setup_insert_menu()
        self.setup_format_menu()
        
        # Create an event->method dictionary and connect it to the widgets
        dic = {
            'on_back_one_day_button_clicked': self.on_back_one_day_button_clicked,
            'on_today_button_clicked': self.on_today_button_clicked,
            'on_forward_one_day_button_clicked': self.on_forward_one_day_button_clicked,
            #'on_calendar_day_selected': self.on_calendar_day_selected,
            
            'on_preview_button_clicked': self.on_preview_button_clicked,
            
            'on_main_frame_configure_event': self.on_main_frame_configure_event,
            'on_main_frame_window_state_event': self.on_main_frame_window_state_event,
            
            'on_add_new_entry_button_clicked': self.on_add_new_entry_button_clicked,
            'on_add_tag_button_clicked': self.on_add_tag_button_clicked,
            'on_delete_entry_button_clicked': self.on_delete_entry_button_clicked,
            
            'on_search_notebook_switch_page': self.on_search_notebook_switch_page,
            
            'on_template_button_clicked': self.on_template_button_clicked,
            'on_template_menu_show_menu': self.on_template_menu_show_menu,
            'on_template_menu_clicked': self.on_template_menu_clicked,
            
            'on_search_type_box_changed': self.on_search_type_box_changed,
            'on_cloud_combo_box_changed': self.on_cloud_combo_box_changed,
            
            'on_main_frame_delete_event': self.on_main_frame_delete_event,
            
            # connect_signals can only be called once, it seems
            # Otherwise RuntimeWarnings are raised: RuntimeWarning: missing handler '...'
             }
        self.builder.connect_signals(dic)
        
        
        self.setup_clouds()
        self.set_shortcuts()
        self.setup_stats_dialog()
        
        self.template_manager = templates.TemplateManager(self)
        self.template_manager.make_empty_template_files()
        self.setup_template_menu()
        self.setup_tray_icon()
        
        #self.menubar_manager.set_tooltips()
        self.set_tooltips()
        
        
        # Only add the config variable if zeitgeist is available
        use_zeitgeist = test_zeitgeist and journalgeist.zeitgeist and \
                        self.journal.config.read('useZeitgeist', 0)
        self.zeitgeist_widget = None
        #use_zeitgeist = True
        logging.info('Using zeitgeist: %s' % use_zeitgeist)
        
        if use_zeitgeist:
            self.setup_zeitgeist_view()
        
    
    def setup_zeitgeist_view(self):
        '''Zeigeist integration'''
        #from rednotebook.gui.journalgeist import JournalZeitgeistWidget
        self.zeitgeist_widget = journalgeist.ZeitgeistWidget()
        annotations_pane = self.builder.get_object('annotations_pane')
        annotations_pane.add2(self.zeitgeist_widget)
        
        
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
        self.accel_group = self.builder.get_object('accelgroup1')#gtk.AccelGroup()
        #self.accel_group = gtk.AccelGroup()
        self.main_frame.add_accel_group(self.accel_group)
        #self.main_frame.add_accel_group()
        #for key, signal in [('C', 'copy_clipboard'), ('V', 'paste_clipboard'), \
        #                   ('X', 'cut_clipboard')]:
        #   self.day_text_field.day_text_view.add_accelerator(signal, self.accel_group,
        #                   ord(key), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        
        shortcuts = [(self.back_one_day_button, 'clicked', '<Ctrl>Page_Down'),
                    (self.forward_one_day_button, 'clicked', '<Ctrl>Page_Up'),
                    #(self.builder.get_object('undo_menuitem'), 'activate', '<Ctrl>z'),
                    #(self.builder.get_object('redo_menuitem'), 'activate', '<Ctrl>y'),
                    #(self.builder.get_object('options_menuitem'), 'activate', '<Ctrl><Alt>p'),
                    ]
        
        for button, signal, shortcut in shortcuts:
            (keyval, mod) = gtk.accelerator_parse(shortcut)
            button.add_accelerator(signal, self.accel_group, \
                                keyval, mod, gtk.ACCEL_VISIBLE)
            
            
    # TRAY-ICON / CLOSE --------------------------------------------------------
            
    def setup_tray_icon(self):
        self.tray_icon = gtk.StatusIcon()
        visible = (self.journal.config.read('closeToTray', 0) == 1)
        self.tray_icon.set_visible(visible)
        logging.debug('Tray icon visible: %s' % visible)
        
        self.tray_icon.set_tooltip('RedNotebook')
        icon_file = os.path.join(self.journal.dirs.frame_icon_dir, 'rn-32.png')
        self.tray_icon.set_from_file(icon_file)
        
        self.tray_icon.connect('activate', self.on_tray_icon_activated)
        self.tray_icon.connect('popup-menu', self.on_tray_popup_menu)
        
    def on_tray_icon_activated(self, tray_icon):
        if self.main_frame.get_property('visible'):
            self.hide()
        else:
            self.main_frame.show()
            
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
                None, None, lambda widget: self.main_frame.show()),
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
            
    def hide(self):
        self.main_frame.hide()
        self.journal.save_to_disk(exit_imminent=False)
        
    def on_main_frame_delete_event(self, widget, event):
        '''
        Exit if not close_to_tray
        '''
        logging.debug('Main frame destroyed')
        #self.save_to_disk(exit_imminent=False)
        
        if self.journal.config.read('closeToTray', 0):
            self.hide()
        
            # the default handler is _not_ to be called, 
            # and therefore the window will not be destroyed.
            return True
        else:
            self.journal.exit()
        
    def on_quit_activate(self, widget):
        '''
        User selected quit from the menu -> exit unconditionally
        '''
        #self.on_main_frame_destroy(None)
        self.journal.exit()
        
    # -------------------------------------------------------- TRAY-ICON / CLOSE
        
        
    def setup_stats_dialog(self):
        self.stats_dialog = self.builder.get_object('stats_dialog')
        overall_box = self.builder.get_object('overall_box')
        day_box = self.builder.get_object('day_stats_box')
        overall_list = CustomListView()
        day_list = CustomListView()
        overall_box.pack_start(overall_list, True, True)
        day_box.pack_start(day_list, True, True)
        setattr(self.stats_dialog, 'overall_list', overall_list)
        setattr(self.stats_dialog, 'day_list', day_list)
        for list in [overall_list, day_list]:
            list.set_headers_visible(False)
            
            
    def on_preview_button_clicked(self, button):
        self.journal.save_old_day()
        
        text_scrolledwindow = self.builder.get_object('text_scrolledwindow')
        template_button = self.builder.get_object('template_menu_button')
        
        # Do not forget to update the text in editor and preview respectively
        
        if self.preview_mode:
            # Enter edit mode
            self.day_text_field.set_text(self.day.text, undoing=True)
            self.day_text_field.day_text_view.grab_focus()
            
            text_scrolledwindow.show()
            self.html_editor.hide()
            self.preview_button.set_stock_id('gtk-media-play')
            ### Translators: Verb
            self.preview_button.set_label(_('Preview'))
            
            self.preview_mode = False
        else:
            # Enter preview mode            
            text_scrolledwindow.hide()
            self.html_editor.show()
            day = self.journal.day
            text_markup = day.text
            html = markup.convert(text_markup, 'xhtml', append_whitespace=True)
            
            self.html_editor.load_html(html)
            
            self.preview_button.set_stock_id('gtk-edit')
            #self.preview_button.set_label(' '*3 + 'Edit' + ' '*4)
            self.preview_button.set_label(_('Edit'))
            
            self.preview_mode = True
            
        template_button.set_sensitive(not self.preview_mode)
        self.single_menu_toolbutton.set_sensitive(not self.preview_mode)
        self.format_toolbutton.set_sensitive(not self.preview_mode)
        
            
    def setup_search(self):
        self.search_notebook = self.builder.get_object('search_notebook')
        
        self.search_tree_view = SearchTreeView(self.builder.get_object(\
                                    'search_tree_view'), self)
        self.search_type_box = self.builder.get_object('search_type_box')
        self.search_type_box.set_active(0)
        self.search_box = SearchComboBox(self.builder.get_object('search_box'), \
                                    self)
        
        
    def on_search_type_box_changed(self, widget):
        search_type = widget.get_active()
        self.search_box.set_search_type(search_type)
        
            
    def on_search_notebook_switch_page(self, notebook, page, page_number):
        '''
        Called when the page actually changes
        '''
        if page_number == 0:
            # Switched to search tab
            #self.search_tree_view.update_data()
            
            # Put cursor into search field, when search tab is opened
            # Strangely it only works with the idle_add workaround
            gobject.idle_add(self.search_box.entry.grab_focus)
        if page_number == 1:
            # Switched to cloud tab
            self.cloud.update(force_update=True)
        
        
    def setup_clouds(self):
        self.cloud_box = self.builder.get_object('cloud_box')
        
        if browser.webkit:
            from rednotebook.gui.clouds import Cloud
            self.cloud = Cloud(self.journal)
            logging.info('Using pywebkitgtk for the clouds.')
        else:
            logging.warning('pywebkitgtk is not installed and cannot ' \
                    'be used for the clouds. You may experience errors')
            #self.search_notebook.remove_page(1)
            self.cloud = CloudView(self.journal)
            
        self.cloud_box.pack_start(self.cloud)
        
        self.cloud_combo_box = self.builder.get_object('cloud_combo_box')
        self.cloud_combo_box.set_active(0)
        
        
    def on_cloud_combo_box_changed(self, cloud_combo_box):
        value_int = cloud_combo_box.get_active()
        self.cloud.set_type(value_int)
    
        
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
        state = event.new_window_state
        maximized = state and gtk.gdk.WINDOW_STATE_MAXIMIZED
        maximized = int(bool(maximized))
        self.journal.config['mainFrameMaximized'] = maximized
        
        
    def on_back_one_day_button_clicked(self, widget):
        self.journal.go_to_prev_day()
        
    def on_today_button_clicked(self, widget):
        actual_date = datetime.date.today()
        self.journal.change_date(actual_date)
        
    def on_forward_one_day_button_clicked(self, widget):
        self.journal.go_to_next_day()
        
    def on_calendar_day_selected(self, widget):
        pass#
        #self.journal.change_date(self.calendar.get_date())
        
    def show_dir_chooser(self, type, dir_not_found=False):
        dir_chooser = self.builder.get_object('dir_chooser')
        label = self.builder.get_object('dir_chooser_label')
        
        if type == 'new':
            #dir_chooser.set_action(gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER)
            dir_chooser.set_title(_('Select an empty folder for your new journal'))
            msg_part1 = _('Journals are saved in a directory, not in a single file.')
            msg_part2 = _('The directory name will be the title of the new journal.')
            label.set_markup('<b>' + msg_part1 + '\n' + msg_part2 + '</b>')
        elif type == 'open':
            #dir_chooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
            dir_chooser.set_title(_('Select an existing journal directory'))
            label.set_markup('<b>' + \
                _("The directory should contain your journal's data files") + '</b>')
        elif type == 'saveas':
            dir_chooser.set_title(_('Select an empty folder for the new location of your journal'))
            label.set_markup('<b>' + \
                _('The directory name will be the new title of the journal') + '</b>')
        dir_chooser.set_current_folder(self.journal.dirs.data_dir)
        
        response = dir_chooser.run()
        dir_chooser.hide()
        
        if response == gtk.RESPONSE_OK:
            dir = dir_chooser.get_current_folder()
            
            if type == 'saveas':
                self.journal.dirs.data_dir = dir
                self.journal.save_to_disk(saveas=True)
                
            load_files = type in ['open', 'saveas']
            self.journal.open_journal(dir, load_files=load_files)
        
        # If the dir was not found previously, we have nothing to open
        # if the user selects "Abort". So select default dir and show message
        elif dir_not_found:
            default_dir = self.journal.dirs.default_data_dir
            self.journal.open_journal(default_dir, load_files=True)
            ### Translators: The default journal is located at $HOME/.rednotebook/data
            self.journal.show_message(_('The default journal has been opened'))
            
    def show_save_error_dialog(self, exit_imminent):
        dialog = self.builder.get_object('save_error_dialog')
        
        exit_without_save_button = self.builder.get_object('exit_without_save_button')
        if exit_imminent:
            exit_without_save_button.show()
        else:
            exit_without_save_button.hide()
        
        answer = dialog.run()
        dialog.hide()
        
        if answer == gtk.RESPONSE_OK:
            # Let the user select a new directory. Nothing has been saved yet.
            self.show_dir_chooser('saveas')
        elif answer == gtk.RESPONSE_CANCEL and exit_imminent:
            self.journal.is_allowed_to_exit = False
        else: # answer == 10:
            # Do nothing if user wants to exit without saving
            pass
            
        
        
    def add_values_to_config(self):
        config = self.journal.config
        
        config['leftDividerPosition'] = \
                self.builder.get_object('main_pane').get_position()
        config['rightDividerPosition'] = \
                self.builder.get_object('edit_pane').get_position()
                
        # Remember if window was maximized in separate method
        
        config['cloudTabActive'] = self.search_notebook.get_current_page()
        
        # Actually this is unnecessary as the list gets saved when it changes
        # so we use it to sort the list ;)
        config.write_list('cloudIgnoreList', sorted(self.cloud.ignore_list))
        config.write_list('cloudIncludeList', sorted(self.cloud.include_list))
        
    
    def load_values_from_config(self):
        config = self.journal.config
        main_frame_width = config.read('mainFrameWidth', 1024)
        main_frame_height = config.read('mainFrameHeight', 768)
        
        screen_width = gtk.gdk.screen_width()
        screen_height = gtk.gdk.screen_height()
        
        main_frame_width = min(main_frame_width, screen_width)
        main_frame_height = min(main_frame_height, screen_height)
        
        self.main_frame.resize(main_frame_width, main_frame_height)
        
        if config.read('mainFrameMaximized', 0):
            self.main_frame.maximize()
        
        if 'leftDividerPosition' in config:
            self.builder.get_object('main_pane').set_position(config.read('leftDividerPosition', -1))
        self.builder.get_object('edit_pane').set_position(config.read('rightDividerPosition', 500))
        
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
        self.template_menu_button = self.builder.get_object('template_menu_button')
        self.template_menu_button.set_menu(gtk.Menu())
        self.template_menu_button.set_menu(self.template_manager.get_menu())
                
    
    def on_template_menu_show_menu(self, widget):
        self.template_menu_button.set_menu(self.template_manager.get_menu())
        
    def on_template_menu_clicked(self, widget):
        text = self.template_manager.get_weekday_text()
        #self.day_text_field.insert_template(text)
        self.day_text_field.insert(text)
        
    def on_template_button_clicked(self, widget):
        text = self.template_manager.get_weekday_text()
        self.day_text_field.insert(text)
        
        
    def setup_format_menu(self):
        '''
        See http://www.pygtk.org/pygtk2tutorial/sec-UIManager.html for help
        A popup menu cannot show accelerators (HIG).
        '''
        
        format_menu_xml = '''
        <ui>
        <popup action="FormatMenu">
            <menuitem action="Bold"/>
            <menuitem action="Italic"/>
            <menuitem action="Underline"/>
            <menuitem action="Strikethrough"/>
        </popup>
        </ui>'''
            
        uimanager = self.uimanager

        # Create an ActionGroup
        actiongroup = gtk.ActionGroup('FormatActionGroup')
        #self.actiongroup = actiongroup

        def tmpl(word):
            return word + ' (Ctrl+%s)' % word[0]
        
        def apply_format(action, format='bold'):
            format_to_markup = {'bold': '**', 'italic': '//', 'underline': '__',
                                'strikethrough': '--'}
            if type(action) == gtk.Action:
                format = action.get_name().lower()
            
            markup = format_to_markup[format]
            
            focus = self.main_frame.get_focus()
            
            
            if focus == self.categories_tree_view.tree_view:
                iter = self.categories_tree_view.get_selected_node()
                if iter:
                    text = self.categories_tree_view.get_iter_value(iter)
                    text = '%s%s%s' % (markup, text, markup)
                    self.categories_tree_view.set_iter_value(iter, text)
                    return
            #if focus is None or focus == self.day_text_field.day_text_view:
            self.day_text_field.apply_format(format, markup)
            
        def shortcut(char):
            ### Translators: The Control (Ctrl) key
            return ' (%s+%s)' % (_('Ctrl'), char)
        
        # Create actions
        actions = [ ('Bold', gtk.STOCK_BOLD, _('Bold') + shortcut('B'), '<Control>B', None, apply_format),
                    ('Italic', gtk.STOCK_ITALIC, _('Italic') + shortcut('I'), '<Control>I', None, apply_format),
                    ('Underline', gtk.STOCK_UNDERLINE, _('Underline') + shortcut('U'), '<Control>U', None, apply_format),
                    ('Strikethrough', gtk.STOCK_STRIKETHROUGH, _('Strikethrough'), None, None, apply_format)]
        
        actiongroup.add_actions(actions)

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)

        # Add a UI description
        uimanager.add_ui_from_string(format_menu_xml)

        # Create a Menu
        menu = uimanager.get_widget('/FormatMenu')
        
        #single_menu_toolbutton = SingleMenuToolButton(menu, 'Insert ')
        self.format_toolbutton = gtk.MenuToolButton(gtk.STOCK_BOLD)
        ### Translators: noun
        self.format_toolbutton.set_label(_('Format'))
        tip = _('Format the selected text or category entry')
        self.format_toolbutton.set_tooltip_text(tip)
        self.format_toolbutton.set_menu(menu)
        bold_func = apply_format#lambda widget: self.day_text_field.apply_format('bold')
        self.format_toolbutton.connect('clicked', bold_func)
        edit_toolbar = self.builder.get_object('edit_toolbar')
        edit_toolbar.insert(self.format_toolbutton, -1)
        self.format_toolbutton.show()
        
        
    def setup_insert_menu(self):
        '''
        See http://www.pygtk.org/pygtk2tutorial/sec-UIManager.html for help
        A popup menu cannot show accelerators (HIG).
        '''
        
        insert_menu_xml = '''
        <ui>
        <popup action="InsertMenu">
            <menuitem action="Picture"/>
            <menuitem action="File"/>
            <menuitem action="Link"/>
            <menuitem action="BulletList"/>
            %(numlist_ui)s
            <menuitem action="Title"/>
            <menuitem action="Line"/>
            %(title_ui)s
            <menuitem action="Date"/>
            <menuitem action="LineBreak"/>
        </popup>
        </ui>'''
        
        numlist_ui = '' #'<menuitem action="NumberedList"/>' if self.use_webkit else ''
        title_ui = ''# '<menuitem action="Table"/>' if self.use_webkit else ''
        
        insert_menu_xml = insert_menu_xml % locals()
            
        uimanager = self.uimanager

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.main_frame.add_accel_group(accelgroup)

        # Create an ActionGroup
        actiongroup = gtk.ActionGroup('InsertActionGroup')
        self.actiongroup = actiongroup
        
        line = '\n====================\n'
        
        item1 = _('First Item')
        item2 = _('Second Item')
        item3 = _('Indented Item')
        close = _('Two blank lines close the list')
        bullet_list = '\n- %s\n- %s\n  - %s (%s)\n\n\n' % (item1, item2, item3, close)
        numbered_list = bullet_list.replace('-', '+')
        
        title_text = _('Title text')
        title = '\n=== %s ===\n' % title_text
        
        table = '\n|| Whitespace Left | Whitespace Right | Resulting Alignment |\n' \
                   '| 1               | more than 1     | Align left   |\n' \
                   '|     more than 1 |               1 |   Align right |\n' \
                   '|   more than 1   |   more than 1   |   Center   |\n' \
                   '|| Title rows | are always | centered |\n' \
                   '|  Use two vertical  |  lines on the left  |  for title rows  |\n' \
                   '|  Always use  |  at least  |  one whitespace  |\n' \
        
        line_break = r'\\'
        
        def insert_date_time(widget):
            default_date_string = '%A, %x %X'
            date_string = self.journal.config.read('dateTimeString', default_date_string)
            self.day_text_field.insert(time.strftime(date_string))

        def tmpl(letter):
            return ' (Ctrl+%s)' % letter
        
        # Create actions
        actiongroup.add_actions([
            ('Picture', gtk.STOCK_ORIENTATION_PORTRAIT, \
                _('Picture'), \
                None, _('Insert an image from the harddisk'), \
                self.on_insert_pic_menu_item_activate),
            ('File', gtk.STOCK_FILE, _('File'), None, \
                _('Insert a link to a file'), \
                self.on_insert_file_menu_item_activate),
            ### Translators: Noun
            ('Link', gtk.STOCK_JUMP_TO, _('_Link') + tmpl('L'), '<Control>L', \
                _('Insert a link to a website'), \
                self.on_insert_link_menu_item_activate),
            ('BulletList', None, _('Bullet List'), None, \
                None, \
                lambda widget: self.day_text_field.insert(bullet_list)),
            ('NumberedList', None, _('Numbered List'), None, \
                None, \
                lambda widget: self.day_text_field.insert(numbered_list)),
            ('Title', None, _('Title'), None, \
                None, \
                lambda widget: self.day_text_field.insert(title)),
            ('Line', None, _('Line'), None, \
                _('Insert a separator line'), \
                lambda widget: self.day_text_field.insert(line)),
            ('Table', None, _('Table'), None, None, \
                lambda widget: self.day_text_field.insert(table)),
            ('Date', None, _('Date/Time') + tmpl('D'), '<Ctrl>D', \
                _('Insert the current date and time (edit format in preferences)'), \
                insert_date_time),
            ('LineBreak', None, _('Line Break'), None, \
                _('Insert a manual line break'), \
                lambda widget: self.day_text_field.insert(line_break)),
            ])

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)

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
        
        self.single_menu_toolbutton = gtk.MenuToolButton(gtk.STOCK_ADD)
        self.single_menu_toolbutton.set_label(_('Insert'))
            
        self.single_menu_toolbutton.set_menu(menu)
        self.single_menu_toolbutton.connect('clicked', self.show_insert_menu)
        self.single_menu_toolbutton.set_tooltip_text(_('Insert images, files, links and other content'))
        edit_toolbar = self.builder.get_object('edit_toolbar')
        edit_toolbar.insert(self.single_menu_toolbutton, -1)
        self.single_menu_toolbutton.show()
        
    def show_insert_menu(self, button):
        '''
        Show the insert menu, when the Insert Button is clicked.
        
        A little hack for button and activate_time is needed as the "clicked" does
        not have an associated event parameter. Otherwise we would use event.button
        and event.time
        '''
        self.single_menu_toolbutton.get_menu().popup(parent_menu_shell=None, \
                            parent_menu_item=None, func=None, button=0, activate_time=0, data=None)
        
    def on_insert_pic_menu_item_activate(self, widget):
        dirs = self.journal.dirs
        picture_chooser = self.builder.get_object('picture_chooser')
        picture_chooser.set_current_folder(dirs.last_pic_dir)
        
        filter = gtk.FileFilter()
        filter.set_name("Images")
        filter.add_mime_type("image/png")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/gif")
        filter.add_pattern("*.png")
        filter.add_pattern("*.jpg")
        filter.add_pattern("*.gif")

        picture_chooser.add_filter(filter)

        response = picture_chooser.run()
        picture_chooser.hide()
        
        if response == gtk.RESPONSE_OK:
            dirs.last_pic_dir = picture_chooser.get_current_folder()
            base, ext = os.path.splitext(picture_chooser.get_filename())
            
            # On windows firefox accepts absolute filenames only 
            # with the file:// prefix
            if not base.startswith('file://'):
                base = 'file://' + base
                
            self.day_text_field.insert('[""%s""%s]' % (base, ext))
            
    def on_insert_file_menu_item_activate(self, widget):
        dirs = self.journal.dirs
        file_chooser = self.builder.get_object('file_chooser')
        file_chooser.set_current_folder(dirs.last_file_dir)

        response = file_chooser.run()
        file_chooser.hide()
        
        if response == gtk.RESPONSE_OK:
            dirs.last_file_dir = file_chooser.get_current_folder()
            filename = file_chooser.get_filename()
            filename = os.path.normpath(filename)
            filename = 'file://' + filename
            head, tail = os.path.split(filename)
            # It is always safer to add the "file://" protocol and the ""s
            self.day_text_field.insert('[%s ""%s""]' % (tail, filename))
            
    def on_insert_link_menu_item_activate(self, widget):
        link_creator = self.builder.get_object('link_creator')
        link_location_entry = self.builder.get_object('link_location_entry')
        link_name_entry = self.builder.get_object('link_name_entry')
        
        link_location_entry.set_text('http://')
        link_name_entry.set_text('')

        response = link_creator.run()
        link_creator.hide()
        
        if response == gtk.RESPONSE_OK:
            link_location = self.builder.get_object('link_location_entry').get_text()
            link_name = self.builder.get_object('link_name_entry').get_text()
            
            # It is safer to add the http://
            if not link_location.lower().startswith('http://'):
                link_location = 'http://' + link_location
            
            if link_location and link_name:
                self.day_text_field.insert('[%s ""%s""]' % (link_name, link_location))
            elif link_location:
                self.day_text_field.insert(link_location)
            else:
                self.journal.show_message(_('No link location has been entered'), error=True)       
    
        
    def on_add_new_entry_button_clicked(self, widget):
        self.categories_tree_view._on_add_entry_clicked(None)
        
    def on_add_tag_button_clicked(self, widget):
        self.new_entry_dialog.show_dialog(category='Tags')
        
    def on_delete_entry_button_clicked(self, widget):
        self.categories_tree_view.delete_selected_node()
        
    def set_date(self, new_month, new_date, day):
        self.categories_tree_view.clear()
        
        self.calendar.set_date(new_date)
        self.calendar.set_month(new_month)
        
        # Converting markup to html takes time, so only do it when necessary
        if self.preview_mode:
            html = markup.convert(day.text, 'xhtml')
            self.html_editor.load_html(html)
        # Why do we always have to set the text of the day_text_field?
        self.day_text_field.set_text(day.text)
        self.categories_tree_view.set_day_content(day)
        
        if self.zeitgeist_widget:
            self.zeitgeist_widget.set_date(new_date)
        
        self.undo_redo_manager.clear()
        
        self.day = day
        
    def get_day_text(self):
        return self.day_text_field.get_text()
    
    def get_backup_file(self):
        if self.journal.title == 'data':
            name = ''
        else:
            name = '-' + self.journal.title
            
        proposed_file_name = 'RedNotebook-Backup%s_%s.zip' % (name, datetime.date.today())
            
        backup_dialog = self.builder.get_object('backup_dialog')
        backup_dialog.set_current_folder(os.path.expanduser('~'))
        backup_dialog.set_current_name(proposed_file_name)
        
        filter = gtk.FileFilter()
        filter.set_name("Zip")
        filter.add_pattern("*.zip")
        backup_dialog.add_filter(filter)

        response = backup_dialog.run()
        backup_dialog.hide()
        
        if response == gtk.RESPONSE_OK:
            return backup_dialog.get_filename()
            
            
    def highlight_text(self, search_text):
        # let the search function highlight found strings in the page
        #if self.preview_mode:
            # If we search twice on the same day, the html is not reloaded
            # so we have to manually highlight
        self.html_editor.highlight(search_text)
        #else:
        self.day_text_field.highlight(search_text)
            


class NewEntryDialog(object):
    def __init__(self, main_frame):
        dialog = main_frame.builder.get_object('new_entry_dialog')
        self.dialog = dialog
        
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
        self.new_entry_combo_box.connect('changed', self.on_entry_changed)
        
    def on_category_changed(self, widget):
        '''Show Tags in ComboBox when "Tags" is selected as category'''
        if self.categories_combo_box.get_active_text().upper() == 'TAGS':
            self.new_entry_combo_box.set_entries(self.journal.tags)
        elif self.new_entry_combo_box.liststore:
            self.new_entry_combo_box.liststore.clear()
            
        # only make the entry submittable, if text has been entered
        self.dialog.set_response_sensitive(gtk.RESPONSE_OK, self._text_entered())
        
    def on_entry_changed(self, widget):          
        # only make the entry submittable, if text has been entered
        self.dialog.set_response_sensitive(gtk.RESPONSE_OK, self._text_entered())
             
    def _text_entered(self):
        return bool(self.categories_combo_box.get_active_text() and \
                self.new_entry_combo_box.get_active_text())
        
    def show_dialog(self, category=''):
        # Has to be first, because it may be populated later
        self.new_entry_combo_box.clear()
        
        # Show the list of categories even if adding a tag
        self.categories_combo_box.set_entries(self.categories_tree_view.categories)
        
        if category:
            self.categories_combo_box.set_active_text(category)
        
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
        if not self.categories_tree_view.check_entry(entry_text):
            return
        
        self.categories_tree_view.add_entry(category_name, entry_text)
        
        # Update cloud
        self.main_frame.cloud.update()
        
            
            
            

    
    
class SearchComboBox(CustomComboBoxEntry):
    def __init__(self, combo_box, main_window):
        CustomComboBoxEntry.__init__(self, combo_box)
        
        self.main_window = main_window
        self.journal = main_window.journal
        
        #self.entry = self.combo_box.get_child()
        self.set_active_text(_('Search ...'))

        self.entry.connect('changed', self.on_entry_changed)
        self.entry.connect('activate', self.on_entry_activated)
        
        self.recent_searches = []
        
        self.search_type = 0
        
        
    def set_search_type(self, search_type):
        
        self.main_window.search_tree_view.set_search_type(search_type)
        
        if search_type == 0:
            # Search for text
            self.set_entries(self.recent_searches)
        if search_type == 1:
            # Search for category
            categories = self.main_window.categories_tree_view.categories
            self.set_entries(categories)
        if search_type == 2:
            # Search for tags
            self.set_entries(self.journal.tags)
            
        self.search_type = search_type
        

    def on_entry_changed(self, entry):
        """
            Called when the entry changes
        """
        self.search(self.get_active_text())
        
    def on_entry_activated(self, entry):
        """
            Called when the user hits enter
        """
        search_text = entry.get_text()
        
        if self.search_type == 0:
            # Search for text
            self.recent_searches.append(search_text)
            self.recent_searches = self.recent_searches[-20:]
            self.add_entry(search_text)
            
        self.search(self.get_active_text())
            
    def search(self, search_text):
        if self.search_type == 0:
            # Tell the webview which text to highlight after the html is loaded
            self.main_window.html_editor.search_text = search_text
        
            # Highlight all occurences in the current day's text
            self.main_window.highlight_text(search_text)
        
        self.main_window.search_tree_view.update_data(search_text)
        
        
        
class CloudView(HtmlWindow):
    def __init__(self, journal):
        HtmlWindow.__init__(self)
        
        self.journal = journal
        
        self.update_lists()
        
        self.htmlview.connect("url-clicked", self.word_clicked)
        self.htmlview.connect('populate-popup', self.create_popup_menu)
        self.htmlview.connect('right-click', self.on_right_click)
        
        self.htmlview.set_cursor_visible(False)
        
        self.set_type(0, init=True)
        
    def set_type(self, type_int, init=False):
        self.type_int = type_int
        self.type = ['word', 'category', 'tag'][type_int]
        if not init:
            self.update(force_update=True)
            
    def update_lists(self):
        config = self.journal.config
        
        default_ignore_list = _('filter, these, comma, separated, words')
        self.ignore_list = config.read_list('cloudIgnoreList', default_ignore_list)
        self.ignore_list = map(str.lower, self.ignore_list)
        logging.info('Cloud ignore list: %s' % self.ignore_list)
        
        ### Translators: These are example whitelist words with 4 or less letters
        default_include_list = _('mtv, spam, work, job, play')
        self.include_list = config.read_list('cloudIncludeList', default_include_list)
        self.include_list = map(str.lower, self.include_list)
        logging.info('Cloud include list: %s' % self.include_list)
        
        
    def update(self, force_update=False):
        if self.journal.frame is None:
            return
        
        logging.debug('Update the cloud (Type: %s, Force: %s)' % (self.type, force_update))
        
        # Do not update the cloud with words as it requires a lot of searching      
        if self.type == 'word' and not force_update:
            return
        
        self.journal.save_old_day()
        
        word_count_dict = self.journal.get_word_count_dict(self.type)
        logging.debug('Retrieved WordCountDict. Length: %s' % len(word_count_dict))
        
        self.tag_cloud_words, html = \
            utils.get_html_doc_from_word_count_dict(word_count_dict, self.type, \
                                            self.ignore_list, self.include_list)
        logging.debug('%s cloud words found' % len(self.tag_cloud_words))
        
        self.write(html)
        
        logging.debug('Cloud updated')
        
        
    def word_clicked(self, htmlview, uri, type_):
        self.journal.save_old_day()
        # uri has the form "something/somewhere/search/search_index"
        if 'search' in uri:
            # search_index is the part after last slash
            search_index = int(uri.split('/')[-1])
            search_text, count = self.tag_cloud_words[search_index]
            
            self.journal.frame.search_type_box.set_active(self.type_int)
            self.journal.frame.search_box.set_active_text(search_text)
            self.journal.frame.search_notebook.set_current_page(0)
            
            # returning True here stops loading the document
            return True

    def on_right_click(self, view, uri, type_):
        #logging.debug('URI clicked %s' % uri)
        # search_index is the part after last slash
        search_index = int(uri.split('/')[-1])
        word, count = self.tag_cloud_words[search_index]
        self.on_ignore_menu_activate(None, selected_words=[word])
        
    def create_popup_menu(self, textview, menu):
        '''
        Called when the cloud's popup menu is created
        '''
        label = _('Hide selected words')
        ignore_menu_item = gtk.MenuItem(label)
        separator = gtk.SeparatorMenuItem()
        
        ignore_menu_item.show()
        separator.show()
        
        menu.prepend(separator)
        menu.prepend(ignore_menu_item)
        
        ignore_menu_item.connect('activate', self.on_ignore_menu_activate)
        
    def on_ignore_menu_activate(self, menu_item, selected_words=None):
        if selected_words is None:
            selected_words = self.get_selected_words()
            
        logging.info('The following words will be hidden from clouds: %s' % selected_words)
        self.ignore_list.extend(selected_words)
        self.journal.config.write_list('cloudIgnoreList', self.ignore_list)
        self.update(force_update=True)
        
    def get_selected_words(self):
        bounds = self.htmlview.get_buffer().get_selection_bounds()
        
        if not bounds:
            return []
        
        text = self.htmlview.get_buffer().get_text(*bounds).decode('utf-8')
        words = text.split(' ')
        
        # Delete pseudo whitespace
        words = map(lambda word: word.replace('_', ''), words)
        
        # Delete whitespace
        words = map(lambda word: word.strip(), words)
        
        # Delete empty words
        words = filter(lambda word: len(word) > 0, words)
        
        return words
        
        

class SearchTreeView(object):
    def __init__(self, tree_view, main_window):
        self.tree_view = tree_view
        
        self.main_window = main_window
        
        self.journal = self.main_window.journal
        
        self.search_type = 0
        
        # Normally unneeded, but just to be sure everything works fine
        self.searched_text = ''
        
        # create a TreeStore with two string columns to use as the model
        self.tree_store = gtk.ListStore(str, str)

        # create the TreeView using tree_store
        self.tree_view.set_model(self.tree_store)

        # create the TreeViewColumns to display the data
        self.date_column = gtk.TreeViewColumn(_('Date'))
        self.matching_column = gtk.TreeViewColumn(_('Text'))
        
        columns = [self.date_column,self.matching_column, ]
                        #self.category_column, self.entry_column]

        # add tvcolumns to tree_view
        for index, column in enumerate(columns):
            self.tree_view.append_column(column)

            # create a CellRendererText to render the data
            cell_renderer = gtk.CellRendererText()

            # add the cell to the tvcolumn and allow it to expand
            column.pack_start(cell_renderer, True)

            # Get markup for column, not text
            column.set_attributes(cell_renderer, markup=index)
            
            # Allow sorting on the column
            column.set_sort_column_id(index)
        
        self.update_data()

        # make it searchable
        self.tree_view.set_search_column(1)
        
        self.tree_view.connect('row_activated', self.on_row_activated)
        
        
    def update_data(self, search_text=''):      
        self.tree_store.clear()
        
        rows = None
        
        if not search_text:
            return
        
        # Save the search text for highlighting
        self.searched_text = search_text
        
        if self.search_type == 0:
            # Search for text
            self.matching_column.set_title(_('Text'))
            rows = self.journal.search(text=search_text)
        if self.search_type == 1:
            # Search for category
            self.matching_column.set_title(_('Entry'))
            rows = self.journal.search(category=search_text)
        if self.search_type == 2:
            # Search for tags
            self.matching_column.set_title(_('Text'))
            rows = self.journal.search(tag=search_text)
            
        if rows:
            for date_string, entry in rows:
                if self.search_type == 1:
                    # We want **done** to be bold in the list,
                    # but the text should only be bold where the search text occurs
                    entry = markup.convert_to_pango(entry)
                else:
                    entry = entry.replace('&', '&amp;')
                self.tree_store.append([date_string, entry])
                
                
    def on_row_activated(self, treeview, path, view_column):
        date_string = self.tree_store[path][0]
        new_date = dates.get_date_from_date_string(date_string)
        self.journal.change_date(new_date)
        
        if self.search_type == 0:
            self.main_window.highlight_text(self.searched_text)
        
        
    def set_search_type(self, search_type):
        self.search_type = search_type
        
    
        
        
class DayTextField(object):
    def __init__(self, day_text_view, undo_redo_manager):
        self.day_text_view = day_text_view
        #self.day_text_buffer = gtk.TextBuffer()
        self.day_text_buffer = t2t_highlight.get_highlight_buffer()
        self.day_text_view.set_buffer(self.day_text_buffer)
        
        self.undo_redo_manager = undo_redo_manager
        
        self.changed_connection = self.day_text_buffer.connect('changed', self.on_text_change)
        
        self.old_text = ''
        
        # Some actions should get a break point even if not much text has been
        # changed
        self.force_adding_undo_point = False
        
        # spell checker
        self._spell_checker = None
        self.enable_spell_check(False)
        
        # Enable drag&drop
        #self.day_text_view.connect('drag-drop', self.on_drop) # unneeded
        self.day_text_view.connect('drag-data-received', self.on_drag_data_received)
        
    def set_text(self, text, undoing=False):
        self.insert(text, overwrite=True, undoing=undoing)
        
        
    def get_text(self):
        iter_start = self.day_text_buffer.get_start_iter()
        iter_end = self.day_text_buffer.get_end_iter()
        return self.day_text_buffer.get_text(iter_start, iter_end).decode('utf-8')
    
    
    def insert(self, text, iter=None, overwrite=False, undoing=False):
        self.force_adding_undo_point = True
        
        self.day_text_buffer.handler_block(self.changed_connection)
        
        if overwrite:
            self.day_text_buffer.set_text('')
            iter = self.day_text_buffer.get_start_iter()
        
        if iter is None:
            self.day_text_buffer.insert_at_cursor(text)
        else:
            if type(iter) == gtk.TextMark:
                iter = self.day_text_buffer.get_iter_at_mark(iter)
            self.day_text_buffer.insert(iter, text)
            
        self.day_text_buffer.handler_unblock(self.changed_connection)
        
        self.on_text_change(self.day_text_buffer, undoing=undoing)
        
            
    def highlight(self, text):
        iter_start = self.day_text_buffer.get_start_iter()
        
        # Hack: Ignoring the case is not supported for the search so we search
        # for the most common variants, but do not search identical ones
        variants = set([text, text.capitalize(), text.lower(), text.upper()])
        
        for search_text in variants:
            iter_tuple = iter_start.forward_search(search_text, \
                                gtk.TEXT_SEARCH_VISIBLE_ONLY \
                                #| gtk.SEARCH_CASE_INSENSITIVE # non-existent
                                )
            
            # When we find one variant, highlight it, scroll to it and quit
            if iter_tuple:
                self.set_selection(*iter_tuple)
                
                # It is safer to scroll to a mark than an iter
                mark = self.day_text_buffer.create_mark('highlight', iter_tuple[0], left_gravity=False)
                #self.day_text_view.scroll_to_iter(iter_tuple[0], 0)
                self.day_text_view.scroll_to_mark(mark, 0)
                self.day_text_buffer.delete_mark(mark)
                return
        
            
    def get_selected_text(self):
        bounds = self.day_text_buffer.get_selection_bounds()
        if bounds:
            return self.day_text_buffer.get_text(*bounds).decode('utf-8')
        else:
            return None

    def set_selection(self, iter1, iter2):
        '''
        Sort the two iters and select the text between them
        '''     
        sort_by_position = lambda iter: iter.get_offset()
        iter1, iter2 = sorted([iter1, iter2], key=sort_by_position)
        assert iter1.get_offset() <= iter2.get_offset()
        self.day_text_buffer.select_range(iter1, iter2)
        
    def get_selection_bounds(self):
        '''
        Return sorted iters
        
        Do not mix this method up with the textbuffer's method of the same name
        That method returns an empty tuple, if there is no selection
        '''
        mark1 = self.day_text_buffer.get_insert()
        mark2 = self.day_text_buffer.get_selection_bound()
        
        iter1 = self.day_text_buffer.get_iter_at_mark(mark1)
        iter2 = self.day_text_buffer.get_iter_at_mark(mark2)
        
        sort_by_position = lambda iter: iter.get_offset()
        iter1, iter2 = sorted([iter1, iter2], key=sort_by_position)
        
        assert iter1.get_offset() <= iter2.get_offset()
        return (iter1, iter2)
        
            
    def apply_format(self, format, markup):
        selected_text = self.get_selected_text()
        
        # If no text has been selected add example text and select it
        if not selected_text:
            selected_text = '%s text' % format
            self.insert(selected_text)
            
            # Set the selection to the new text
            
            # get_insert() returns the position of the cursor (after 2nd markup)
            insert_mark = self.day_text_buffer.get_insert()
            insert_iter = self.day_text_buffer.get_iter_at_mark(insert_mark)
            markup_start_iter = insert_iter.copy()
            markup_end_iter = insert_iter.copy()
            markup_start_iter.backward_chars(len(selected_text))
            markup_end_iter.backward_chars(0)
            self.set_selection(markup_start_iter, markup_end_iter)
            
        # Check that there is a selection
        assert self.day_text_buffer.get_selection_bounds()
            
        # Add the markup around the selected text
        insert_bound = self.day_text_buffer.get_insert()
        selection_bound = self.day_text_buffer.get_selection_bound()
        self.insert(markup, insert_bound)
        self.insert(markup, selection_bound)
        
        # Set the selection to the formatted text
        iter1, iter2 = self.get_selection_bounds()
        selection_start_iter = iter2.copy()
        selection_end_iter = iter2.copy()
        selection_start_iter.backward_chars(len(selected_text) + len(markup))
        selection_end_iter.backward_chars(len(markup))
        self.set_selection(selection_start_iter, selection_end_iter)
            
    def set_font_size(self, size):
        font = pango.FontDescription(str(size))
        self.day_text_view.modify_font(font)
    
    def hide(self):
        self.day_text_view.hide()
    
    def on_text_change(self, textbuffer, undoing=False):
        # Do not record changes while undoing or redoing
        if undoing:
            self.old_text = self.get_text()
            return
        
        new_text = self.get_text()
        old_text = self.old_text[:]     
        
        #Determine whether to add a save point
        much_text_changed = abs(len(new_text) - len(old_text)) >= 5
        
        if much_text_changed or self.force_adding_undo_point:
            
            def undo_func():
                self.set_text(old_text, undoing=True)
                
            def redo_func():
                self.set_text(new_text, undoing=True)
                
            action = undo.Action(undo_func, redo_func, 'day_text_field')
            self.undo_redo_manager.add_action(action)
        
            self.old_text = new_text
            self.force_adding_undo_point = False
            
    #===========================================================
    # Spell check code taken from KeepNote project
    
    def can_spell_check(self):
        """Returns True if spelling is available"""
        return gtkspell is not None
    
    def enable_spell_check(self, enabled=True):
        """Enables/disables spell check"""
        if not self.can_spell_check():
            return
        
        if enabled:
            if self._spell_checker is None:
                try:
                    self._spell_checker = gtkspell.Spell(self.day_text_view)
                except gobject.GError, err:
                    logging.error('Spell checking could not be enabled: "%s"' % err)
                    self._spell_checker = None
        else:
            if self._spell_checker is not None:
                self._spell_checker.detach()
                self._spell_checker = None

    def is_spell_check_enabled(self):
        """Returns True if spell check is enabled"""
        return self._spell_checker != None
        
    #===========================================================
    
    #def on_drop(self, widget, drag_context, x, y, timestamp):
        #logging.info('Drop occured')
        #self.day_text_view.emit_stop_by_name('drag-drop')
        #return True
        
    def on_drag_data_received(self, widget, drag_context, x, y, selection, info, timestamp):
        # We do not want the default behaviour
        self.day_text_view.emit_stop_by_name('drag-data-received')
        
        iter = self.day_text_view.get_iter_at_location(x, y)
        
        def is_pic(uri):
            head, ext = os.path.splitext(uri)
            return ext.lower().strip('.') in 'png jpeg jpg gif eps bmp'.split()
        
        uris = selection.data.strip('\r\n\x00')
        logging.debug('URIs: "%s"' % uris)
        uris = uris.split() # we may have more than one file dropped
        uris = map(str.strip, uris)
        for uri in uris:
            uri = urllib.url2pathname(uri)
            dirs, filename = os.path.split(uri)
            uri_without_ext, ext = os.path.splitext(uri)
            if is_pic(uri):
                self.insert('[""%s""%s]\n' % (uri_without_ext, ext), iter)
            else:
                # It is always safer to add the "file://" protocol and the ""s
                self.insert('[%s ""%s""]\n' % (filename, uri), iter)
        
        drag_context.finish(True, False, timestamp)
        # No further processing
        return True
    
        
        
class Statusbar(object):
    def __init__(self, statusbar):
        self.statusbar = statusbar
        
        self.context_i_d = self.statusbar.get_context_id('RedNotebook')
        self.last_message_i_d = None
        self.timespan = 7
        
    def remove_message(self):
        if hasattr(self.statusbar, 'remove_message'):
            self.statusbar.remove_message(self.context_i_d, self.last_message_i_d)
        else:
            # Deprecated
            self.statusbar.remove(self.context_i_d, self.last_message_i_d)
        
    def show_text(self, text, error=False, countdown=True):
        if self.last_message_i_d is not None:
            self.remove_message()
        self.last_message_i_d = self.statusbar.push(self.context_i_d, text)
        
        self.error = error
        
        if error:
            red = gtk.gdk.color_parse("red")
            self.statusbar.modify_bg(gtk.STATE_NORMAL, red)
        
        if countdown:
            self.start_countdown(text)
        
    def start_countdown(self, text):
        self.saved_text = text
        self.time_left = self.timespan
        self.countdown = gobject.timeout_add(1000, self.count_down)
        
    def count_down(self):
        self.time_left -= 1
        
        if self.error:
            if self.time_left % 2 == 0:
                self.show_text('', error=self.error, countdown=False)
            else:
                self.show_text(self.saved_text, error=self.error, countdown=False)
            
        if self.time_left <= 0:
            gobject.source_remove(self.countdown)
            self.show_text('', countdown=False)
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
        self.calendar.select_month(date.month-1, date.year)
        
        # Select the day after the month and year have been set
        self.calendar.select_day(date.day)
        
        # We want to listen to manual date changes
        self.calendar.handler_unblock(self.date_listener)
        
    def get_date(self):
        year, month, day = self.calendar.get_date()
        return datetime.date(year, month+1, day)
        
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
            logging.debug('Non-existent date in calendar: %s.%s.%s' % \
                        (day_number, cal_month, cal_year))
            return False
        return True
            
            
def get_image(name):
    image = gtk.Image()
    file_name = os.path.join(filesystem.image_dir, name)
    image.set_from_file(file_name)
    return image
