#!/usr/bin/env python
from __future__ import with_statement
import os
import datetime
import pygtk
pygtk.require("2.0")
import gtk
import gobject

'Initialize the gtk thread engine'
#gtk.gdk.threads_init()
import gtk.glade

import gnome
import gtkhtml2
#TODO: Is this really needed?
#if os.path.exists('/usr/lib/xulrunner-1.9.0.5'):
#	print 'XUL path changed'
#	gtkmozembed.set_comp_path('/usr/lib/xulrunner-1.9.0.5')
#import gnome.ui

#gnome.init()
#print help(gnome)

from rednotebook.util import filesystem
from rednotebook import info
from rednotebook.gui.htmltextview import HtmlTextView
from rednotebook.util import markup



	


class MainWindow(object):
	'''Class
	'''
	def __init__(self, redNotebook):
		
		self.redNotebook = redNotebook
		
		'Set the Glade file'
		self.gladefile = os.path.join(filesystem.filesDir, 'mainWindow.glade')
		self.wTree = gtk.glade.XML(self.gladefile)
		
			
		'Create an event->method dictionary and connect it to the widgets'
		dic = {
			'on_backOneDayButton_clicked': self.on_backOneDayButton_clicked,
			'on_todayButton_clicked': self.on_todayButton_clicked,
			'on_forwardOneDayButton_clicked': self.on_forwardOneDayButton_clicked,
			'on_calendar_day_selected': self.on_calendar_day_selected,
			'on_saveButton_clicked': self.on_saveButton_clicked,
			'on_saveMenuItem_activate': self.on_saveButton_clicked,
			'on_exportMenuItem_activate': self.on_exportMenuItem_activate,
			'on_statisticsMenuItem_activate': self.on_statisticsMenuItem_activate,
			'on_addNewEntryButton_clicked': self.on_addNewEntryButton_clicked,
			'on_deleteEntryButton_clicked': self.on_deleteEntryButton_clicked,
			'on_dayNotebook_switch_page': self.on_dayNotebook_switch_page,
			'on_info_activate': self.on_info_activate,
			'on_backup_activate': self.on_backup_activate,
			'on_quit_activate': self.on_quit_activate,
			'on_mainFrame_destroy': self.on_mainFrame_destroy,
			 }
		self.wTree.signal_autoconnect(dic)
		
		'Get the main window and set the icon'
		self.mainFrame = self.wTree.get_widget('mainFrame')
		#self.mainFrame.set_icon(gtk.gdk.pixbuf_new_from_file('logo-64.png'))
		
		self.calendar = Calendar(self.wTree.get_widget('calendar'))
		self.dayTextField = DayTextField(self.wTree.get_widget('dayTextView'))
		self.statusbar = Statusbar(self.wTree.get_widget('statusbar'))
		
		print 'Nodes', self.redNotebook.nodeNames
		
		self.categoriesTreeView = CategoriesTreeView(self.wTree.get_widget(\
									'categoriesTreeView'), self)
		
		self.previewScrolledWindow = self.wTree.get_widget('previewScrolledWindow')
		self.preview = Preview(self.previewScrolledWindow)
		
		
	def on_backOneDayButton_clicked(self, widget):
		self.redNotebook.goToPrevDay()
		
	def on_todayButton_clicked(self, widget):
		actualDate = datetime.date.today()
		self.redNotebook.changeDate(actualDate)
		
	def on_forwardOneDayButton_clicked(self, widget):
		self.redNotebook.goToNextDay()
		
	def on_calendar_day_selected(self, widget):
		print 'Date changed', widget
		self.redNotebook.changeDate(self.calendar.get_date())
		
	def on_saveButton_clicked(self, widget):
		self.redNotebook.saveToDisk()
		
	def on_mainFrame_destroy(self, widget):
		self.redNotebook.saveToDisk()
		#self.redNotebook.saveConfig()
		gtk.main_quit()
		
	def on_backup_activate(self, widget):
		self.redNotebook.backupContents()
		
	def on_quit_activate(self, widget):
		self.on_mainFrame_destroy(None)
		
	def on_info_activate(self, widget):
		self.infoDialog = self.wTree.get_widget('aboutDialog')
		self.infoDialog.set_version(info.version)
		self.infoDialog.set_copyright('Copyright (c) 2008 Jendrik Seipp')
		self.infoDialog.set_comments('A Desktop Diary')
		gtk.about_dialog_set_url_hook(lambda dialog, url: gnome.url_show(url))
		self.infoDialog.set_website(info.url)
		self.infoDialog.set_website_label(info.url)
		self.infoDialog.set_authors(info.developers)
		self.infoDialog.set_logo(gtk.gdk.pixbuf_new_from_file(\
					os.path.join(filesystem.imageDir,'redNotebookIcon/rn-128.png')))
		self.infoDialog.set_license(info.licenseText)
		self.infoDialog.run()
		self.infoDialog.hide()
		
	def on_exportMenuItem_activate(self, widget):
		pass
		
	def on_statisticsMenuItem_activate(self, widget):
		
		statisticsScrolledWindow = self.wTree.get_widget('statisticsScrolledWindow')
		statsHTMLView = HTMLView()
		statsHTMLView.write(self.redNotebook.stats.getStatsHTML())
		statisticsScrolledWindow.add(statsHTMLView)
		
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
		#backupDialog.set_current_folder(pathname)
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
			self.day.text = self.get_day_text()
			self.preview.set_day(self.day)
			
			
class CustomComboBox:
	def __init__(self, comboBox):
		self.comboBox = comboBox
		self.liststore = self.comboBox.get_model()
		#self.comboBox.set_wrap_width(5)
	
	def set_entries(self, value_list):
		self.liststore.clear()
		for entry in value_list:
			self.liststore.append([entry])
		self.comboBox.set_active(0)
	
	def get_active_text(self):
		model = self.comboBox.get_model()
		index = self.comboBox.get_active()
		if index > -1:
			return model[index][0]
		else:
			return ''
		

	
class HTMLView(gtkhtml2.View):
	def __init__(self, *args, **kargs):
		gtkhtml2.View.__init__(self, *args, **kargs)
		self.document = gtkhtml2.Document()
		self.document.clear()
		
		#view = gtkhtml2.View()
		self.set_document(self.document)
		self.show()
		
	def write(self, text):
		self.document.clear()
		self.document.open_stream('text/html')
		self.document.write_stream(text)
		self.document.close_stream()
		
		
	

class Preview(object):
	def __init__(self, previewScrolledWindow):
		self.previewScrolledWindow = previewScrolledWindow
		self.htmlView = HTMLView()
		self.previewScrolledWindow.add(self.htmlView)
		
	def set_day(self, day):
		markupText = markup.getMarkupForDay(day, withDate=False)
		html = markup.convertMarkupToTarget(markupText, 'html', title=str(day.date))
		#print html
		self.htmlView.write(html)
		
	
		
	

class CategoriesTreeView(object):
	def __init__(self, treeView, mainWindow):
		self.treeView = treeView
		
		self.mainWindow = mainWindow
		
		'Maintain a list of all entered categories'
		self.categories = self.mainWindow.redNotebook.nodeNames
		
		self.statusbar = self.mainWindow.statusbar
		
		# create a TreeStore with one string column to use as the model
		self.treeStore = gtk.TreeStore(str)

		# create the TreeView using treeStore
		self.treeView.set_model(self.treeStore)

		# create the TreeViewColumn to display the data
		self.tvcolumn = gtk.TreeViewColumn('Categories')

		# add tvcolumn to treeView
		self.treeView.append_column(self.tvcolumn)

		# create a CellRendererText to render the data
		self.cell = gtk.CellRendererText()
		
		self.cell.set_property('editable', True)
		self.cell.connect('edited', self.edited_cb, self.treeStore)

		# add the cell to the tvcolumn and allow it to expand
		self.tvcolumn.pack_start(self.cell, True)

		# set the cell "text" attribute to column 0 - retrieve text
		# from that column in treeStore
		self.tvcolumn.add_attribute(self.cell, 'text', 0)

		# make it searchable
		self.treeView.set_search_column(0)

		# Allow sorting on the column
		self.tvcolumn.set_sort_column_id(0)

		# Allow drag and drop reordering of rows
		#self.treeView.set_reorderable(True)
		
	def edited_cb(self, cell, path, new_text, user_data):
		'''Called when text in a cell is changed'''
		print 'Path', path
		if new_text == 'text':
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
			print parent, key
			newChild = self.treeStore.append(parent, [key])
			if not value == None:
				#print 'set', key
				self.add_element(newChild, value)
			
		
	def set_day_content(self, day):
		for key, value in day.content.iteritems():
			if not key == 'text':
				print key, value
				self.add_element(None, {key: value})
		self.treeView.expand_all()
				
	def get_day_content(self):
		if not self.empty():#self.treeStore.iter_has_child(None):
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
				text = self.get_iter_value(child)#model.get_value(child, 0)
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
		print 'Number of Categories:', self.treeStore.iter_n_children(None)
		for iterIndex in range(self.treeStore.iter_n_children(None)):
			currentCategoryIter = self.treeStore.iter_nth_child(None, iterIndex)
			currentCategoryName = self.get_iter_value(currentCategoryIter)
			print 'CMP:', currentCategoryName, categoryName
			if currentCategoryName == categoryName:
				return currentCategoryIter
		
		'If the category was not found, return None'
		return None
	
	def addEntry(self, categoryName, text):
		if categoryName not in self.categories and categoryName is not None:
			self.categories.append(categoryName)
			
		categoryIter = self._get_category_iter(categoryName)
		if categoryIter is None:
			categoryIter = self.treeStore.append(None, [categoryName])
			self.treeStore.append(categoryIter, [text])
		else:
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
		
	
		
		
	def __wxinit__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		
		self.buttonInsertTemplate = wx.Button(self, -1, "Insert Template")

		self.undoButton = wx.BitmapButton(self, -1, wx.NullBitmap)
		self.redoButton = wx.BitmapButton(self, -1, wx.NullBitmap)
		self.undoButton.SetBitmapLabel(getBitmap('edit-undo.png'))
		self.redoButton.SetBitmapLabel(getBitmap('edit-redo.png'))
		self.undoButton.Enable(False)
		self.redoButton.Enable(False)
		self.undoButton.SetToolTipString('Undo')
		self.redoButton.SetToolTipString('Redo')
		
		self.buttonInsertTemplate.SetToolTipString("Insert text defined for that weekday in template file")
		
		self.textField = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_TAB|wx.TE_MULTILINE|wx.TE_WORDWRAP)
		self.textField.textPanel = self
		
		self.Bind(wx.EVT_BUTTON, self.onInsertTemplate, self.buttonInsertTemplate)
		self.Bind(wx.EVT_BUTTON, self.onUndo, self.undoButton)
		self.Bind(wx.EVT_BUTTON, self.onRedo, self.redoButton)
		self.Bind(wx.EVT_TEXT, self.onTextChange, self.textField)
		
		self.__do_layout()
		
		self.history = []
		self.historyPosition = -1
		
	def __do_layout(self):
		sizer_3 = wx.BoxSizer(wx.VERTICAL)
		sizer_9 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_9.Add(self.buttonInsertTemplate, 0, wx.ADJUST_MINSIZE, 0)
		sizer_9.Add(self.undoButton, 0, wx.ADJUST_MINSIZE, 0)
		sizer_9.Add(self.redoButton, 0, wx.ADJUST_MINSIZE, 0)
		sizer_3.Add(sizer_9, 0, 0, 0)
		sizer_3.Add(self.textField, 1, wx.ALL|wx.EXPAND, 0)
		self.SetSizer(sizer_3)
		
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
		
		
	def onInsertTemplate(self, event):
		
		'''Load template'''
		textToLoad = self.redNotebook.getTemplateEntry()
		if len(textToLoad) == 0:
			dialog = wx.MessageDialog(self, "The template file for this weekday is empty.\n" + \
									  "You can edit the template files in the directory '" + \
									  filesystem.templateDir + "'.", 
									  "Template empty", wx.OK | wx.ICON_INFORMATION) # Create a message dialog box
			dialog.ShowModal()
		currentText = self.textField.GetValue()
		newText = textToLoad + currentText.encode('utf-8')
		self.textField.SetValue(newText)
		#print self.history
		event.Skip()
		
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
		
		#print self.history

	def onRedo(self, event):
		
		if self.historyPosition == len(self.history) - 1:
			return
		
		self.historyPosition += 1
		redoText = self.history[self.historyPosition]
		self.textField.ChangeValue(redoText)
		
		if self.historyPosition == len(self.history) - 1:
			self.redoButton.Enable(False)
			
		self.undoButton.Enable(True)
		
		#print self.history
		
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
		print self.timeLeft
		
		if self.timeLeft % 2 == 0:
			self.showText('', countdown=False)
		else:
			self.showText(self.savedText, countdown=False)
			
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
		
		
if __name__ == "__main__":
	print 0
	application = MainWindow(None)
	gtk.main()