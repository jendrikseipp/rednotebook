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

from __future__ import with_statement
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


'Initialize the gtk thread engine'
#gtk.gdk.threads_init()

from rednotebook.util import utils
import rednotebook.util.unicode

from rednotebook.gui.menu import MainMenuBar
from rednotebook.gui.htmltextview import HtmlWindow
from rednotebook.gui.options import OptionsManager
from rednotebook.gui import widgets
from rednotebook.gui.widgets import CustomComboBoxEntry, CustomListView
from rednotebook.gui.richtext import HtmlEditor
from rednotebook.util import filesystem
from rednotebook import info
from rednotebook import templates
from rednotebook.util import markup
from rednotebook.util import dates
from rednotebook import undo

from rednotebook.gui.exportAssistant import ExportAssistant


class MainWindow(object):
	'''
	Class that holds the reference to the main glade file and handles
	all actions
	'''
	def __init__(self, redNotebook):
		
		self.redNotebook = redNotebook
		
		# Set the Glade file
		self.gladefile = os.path.join(filesystem.filesDir, 'mainWindow.glade')
		self.builder = gtk.Builder()
		try:
			self.builder.add_from_file(self.gladefile)
		except gobject.GError, err:
			logging.error('An error occured while loading the GUI: %s' % err)
			logging.error('RedNotebook requires at least gtk+ 2.14. '
							'If you cannot update gtk, you might want to try an '
							'older version of RedNotebook.')
			sys.exit(1)
			
		
		# Get the main window and set the icon
		self.mainFrame = self.builder.get_object('mainFrame')
		self.mainFrame.set_title('RedNotebook')
		self.mainFrame.set_icon_list(*map(lambda file: gtk.gdk.pixbuf_new_from_file(file), \
								filesystem.get_icons()))
		
		self.uimanager = gtk.UIManager()
		
		self.menubar_manager = MainMenuBar(self)
		self.menubar = self.menubar_manager.get_menu_bar()
		main_vbox = self.builder.get_object('vbox3')
		main_vbox.pack_start(self.menubar, False)
		main_vbox.reorder_child(self.menubar, 0)
		
		self.undo_redo_manager = undo.UndoRedoManager(self)
		
		
		
		self.calendar = Calendar(self.redNotebook, self.builder.get_object('calendar'))
		self.dayTextField = DayTextField(self.builder.get_object('dayTextView'), \
										self.undo_redo_manager)
		self.dayTextField.dayTextView.grab_focus()
		spell_check_enabled = self.redNotebook.config.read('spellcheck', 0)
		self.dayTextField.enable_spell_check(spell_check_enabled)
		
		self.statusbar = Statusbar(self.builder.get_object('statusbar'))
		
		self.newEntryDialog = NewEntryDialog(self)
		
		self.categoriesTreeView = CategoriesTreeView(self.builder.get_object(\
									'categoriesTreeView'), self)
		
		self.newEntryDialog.categoriesTreeView = self.categoriesTreeView
		
		self.backOneDayButton = self.builder.get_object('backOneDayButton')
		self.forwardOneDayButton = self.builder.get_object('forwardOneDayButton')
		
		self.editPane = self.builder.get_object('editPane')
		
		self.html_editor = HtmlEditor()
		self.text_vbox = self.builder.get_object('text_vbox')
		self.text_vbox.pack_start(self.html_editor)
		self.html_editor.hide()
		self.html_editor.set_editable(False)
		self.preview_mode = False
		self.preview_button = self.builder.get_object('previewButton')
		
		self.load_values_from_config()
		self.mainFrame.show()
		
		self.options_manager = OptionsManager(self)
		self.export_assistant = ExportAssistant(self)
		
		self.setup_search()
		self.setup_insert_menu()
		self.setup_format_menu()
		
		'Create an event->method dictionary and connect it to the widgets'
		dic = {
			'on_backOneDayButton_clicked': self.on_backOneDayButton_clicked,
			'on_todayButton_clicked': self.on_todayButton_clicked,
			'on_forwardOneDayButton_clicked': self.on_forwardOneDayButton_clicked,
			#'on_calendar_day_selected': self.on_calendar_day_selected,
			
			'on_previewButton_clicked': self.on_previewButton_clicked,
			
			'on_mainFrame_configure_event': self.on_mainFrame_configure_event,
			
			'on_addNewEntryButton_clicked': self.on_addNewEntryButton_clicked,
			'on_addTagButton_clicked': self.on_addTagButton_clicked,
			'on_deleteEntryButton_clicked': self.on_deleteEntryButton_clicked,
			
			'on_searchNotebook_switch_page': self.on_searchNotebook_switch_page,
			
			'on_templateButton_clicked': self.on_templateButton_clicked,
			'on_templateMenu_show_menu': self.on_templateMenu_show_menu,
			'on_templateMenu_clicked': self.on_templateMenu_clicked,
			
			'on_searchTypeBox_changed': self.on_searchTypeBox_changed,
			'on_cloudComboBox_changed': self.on_cloudComboBox_changed,
			
			'on_mainFrame_delete_event': self.on_mainFrame_delete_event,
			
			# connect_signals can only be called once, it seems
			# Otherwise RuntimeWarnings are raised: RuntimeWarning: missing handler '...'
			
			# Export Assistant
			'on_export_assistant_quit': self.export_assistant.on_quit,
			'on_export_assistant_cancel': self.export_assistant.on_cancel,
			'change_date_selector_status': self.export_assistant.change_date_selector_status,
			'select_category': self.export_assistant.select_category,
			'unselect_category': self.export_assistant.unselect_category,
			'change_categories_selector_status': self.export_assistant.change_categories_selector_status,
			'change_export_text_status': self.export_assistant.change_export_text_status,
			 }
		self.builder.connect_signals(dic)
		
		
		self.setup_clouds()
		self.set_shortcuts()
		self.setup_stats_dialog()
		
		self.template_manager = templates.TemplateManager(self)
		self.template_manager.make_empty_template_files()
		self.setup_template_menu()
		self.setup_tray_icon()
		
		
		
		
	def set_shortcuts(self):
		'''
		This method actually is not responsible for the Ctrl-C etc. actions
		'''
		self.accel_group = self.builder.get_object('accelgroup1')#gtk.AccelGroup()
		#self.accel_group = gtk.AccelGroup()
		self.mainFrame.add_accel_group(self.accel_group)
		#self.mainFrame.add_accel_group()
		#for key, signal in [('C', 'copy_clipboard'), ('V', 'paste_clipboard'), \
		#					('X', 'cut_clipboard')]:
		#	self.dayTextField.dayTextView.add_accelerator(signal, self.accel_group,
		#					ord(key), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		
		shortcuts = [(self.backOneDayButton, 'clicked', '<Ctrl>Page_Down'),
					(self.forwardOneDayButton, 'clicked', '<Ctrl>Page_Up'),
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
		self.tray_icon = widgets.RedNotebookTrayIcon()
		visible = (self.redNotebook.config.read('closeToTray', 0) == 1)
		self.tray_icon.set_visible(visible)
		logging.debug('Tray icon visible: %s' % visible)
		
		self.tray_icon.set_tooltip('RedNotebook')
		icon_file = os.path.join(self.redNotebook.dirs.frameIconDir, 'rn-32.png')
		self.tray_icon.set_from_file(icon_file)
		
		self.tray_icon.connect('activate', self.on_tray_icon_activated)
		self.tray_icon.connect('popup-menu', self.on_tray_popup_menu)
		
	def on_tray_icon_activated(self, tray_icon):
		if self.mainFrame.get_property('visible'):
			self.hide()
		else:
			self.mainFrame.show()
			
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
			('Show', gtk.STOCK_MEDIA_PLAY, 'Show RedNotebook', 
				None, None, lambda widget: self.mainFrame.show()),
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
		self.mainFrame.hide()
		self.redNotebook.saveToDisk(exitImminent=False)
		
	def on_mainFrame_delete_event(self, widget, event):
		'''
		Exit if not closeToTray
		'''
		#logging.debug('on_mainFrame_destroy')
		#self.saveToDisk(exitImminent=False)
		
		if self.redNotebook.config.read('closeToTray', 0):
			self.hide()
		
			# the default handler is _not_ to be called, 
			# and therefore the window will not be destroyed. 
			return True
		else:
			self.redNotebook.exit()
		
	def on_quit_activate(self, widget):
		'''
		User selected quit from the menu -> exit unconditionally
		'''
		#self.on_mainFrame_destroy(None)
		self.redNotebook.exit()
		
	# -------------------------------------------------------- TRAY-ICON / CLOSE
		
		
	def setup_stats_dialog(self):
		self.stats_dialog = self.builder.get_object('stats_dialog')
		overall_box = self.builder.get_object('overall_box')
		day_box = self.builder.get_object('day_box')
		overall_list = CustomListView()
		day_list = CustomListView()
		overall_box.pack_start(overall_list, True, True)
		day_box.pack_start(day_list, True, True)
		setattr(self.stats_dialog, 'overall_list', overall_list)
		setattr(self.stats_dialog, 'day_list', day_list)
		for list in [overall_list, day_list]:
			list.set_headers_visible(False)
			
			
	def on_previewButton_clicked(self, button):
		self.redNotebook.saveOldDay()
		
		text_scrolledwindow = self.builder.get_object('text_scrolledwindow')
		template_button = self.builder.get_object('templateMenuButton')
		
		# Do not forget to update the text in editor and preview respectively
		
		if self.preview_mode:
			# Enter edit mode
			self.dayTextField.set_text(self.day.text, undoing=True)
			self.dayTextField.dayTextView.grab_focus()
			
			text_scrolledwindow.show()
			self.html_editor.hide()
			self.preview_button.set_stock_id('gtk-media-play')
			self.preview_button.set_label('Preview')
			
			self.preview_mode = False
		else:
			# Enter preview mode			
			text_scrolledwindow.hide()
			self.html_editor.show()
			day = self.redNotebook.day
			text_markup = day.text
			html = markup.convert(text_markup, 'xhtml', append_whitespace=True)
			
			self.html_editor.load_html(html)
			
			self.preview_button.set_stock_id('gtk-edit')
			self.preview_button.set_label(' '*3 + 'Edit' + ' '*4)
		
			self.preview_mode = True
			
		template_button.set_sensitive(not self.preview_mode)
		self.single_menu_toolbutton.set_sensitive(not self.preview_mode)
		self.format_toolbutton.set_sensitive(not self.preview_mode)
		
			
	def setup_search(self):
		self.searchNotebook = self.builder.get_object('searchNotebook')
		
		self.searchTreeView = SearchTreeView(self.builder.get_object(\
									'searchTreeView'), self)
		self.searchTypeBox = self.builder.get_object('searchTypeBox')
		self.searchTypeBox.set_active(0)
		self.searchBox = SearchComboBox(self.builder.get_object('searchBox'), \
									self)
		
		
	def on_searchTypeBox_changed(self, widget):
		searchType = widget.get_active()
		self.searchBox.set_search_type(searchType)
		
			
	def on_searchNotebook_switch_page(self, notebook, page, pageNumber):
		if pageNumber == 0:
			'Switched to search tab'
			#self.searchTreeView.update_data()
		if pageNumber == 1:
			'Switched to cloud tab'
			self.cloud.update(force_update=True)
		
		
	def setup_clouds(self):
		self.cloudBox = self.builder.get_object('cloudBox')
		
		self.cloud = CloudView(self.redNotebook)
		self.cloudBox.pack_start(self.cloud)
		
		self.cloudComboBox = self.builder.get_object('cloudComboBox')
		self.cloudComboBox.set_active(0)
		
		
	def on_cloudComboBox_changed(self, cloudComboBox):
		value_int = cloudComboBox.get_active()
		self.cloud.set_type(value_int)
	
		
	def on_mainFrame_configure_event(self, widget, event):
		'''
		Is called when the frame size is changed. Unfortunately this is
		the way to go as asking for frame.get_size() at program termination
		gives strange results.		
		'''
		mainFrameWidth, mainFrameHeight = self.mainFrame.get_size()
		self.redNotebook.config['mainFrameWidth'] = mainFrameWidth
		self.redNotebook.config['mainFrameHeight'] = mainFrameHeight
		
	def on_backOneDayButton_clicked(self, widget):
		self.redNotebook.goToPrevDay()
		
	def on_todayButton_clicked(self, widget):
		actualDate = datetime.date.today()
		self.redNotebook.changeDate(actualDate)
		
	def on_forwardOneDayButton_clicked(self, widget):
		self.redNotebook.goToNextDay()
		
	def on_calendar_day_selected(self, widget):
		pass#
		#self.redNotebook.changeDate(self.calendar.get_date())
		
	def show_dir_chooser(self, type, dir_not_found=False):
		dir_chooser = self.builder.get_object('dir_chooser')
		label = self.builder.get_object('dir_chooser_label')
		
		if type == 'new':
			#dir_chooser.set_action(gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER)
			dir_chooser.set_title('Select an empty folder for your new journal')
			label.set_markup('<b>Journals are saved in a directory, not in a single file.\n' \
							'The directory name will be the title of the new journal.</b>')
		elif type == 'open':
			#dir_chooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
			dir_chooser.set_title("Select an existing journal directory")
			label.set_markup("<b>The directory should contain your journal's data files</b>")
		elif type == 'saveas':
			dir_chooser.set_title('Select an empty folder for the new location your journal')
			label.set_markup('<b>The directory name will be the new title of the journal</b>')
		dir_chooser.set_current_folder(self.redNotebook.dirs.dataDir)
		
		response = dir_chooser.run()
		dir_chooser.hide()
		
		if response == gtk.RESPONSE_OK:
			dir = dir_chooser.get_current_folder()
			
			if type == 'saveas':
				self.redNotebook.dirs.dataDir = dir
				
			load_files = type in ['open', 'saveas']
			self.redNotebook.open_journal(dir, load_files=load_files)
		
		# If the dir was not found previously, we have nothing to open
		# if the user selects "Abort". So select default dir and show message
		elif dir_not_found:
			default_dir = self.redNotebook.dirs.defaultDataDir
			self.redNotebook.open_journal(default_dir, load_files=True)
			self.redNotebook.showMessage('The default journal has been opened')
		
		
	def add_values_to_config(self):
		config = self.redNotebook.config
		
		config['leftDividerPosition'] = \
				self.builder.get_object('mainPane').get_position()
		config['rightDividerPosition'] = \
				self.builder.get_object('editPane').get_position()
		
		# Actually this is unnecessary as the list gets saved when it changes
		# so we use it to sort the list ;)
		config.write_list('cloudIgnoreList', sorted(self.cloud.ignore_list))
		
	
	def load_values_from_config(self):
		config = self.redNotebook.config
		mainFrameWidth = config.read('mainFrameWidth', 1024)
		mainFrameHeight = config.read('mainFrameHeight', 768)
		
		screen_width = gtk.gdk.screen_width()
		screen_height = gtk.gdk.screen_height()
		
		mainFrameWidth = min(mainFrameWidth, screen_width)
		mainFrameHeight = min(mainFrameHeight, screen_height)
		
		self.mainFrame.resize(mainFrameWidth, mainFrameHeight)
		
		#self.mainFrame.maximize()
		
		if config.has_key('leftDividerPosition'):
			self.builder.get_object('mainPane').set_position(config.read('leftDividerPosition', -1))
		self.builder.get_object('editPane').set_position(config.read('rightDividerPosition', 500))
		
		# A font size of -1 applies the standard font size
		main_font_size = config.read('mainFontSize', -1)
		
		self.set_font_size(main_font_size)
		
	def set_font_size(self, main_font_size):
		# -1 sets the default font size on Linux
		# -1 does not work on windows, 0 means invisible
		if sys.platform == 'win32' and main_font_size <= 0:
			main_font_size = 10
			
		self.dayTextField.set_font_size(main_font_size)
		self.html_editor.set_font_size(main_font_size)
		
		
	def setup_template_menu(self):
		self.template_menu_button = self.builder.get_object('templateMenuButton')
		self.template_menu_button.set_menu(gtk.Menu())
		self.template_menu_button.set_menu(self.template_manager.get_menu())
				
	
	def on_templateMenu_show_menu(self, widget):
		self.template_menu_button.set_menu(self.template_manager.get_menu())
		
	def on_templateMenu_clicked(self, widget):
		text = self.template_manager.get_weekday_text()
		#self.dayTextField.insert_template(text)
		self.dayTextField.insert(text)
		
	def on_templateButton_clicked(self, widget):
		text = self.template_manager.get_weekday_text()
		self.dayTextField.insert(text)
		
		
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
			<menuitem action="Stricken"/>
		</popup>
		</ui>'''
			
		uimanager = self.uimanager

		# Create an ActionGroup
		actiongroup = gtk.ActionGroup('FormatActionGroup')
		#self.actiongroup = actiongroup

		def tmpl(word):
			return word + ' (Ctrl+%s)' % word[0]
		
		def apply_format(action):
			format_to_markup = {'bold': '**', 'italic': '//', 'underline': '__',
								'stricken': '--'}
			if type(action) == gtk.Action:
				format = action.get_name().lower()
			else:
				format = 'bold'
			
			markup = format_to_markup[format]
			
			focus = self.mainFrame.get_focus()
			
			
			if focus == self.categoriesTreeView.treeView:
				iter = self.categoriesTreeView.get_selected_node()
				if iter:
					text = self.categoriesTreeView.get_iter_value(iter)
					text = '%s%s%s' % (markup, text, markup)
					self.categoriesTreeView.set_iter_value(iter, text)
					return
			#if focus is None or focus == self.dayTextField.dayTextView:
			self.dayTextField.apply_format(format, markup)
			
		
		def get_action(format):
			return (format, getattr(gtk, 'STOCK_' + format.upper()), \
				'_' + tmpl(format), \
				'<Control>' + format[0], None, \
				apply_format,
				)
		# Create actions
		strike_action = ('Stricken', gtk.STOCK_STRIKETHROUGH, \
				'Stricken', None, None, apply_format,)
		actions = map(get_action, ['Bold', 'Italic', 'Underline']) + [strike_action]
		actiongroup.add_actions(actions)

		# Add the actiongroup to the uimanager
		uimanager.insert_action_group(actiongroup, 0)

		# Add a UI description
		uimanager.add_ui_from_string(format_menu_xml)

		# Create a Menu
		menu = uimanager.get_widget('/FormatMenu')
		
		tooltips = gtk.Tooltips()
		
		#single_menu_toolbutton = SingleMenuToolButton(menu, 'Insert ')
		self.format_toolbutton = gtk.MenuToolButton(gtk.STOCK_BOLD)
		self.format_toolbutton.set_label('Format')
		tip = 'Format the selected text or category entry'
		self.format_toolbutton.set_tooltip(tooltips, tip)
		self.format_toolbutton.set_menu(menu)
		bold_func = apply_format#lambda widget: self.dayTextField.apply_format('bold')
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
			<!-- <menuitem action="NumberedList"/> -->
			<menuitem action="Title"/>
			<menuitem action="Line"/>
			<menuitem action="Date"/>
			<menuitem action="LineBreak"/>
		</popup>
		</ui>'''
			
		uimanager = self.uimanager

		# Add the accelerator group to the toplevel window
		accelgroup = uimanager.get_accel_group()
		self.mainFrame.add_accel_group(accelgroup)

		# Create an ActionGroup
		actiongroup = gtk.ActionGroup('InsertActionGroup')
		self.actiongroup = actiongroup
		
		line = '\n====================\n'
		bullet_list = '\n- First Item\n- Second Item\n  - Indented Item ' + \
						'(Two blank lines close the list)\n\n\n'
		numbered_list = bullet_list.replace('-', '+')
		title = '\n=== Title text ===\n'
		line_break = r'\\'
		
		def insert_date_time(widget):
			default_date_string = '%A, %x %X'
			date_string = self.redNotebook.config.read('dateTimeString', default_date_string)
			self.dayTextField.insert(time.strftime(date_string))

		def tmpl(letter):
			return ' (Ctrl+%s)' % letter
		
		# Create actions
		actiongroup.add_actions([
			('Picture', gtk.STOCK_ORIENTATION_PORTRAIT, \
				'Picture', \
				None, 'Insert a picture at the current position', \
				self.on_insert_pic_menu_item_activate),
			('File', gtk.STOCK_FILE, 'File', None, \
				'Insert a file at the current position', \
				self.on_insert_file_menu_item_activate),
			('Link', gtk.STOCK_JUMP_TO, '_Link' + tmpl('L'), '<Control>L', \
				'Insert a link at the current position', \
				self.on_insert_link_menu_item_activate),
			('BulletList', None, 'Bullet List', None, \
				'Insert a bullet list at the current position', \
				lambda widget: self.dayTextField.insert(bullet_list)),
			('NumberedList', None, 'Numbered List', None, \
				'Insert a numbered list at the current position', \
				lambda widget: self.dayTextField.insert(numbered_list)),
			('Title', None, 'Title', None, \
				'Insert a title at the current position', \
				lambda widget: self.dayTextField.insert(title)),
			('Line', None, 'Line', None, \
				'Insert a separator line at the current position', \
				lambda widget: self.dayTextField.insert(line)),
			('Table', None, 'Table', None, \
				'Insert a table at the current position', \
				lambda widget: self.dayTextField.insert(table)),
			('Date', None, 'Date/Time' + tmpl('D'), '<Ctrl>D', \
				'Insert the current date and time at the current position', \
				insert_date_time),
			('LineBreak', None, 'Line Break', None, \
				'Insert a line break at the current position', \
				lambda widget: self.dayTextField.insert(line_break)),
			])

		# Add the actiongroup to the uimanager
		uimanager.insert_action_group(actiongroup, 0)

		# Add a UI description
		uimanager.add_ui_from_string(insert_menu_xml)

		# Create a Menu
		menu = uimanager.get_widget('/InsertMenu')
		
		image_items = 'Picture Link BulletList Title Line Date LineBreak'.split()
		image_file_names = 'picture-16 link bulletlist title line date enter'.split()
		items_and_files = zip(image_items, image_file_names)
		
		for item, file_name in items_and_files:
			menu_item = uimanager.get_widget('/InsertMenu/'+ item)
			menu_item.set_image(get_image(file_name + '.png'))
		
		#single_menu_toolbutton = SingleMenuToolButton(menu, 'Insert ')
		# Ugly hack for windows: It expects toolbar icons to be 16x16
		#if sys.platform == 'win32':
			#self.single_menu_toolbutton = gtk.MenuToolButton(get_image('insert-image-16.png'), 'Insert')
		#else:
			#self.single_menu_toolbutton = gtk.MenuToolButton(get_image('insert-image-22.png'), 'Insert')
		self.single_menu_toolbutton = gtk.MenuToolButton(gtk.STOCK_ADD)
		self.single_menu_toolbutton.set_label('Insert')
			
		self.single_menu_toolbutton.set_menu(menu)
		self.single_menu_toolbutton.connect('clicked', self.show_insert_menu)
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
		dirs = self.redNotebook.dirs
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
			self.dayTextField.insert('[""%s""%s]' % (base, ext))
			
	def on_insert_file_menu_item_activate(self, widget):
		dirs = self.redNotebook.dirs
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
			#if ' ' in filename:
			self.dayTextField.insert('[%s ""%s""]' % (tail, filename))
			#else:
				#self.dayTextField.insert('[%s %s]' % (tail, filename))
			
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
				self.dayTextField.insert('[%s ""%s""]' % (link_name, link_location))
			elif link_location:
				self.dayTextField.insert(link_location)
			else:
				self.redNotebook.showMessage('No link location has been entered', error=True)		
	
		
	def on_addNewEntryButton_clicked(self, widget):
		self.categoriesTreeView._on_add_entry_clicked(None)
		
	def on_addTagButton_clicked(self, widget):
		self.newEntryDialog.show_dialog(category='Tags')
		
	def on_deleteEntryButton_clicked(self, widget):
		self.categoriesTreeView.delete_selected_node()
		
	def set_date(self, newMonth, newDate, day):
		self.categoriesTreeView.clear()
		
		self.calendar.set_date(newDate)
		self.calendar.setMonth(newMonth)
		
		# Converting markup to html takes time, so only do it when necessary
		if self.preview_mode:
			html = markup.convert(day.text, 'xhtml')
			self.html_editor.load_html(html)
		# Why do we always have to set the text of the dayTextField?
		self.dayTextField.set_text(day.text)
		self.categoriesTreeView.set_day_content(day)
		
		self.undo_redo_manager.clear()
		
		self.day = day
		
	def get_day_text(self):
		return self.dayTextField.get_text()
	
	def get_backup_file(self):
		if self.redNotebook.title == 'data':
			name = ''
		else:
			name = '-' + self.redNotebook.title
			
		proposedFileName = 'RedNotebook-Backup%s_%s.zip' % (name, datetime.date.today())
			
		backupDialog = self.builder.get_object('backupDialog')
		backupDialog.set_current_folder(os.path.expanduser('~'))
		backupDialog.set_current_name(proposedFileName)
		
		filter = gtk.FileFilter()
		filter.set_name("Zip")
		filter.add_pattern("*.zip")
		backupDialog.add_filter(filter)

		response = backupDialog.run()
		backupDialog.hide()
		
		if response == gtk.RESPONSE_OK:
			return backupDialog.get_filename()
	
	
	def show_new_version_dialog(self):
		newVersionDialog = self.builder.get_object('newVersionDialog')
		response = newVersionDialog.run()
		newVersionDialog.hide()
		
		if response == gtk.RESPONSE_OK:
			webbrowser.open(info.url)
		elif response == 20:
			#do not ask again
			self.redNotebook.config['checkForNewVersion'] = 0
			
	def show_no_new_version_dialog(self):
		dialog = self.builder.get_object('noNewVersionDialog')
		response = dialog.run()
		dialog.hide()
		
		if response == 30:
			#Ask at startup
			self.redNotebook.config['checkForNewVersion'] = 1
			

class NewEntryDialog(object):
	def __init__(self, mainFrame):
		dialog = mainFrame.builder.get_object('newEntryDialog')
		self.dialog = dialog
		
		self.mainFrame = mainFrame
		self.redNotebook = self.mainFrame.redNotebook
		self.categoriesComboBox = CustomComboBoxEntry(mainFrame.builder.get_object('categoriesComboBox'))
		self.newEntryComboBox = CustomComboBoxEntry(mainFrame.builder.get_object('entryComboBox'))
		
		# Let the user finish a new category entry by hitting ENTER
		def respond(widget):
			if self._text_entered():
				self.dialog.response(gtk.RESPONSE_OK)
		self.newEntryComboBox.entry.connect('activate', respond)
		self.categoriesComboBox.entry.connect('activate', respond)
		
		self.categoriesComboBox.connect('changed', self.on_category_changed)
		self.newEntryComboBox.connect('changed', self.on_entry_changed)
		
	def on_category_changed(self, widget):
		'''Show Tags in ComboBox when "Tags" is selected as category'''
		if self.categoriesComboBox.get_active_text().upper() == 'TAGS':
			self.newEntryComboBox.set_entries(self.redNotebook.tags)
			 
		# only make the entry submittable, if text has been entered
		self.dialog.set_response_sensitive(gtk.RESPONSE_OK, self._text_entered())
		
	def on_entry_changed(self, widget):			 
		# only make the entry submittable, if text has been entered
		self.dialog.set_response_sensitive(gtk.RESPONSE_OK, self._text_entered())
			 
	def _text_entered(self):
		return bool(self.categoriesComboBox.get_active_text() and \
				self.newEntryComboBox.get_active_text())
		
	def show_dialog(self, category=''):
		# Show the list of categories even if adding a tag
		self.categoriesComboBox.set_entries(self.categoriesTreeView.categories)
		
		# Has to be first, because it may be popularized later
		self.newEntryComboBox.clear()
		
		self.categoriesComboBox.set_active_text(category)
		
		if category:			
			# We already know the category so let's get the entry
			self.newEntryComboBox.comboBox.grab_focus()
		else:
			self.categoriesComboBox.comboBox.grab_focus()
		
		response = self.dialog.run()
		self.dialog.hide()
		
		if not response == gtk.RESPONSE_OK:
			return
		
		categoryName = self.categoriesComboBox.get_active_text()
		if not self.categoriesTreeView.check_category(categoryName):
			return
		
		entryText = self.newEntryComboBox.get_active_text()
		if not self.categoriesTreeView.check_entry(entryText):
			return
		
		self.categoriesTreeView.addEntry(categoryName, entryText)
		
		# Update cloud
		self.mainFrame.cloud.update()
		
			
			
			

	
	
class SearchComboBox(CustomComboBoxEntry):
	def __init__(self, comboBox, mainWindow):
		CustomComboBoxEntry.__init__(self, comboBox)
		
		self.mainWindow = mainWindow
		self.redNotebook = mainWindow.redNotebook
		
		#self.entry = self.comboBox.get_child()
		self.set_active_text('Search ...')

		self.entry.connect('changed', self.on_entry_changed)
		self.entry.connect('activate', self.on_entry_activated)
		
		self.recentSearches = []
		
		self.searchType = 0
		
		
	def set_search_type(self, searchType):
		
		self.mainWindow.searchTreeView.set_search_type(searchType)
		
		if searchType == 0:
			'Search for text'
			self.set_entries(self.recentSearches)
		if searchType == 1:
			'Search for category'
			categories = self.mainWindow.categoriesTreeView.categories
			self.set_entries(categories)
		if searchType == 2:
			'Search for tags'
			self.set_entries(self.redNotebook.tags)
			
		self.searchType = searchType
		

	def on_entry_changed(self, entry):
		"""
			Called when the entry changes
		"""
		#self.search(entry.get_text())
		self.search(self.get_active_text())
		
	def on_entry_activated(self, entry):
		"""
			Called when the user hits enter
		"""
		searchText = entry.get_text()
		
		if self.searchType == 0:
			'Search for text'
			self.recentSearches.append(searchText)
			self.recentSearches = self.recentSearches[-20:]
			self.add_entry(searchText)
			
		self.search(self.get_active_text())
			
	def search(self, searchText):
		self.mainWindow.searchTreeView.update_data(searchText)
		
		
		
class CloudView(HtmlWindow):
	def __init__(self, redNotebook):
		HtmlWindow.__init__(self)
		
		self.redNotebook = redNotebook
		
		self.update_ignore_list()
		
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
			
	def update_ignore_list(self):
		default_ignore_list = 'filter, these, comma, separated, words'
		self.ignore_list = self.redNotebook.config.read_list('cloudIgnoreList', \
															default_ignore_list)
		self.ignore_list = map(lambda word: word.lower(), self.ignore_list)
		logging.info('Cloud ignore list: %s' % self.ignore_list)
		
		
	def update(self, force_update=False):
		if self.redNotebook.frame is None:
			return
		
		logging.debug('Update the cloud (Type: %s, Force: %s)' % (self.type, force_update))
		
		# Do not update the cloud with words as it requires a lot of searching		
		if self.type == 'word' and not force_update:
			return
		
		self.redNotebook.saveOldDay()
		
		wordCountDict = self.redNotebook.getWordCountDict(self.type)
		logging.debug('Retrieved WordCountDict. Length: %s' % len(wordCountDict))
		
		self.tagCloudWords, html = utils.getHtmlDocFromWordCountDict(wordCountDict, \
												self.type, self.ignore_list)
		logging.debug('%s cloud words found' % len(self.tagCloudWords))
		
		self.write(html)
		
		logging.debug('Cloud updated')
		
		
	def word_clicked(self, htmlview, uri, type_):
		self.redNotebook.saveOldDay()
		# uri has the form "something/somewhere/search/searchIndex"
		if 'search' in uri:
			# searchIndex is the part after last slash
			searchIndex = int(uri.split('/')[-1])
			searchText, count = self.tagCloudWords[searchIndex]
			
			self.redNotebook.frame.searchTypeBox.set_active(self.type_int)
			self.redNotebook.frame.searchBox.set_active_text(searchText)
			self.redNotebook.frame.searchNotebook.set_current_page(0)
			
			'returning True here stops loading the document'
			return True

	def on_right_click(self, view, uri, type_):
		#logging.debug('URI clicked %s' % uri)
		# searchIndex is the part after last slash
		searchIndex = int(uri.split('/')[-1])
		word, count = self.tagCloudWords[searchIndex]
		self.on_ignore_menu_activate(None, selected_words=[word])
		
	def create_popup_menu(self, textview, menu):
		'''
		Called when the cloud's popup menu is created
		'''
		label = 'Hide selected words'
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
		self.redNotebook.config.write_list('cloudIgnoreList', self.ignore_list)
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
	def __init__(self, treeView, mainWindow):
		self.treeView = treeView
		
		self.mainWindow = mainWindow
		
		self.redNotebook = self.mainWindow.redNotebook
		
		self.searchType = 0
		
		# Normally unneeded, but just to be sure everything works fine
		self.searched_text = ''
		
		'create a TreeStore with two string columns to use as the model'
		self.treeStore = gtk.ListStore(str, str)

		'create the TreeView using treeStore'
		self.treeView.set_model(self.treeStore)

		'create the TreeViewColumns to display the data'
		self.dateColumn = gtk.TreeViewColumn('Date')
		self.matchingColumn = gtk.TreeViewColumn('Text')
		
		columns = [self.dateColumn,self.matchingColumn, ]
						#self.categoryColumn, self.entryColumn]

		'add tvcolumns to treeView'
		for index, column in enumerate(columns):
			self.treeView.append_column(column)

			'create a CellRendererText to render the data'
			cellRenderer = gtk.CellRendererText()

			'add the cell to the tvcolumn and allow it to expand'
			column.pack_start(cellRenderer, True)

			'Get markup for column, not text'
			column.set_attributes(cellRenderer, markup=index)
			
			'Allow sorting on the column'
			column.set_sort_column_id(index)
		
		self.update_data()

		'make it searchable'
		self.treeView.set_search_column(1)
		
		self.treeView.connect('row_activated', self.on_row_activated)
		
		
	def update_data(self, searchText=''):
		self.treeStore.clear()
		
		rows = None
		
		if not searchText:
			return
		
		# Save the search text for highlighting
		self.searched_text = searchText
		
		if self.searchType == 0:
			'Search for text'
			self.matchingColumn.set_title('Text')
			rows = self.redNotebook.search(text=searchText)
		if self.searchType == 1:
			'Search for category'
			self.matchingColumn.set_title('Entry')
			rows = self.redNotebook.search(category=searchText)
		if self.searchType == 2:
			'Search for tags'
			self.matchingColumn.set_title('Text')
			rows = self.redNotebook.search(tag=searchText)
			
		if rows:
			for dateString, entry in rows:
				if self.searchType == 1:
					entry = markup.convert_to_pango(entry)
				
				self.treeStore.append([dateString, entry])
				
				
	def on_row_activated(self, treeview, path, view_column):
		dateString = self.treeStore[path][0]
		newDate = dates.get_date_from_date_string(dateString)
		self.redNotebook.changeDate(newDate)
		
		if self.searchType == 0:
			# let the search function highlight found strings in the page
			if self.mainWindow.preview_mode:
				self.mainWindow.html_editor._textview.highlight(self.searched_text)
			else:
				self.mainWindow.dayTextField.highlight(self.searched_text)
		
		
	def set_search_type(self, searchType):
		self.searchType = searchType
		
	

class CategoriesTreeView(object):
	def __init__(self, treeView, mainWindow):
		self.treeView = treeView
		
		self.mainWindow = mainWindow
		self.undo_redo_manager = mainWindow.undo_redo_manager
		
		'Maintain a list of all entered categories. Initialized by rn.__init__()'
		self.categories = None
		
		self.statusbar = self.mainWindow.statusbar
		
		'create a TreeStore with one string column to use as the model'
		self.treeStore = gtk.TreeStore(str)

		'create the TreeView using treeStore'
		self.treeView.set_model(self.treeStore)

		'create the TreeViewColumn to display the data'
		self.tvcolumn = gtk.TreeViewColumn('Categories')

		'add tvcolumn to treeView'
		self.treeView.append_column(self.tvcolumn)

		'create a CellRendererText to render the data'
		self.cell = gtk.CellRendererText()
		
		self.cell.set_property('editable', True)
		self.cell.connect('edited', self.edited_cb, self.treeStore)
		self.cell.connect('editing-started', self.on_editing_started)

		'add the cell to the tvcolumn and allow it to expand'
		self.tvcolumn.pack_start(self.cell, True)

		''' set the cell "text" attribute to column 0 - retrieve text
			from that column in treeStore'''
		#self.tvcolumn.add_attribute(self.cell, 'text', 0)
		self.tvcolumn.add_attribute(self.cell, 'markup', 0)

		'make it searchable'
		self.treeView.set_search_column(0)

		'Allow sorting on the column'
		self.tvcolumn.set_sort_column_id(0)
		
		# Enable a context menu
		self.context_menu = self._get_context_menu()
		
		self.treeView.connect('button-press-event', self.on_button_press_event)
		
		# Wrap lines
		self.cell.props.wrap_mode = pango.WRAP_WORD
		self.cell.props.wrap_width = 200
		self.treeView.connect_after("size-allocate", self.on_size_allocate, self.tvcolumn, self.cell)

		
	def node_on_top_level(self, iter):
		if not type(iter) == gtk.TreeIter:
			# iter is a path -> convert to iter
			iter = self.treeStore.get_iter(iter)
		assert self.treeStore.iter_is_valid(iter)
		return self.treeStore.iter_depth(iter) == 0
		
		
	def on_editing_started(self, cell, editable, path):		
		# Let the renderer use text not markup temporarily
		self.tvcolumn.clear_attributes(self.cell)
		self.tvcolumn.add_attribute(self.cell, 'text', 0)
		
		# Fetch the markup
		pango_markup = self.treeStore[path][0]
		
		# Reset the renderer to use markup
		self.tvcolumn.clear_attributes(self.cell)
		self.tvcolumn.add_attribute(self.cell, 'markup', 0)
		
		# We want to show txt2tags markup and not pango markup
		editable.set_text(markup.convert_from_pango(pango_markup))
		
		
	def edited_cb(self, cell, path, new_text, user_data):
		'''
		Called when text in a cell is changed
		
		new_text is txt2tags markup
		'''
		if new_text == 'text' and self.node_on_top_level(path):
			self.statusbar.showText('"text" is a reserved keyword', error=True)
			return
		if len(new_text) < 1:
			self.statusbar.showText('Empty nodes are not allowed', error=True)
			return
		
		liststore = user_data
		pango_markup = markup.convert_to_pango(new_text)
		liststore[path][0] = pango_markup
		
		# Category name changed
		if self.node_on_top_level(path):
			if new_text not in self.categories:
				self.categories.insert(0, new_text)
		
		# Tag name changed
		else:
			iter = self.treeStore.get_iter(path)
			iter_parent = self.treeStore.iter_parent(iter)
			tags_iter = self._get_category_iter('Tags')
			
			tags_node_is_parent = self.get_iter_value(iter_parent).capitalize() == 'Tags'
			if tags_node_is_parent and self.node_on_top_level(iter_parent):
				self.mainWindow.redNotebook.saveOldDay()
				
		# Update cloud
		self.mainWindow.cloud.update()
		
		
	def check_category(self, category):
		if category == 'text':
			self.statusbar.showText('"text" is a reserved keyword', error=True)
			return False
		if len(category) < 1:
			self.statusbar.showText('Empty category names are not allowed', error=True)
			return False
		
		return True
		
		
	def check_entry(self, text):
		if len(text) < 1:
			self.statusbar.showText('Empty entries are not allowed', error=True)
			return False
		
		return True

	
	def add_element(self, parent, elementContent):
		'''Recursive Method for adding the content'''
		for key, value in elementContent.iteritems():
			if key is not None:
				key_pango = markup.convert_to_pango(key)
			newChild = self.treeStore.append(parent, [key_pango])
			if not value == None:
				self.add_element(newChild, value)
			
		
	def set_day_content(self, day):
		for key, value in day.content.iteritems():
			if not key == 'text':
				self.add_element(None, {key: value})
		self.treeView.expand_all()
				
				
	def get_day_content(self):
		if self.empty():
			return {}
		
		content = self._get_element_content(None)
		
		return content
		   
		   
	def _get_element_content(self, element):
		model = self.treeStore
		if self.treeStore.iter_n_children(element) == 0:
			return None
		else:
			content = {}
				
			for i in range(model.iter_n_children(element)):
				child = model.iter_nth_child(element, i)
				txt2tags_markup = self.get_iter_value(child)				
				content[txt2tags_markup] = self._get_element_content(child)
			
			return content
		
		
	def empty(self, category_iter=None):
		'''
		Tests whether a category has children
		
		If no category is given, test whether there are any categories
		'''
		return self.treeStore.iter_n_children(category_iter) == 0
		
		
	def clear(self):
		self.treeStore.clear()
		assert self.empty(), self.treeStore.iter_n_children(None)
		
		
	def get_iter_value(self, iter):
		# Let the renderer use text not markup temporarily
		self.tvcolumn.clear_attributes(self.cell)
		self.tvcolumn.add_attribute(self.cell, 'text', 0)
		
		pango_markup = self.treeStore.get_value(iter, 0).decode('utf-8')
		
		# Reset the renderer to use markup
		self.tvcolumn.clear_attributes(self.cell)
		self.tvcolumn.add_attribute(self.cell, 'markup', 0)
				
		# We want to have txt2tags markup and not pango markup
		text = markup.convert_from_pango(pango_markup)
		return text
	
	
	def set_iter_value(self, iter, txt2tags_markup):
		'''
		text is txt2tags markup
		'''
		pango_markup = markup.convert_to_pango(txt2tags_markup)
		self.treeStore.set_value(iter, 0, pango_markup)
	
	def find_iter(self, category, entry):
		logging.debug('Looking for iter: "%s", "%s"' % (category, entry))
		category_iter = self._get_category_iter(category)
		
		if not category_iter:
			# If the category was not found, return None
			return None
		
		for iterIndex in range(self.treeStore.iter_n_children(category_iter)):
			current_entry_iter = self.treeStore.iter_nth_child(category_iter, iterIndex)
			current_entry = self.get_iter_value(current_entry_iter)
			if str(current_entry) == str(entry):
				return current_entry_iter
		
		# If the entry was not found, return None
		logging.debug('Iter not found: "%s", "%s"' % (category, entry))
		return None
		
		
		
	def _get_category_iter(self, categoryName):
		for iterIndex in range(self.treeStore.iter_n_children(None)):
			currentCategoryIter = self.treeStore.iter_nth_child(None, iterIndex)
			currentCategoryName = self.get_iter_value(currentCategoryIter)
			if str(currentCategoryName).lower() == str(categoryName).lower():
				return currentCategoryIter
		
		# If the category was not found, return None
		logging.debug('Category not found: "%s"' % categoryName)
		return None
	
	
	def addEntry(self, category, entry, undoing=False):
		if category not in self.categories and category is not None:
			self.categories.insert(0, category)
			
		categoryIter = self._get_category_iter(category)
			
		entry_pango = markup.convert_to_pango(entry)
		category_pango = markup.convert_to_pango(category)	
		
		if categoryIter is None:
			'If category does not exist add new category'
			categoryIter = self.treeStore.append(None, [category_pango])
			entry_node = self.treeStore.append(categoryIter, [entry_pango])
		else:
			'If category exists add entry to existing category'
			entry_node = self.treeStore.append(categoryIter, [entry_pango])
			
		if not undoing:
			undo_func = lambda: self.delete_node(self.find_iter(category, entry), undoing=True)
			redo_func = lambda: self.addEntry(category, entry, undoing=True)
			action = undo.Action(undo_func, redo_func, 'categories_tree_view')
			self.undo_redo_manager.add_action(action)
		
		self.treeView.expand_all()
			
	
	def get_selected_node(self):
		'''
		Returns selected node or None if none is selected
		'''
		treeSelection = self.treeView.get_selection()
		model, selectedIter = treeSelection.get_selected()
		return selectedIter
	
	
	def delete_node(self, iter, undoing=False):
		if not iter:
			# The user has changed the text of the node or deleted it
			return
		
		# Save for undoing ------------------------------------
		
		# An entry is deleted
		# We want to delete empty categories too
		if not self.node_on_top_level(iter):
			deleting_entry = True
			category_iter = self.treeStore.iter_parent(iter)
			category = self.get_iter_value(category_iter)
			entries = [self.get_iter_value(iter)]
		
		# A category is deleted
		else:
			deleting_entry = False
			category_iter = iter
			category = self.get_iter_value(category_iter)
			entries = self._get_element_content(category_iter).keys()
			
			
		# Delete ---------------------------------------------
			
		self.treeStore.remove(iter)
		
		# Delete empty category
		if deleting_entry and self.empty(category_iter):
			self.treeStore.remove(category_iter)
		
		# ----------------------------------------------------
			
			
		
		if not undoing:
				
			def undo_func():
				for entry in entries:
					self.addEntry(category, entry, undoing=True)
					
			def redo_func():
				for entry in entries:
					delete_iter = self.find_iter(category, entry)
					self.delete_node(delete_iter, undoing=True)
				
			action = undo.Action(undo_func, redo_func, 'categories_tree_view')
			self.undo_redo_manager.add_action(action)
		
		# Update cloud
		self.mainWindow.cloud.update()
		
		
	def delete_selected_node(self):
		'''
		This method used to show a warning dialog. This has become obsolete
		with the addition of undo functionality for the categories
		'''
		selectedIter = self.get_selected_node()
		if selectedIter:
			self.delete_node(selectedIter)
			return
		
		
			message = 'Do you really want to delete this node?'
			sortOptimalDialog = gtk.MessageDialog(parent=self.mainWindow.mainFrame, \
									flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_QUESTION, \
									buttons=gtk.BUTTONS_YES_NO, message_format=message)
			response = sortOptimalDialog.run()
			sortOptimalDialog.hide()
			
			if response == gtk.RESPONSE_YES:
				self.delete_node(selectedIter)
				
				
				
				
	def on_button_press_event(self, widget, event):
		"""
		@param widget - gtk.TreeView - The Tree View
		@param event - gtk.gdk.event - Event information
		"""
		#Get the path at the specific mouse position
		path = widget.get_path_at_pos(int(event.x), int(event.y))
		if (path == None):
			"""If we didn't get a path then we don't want anything
			to be selected."""
			selection = widget.get_selection()
			selection.unselect_all()
			
		# Do not show change and delete options, if nothing is selected
		something_selected = (path is not None)
		uimanager = self.mainWindow.uimanager
		change_entry_item = uimanager.get_widget('/ContextMenu/ChangeEntry')
		change_entry_item.set_sensitive(something_selected)
		delete_entry_item = uimanager.get_widget('/ContextMenu/Delete')
		delete_entry_item.set_sensitive(something_selected)
			
		if (event.button == 3):
			#This is a right-click
			self.context_menu.popup(None, None, None, event.button, event.time)
			
	def _get_context_menu(self):
		context_menu_xml = '''
		<ui>
		<popup action="ContextMenu">
			<menuitem action="ChangeEntry"/>
			<menuitem action="AddEntry"/>
			<menuitem action="Delete"/>
		</popup>
		</ui>'''
			
		uimanager = self.mainWindow.uimanager

		# Create an ActionGroup
		actiongroup = gtk.ActionGroup('ContextMenuActionGroup')
		
		new_entry_dialog = self.mainWindow.newEntryDialog
		
		# Create actions
		actiongroup.add_actions([
			('ChangeEntry', gtk.STOCK_EDIT, \
				'Change this text', \
				None, None, self._on_change_entry_clicked
			),
			('AddEntry', gtk.STOCK_NEW, \
				'Add new entry', \
				None, None, self._on_add_entry_clicked
			),
			('Delete', gtk.STOCK_DELETE, \
				'Delete this node', \
				None, None, self._on_delete_entry_clicked
			),
			])

		# Add the actiongroup to the uimanager
		uimanager.insert_action_group(actiongroup, 0)

		# Add a UI description
		uimanager.add_ui_from_string(context_menu_xml)

		# Create a Menu
		menu = uimanager.get_widget('/ContextMenu')
		return menu
	
	def _on_change_entry_clicked(self, action):
		iter = self.get_selected_node()
		self.treeView.set_cursor(self.treeStore.get_path(iter), \
								focus_column=self.tvcolumn, start_editing=True)
		self.treeView.grab_focus()
	
	def _on_add_entry_clicked(self, action):
		iter = self.get_selected_node()
		
		dialog = self.mainWindow.newEntryDialog
		
		# Either nothing was selected -> show normal newEntryDialog
		if iter is None:
			dialog.show_dialog()
		# or a category was selected
		elif self.node_on_top_level(iter):
			category = self.get_iter_value(iter)
			dialog.show_dialog(category=category)
		# or an entry was selected
		else:
			parent_iter = self.treeStore.iter_parent(iter)
			category = self.get_iter_value(parent_iter)
			dialog.show_dialog(category=category)
			
	def _on_delete_entry_clicked(self, action):
		self.delete_selected_node()
		
	
	def on_size_allocate(self, treeview, allocation, column, cell):
		'''
		Code from pychess project
		(http://code.google.com/p/pychess/source/browse/trunk/lib/pychess/
		System/uistuff.py?r=1025#62)
		
		Allows dynamic line wrapping in a treeview
		'''
		otherColumns = (c for c in treeview.get_columns() if c != column)
		newWidth = allocation.width - sum(c.get_width() for c in otherColumns)
		newWidth -= treeview.style_get_property("horizontal-separator") * 2
		
		## Customize for treeview with expanders
		## The behaviour can only be fitted to one depth -> take the second one
		newWidth -= treeview.style_get_property('expander-size') * 3
		
		if cell.props.wrap_width == newWidth or newWidth <= 0:
			return
		cell.props.wrap_width = newWidth
		store = treeview.get_model()
		iter = store.get_iter_first()
		while iter and store.iter_is_valid(iter):
			store.row_changed(store.get_path(iter), iter)
			iter = store.iter_next(iter)
		treeview.set_size_request(0,-1)
		
		## The heights may have changed
		column.queue_resize()
		
	
		
		
class DayTextField(object):
	def __init__(self, dayTextView, undo_redo_manager):
		self.dayTextView = dayTextView
		self.dayTextBuffer = gtk.TextBuffer()
		self.dayTextView.set_buffer(self.dayTextBuffer)
		
		self.undo_redo_manager = undo_redo_manager
		
		self.changed_connection = self.dayTextBuffer.connect('changed', self.on_text_change)
		
		self.old_text = ''
		
		# Some actions should get a break point even if not much text has been
		# changed
		self.force_adding_undo_point = False
		
		# spell checker
		self._spell_checker = None
		self.enable_spell_check(False)
		
		
	def set_text(self, text, undoing=False):
		self.insert(text, overwrite=True, undoing=undoing)
		
		
	def get_text(self):
		iterStart = self.dayTextBuffer.get_start_iter()
		iterEnd = self.dayTextBuffer.get_end_iter()
		return self.dayTextBuffer.get_text(iterStart, iterEnd).decode('utf-8')
	
	
	def insert(self, text, iter=None, overwrite=False, undoing=False):
		self.force_adding_undo_point = True
		
		self.dayTextBuffer.handler_block(self.changed_connection)
		
		if overwrite:
			self.dayTextBuffer.set_text('')
			iter = self.dayTextBuffer.get_start_iter()
		
		if iter is None:
			self.dayTextBuffer.insert_at_cursor(text)
		else:
			if type(iter) == gtk.TextMark:
				iter = self.dayTextBuffer.get_iter_at_mark(iter)
			self.dayTextBuffer.insert(iter, text)
			
		self.dayTextBuffer.handler_unblock(self.changed_connection)
		
		self.on_text_change(self.dayTextBuffer, undoing=undoing)
		
	
#	def insert_template(self, template):
#		logging.debug('Inserting template')
#		currentText = self.get_text()
#		try:
#			self.insert(template.decode('utf-8') + '\n', self.dayTextBuffer.get_start_iter())
#		except UnicodeDecodeError, err:
#			logging.error('Template file contains unreadable content. Is it really just ' \
#			'a text file?')
			
	def highlight(self, text):
		iter_start = self.dayTextBuffer.get_start_iter()
		
		# Hack: Ignoring the case is not supported for the search so we search
		# for the most common variants, but do not search identical ones
		variants = set([text, text.capitalize(), text.lower(), text.upper()])
		
		for search_text in variants:
			iter_tuple = iter_start.forward_search(search_text, gtk.TEXT_SEARCH_VISIBLE_ONLY)
			
			# When we find one variant, highlight it and quit
			if iter_tuple:
				self.set_selection(*iter_tuple)
				return
		
			
	def get_selected_text(self):
		bounds = self.dayTextBuffer.get_selection_bounds()
		if bounds:
			return self.dayTextBuffer.get_text(*bounds).decode('utf-8')
		else:
			return None

	def set_selection(self, iter1, iter2):
		'''
		Sort the two iters and select the text between them
		'''		
		sort_by_position = lambda iter: iter.get_offset()
		iter1, iter2 = sorted([iter1, iter2], key=sort_by_position)
		assert iter1.get_offset() <= iter2.get_offset()
		self.dayTextBuffer.select_range(iter1, iter2)
		
	def get_selection_bounds(self):
		'''
		Return sorted iters
		
		Do not mix this method up with the textbuffer's method of the same name
		That method returns an empty tuple, if there is no selection
		'''
		mark1 = self.dayTextBuffer.get_insert()
		mark2 = self.dayTextBuffer.get_selection_bound()
		
		iter1 = self.dayTextBuffer.get_iter_at_mark(mark1)
		iter2 = self.dayTextBuffer.get_iter_at_mark(mark2)
		
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
			insert_mark = self.dayTextBuffer.get_insert()
			insert_iter = self.dayTextBuffer.get_iter_at_mark(insert_mark)
			markup_start_iter = insert_iter.copy()
			markup_end_iter = insert_iter.copy()
			markup_start_iter.backward_chars(len(selected_text))
			markup_end_iter.backward_chars(0)
			self.set_selection(markup_start_iter, markup_end_iter)
			
		# Check that there is a selection
		assert self.dayTextBuffer.get_selection_bounds()
			
		# Add the markup around the selected text
		insert_bound = self.dayTextBuffer.get_insert()
		selection_bound = self.dayTextBuffer.get_selection_bound()
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
		self.dayTextView.modify_font(font)
	
	def hide(self):
		self.dayTextView.hide()
	
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
				self._spell_checker = gtkspell.Spell(self.dayTextView)
		else:
			if self._spell_checker is not None:
				self._spell_checker.detach()
				self._spell_checker = None

	def is_spell_check_enabled(self):
		"""Returns True if spell check is enabled"""
		return self._spell_checker != None
		
	#===========================================================
		
	
		
		
class Statusbar(object):
	def __init__(self, statusbar):
		self.statusbar = statusbar
		
		self.contextID = self.statusbar.get_context_id('RedNotebook')
		self.lastMessageID = None
		self.timespan = 7
		
	def showText(self, text, error=False, countdown=True):
		if self.lastMessageID is not None:
			self.statusbar.remove(self.contextID, self.lastMessageID)
		self.lastMessageID = self.statusbar.push(self.contextID, text)
		
		self.error = error
		
		if error:
			red = gtk.gdk.color_parse("red")
			self.statusbar.modify_bg(gtk.STATE_NORMAL, red)
		
		if countdown:
			self.start_countdown(text)
		
	def start_countdown(self, text):
		self.savedText = text
		self.timeLeft = self.timespan
		self.countdown = gobject.timeout_add(1000, self.count_down)
		
	def count_down(self):
		self.timeLeft -= 1
		
		if self.error:
			if self.timeLeft % 2 == 0:
				self.showText('', error=self.error, countdown=False)
			else:
				self.showText(self.savedText, error=self.error, countdown=False)
			
		if self.timeLeft <= 0:
			gobject.source_remove(self.countdown)
			self.showText('', countdown=False)
		return True
	
		
class Calendar(object):
	def __init__(self, redNotebook, calendar):
		self.redNotebook = redNotebook
		self.calendar = calendar
		
		self.date_listener = self.calendar.connect('day-selected', self.on_day_selected)
		
	def on_day_selected(self, cal):
		self.redNotebook.changeDate(self.get_date())
		
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
		
	def setDayEdited(self, dayNumber, edited):
		'''
		It may happen that we try to mark a day that is non-existent in this month
		if we switch by clicking on the calendar e.g. from Aug 31 to Sep 1.
		The month has already changed and there is no Sep 31. 
		Still saveOldDay tries to mark the 31st.
		'''
		if not self._check_date(dayNumber):
			return
		
		if edited:
			self.calendar.mark_day(dayNumber)
		else:
			self.calendar.unmark_day(dayNumber)
			
	def setMonth(self, month):
		#month_days = dates.get_number_of_days(month.yearNumber, month.monthNumber)
		#for dayNumber in range(1, month_days + 1):
		#	self.setDayEdited(dayNumber, False)
		self.calendar.clear_marks()
		for dayNumber, day in month.days.items():
			self.setDayEdited(dayNumber, not day.empty)
			
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
	file_name = os.path.join(filesystem.imageDir, name)
	image.set_from_file(file_name)
	return image
