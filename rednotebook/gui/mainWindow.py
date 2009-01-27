#!/usr/bin/env python
from __future__ import with_statement
import sys
import os
import datetime
import urllib
import urlparse
import webbrowser

import pygtk
pygtk.require("2.0")
import gtk
import gobject
import gtk.glade

'Initialize the gtk thread engine'
#gtk.gdk.threads_init()

from rednotebook.util import utils

try:
	import gtkhtml2
except ImportError:
	utils.printError('gtkhtml2 is not installed (install python-gtkhtml2)')
	sys.exit(1)

try:
	import gtkmozembed
except ImportError:
	utils.printError('gtkmozembed is not installed (install python-gnome2-extras)')
	sys.exit(1)


from rednotebook.util import filesystem
from rednotebook import info
from rednotebook.util import markup
from rednotebook.util import dates

print sys.path

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
		
		self.calendar = Calendar(self.wTree.get_widget('calendar'))
		self.dayTextField = DayTextField(self.wTree.get_widget('dayTextView'))
		self.statusbar = Statusbar(self.wTree.get_widget('statusbar'))
		
		self.categoriesTreeView = CategoriesTreeView(self.wTree.get_widget(\
									'categoriesTreeView'), self)
		
		self.setup_search()
		
		#self.previewScrolledWindow = self.wTree.get_widget('previewScrolledWindow')
		#self.preview = Preview(self.previewScrolledWindow)
		self.preview = MozillaView(self.wTree.get_widget('previewBox'))
								
		self.set_shortcuts()
		
		'Create an event->method dictionary and connect it to the widgets'
		dic = {
			'on_backOneDayButton_clicked': self.on_backOneDayButton_clicked,
			'on_todayButton_clicked': self.on_todayButton_clicked,
			'on_forwardOneDayButton_clicked': self.on_forwardOneDayButton_clicked,
			'on_calendar_day_selected': self.on_calendar_day_selected,
			'on_saveButton_clicked': self.on_saveButton_clicked,
			'on_saveMenuItem_activate': self.on_saveButton_clicked,
			
			'on_copyMenuItem_activate': self.on_copyMenuItem_activate,
			'on_pasteMenuItem_activate': self.on_pasteMenuItem_activate,
			'on_cutMenuItem_activate': self.on_cutMenuItem_activate,
			
			'on_exportMenuItem_activate': self.on_exportMenuItem_activate,
			'on_statisticsMenuItem_activate': self.on_statisticsMenuItem_activate,
			'on_addNewEntryButton_clicked': self.on_addNewEntryButton_clicked,
			'on_deleteEntryButton_clicked': self.on_deleteEntryButton_clicked,
			'on_dayNotebook_switch_page': self.on_dayNotebook_switch_page,
			'on_searchNotebook_switch_page': self.on_searchNotebook_switch_page,
			'on_templateButton_clicked': self.on_templateButton_clicked,
			'on_searchTypeBox_changed': self.on_searchTypeBox_changed,
			'on_info_activate': self.on_info_activate,
			'on_helpMenuItem_activate': self.on_helpMenuItem_activate,
			'on_backup_activate': self.on_backup_activate,
			'on_quit_activate': self.on_quit_activate,
			'on_mainFrame_destroy': self.on_mainFrame_destroy,
			 }
		self.wTree.signal_autoconnect(dic)
		
		
	def set_shortcuts(self):
		self.accel_group = gtk.AccelGroup()
		self.mainFrame.add_accel_group(self.accel_group)
		for key, signal in [('C', 'copy_clipboard'), ('V', 'paste_clipboard'), \
							('X', 'cut_clipboard')]:
			self.dayTextField.dayTextView.add_accelerator(signal, self.accel_group,
							ord(key), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
			
			
	def setup_search(self):
		self.searchTreeView = SearchTreeView(self.wTree.get_widget(\
									'searchTreeView'), self)
		self.searchTypeBox = self.wTree.get_widget('searchTypeBox')
		self.searchTypeBox.set_active(0)
		self.searchBox = SearchComboBox(self.wTree.get_widget('searchBox'), \
									self)
		
		
	def on_searchTypeBox_changed(self, widget):
		searchType = widget.get_active()
		self.searchBox.set_search_type(searchType)
		
		
							
							
	def on_copyMenuItem_activate(self, widget):
		self.dayTextField.dayTextView.emit('copy_clipboard')
		
	def on_pasteMenuItem_activate(self, widget):
		self.dayTextField.dayTextView.emit('paste_clipboard')
		
	def on_cutMenuItem_activate(self, widget):
		self.dayTextField.dayTextView.emit('cut_clipboard')
		
		
	def on_backOneDayButton_clicked(self, widget):
		self.redNotebook.goToPrevDay()
		
	def on_todayButton_clicked(self, widget):
		actualDate = datetime.date.today()
		self.redNotebook.changeDate(actualDate)
		
	def on_forwardOneDayButton_clicked(self, widget):
		self.redNotebook.goToNextDay()
		
	def on_calendar_day_selected(self, widget):
		self.redNotebook.changeDate(self.calendar.get_date())
		
	def on_saveButton_clicked(self, widget):
		self.redNotebook.saveToDisk()
		
	def on_mainFrame_destroy(self, widget):
		self.redNotebook.saveToDisk()
		#self.redNotebook.saveConfig()
		gtk.main_quit()
		
	def on_backup_activate(self, widget):
		self.redNotebook.backupContents()
		
	def on_templateButton_clicked(self, widget):
		self.dayTextField.insert_template(self.redNotebook.getTemplateEntry())
		
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
		assistant = ExportAssistant (self)
		
	def on_statisticsMenuItem_activate(self, widget):
		
		statisticsScrolledWindow = self.wTree.get_widget('statisticsScrolledWindow')
		self.statsHTMLView = HTMLView()
		for child in statisticsScrolledWindow.get_children():
			statisticsScrolledWindow.remove(child)
			
		self.statsHTMLView.write(self.redNotebook.stats.getStatsHTML())
		statisticsScrolledWindow.add(self.statsHTMLView)
		
		statisticsDialog = self.wTree.get_widget('statisticsDialog')
		statisticsDialog.set_default_size(350, 200)
		statisticsDialog.run()
		statisticsDialog.hide()
		
	def on_addNewEntryButton_clicked(self, widget):
		self.newEntryDialog = self.wTree.get_widget('newEntryDialog')
		self.categoriesComboBox = CustomComboBox(self.wTree.get_widget('categoriesComboBox'))
		self.newEntryTextBox = self.wTree.get_widget('newEntryTextBox')
		self.newEntryTextBox.set_text('')
		
		self.categoriesComboBox.set_entries(self.categoriesTreeView.categories)
		
		response = self.newEntryDialog.run()
		self.newEntryDialog.hide()
		
		if response != gtk.RESPONSE_OK:
			return
		
		categoryName = self.categoriesComboBox.get_active_text()
		if not self.categoriesTreeView.check_category(categoryName):
			return
		
		entryText = self.newEntryTextBox.get_text()
		if not self.categoriesTreeView.check_entry(entryText):
			return
		
		self.categoriesTreeView.addEntry(categoryName, entryText)
		self.categoriesTreeView.treeView.expand_all()
		
	def on_deleteEntryButton_clicked(self, widget):
		self.categoriesTreeView.delete_selected_node()
		
	def on_helpMenuItem_activate(self, widget):
		helpScrolledWindow = self.wTree.get_widget('helpScrolledWindow')
		for child in helpScrolledWindow.get_children():
			helpScrolledWindow.remove(child)
		helpHTMLView = HTMLView()
		helpHTMLView.write(info.htmlHelp)
		helpScrolledWindow.add(helpHTMLView)
		
		helpDialog = self.wTree.get_widget('helpDialog')
		helpDialog.set_default_size(350, 200)
		helpDialog.run()
		helpDialog.hide()
		
		
		
	def set_date(self, newMonth, newDate, day):
		self.categoriesTreeView.clear()
		self.calendar.setMonth(newMonth)
		
		self.calendar.set_date(newDate)
		self.dayTextField.set_text(day.text)
		self.categoriesTreeView.set_day_content(day)
		self.preview.set_day(day)
		
		self.day = day
		
	def get_day_text(self):
		return self.dayTextField.get_text()
	
	def get_backup_file(self):
		proposedFileName = 'RedNotebook-Backup_' + str(datetime.date.today()) + ".zip"
		backupDialog = self.wTree.get_widget('backupDialog')
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
	
	
	def on_dayNotebook_switch_page(self, notebook, page, pageNumber):
		if pageNumber == 1:
			'Switched to preview tab'
			self.redNotebook.saveOldDay()
			#self.day.text = self.get_day_text()
			self.preview.set_day(self.redNotebook.day)
			
	def on_searchNotebook_switch_page(self, notebook, page, pageNumber):
		if pageNumber == 0:
			'Switched to search tab'
			#self.searchTreeView.update_data()
			
			
class CustomComboBox:
	def __init__(self, comboBox):
		self.comboBox = comboBox
		self.liststore = self.comboBox.get_model()
		#self.comboBox.set_wrap_width(5)
		self.entry = self.comboBox.get_child()
		
	def add_entry(self, entry):
		self.liststore.append([entry])
	
	def set_entries(self, value_list):
		self.liststore.clear()
		self.entry.set_text('')
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
		entry = self.comboBox.get_child()
		return entry.get_text()
	
	
	
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
		
		
		
		
class MozillaView(gtkmozembed.MozEmbed):
	def __init__(self, containerBox):
		gtkmozembed.MozEmbed.__init__(self)
		gtkmozembed.set_profile_path("/tmp", "simple_browser_user") # Set a temporary Mozilla profile (works around some bug)
		containerBox.add(self)
		'Attempt to set the size of the browser widget to 600x400 pixels'
		self.set_size_request(600,400) 
		self.show()
	
	def write(self, html):
		#import tempfile
		#with tempfile.NamedTemporaryFile(suffix='.html') as tempFile:
#			tempFile.write("Yeah")
#			print 'TMP', tempFile.readlines()
		with open(os.path.join(filesystem.tempDir, 'tmp.html'), 'w+r') as tempFile:
			tempFile.write(html)
			tempFile.flush()
			#'Move to beginning of file'
			#tempFile.seek(0, 0)
			#print 'TMP', tempFile.readlines()
			#tempFile.close()
			#print str(tempFile.name)
			htmlFile = os.path.abspath(tempFile.name)
			#os.chmod(htmlFile, 0777)
			htmlFile = 'file://' + htmlFile
			#print htmlFile
			
			self.load_url(htmlFile)
			
			
	def set_day(self, day):
		markupText = markup.getMarkupForDay(day, withDate=False)
		html = markup.convertMarkupToTarget(markupText, 'html', title=str(day.date))
		self.write(html)
				
	
class HTMLView(gtkhtml2.View):
	def __init__(self, *args, **kargs):
		gtkhtml2.View.__init__(self, *args, **kargs)
		
		self.opener = urllib.FancyURLopener()
		self.currentURL = None
		
		self.document = gtkhtml2.Document()
		self.document.clear()
		
		#view = gtkhtml2.View()
		self.set_document(self.document)
		self.show()
		
		self.connect('request_object', self.request_object)
		self.document.connect('request_url', self.request_url)
		self.document.connect('link_clicked', self.link_clicked)
		
	def write(self, text):
		self.document.clear()
		self.document.open_stream('text/html')
		self.document.write_stream(text)
		self.document.close_stream()
	
	def is_relative_to_server(self, url):
		parts = urlparse.urlparse(url)
		if parts[0] or parts[1]:
			return 0
		return 1
	
	def open_url(self, url):
		uri = self.resolve_uri(url)
		return self.opener.open(uri)
	
	def resolve_uri(self, uri):
		if self.is_relative_to_server(uri):
			return urlparse.urljoin(self.currentURL, uri)
		return uri
	
	def request_url(self, document, url, stream):
		f = self.open_url(url)
		stream.write(f.read())
	
	def link_clicked(self, document, link):
		print 'link_clicked:', link
		try:
			f = self.open_url(link)
		except OSError:
			print "failed to open", link
			return
		self.currentURL = self.resolve_uri(link)
		self.document.clear()
		headers = f.info()
		mime = headers.getheader('Content-type').split(';')[0]
		print mime
		if mime:
			self.document.open_stream(mime)
		else:
			self.document.open_stream('text/plain')
		self.document.write_stream(f.read())
		self.document.close_stream()
		
	def request_object(self, *args):
		print 'request object', args
		
		 	
	
		

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
		
		'Maintain a list of all entered categories'
		self.categories = self.mainWindow.redNotebook.nodeNames
		
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

		
	def node_on_top_level(self, path):
		return ':' not in path
		
		
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
			if currentCategoryName == categoryName:
				return currentCategoryIter
		
		'If the category was not found, return None'
		return None
	
	
	def addEntry(self, categoryName, text):
		if categoryName not in self.categories and categoryName is not None:
			self.categories.append(categoryName)
			
		categoryIter = self._get_category_iter(categoryName)
		if categoryIter is None:
			'If category does not exist add new category'
			categoryIter = self.treeStore.append(None, [categoryName])
			self.treeStore.append(categoryIter, [text])
		else:
			'If category exists add entry to existing category'
			self.treeStore.append(categoryIter, [text])
		
		
	def delete_selected_node(self):
		treeSelection = self.treeView.get_selection()
		model, selectedIter = treeSelection.get_selected()
		if selectedIter:
			message = 'Do you really want to delete this node?'
			sortOptimalDialog = gtk.MessageDialog(parent=self.mainWindow.mainFrame, \
									flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_QUESTION, \
									buttons=gtk.BUTTONS_YES_NO, message_format=message)
			response = sortOptimalDialog.run()
			sortOptimalDialog.hide()
			
			if response == gtk.RESPONSE_YES:
				model.remove(selectedIter)
		
		
		
class DayTextField(object):
	def __init__(self, dayTextView):
		self.dayTextView = dayTextView
		self.dayTextBuffer = gtk.TextBuffer()
		self.dayTextView.set_buffer(self.dayTextBuffer)
		
		'''First, get an instance of the default display 
		from the globalgtk.gdk.DisplayManager:'''
		#self.display = gtk.gdk.display_manager_get().get_default_display()

		'''Then get a reference to a gtk.Clipboard object, specifying 
		the CLIPBOARD clipboard (and *not* PRIMARY):'''
		#self.clipboard = gtk.Clipboard(self.display, "CLIPBOARD")
		
		'Now your cut/copy/paste callbacks can be written as follows:'
	
	#def on_cut_activate(self, obj):
	#	self.dayTextBuffer.cut_clipboard(self.clipboard, \
	#									self.dayTextView.get_editable())
		
	#def on_copy_activate(self, obj):
	#	pass#self.dayTextBuffer.copy_clipboard(self.clipboard)
		
	#def on_paste_activate(self, obj):
	#	self.dayTextBuffer.paste_clipboard(self.clipboard, None, \
	#									self.dayTextView.get_editable())	
	
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
	
	def insert_template(self, template):
		currentText = self.get_text()
		self.set_text(template.encode('utf-8') + '\n' + \
						currentText.encode('utf-8'))
		
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