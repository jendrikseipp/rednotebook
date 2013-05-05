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
import webbrowser

import gtk

from rednotebook.util import utils
from rednotebook import info
from rednotebook.util import filesystem
from rednotebook.util import markup
from rednotebook import storage
#from rednotebook.gui.imports import ImportAssistant
from rednotebook.gui import insert_menu
from rednotebook.gui import format_menu


MENUBAR_XML = '''\
<ui>
<menubar name="MainMenuBar">
    <menu action="Journal">
        <menuitem action="New"/>
        <menuitem action="Open"/>
        <separator/>
        <menuitem action="Save"/>
        <menuitem action="SaveAs"/>
        <separator/>
        <!--<menuitem action="Import"/>-->
        <menuitem action="Export"/>
        <menuitem action="Backup"/>
        <menuitem action="Statistics"/>
        <separator/>
        <menuitem action="Quit"/>
    </menu>
    <menu action="Edit">
        <menuitem action="Undo"/>
        <menuitem action="Redo"/>
        <separator/>
        <menuitem action="Cut"/>
        <menuitem action="Copy"/>
        <menuitem action="Paste"/>
        <separator/>
        <menuitem action="Fullscreen"/>
        <separator/>
        <menuitem action="Find"/>
        <separator/>
        <menuitem action="CheckSpelling"/>
        <menuitem action="Options"/>
    </menu>
    %s
    %s
    <menu action="HelpMenu">
        <menuitem action="Help"/>
        <separator/>
        <menuitem action="OnlineHelp"/>
        <menuitem action="Translate"/>
        <menuitem action="ReportBug"/>
        <separator/>
        <menuitem action="Info"/>
    </menu>
</menubar>
</ui>''' % (insert_menu.MENUBAR_XML, format_menu.MENUBAR_XML)


class MainMenuBar(object):
    def __init__(self, main_window, *args, **kwargs):
        self.main_window = main_window
        self.uimanager = main_window.uimanager
        self.journal = self.main_window.journal
        self.setup()

    def get_actiongroup(self):
        # Create an ActionGroup
        actiongroup = gtk.ActionGroup('MainMenuActionGroup')

        # Create actions
        actiongroup.add_actions([
            ('Journal', None, _('_Journal')),
            ('New', gtk.STOCK_NEW, None,
                '', _('Create a new journal. The old one will be saved'),
                self.on_new_journal_button_activate),
            ('Open', gtk.STOCK_OPEN, None,
                None, _('Load an existing journal. The old journal will be saved'),
                self.on_open_journal_button_activate),
            ('Save', gtk.STOCK_SAVE, None,
                None, None, self.on_save_button_clicked),
            ('SaveAs', gtk.STOCK_SAVE_AS, None,
                None, _('Save journal at a new location. The old journal files will also be saved'),
                self.on_save_as_menu_item_activate),
            ### Translators: Verb
            #('Import', gtk.STOCK_ADD, _('_Import'),
            #    None, _('Open the import assistant'), self.on_import_menu_item_activate),
            ### Translators: Verb
            ('Export', gtk.STOCK_CONVERT, _('Export'),
                '<Ctrl>e', _('Open the export assistant'), self.on_export_menu_item_activate),
            ### Translators: Verb
            ('Backup', gtk.STOCK_HARDDISK, _('_Backup'),
                None, _('Save all the data in a zip archive'), self.on_backup_activate),
            ('Statistics', None, _('S_tatistics'),
                None, _('Show some statistics about the journal'), self.on_statistics_menu_item_activate),
            ('Quit', gtk.STOCK_QUIT, None,
                None, _('Shutdown RedNotebook. It will not be sent to the tray.'),
                self.main_window.on_quit_activate),

            ('Edit', None, _('_Edit'), None, None, self.on_edit_menu_activate),
            ('Undo', gtk.STOCK_UNDO, None,
                '<Ctrl>z', _('Undo text or tag edits'), self.on_undo),
            ('Redo', gtk.STOCK_REDO, None,
                '<Ctrl>y', _('Redo text or tag edits'), self.on_redo),
            ('Cut', gtk.STOCK_CUT, None,
                '', None, self.on_cut_menu_item_activate),
            ('Copy', gtk.STOCK_COPY, None,
                '', None, self.on_copy_menu_item_activate),
            ('Paste', gtk.STOCK_PASTE, None,
                '', None, self.on_paste_menu_item_activate),
            ('Fullscreen', gtk.STOCK_FULLSCREEN, None,
                'F11', None, self.on_fullscreen_menuitem_activate),
            ('Find', gtk.STOCK_FIND, None,
                None, None, self.on_find_menuitem_activate),
        ])
        actiongroup.add_toggle_actions([
            ('CheckSpelling', gtk.STOCK_SPELL_CHECK, None,
                'F7', _('Underline misspelled words'), self.on_checkspelling_menuitem_toggled),
        ])
        actiongroup.add_actions([
            ('Options', gtk.STOCK_PREFERENCES, None,
                '<Ctrl><Alt>p', None, self.on_options_menuitem_activate),
            ('HelpMenu', None, _('_Help')),
            ('Help', gtk.STOCK_HELP, _('Contents'),
                '<Ctrl>h', _('Open the RedNotebook documentation'), self.on_help_menu_item_activate),
            ('OnlineHelp', None, _('Get Help Online'),
                None, _('Browse answered questions or ask a new one'), self.on_online_help),
            ('Translate', None, _('Translate RedNotebook'),
                None, _('Connect to the Launchpad website to help translate RedNotebook'),
                self.on_translate),
            ('ReportBug', None, _('Report a Problem'),
                None, _('Fill out a short form about the problem'),
                self.on_report_bug),
            ('Info', gtk.STOCK_ABOUT, None,
                None, None, self.on_info_activate),
        ])
        return actiongroup

    def setup(self):
        # Add the actiongroup to the uimanager
        self.uimanager.insert_action_group(self.get_actiongroup(), 0)

        # Add a UI description
        self.uimanager.add_ui_from_string(MENUBAR_XML)

    def get_menu_bar(self):
        return self.uimanager.get_widget('/MainMenuBar')

    def check_journal_dir(self, action, new_dir):
        if not new_dir:
            return False
        title = _('Wrong directory')
        # Check if dir exists and is no forbidden path (e.g. $HOME dir).
        if not self.journal.dirs.is_valid_journal_path(new_dir):
            self.journal.show_message(_('You cannot use this directory for your journal:') +
                                      ' %s' % new_dir, title=title, error=True)
            return False
        if action in ['new', 'saveas'] and os.listdir(new_dir):
            self.journal.show_message(_('Please select an empty directory.'),
                                      title=title, error=True)
            return False
        elif action in ['open'] and not list(storage.get_journal_files(new_dir)):
            self.journal.show_message(_('This directory contains no journal files:') +
                                      ' ' + new_dir, title=title, error=True)
            return False
        return True

    def select_journal(self, action, title, message):
        new_dir = self.main_window.get_new_journal_dir(title, message)
        if not self.check_journal_dir(action, new_dir):
            return

        if action == 'saveas':
            self.journal.dirs.data_dir = new_dir
            self.journal.save_to_disk(saveas=True)
        self.journal.open_journal(new_dir)

    def on_new_journal_button_activate(self, widget):
        msg = ('%s\n%s' % (_('Journals are saved in a directory, not in a single file.'),
                           _('The directory name will be the title of the new journal.')))
        self.select_journal('new', _('Select an empty folder for your new journal'), msg)

    def on_open_journal_button_activate(self, widget):
        self.select_journal('open', _('Select an existing journal directory'),
                            _("The directory should contain your journal's data files"))

    def on_save_button_clicked(self, widget):
        self.journal.save_to_disk()

    def on_save_as_menu_item_activate(self, widget):
        # widget is None when we call this method after the journal could not be
        # saved. Then another try won't succeed either.
        if widget is not None:
            self.journal.save_to_disk()
        self.select_journal('saveas', _('Select an empty folder for the new location of your journal'),
                            _('The directory name will be the new title of the journal'))

    def on_edit_menu_activate(self, widget):
        """Only set the menu items sensitive if the actions can be performed."""
        edit_mode = not self.main_window.preview_mode
        for action in ['Cut', 'Paste']:
            self.main_window.uimanager.get_widget('/MainMenuBar/Edit/%s' % action).set_sensitive(edit_mode)

    def on_undo(self, widget):
        self.main_window.undo_redo_manager.undo()

    def on_redo(self, widget):
        self.main_window.undo_redo_manager.redo()

    def _get_active_editor_widget(self):
        if self.main_window.preview_mode:
            return self.main_window.html_editor.webview
        else:
            return self.main_window.day_text_field.day_text_view

    def on_copy_menu_item_activate(self, widget):
        self._get_active_editor_widget().emit('copy_clipboard')

    def on_paste_menu_item_activate(self, widget):
        self._get_active_editor_widget().emit('paste_clipboard')

    def on_cut_menu_item_activate(self, widget):
        self._get_active_editor_widget().emit('cut_clipboard')

    def on_fullscreen_menuitem_activate(self, widget):
        self.main_window.toggle_fullscreen()

    def on_find_menuitem_activate(self, widget):
        '''
        Change to search page and put the cursor into the search box
        '''
        self.main_window.search_box.entry.grab_focus()

    def on_checkspelling_menuitem_toggled(self, widget):
        self.main_window.day_text_field.enable_spell_check(widget.get_active())
        self.journal.config['spellcheck'] = int(widget.get_active())

    def on_options_menuitem_activate(self, widget):
        self.main_window.options_manager.on_options_dialog()

    def on_backup_activate(self, widget):
        self.journal.archiver.backup()

    #def on_import_menu_item_activate(self, widget):
    #    assistant = ImportAssistant(self.journal)
    #    assistant.run()

    def on_export_menu_item_activate(self, widget):
        self.journal.save_old_day()
        selected_text = self.main_window.day_text_field.get_selected_text()
        self.main_window.export_assistant.run(selected_text)

    def on_statistics_menu_item_activate(self, widget):
        self.journal.stats.show_dialog(self.main_window.stats_dialog)

    def on_help_menu_item_activate(self, widget):
        temp_dir = self.journal.dirs.temp_dir
        filesystem.write_file(os.path.join(temp_dir, 'source.txt'), info.help_text)
        html = markup.convert(info.help_text, 'xhtml',
                              self.journal.dirs.data_dir,
                              headers=[_('RedNotebook Documentation'), info.version, ''],
                              options={'toc': 1})
        utils.show_html_in_browser(html, os.path.join(temp_dir, 'help.html'))

    def on_online_help(self, widget):
        webbrowser.open(info.answers_url)

    def on_translate(self, widget):
        webbrowser.open(info.translation_url)

    def on_report_bug(self, widget):
        webbrowser.open(info.bug_url)

    def on_info_activate(self, widget):
        self.info_dialog = self.main_window.builder.get_object('about_dialog')
        self.info_dialog.set_transient_for(self.main_window.main_frame)
        self.info_dialog.set_name('RedNotebook')
        self.info_dialog.set_version(info.version)
        self.info_dialog.set_copyright('Copyright (c) 2008-2012 Jendrik Seipp')
        self.info_dialog.set_comments(_('A Desktop Journal'))
        gtk.about_dialog_set_url_hook(lambda dialog, url: webbrowser.open(url))
        self.info_dialog.set_website(info.url)
        self.info_dialog.set_website_label(info.url)
        self.info_dialog.set_authors(info.developers)
        # TODO: Use svg again once it's fixed under Windows.
        img_path = os.path.join(filesystem.image_dir, 'rednotebook-icon', 'rn-192.png')
        self.info_dialog.set_logo(gtk.gdk.pixbuf_new_from_file(img_path))
        self.info_dialog.set_license(info.license_text)
        self.info_dialog.run()
        self.info_dialog.hide()
