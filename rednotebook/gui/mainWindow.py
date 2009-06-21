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
import urllib
import urlparse
import webbrowser
import logging

import gtk
import gobject
import gtk.glade

'Initialize the gtk thread engine'
#gtk.gdk.threads_init()

from rednotebook.util import utils
import rednotebook.util.unicode

from rednotebook.gui.htmltextview import HtmlWindow
from rednotebook.gui.richtext import HtmlEditor
from rednotebook.util import filesystem
from rednotebook import info
from rednotebook import templates
from rednotebook.util import markup
from rednotebook.util import dates

from rednotebook.gui.exportAssistant import ExportAssistant


class MainWindow(object):
	'''
	Class that holds the reference to the main glade file and handles
	all actions
	'''
	def __init__(self, redNotebook):
		
		self.redNotebook = redNotebook
		
		'Set the Glade file'
		self.gladefile = os.path.join(filesystem.filesDir, 'mainWindow.glade')
		self.wTree = gtk.glade.XML(self.gladefile)
		
		
		'Get the main window and set the icon'
		self.mainFrame = self.wTree.get_widget('mainFrame')
		self.mainFrame.set_title('RedNotebook')
		self.mainFrame.set_icon_list(*map(lambda file: gtk.gdk.pixbuf_new_from_file(file), \
								filesystem.get_icons()))
		self.load_values_from_config()
		self.mainFrame.show()
		
		self.uimanager = gtk.UIManager()
		
		self.calendar = Calendar(self.wTree.get_widget('calendar'))
		self.dayTextField = DayTextField(self.wTree.get_widget('dayTextView'))
		self.statusbar = Statusbar(self.wTree.get_widget('statusbar'))
		
		self.newEntryDialog = NewEntryDialog(self)
		
		self.categoriesTreeView = CategoriesTreeView(self.wTree.get_widget(\
									'categoriesTreeView'), self)
		
		self.newEntryDialog.categoriesTreeView = self.categoriesTreeView
		
		self.backOneDayButton = self.wTree.get_widget('backOneDayButton')
		self.forwardOneDayButton = self.wTree.get_widget('forwardOneDayButton')
		
		self.editPane = self.wTree.get_widget('editPane')
		
		self.html_editor = HtmlEditor()
		self.text_vbox = self.wTree.get_widget('text_vbox')
		self.text_vbox.pack_start(self.html_editor)
		self.html_editor.hide()
		self.html_editor.set_editable(False)
		self.preview_mode = False
		self.preview_button = self.wTree.get_widget('previewButton')
		
		
		self.setup_search()
		self.setup_insert_menu()
		
		'Create an event->method dictionary and connect it to the widgets'
		dic = {
			'on_backOneDayButton_clicked': self.on_backOneDayButton_clicked,
			'on_todayButton_clicked': self.on_todayButton_clicked,
			'on_forwardOneDayButton_clicked': self.on_forwardOneDayButton_clicked,
			'on_calendar_day_selected': self.on_calendar_day_selected,
			
			'on_newJournalButton_activate': self.on_newJournalButton_activate,
			'on_openJournalButton_activate': self.on_openJournalButton_activate,
			'on_saveMenuItem_activate': self.on_saveButton_clicked,
			'on_saveAsMenuItem_activate': self.on_saveAsMenuItem_activate,
			
			'on_copyMenuItem_activate': self.on_copyMenuItem_activate,
			'on_pasteMenuItem_activate': self.on_pasteMenuItem_activate,
			'on_cutMenuItem_activate': self.on_cutMenuItem_activate,
			
			'on_previewButton_clicked': self.on_previewButton_clicked,
			'on_checkVersionMenuItem_activate': self.on_checkVersionMenuItem_activate,
			
			'on_mainFrame_configure_event': self.on_mainFrame_configure_event,
			
			'on_exportMenuItem_activate': self.on_exportMenuItem_activate,
			'on_statisticsMenuItem_activate': self.on_statisticsMenuItem_activate,
			
			'on_addNewEntryButton_clicked': self.on_addNewEntryButton_clicked,
			'on_addTagButton_clicked': self.on_addTagButton_clicked,
			'on_deleteEntryButton_clicked': self.on_deleteEntryButton_clicked,
			
			'on_searchNotebook_switch_page': self.on_searchNotebook_switch_page,
			
			'on_templateButton_clicked': self.on_templateButton_clicked,
			'on_templateMenu_show_menu': self.on_templateMenu_show_menu,
			'on_templateMenu_clicked': self.on_templateMenu_clicked,
			
			'on_searchTypeBox_changed': self.on_searchTypeBox_changed,
			'on_cloudComboBox_changed': self.on_cloudComboBox_changed,
			'on_info_activate': self.on_info_activate,
			'on_helpMenuItem_activate': self.on_helpMenuItem_activate,
			'on_backup_activate': self.on_backup_activate,
			'on_quit_activate': self.on_quit_activate,
			'on_mainFrame_destroy': self.on_mainFrame_destroy,
			 }
		self.wTree.signal_autoconnect(dic)
		
		
		self.setup_clouds()
		self.set_shortcuts()
		
		self.template_manager = templates.TemplateManager(self)
		self.template_manager.make_empty_template_files()
		self.setup_template_menu()
		
		
		
		
	def set_shortcuts(self):
		'''
		This method actually is not responsible for the Ctrl-C etc. actions
		'''
		self.accel_group = gtk.AccelGroup()
		self.mainFrame.add_accel_group(self.accel_group)
		#for key, signal in [('C', 'copy_clipboard'), ('V', 'paste_clipboard'), \
		#					('X', 'cut_clipboard')]:
		#	self.dayTextField.dayTextView.add_accelerator(signal, self.accel_group,
		#					ord(key), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		(page_down_keyval, mod) = gtk.accelerator_parse('<Ctrl>Page_Down')
		self.backOneDayButton.add_accelerator('clicked', self.accel_group, \
							page_down_keyval, mod, gtk.ACCEL_VISIBLE)
		(page_up_keyval, mod) = gtk.accelerator_parse('<Ctrl>Page_Up')
		self.forwardOneDayButton.add_accelerator('clicked', self.accel_group, \
							page_up_keyval, mod, gtk.ACCEL_VISIBLE)
			
			
	def on_previewButton_clicked(self, button):
		self.redNotebook.saveOldDay()
		
		text_scrolledwindow = self.wTree.get_widget('text_scrolledwindow')
		template_button = self.wTree.get_widget('templateMenuButton')
		
		
		if self.preview_mode:
			text_scrolledwindow.show()
			self.html_editor.hide()
			self.preview_button.set_stock_id('gtk-media-play')
			self.preview_button.set_label('Preview')
			
			self.preview_mode = False
		else:
			text_scrolledwindow.hide()
			self.html_editor.show()
			day = self.redNotebook.day
			text_markup = day.text
			html = markup.convert(text_markup, 'xhtml')
			
			self.html_editor.load_html(html)
			
			self.preview_button.set_stock_id('gtk-edit')
			self.preview_button.set_label('   Edit   ')
		
			self.preview_mode = True
			
		template_button.set_sensitive(not self.preview_mode)
		self.single_menu_toolbutton.set_sensitive(not self.preview_mode)
			
		
			
	def setup_search(self):
		self.searchNotebook = self.wTree.get_widget('searchNotebook')
		
		self.searchTreeView = SearchTreeView(self.wTree.get_widget(\
									'searchTreeView'), self)
		self.searchTypeBox = self.wTree.get_widget('searchTypeBox')
		self.searchTypeBox.set_active(0)
		self.searchBox = SearchComboBox(self.wTree.get_widget('searchBox'), \
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
		self.cloudBox = self.wTree.get_widget('cloudBox')
		
		self.cloud = CloudView(self.redNotebook)
		self.cloudBox.pack_start(self.cloud)
		
		self.cloudComboBox = self.wTree.get_widget('cloudComboBox')
		self.cloudComboBox.set_active(0)
		
		
	def on_cloudComboBox_changed(self, cloudComboBox):
		value_int = cloudComboBox.get_active()
		self.cloud.set_type(value_int)
					
							
	def on_copyMenuItem_activate(self, widget):
		self.dayTextField.dayTextView.emit('copy_clipboard')
		
	def on_pasteMenuItem_activate(self, widget):
		self.dayTextField.dayTextView.emit('paste_clipboard')
		
	def on_cutMenuItem_activate(self, widget):
#		event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
#		event.keyval = ord("X")
#		event.state = gtk.gdk.CONTROL_MASK
#		self.mainFrame.emit("key_press_event",event)
		self.dayTextField.dayTextView.emit('cut_clipboard')
		
	def on_mainFrame_configure_event(self, widget, event):
		'''
		Is called when the frame size is changed. Unfortunately this is
		the way to go as asking for frame.get_size() at program termination
		gives strange results.		
		'''
		mainFrameWidth, mainFrameHeight = self.mainFrame.get_size()
		# print 'SIZE GET', mainFrameWidth, mainFrameHeight
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
		self.redNotebook.changeDate(self.calendar.get_date())
		
	def show_dir_chooser(self, type, dir_not_found=False):
		dir_chooser = self.wTree.get_widget('dir_chooser')
		label = self.wTree.get_widget('dir_chooser_label')
		
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
			
		
	def on_newJournalButton_activate(self, widget):
		self.show_dir_chooser('new')
		
	def on_openJournalButton_activate(self, widget):
		self.show_dir_chooser('open')
		
	def on_saveButton_clicked(self, widget):
		self.redNotebook.saveToDisk()
		
	def on_saveAsMenuItem_activate(self, widget):
		self.redNotebook.saveToDisk()
		
		self.show_dir_chooser('saveas')
		
		
	def on_mainFrame_destroy(self, widget):
		self.redNotebook.exit()
		
	def on_backup_activate(self, widget):
		self.redNotebook.backupContents(backup_file=self.get_backup_file())
		
	def add_values_to_config(self):
		config = self.redNotebook.config
		config['leftDividerPosition'] = \
				self.wTree.get_widget('mainPane').get_position()
		config['rightDividerPosition'] = \
				self.wTree.get_widget('editPane').get_position()
		config.write_list('cloudIgnoreList', self.cloud.ignore_list)
		
	
	def load_values_from_config(self):
		config = self.redNotebook.config
		mainFrameWidth = config.read('mainFrameWidth', 1024)
		mainFrameHeight = config.read('mainFrameHeight', 768)
		#print 'SIZE', mainFrameWidth, mainFrameHeight
		#self.mainFrame.show()
		
		screen_width = gtk.gdk.screen_width()
		screen_height = gtk.gdk.screen_height()
		
		mainFrameWidth = min(mainFrameWidth, screen_width)
		mainFrameHeight = min(mainFrameHeight, screen_height)
		
		self.mainFrame.resize(mainFrameWidth, mainFrameHeight)
		
		#self.mainFrame.maximize()
		
		if config.has_key('leftDividerPosition'):
			self.wTree.get_widget('mainPane').set_position(config.read('leftDividerPosition', -1))	
		self.wTree.get_widget('editPane').set_position(config.read('rightDividerPosition', 500))
		
		
	def setup_template_menu(self):
		self.template_menu_button = self.wTree.get_widget('templateMenuButton')
		self.template_menu_button.set_menu(gtk.Menu())
		self.template_menu_button.set_menu(self.template_manager.get_menu())
				
	
	def on_templateMenu_show_menu(self, widget):
		self.template_menu_button.set_menu(self.template_manager.get_menu())
		
	def on_templateMenu_clicked(self, widget):
		text = self.template_manager.get_weekday_text()
		self.dayTextField.insert_template(text)
		
	def on_templateButton_clicked(self, widget):
		text = self.template_manager.get_weekday_text()
		self.dayTextField.insert_template(text)
		
		
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
			<!-- <menuitem action="Table"/> -->
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
		
		default_date_string = '%A, %x %X'
		date_string = self.redNotebook.config.read('dateTimeString', default_date_string)
		
		table = '''
||   1st Heading   |   2nd Heading	|   3rd Heading	|
|	right aligned |	 centered	 | left aligned	 |
|		   Having |	  tables	  | is			   |
|			   so |	 awesome!	 |				  |
'''

		def tmpl(letter):
			return ' (Ctrl+%s)' % letter
		
		# Create actions
		actiongroup.add_actions([
			('Picture', gtk.STOCK_ORIENTATION_PORTRAIT, \
				'_Picture' + tmpl('P'), \
				'<Control>P', 'Insert a picture at the current position', \
				self.on_insert_pic_menu_item_activate),
			('File', gtk.STOCK_FILE, '_File' + tmpl('F'), '<Control>F', \
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
				lambda widget: self.dayTextField.insert(datetime.datetime.now().strftime(date_string))),
			])

		# Add the actiongroup to the uimanager
		uimanager.insert_action_group(actiongroup, 0)

		# Add a UI description
		uimanager.add_ui_from_string(insert_menu_xml)

		# Create a Menu
		menu = uimanager.get_widget('/InsertMenu')
		
		image_items = 'Picture Link BulletList Title Line Date'.split()
		image_file_names = 'picture-16 link bulletlist title line date'.split()
		items_and_files = zip(image_items, image_file_names)
		
		for item, file_name in items_and_files:
			menu_item = uimanager.get_widget('/InsertMenu/'+ item)
			menu_item.set_image(get_image(file_name + '.png'))
		
		#single_menu_toolbutton = SingleMenuToolButton(menu, 'Insert ')
		self.single_menu_toolbutton = gtk.MenuToolButton(get_image('insert-image-22.png'), 'Insert')
		self.single_menu_toolbutton.set_menu(menu)
		self.single_menu_toolbutton.connect('clicked', self.show_insert_menu)
		edit_toolbar = self.wTree.get_widget('edit_toolbar')
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
		xml = gtk.glade.XML(self.gladefile, 'picture_chooser')
		picture_chooser = xml.get_widget('picture_chooser')
		picture_chooser.set_current_folder(filesystem.last_pic_dir)
		
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
			filesystem.last_pic_dir = picture_chooser.get_current_folder()
			base, ext = os.path.splitext(picture_chooser.get_filename())
			self.dayTextField.insert('[""' + base + '""' + ext + ']')
			
	def on_insert_file_menu_item_activate(self, widget):
		xml = gtk.glade.XML(self.gladefile, 'file_chooser')
		file_chooser = xml.get_widget('file_chooser')
		file_chooser.set_current_folder(filesystem.last_file_dir)

		response = file_chooser.run()
		file_chooser.hide()
		
		if response == gtk.RESPONSE_OK:
			filesystem.last_file_dir = file_chooser.get_current_folder()
			filename = file_chooser.get_filename()
			head, tail = os.path.split(filename)
			if ' ' in filename:
				self.dayTextField.insert('[' + tail + ' ""' + filename + '""]')
			else:
				self.dayTextField.insert('[' + tail + ' ' + filename + ']')
			
	def on_insert_link_menu_item_activate(self, widget):
		xml = gtk.glade.XML(self.gladefile, 'link_creator')
		link_creator = xml.get_widget('link_creator')
		link_location_entry = xml.get_widget('link_location_entry')
		link_name_entry = xml.get_widget('link_name_entry')
		
		link_location_entry.set_text('http://')
		link_name_entry.set_text('')

		response = link_creator.run()
		link_creator.hide()
		
		if response == gtk.RESPONSE_OK:
			link_location = xml.get_widget('link_location_entry').get_text()
			link_name = xml.get_widget('link_name_entry').get_text()
			
			if link_location and link_name:
				self.dayTextField.insert('[' + link_name + ' ""' + link_location + '""]')
			elif link_location:
				self.dayTextField.insert(link_location)
			else:
				self.redNotebook.showMessage('No link location has been entered', error=True)		
		
	def on_quit_activate(self, widget):
		self.on_mainFrame_destroy(None)
		
	def on_info_activate(self, widget):
		self.infoDialog = self.wTree.get_widget('aboutDialog')
		self.infoDialog.set_name('RedNotebook')
		self.infoDialog.set_version(info.version)
		self.infoDialog.set_copyright('Copyright (c) 2008 Jendrik Seipp')
		self.infoDialog.set_comments('A Desktop Diary')
		gtk.about_dialog_set_url_hook(lambda dialog, url: webbrowser.open(url))
		self.infoDialog.set_website(info.url)
		self.infoDialog.set_website_label(info.url)
		self.infoDialog.set_authors(info.developers)
		self.infoDialog.set_logo(gtk.gdk.pixbuf_new_from_file(\
					os.path.join(filesystem.imageDir,'redNotebookIcon/rn-128.png')))
		self.infoDialog.set_license(info.licenseText)
		self.infoDialog.run()
		self.infoDialog.hide()
		
	def on_exportMenuItem_activate(self, widget):
		self.redNotebook.saveOldDay()
		assistant = ExportAssistant.get_instance(self)
		assistant.run()
		
	def on_statisticsMenuItem_activate(self, widget):
		utils.show_html_in_browser(self.redNotebook.stats.getStatsHTML())
		
	def on_addNewEntryButton_clicked(self, widget):
		self.newEntryDialog.show_dialog(adding_tag=False)
		
	def on_addTagButton_clicked(self, widget):
		self.newEntryDialog.show_dialog(adding_tag=True)
		
	def on_deleteEntryButton_clicked(self, widget):
		self.categoriesTreeView.delete_selected_node()
		
	def on_helpMenuItem_activate(self, widget):
		utils.write_file(info.helpText, './source.txt')
		headers = ['RedNotebook Documentation', info.version, '']
		options = {'toc': 1,}
		html = markup.convert(info.helpText, 'xhtml', headers, options)
		utils.show_html_in_browser(html)
		
	def on_checkVersionMenuItem_activate(self, widget):
		utils.check_new_version(self, info.version)
		
		
	def set_date(self, newMonth, newDate, day):
		self.categoriesTreeView.clear()
		self.calendar.setMonth(newMonth)
		
		self.calendar.set_date(newDate)
		self.dayTextField.set_text(day.text)
		self.html_editor.load_html(markup.convert(day.text, 'xhtml'))
		self.categoriesTreeView.set_day_content(day)
		
		self.day = day
		
	def get_day_text(self):
		return self.dayTextField.get_text()
	
	def get_backup_file(self):
		if self.redNotebook.title == 'data':
			name = ''
		else:
			name = '-' + self.redNotebook.title
			
		proposedFileName = 'RedNotebook-Backup%s_%s.zip' % (name, datetime.date.today())
			
		xml = gtk.glade.XML(self.gladefile, 'backupDialog')
		backupDialog = xml.get_widget('backupDialog')
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
		newVersionDialog = self.wTree.get_widget('newVersionDialog')
		response = newVersionDialog.run()
		newVersionDialog.hide()
		
		if response == gtk.RESPONSE_OK:
			webbrowser.open(info.url)
		elif response == 20:
			#do not ask again
			self.redNotebook.config['checkForNewVersion'] = 0
			
	def show_no_new_version_dialog(self):
		dialog = self.wTree.get_widget('noNewVersionDialog')
		response = dialog.run()
		dialog.hide()
		
		if response == 30:
			#Ask at startup
			self.redNotebook.config['checkForNewVersion'] = 1
			

class NewEntryDialog(object):
	def __init__(self, mainFrame):
		dialog = mainFrame.wTree.get_widget('newEntryDialog')
		self.dialog = dialog
		
		self.mainFrame = mainFrame
		self.redNotebook = self.mainFrame.redNotebook
		self.categoriesComboBox = CustomComboBox(mainFrame.wTree.get_widget('categoriesComboBox'))
		self.newEntryComboBox = CustomComboBox(mainFrame.wTree.get_widget('entryComboBox'))
		
		# Allow hitting enter to submit the entry #TODO: Fix
		#print self.dialog.flags()
		#self.dialog.set_flags(gtk.CAN_DEFAULT)
		#self.dialog.set_flags(gtk.HAS_DEFAULT)
		#self.dialog.set_default_response(gtk.RESPONSE_OK)
		self.newEntryComboBox.entry.set_activates_default(True)
		
		#self.categoriesTreeView = self.mainFrame.categoriesTreeView
		
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
		return len(self.categoriesComboBox.get_active_text()) > 0 and \
				len(self.newEntryComboBox.get_active_text()) > 0
		
	def show_dialog(self, category=None, adding_tag=False):
		# Show the list of categories even if adding a tag
		self.categoriesComboBox.set_entries(self.categoriesTreeView.categories)
		
		if category:
			self.categoriesComboBox.set_active_text(category)
			if category.capitalize() == 'Tags':
				adding_tag = True
		
		if adding_tag:
			self.categoriesComboBox.set_active_text('Tags')
			self.newEntryComboBox.set_entries(self.redNotebook.tags)
			self.dialog.set_focus(self.newEntryComboBox.comboBox)
		else:
			self.newEntryComboBox.clear()
			self.dialog.set_focus(self.categoriesComboBox.comboBox)
		
		response = self.dialog.run()
		self.dialog.hide()
		
		if response != gtk.RESPONSE_OK:
			return
		
		categoryName = self.categoriesComboBox.get_active_text()
		if not self.categoriesTreeView.check_category(categoryName):
			return
		
		entryText = self.newEntryComboBox.get_active_text()
		if not self.categoriesTreeView.check_entry(entryText):
			return
		
		self.categoriesTreeView.addEntry(categoryName, entryText)
		self.categoriesTreeView.treeView.expand_all()
		
		# Update cloud
		self.mainFrame.cloud.update()
		
			
			
			
class CustomComboBox:
	def __init__(self, comboBox):
		self.comboBox = comboBox
		self.liststore = self.comboBox.get_model()
		#self.comboBox.set_wrap_width(5)
		self.entry = self.comboBox.get_child()
		
	def add_entry(self, entry):
		self.liststore.append([entry])
	
	def set_entries(self, value_list):
		self.clear()
		for entry in value_list:
			self.add_entry(entry)
		
		if len(value_list) > 0:
			self.comboBox.set_active(0)
	
	def _get_active_text(self):
		model = self.comboBox.get_model()
		index = self.comboBox.get_active()
		if index > -1:
			return model[index][0]
		else:
			return ''
		
	def get_active_text(self):
		return self.entry.get_text()
	
	def set_active_text(self, text):
		return self.entry.set_text(text)
	
	def clear(self):
		if self.liststore:
			self.liststore.clear()
		self.set_active_text('')
	
	def connect(self, *args, **kargs):
		self.comboBox.connect(*args, **kargs)
	
	
class SearchComboBox(CustomComboBox):
	def __init__(self, comboBox, mainWindow):
		CustomComboBox.__init__(self, comboBox)
		
		self.mainWindow = mainWindow
		self.redNotebook = mainWindow.redNotebook
		
		self.entry = self.comboBox.get_child()
		self.entry.set_text('Search ...')

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
		self.search(entry.get_text())
		
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
			
		self.search(searchText)
			
	def search(self, searchText):
		self.mainWindow.searchTreeView.update_data(searchText)
		
	def clear(self):
		self.entry.set_text('')
		
		
		
class CloudView(HtmlWindow):
	def __init__(self, redNotebook):
		HtmlWindow.__init__(self)
		
		self.redNotebook = redNotebook
		
		default_ignore_list = 'filter, these, comma, separated, words'
		self.ignore_list = self.redNotebook.config.read_list('cloudIgnoreList', \
															default_ignore_list)
		self.ignore_list = map(lambda word: word.lower(), self.ignore_list)
		logging.info('Cloud ignore list: %s' % self.ignore_list)
		
		self.htmlview.connect("url-clicked", self.word_clicked)
		self.htmlview.connect('populate-popup', self.create_popup_menu)
		
		self.set_type(0, init=True)
		
	def set_type(self, type_int, init=False):
		self.type_int = type_int
		self.type = ['word', 'category', 'tag'][type_int]
		if not init:
			self.update(force_update=True)
		
	def update(self, force_update=False):
		# Do not update the cloud with words as it requires a lot of searching		
		if self.type == 'word' and not force_update:
			return
		
		if self.redNotebook.frame is not None:
			self.redNotebook.saveOldDay()
		wordCountDict = self.redNotebook.getWordCountDict(self.type)
		self.tagCloudWords, html = utils.getHtmlDocFromWordCountDict(wordCountDict, \
												self.type, self.ignore_list)
		self.write(html)
		
	def word_clicked(self, htmlview, uri, type_):
		'uri has the form "something/somewhere/search/searchIndex"'
		if 'search' in uri:
			'searchIndex is the part after last slash'
			searchIndex = int(uri.split('/')[-1])
			searchText = self.tagCloudWords[searchIndex]
			
			self.redNotebook.frame.searchTypeBox.set_active(self.type_int)
			self.redNotebook.frame.searchBox.set_active_text(searchText)
			self.redNotebook.frame.searchNotebook.set_current_page(0)
			
			'returning True here stops loading the document'
			return True
		
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
		
	def on_ignore_menu_activate(self, menu_item):
		selected_words = self.get_selected_words()
		logging.info('The following words will be hidden from clouds: %s' % selected_words)
		self.ignore_list.extend(selected_words)
		self.update()
		
	def get_selected_words(self):
		bounds = self.htmlview.get_buffer().get_selection_bounds()
		if not bounds:
			return []
		
		text = self.htmlview.get_buffer().get_text(*bounds)
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
		for column in range(len(columns)):
			self.treeView.append_column(columns[column])

			'create a CellRendererText to render the data'
			cellRenderer = gtk.CellRendererText()

			'add the cell to the tvcolumn and allow it to expand'
			columns[column].pack_start(cellRenderer, True)

			'Get markup for column, not text'
			columns[column].set_attributes(cellRenderer, markup=column)
			
			'Allow sorting on the column'
			columns[column].set_sort_column_id(column)
		
		self.update_data()

		'make it searchable'
		self.treeView.set_search_column(1)
		
		self.treeView.connect('row_activated', self.on_row_activated)
		
		
	def update_data(self, searchText=''):
		self.treeStore.clear()
		
		rows = None
		
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
			for dateString, resultString in rows:
				self.treeStore.append([dateString, resultString])
				
				
	def on_row_activated(self, treeview, path, view_column):
		dateString = self.treeStore[path][0]
		newDate = dates.get_date_from_date_string(dateString)
		self.redNotebook.changeDate(newDate)
		
		
	def set_search_type(self, searchType):		
		self.searchType = searchType
		
	

class CategoriesTreeView(object):
	def __init__(self, treeView, mainWindow):
		self.treeView = treeView
		
		self.mainWindow = mainWindow
		
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

		'add the cell to the tvcolumn and allow it to expand'
		self.tvcolumn.pack_start(self.cell, True)

		''' set the cell "text" attribute to column 0 - retrieve text
			from that column in treeStore'''
		self.tvcolumn.add_attribute(self.cell, 'text', 0)

		'make it searchable'
		self.treeView.set_search_column(0)

		'Allow sorting on the column'
		self.tvcolumn.set_sort_column_id(0)
		
		# Enable a context menu
		self.context_menu = self._get_context_menu()
		self.treeView.connect('button-press-event', self.on_button_press_event)

		
	def node_on_top_level(self, iter):
		if not type(iter) == gtk.TreeIter:
			# iter is a path -> convert to iter
			iter = self.treeStore.get_iter(iter)
		return self.treeStore.iter_depth(iter) == 0
		
		
	def edited_cb(self, cell, path, new_text, user_data):
		'''Called when text in a cell is changed'''
		if new_text == 'text' and self.node_on_top_level(path):
			self.statusbar.showText('"text" is a reserved keyword', error=True)
			return
		if len(new_text) < 1:
			self.statusbar.showText('Empty nodes are not allowed', error=True)
			return
		
		liststore = user_data
		liststore[path][0] = new_text
		
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
			newChild = self.treeStore.append(parent, [key])
			if not value == None:
				self.add_element(newChild, value)
			
		
	def set_day_content(self, day):
		for key, value in day.content.iteritems():
			if not key == 'text':
				self.add_element(None, {key: value})
		self.treeView.expand_all()
				
				
	def get_day_content(self):
		if not self.empty():
			return self.get_element_content(None)
		else:
			return {}
		   
		   
	def get_element_content(self, element):
		model = self.treeStore
		if self.treeStore.iter_n_children(element) == 0:
			return None
		else:
			content = {}
				
			for i in range(model.iter_n_children(element)):
				child = model.iter_nth_child(element, i)
				text = self.get_iter_value(child)
				content[text] = self.get_element_content(child)
			
			return content
		
		
	def empty(self):
		return self.treeStore.iter_n_children(None) == 0
		
		
	def clear(self):
		self.treeStore.clear()
		assert self.empty(), self.treeStore.iter_n_children(None)
		
		
	def get_iter_value(self, iter):
		return self.treeStore.get_value(iter, 0)
		
		
	def _get_category_iter(self, categoryName):
		#print 'Number of Categories:', self.treeStore.iter_n_children(None)
		for iterIndex in range(self.treeStore.iter_n_children(None)):
			currentCategoryIter = self.treeStore.iter_nth_child(None, iterIndex)
			currentCategoryName = self.get_iter_value(currentCategoryIter)
			if currentCategoryName.lower() == categoryName.lower():
				return currentCategoryIter
		
		'If the category was not found, return None'
		return None
	
	
	def addEntry(self, categoryName, text):
		if categoryName not in self.categories and categoryName is not None:
			self.categories.insert(0, categoryName)
			
		categoryIter = self._get_category_iter(categoryName)
		if categoryIter is None:
			'If category does not exist add new category'
			categoryIter = self.treeStore.append(None, [categoryName])
			self.treeStore.append(categoryIter, [text])
		else:
			'If category exists add entry to existing category'
			self.treeStore.append(categoryIter, [text])
			
	
	def get_selected_node(self):
		'''
		Returns selected node or None if none is selected
		'''
		treeSelection = self.treeView.get_selection()
		model, selectedIter = treeSelection.get_selected()
		return selectedIter
		
		
	def delete_selected_node(self):
		selectedIter = self.get_selected_node()
		if selectedIter:
			message = 'Do you really want to delete this node?'
			sortOptimalDialog = gtk.MessageDialog(parent=self.mainWindow.mainFrame, \
									flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_QUESTION, \
									buttons=gtk.BUTTONS_YES_NO, message_format=message)
			response = sortOptimalDialog.run()
			sortOptimalDialog.hide()
			
			if response == gtk.RESPONSE_YES:
				self.treeStore.remove(selectedIter)
				
				# Update cloud
				self.mainWindow.cloud.update()
				
				
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
		selection = self.treeView.get_selection()
		model, iter = selection.get_selected()
		
		self.treeView.set_cursor(self.treeStore.get_path(iter), \
								focus_column=self.tvcolumn, start_editing=True)
		self.treeView.grab_focus()
	
	def _on_add_entry_clicked(self, action):
		
		selection = self.treeView.get_selection()
		model, iter = selection.get_selected()
		
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
		
	
		
		
class DayTextField(object):
	def __init__(self, dayTextView):
		self.dayTextView = dayTextView
		self.dayTextBuffer = gtk.TextBuffer()
		self.dayTextView.set_buffer(self.dayTextBuffer)
		
	def wxinit(self, *args, **kwargs):
		
		self.history = []
		self.historyPosition = -1
		
	def set_text(self, text):
		#self.redoButton.Enable(False)
		#self.undoButton.Enable(False)
		#self.history = []
		#self.historyPosition = -1
		self.dayTextBuffer.set_text(text)
		
	def get_text(self):
		iterStart = self.dayTextBuffer.get_start_iter()
		iterEnd = self.dayTextBuffer.get_end_iter()
		return self.dayTextBuffer.get_text(iterStart, iterEnd)
	
	def insert(self, text):
		self.dayTextBuffer.insert_at_cursor(text)
	
	def insert_template(self, template):
		currentText = self.get_text()
		try:
			self.set_text(template.encode('utf-8') + '\n' + \
						currentText.encode('utf-8'))
		except UnicodeDecodeError, err:
			logging.error('Template file contains unreadable content. Is it really just ' \
			'a text file?')
		
	def hide(self):
		self.dayTextView.hide()
		
	#TODO: implement UNDO/REDO
		
	def onTextChange(self, event):

		'''Delete the history after the current historyPosition'''
		del self.history[self.historyPosition + 1:]
		
		'''Disable the undo button'''
		self.redoButton.Enable(False)
		
		currentText = self.textField.GetValue()
		
		'''Only log the bigger changes'''
		#print 'X:', currentText, self.history[self.historyPosition]
		if self.historyPosition == -1 or abs(len(currentText) - len(self.history[self.historyPosition])) >= 5:
		
			self.history.append(currentText)
			self.historyPosition = len(self.history) - 1
			#print self.history, self.historyPosition
			
			'''Enable the undo button'''
			if self.historyPosition > 0:
				self.undoButton.Enable(True)
		
		
		
	def onUndo(self, event):
		
		if self.historyPosition == 0:
			return
		
		self.historyPosition -= 1
		previousText = self.history[self.historyPosition]
		self.textField.ChangeValue(previousText)
		
		if self.historyPosition == 0:
			self.undoButton.Enable(False)
			
		self.redoButton.Enable(True)
	

	def onRedo(self, event):
		
		if self.historyPosition == len(self.history) - 1:
			return
		
		self.historyPosition += 1
		redoText = self.history[self.historyPosition]
		self.textField.ChangeValue(redoText)
		
		if self.historyPosition == len(self.history) - 1:
			self.redoButton.Enable(False)
			
		self.undoButton.Enable(True)
		
		
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
	def __init__(self, calendar):
		self.calendar = calendar
		
	def set_date(self, date):
		if date == self.get_date():
			return
		'PyGTK calendars show months in range [0,11]'
		self.calendar.select_month(date.month-1, date.year)
		self.calendar.select_day(date.day)
		
	def get_date(self):
		year, month, day = self.calendar.get_date()
		return datetime.date(year, month+1, day)
		
	def setDayEdited(self, dayNumber, edited):
		if edited:
			self.calendar.mark_day(dayNumber)
		else:
			self.calendar.unmark_day(dayNumber)
			
	def setMonth(self, month):
		for dayNumber in range(1, 31 + 1):
			self.setDayEdited(dayNumber, False)
		for dayNumber, day in month.days.iteritems():
			self.setDayEdited(dayNumber, not day.empty)
			
			
def get_image(name):
	image = gtk.Image()
	file_name = os.path.join(filesystem.imageDir, name)
	image.set_from_file(file_name)
	return image
