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
from rednotebook.imports import ImportAssistant


class MainMenuBar(object):

	def __init__(self, main_window, *args, **kwargs):
		self.main_window = main_window
		self.uimanager = main_window.uimanager
		self.redNotebook = self.main_window.redNotebook
		self.menubar = None

	def get_menu_bar(self):

		if self.menubar:
			return self.menubar

		menu_xml = '''
		<ui>
		<menubar name="MainMenuBar">
			<menu action="Journal">
				<menuitem action="New"/>
				<menuitem action="Open"/>
				<separator/>
				<menuitem action="Save"/>
				<menuitem action="SaveAs"/>
				<separator/>
				<menuitem action="Import"/>
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
				<menuitem action="Find"/>
				<separator/>
				<menuitem action="Options"/>
			</menu>
			<menu action="HelpMenu">
				<menuitem action="Help"/>
				<separator/>
				<menuitem action="OnlineHelp"/>
				<menuitem action="Translate"/>
				<menuitem action="ReportBug"/>
				<separator/>
				<menuitem action="Examples"/>
				<menuitem action="Info"/>
			</menu>
		</menubar>
		</ui>'''

		# Create an ActionGroup
		actiongroup = gtk.ActionGroup('MainMenuActionGroup')

		# Create actions
		actiongroup.add_actions([
			('Journal', None, _('Journal')),
			('New', gtk.STOCK_NEW, None,
				'', _('Create a new journal. The old one will be saved'),
				self.on_newJournalButton_activate),
			('Open', gtk.STOCK_OPEN, None,
				None, _('Load an existing journal. The old journal will be saved'),
				self.on_openJournalButton_activate),
			('Save', gtk.STOCK_SAVE, None,
				None, None, self.on_saveButton_clicked),
			('SaveAs', gtk.STOCK_SAVE_AS, None,
				None, _('Save journal at a new location. The old journal files will also be saved'),
				self.on_saveAsMenuItem_activate),
			### Translators: Verb
			('Import', gtk.STOCK_ADD, _('Import'),
				None, _('Open the import assistant'), self.on_importMenuItem_activate),
			### Translators: Verb
			('Export', gtk.STOCK_CONVERT, _('Export'),
				None, _('Open the export assistant'), self.on_exportMenuItem_activate),
			### Translators: Verb
			('Backup', gtk.STOCK_HARDDISK, _('Backup'),
				None, _('Save all the data in a zip archive'), self.on_backup_activate),
			('Statistics', None, _('Statistics'),
				None, _('Show some statistics about the journal'), self.on_statisticsMenuItem_activate),
			('Quit', gtk.STOCK_QUIT, None,
				None, _('Shutdown RedNotebook. It will not be sent to the tray.'),
				self.main_window.on_quit_activate),

			('Edit', None, _('_Edit'), None, None, self.on_edit_menu_activate),
			('Undo', gtk.STOCK_UNDO, None,
				'<Ctrl>z', _('Undo text edits or category entry deletions'), self.on_undo),
			('Redo', gtk.STOCK_REDO, None,
				'<Ctrl>y', _('Redo text edits or category entry additions'), self.on_redo),
			('Cut', gtk.STOCK_CUT, None,
				'', None, self.on_cutMenuItem_activate),
			('Copy', gtk.STOCK_COPY, None,
				'', None, self.on_copyMenuItem_activate),
			('Paste', gtk.STOCK_PASTE, None,
				'', None, self.on_pasteMenuItem_activate),
			('Find', gtk.STOCK_FIND, None,
				None, None, self.on_find_menuitem_activate),
			('Options', gtk.STOCK_PREFERENCES, None,
				'<Ctrl><Alt>p', None, self.on_options_menuitem_activate),

			('HelpMenu', None, _('_Help')),
			#('CheckVersion', None, _('Check For New Version'),
			#	None, _('Check for a new version now'), self.on_checkVersionMenuItem_activate),
			('Help', gtk.STOCK_HELP, _('Contents'),
				'<Ctrl>h', _('Open the RedNotebook documentation'), self.on_helpMenuItem_activate),
			('OnlineHelp', None, _('Get Help Online'),
				None, _('Visit the RedNotebook forum'), self.on_online_help),
			('Examples', None, _('Restore example content'),
				None, _('Fill some free days with example content. Do not overwrite anything'),
				self.on_example_menu_item_activate),
			('Translate', None, _('Translate RedNotebook'),
				None, _('Connect to the Launchpad website to help translate RedNotebook'),
				self.on_translate),
			('ReportBug', None, _('Report a Problem'),
				None, _('Fill out a short form about the problem'),
				self.on_report_bug),
			('Info', gtk.STOCK_ABOUT, None,
				None, None, self.on_info_activate),
			])

		# Add the actiongroup to the uimanager
		self.uimanager.insert_action_group(actiongroup, 0)

		# Add a UI description
		self.uimanager.add_ui_from_string(menu_xml)
		
		# We want to hide the examples button for now
		examples_button = self.uimanager.get_widget('/MainMenuBar/HelpMenu/Examples')
		examples_button.hide()

		# Create a Menu
		self.menubar = self.uimanager.get_widget('/MainMenuBar')
		return self.menubar

	def set_tooltips(self):
		groups = self.uimanager.get_action_groups()
		for group in groups:
			actions = group.list_actions()
			for action in actions:
				widgets = action.get_proxies()
				tooltip = action.get_property('tooltip')
				print widgets, tooltip
				if tooltip:
					for widget in widgets:
						widget.set_tooltip_markup(tooltip)

	def on_newJournalButton_activate(self, widget):
		self.main_window.show_dir_chooser('new')

	def on_openJournalButton_activate(self, widget):
		self.main_window.show_dir_chooser('open')

	def on_saveButton_clicked(self, widget):
		self.redNotebook.saveToDisk()

	def on_saveAsMenuItem_activate(self, widget):
		self.redNotebook.saveToDisk()

		self.main_window.show_dir_chooser('saveas')

	def on_edit_menu_activate(self, widget):
		'''
		Only set the menu items for undo and redo sensitive if the actions
		can really be performed

		Probably useless since the buttons are set in undo.py
		'''
		can_undo = self.main_window.undo_redo_manager.can_undo()
		self.main_window.uimanager.get_widget('/MainMenuBar/Edit/Undo').set_sensitive(can_undo)
		can_redo = self.main_window.undo_redo_manager.can_redo()
		self.main_window.uimanager.get_widget('/MainMenuBar/Edit/Redo').set_sensitive(can_redo)

	def on_undo(self, widget):
		self.main_window.undo_redo_manager.undo()

	def on_redo(self, widget):
		self.main_window.undo_redo_manager.redo()

	def on_copyMenuItem_activate(self, widget):
		self.main_window.dayTextField.dayTextView.emit('copy_clipboard')

	def on_pasteMenuItem_activate(self, widget):
		self.main_window.dayTextField.dayTextView.emit('paste_clipboard')

	def on_cutMenuItem_activate(self, widget):
#		event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
#		event.keyval = ord("X")
#		event.state = gtk.gdk.CONTROL_MASK
#		self.mainFrame.emit("key_press_event",event)
		self.main_window.dayTextField.dayTextView.emit('cut_clipboard')

	def on_find_menuitem_activate(self, widget):
		'''
		Change to search page and put the cursor into the search box
		'''
		self.main_window.searchNotebook.set_current_page(0)
		self.main_window.searchBox.entry.grab_focus()

	def on_options_menuitem_activate(self, widget):
		self.main_window.options_manager.on_options_dialog()


	def on_backup_activate(self, widget):
		self.redNotebook.backupContents(backup_file=self.main_window.get_backup_file())
		
	def on_importMenuItem_activate(self, widget):
		assistant = ImportAssistant(self.redNotebook)
		assistant.run()

	def on_exportMenuItem_activate(self, widget):
		self.redNotebook.saveOldDay()
		self.main_window.export_assistant.run()

	def on_statisticsMenuItem_activate(self, widget):
		self.redNotebook.stats.show_dialog(self.main_window.stats_dialog)

	def on_example_menu_item_activate(self, widget):
		self.redNotebook.addInstructionContent()

	def on_helpMenuItem_activate(self, widget):
		temp_dir = self.redNotebook.dirs.tempDir
		utils.write_file(info.helpText, os.path.join(temp_dir, 'source.txt'))
		headers = [_('RedNotebook Documentation'), info.version, '']
		options = {'toc': 1,}
		html = markup.convert(info.helpText, 'xhtml', headers, options)
		utils.show_html_in_browser(html, os.path.join(temp_dir, 'help.html'))

	#def on_checkVersionMenuItem_activate(self, widget):
	#	utils.check_new_version(self.main_window, info.version)
	
	def on_online_help(self, widget):
		webbrowser.open(info.forum_url)
		
	def on_translate(self, widget):
		webbrowser.open(info.translation_url)
		
	def on_report_bug(self, widget):
		webbrowser.open(info.bug_url)

	def on_info_activate(self, widget):
		self.infoDialog = self.main_window.builder.get_object('aboutDialog')
		self.infoDialog.set_name('RedNotebook')
		self.infoDialog.set_version(info.version)
		self.infoDialog.set_copyright('Copyright (c) 2008 Jendrik Seipp')
		self.infoDialog.set_comments(_('A Desktop Journal'))
		gtk.about_dialog_set_url_hook(lambda dialog, url: webbrowser.open(url))
		self.infoDialog.set_website(info.url)
		self.infoDialog.set_website_label(info.url)
		self.infoDialog.set_authors(info.developers)
		self.infoDialog.set_logo(gtk.gdk.pixbuf_new_from_file(\
					os.path.join(filesystem.imageDir,'redNotebookIcon/rn-128.png')))
		self.infoDialog.set_license(info.licenseText)
		self.infoDialog.run()
		self.infoDialog.hide()


