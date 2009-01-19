# -*- coding: utf-8 -*-
from __future__ import with_statement

import wx
import wx.wizard as wizmod
import os.path
import datetime
import operator
import sys
import codecs
import subprocess

#from rednotebook.gui.diaryGui import getBitmapFromFile
from rednotebook.util import dates
from rednotebook import txt2tags
from rednotebook.util import filesystem
from rednotebook.util import markup



padding = 5



def systemCommandAvailable(command):
	'checks whether a system command is available'
	'This could probably be improved'
	try:	
		process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
		returnCode = process.wait()
		return returnCode == 0
	except:
		return False


class WizardPage(wizmod.PyWizardPage):
	''' An extended panel obj with a few methods to keep track of its siblings.  
		This should be modified and added to the wizard.  Season to taste.
		
		Code from http://wiki.wxpython.org/wxWizard
	'''
	def __init__(self, parent, title):
		wx.wizard.PyWizardPage.__init__(self, parent)
		self.next = self.prev = None
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		title = wx.StaticText(self, -1, title)
		title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.sizer.AddWindow(title, 0, wx.ALIGN_LEFT|wx.ALL, padding)
		self.sizer.AddWindow(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, padding)
		self.SetSizer(self.sizer)

	def addStuff(self, stuff):
		'Add aditional widgets to the bottom of the page'
		self.sizer.Add(stuff, 0, wx.EXPAND|wx.ALL, padding)

	def SetNext(self, next):
		'Set the next page'
		self.next = next

	def SetPrev(self, prev):
		'Set the previous page'
		self.prev = prev

	def GetNext(self):
		'Return the next page'
		return self.next

	def GetPrev(self):
		'Return the previous page'
		return self.prev


class Wizard(wx.wizard.Wizard):
	'Add pages to this wizard object to make it useful.'
	def __init__(self, title, img_filename=""):
		if img_filename:
				img = getBitmapFromFile(img_filename)
		else:
			img = wx.NullBitmap
		wx.wizard.Wizard.__init__(self, None, -1, title, img)
		self.pages = []
		# Let's catch the events
		self.Bind(wizmod.EVT_WIZARD_PAGE_CHANGED, self.onPageChanged)
		self.Bind(wizmod.EVT_WIZARD_PAGE_CHANGING, self.onPageChanging)
		self.Bind(wizmod.EVT_WIZARD_CANCEL, self.onCancel)
		self.Bind(wizmod.EVT_WIZARD_FINISHED, self.onFinished)

	def add_page(self, page):
		'Add a wizard page to the list.'
		if self.pages:
			previous_page = self.pages[-1]
			page.SetPrev(previous_page)
			previous_page.SetNext(page)
		self.pages.append(page)

	def run(self):
		self.RunWizard(self.pages[0])

	def onPageChanged(self, evt):
		'Executed after the page has changed.'
		if evt.GetDirection():  dir = "forward"
		else:				   dir = "backward"
		page = evt.GetPage()
		print "page_changed: %s, %s\n" % (dir, page.__class__)

	def onPageChanging(self, evt):
		'Executed before the page changes, so we might veto it.'
		if evt.GetDirection():  dir = "forward"
		else:				   dir = "backward"
		page = evt.GetPage()
		print "page_changing: %s, %s\n" % (dir, page.__class__)

	def onCancel(self, evt):
		'Cancel button has been pressed.  Clean up and exit without continuing.'
		page = evt.GetPage()
		print "onCancel: %s\n" % page.__class__

		# Prevent cancelling of the wizard.
		if page is self.pages[0]:
			wx.MessageBox("Cancelling on the first page has been prevented.", "Sorry")
			evt.Veto()

	def onFinished(self, evt):
		'Finish button has been pressed.  Clean up and exit.'
		print "OnWizFinished\n"
		
class ExportWizard(Wizard):
	'Add pages to this wizard object to make it useful.'
	def __init__(self, redNotebook, *args, **kargs):
		Wizard.__init__(self, *args, **kargs)
		
		self.redNotebook = redNotebook
		
		self.exportFormats = ['Text', 'HTML', 'Latex',]
		self.formatExtensionMap = {'Text': 'txt', 'HTML': 'html', 'Latex': 'tex'}
		
		if systemCommandAvailable('pdflatex -version'):
			print 'pdflatex is available'
			self.exportFormats.append('PDF')
			self.formatExtensionMap['PDF'] = 'pdf'
		
		page1 = WizardPage(self, 'Select Format')  # Create a first page
		self.methodPanel = RadioButtonPanel(page1)
		for format in self.exportFormats:
			self.methodPanel.addOption(format)
		page1.addStuff(self.methodPanel)
		self.add_page(page1)
		
		
		
		page2 = WizardPage(self, 'Select Entries')
		
		firstEntryDate = redNotebook.getEditDateOfEntryNumber(0)
		lastEntryDate = redNotebook.getEditDateOfEntryNumber(-1)
		
		self.fromText = wx.StaticText(page2, -1, 'Entries from')
		self.tillText = wx.StaticText(page2, -1, 'till')
		
		self.fromDate = wx.DatePickerCtrl(page2, size=(120,-1), dt=dates.getWXDateTimeFromPyDate(firstEntryDate), \
									style=wx.DP_DROPDOWN |wx.DP_SHOWCENTURY
														#|wx.calendar.CAL_MONDAY_FIRST
														)
		self.toDate = wx.DatePickerCtrl(page2, size=(120,-1), dt=dates.getWXDateTimeFromPyDate(lastEntryDate), \
									style=wx.DP_DROPDOWN |wx.DP_SHOWCENTURY
														#|wx.calendar.CAL_MONDAY_FIRST
														)
		self.entryPanel = EntryPanel(page2)
		page2.addStuff(self.entryPanel)
		page2.addStuff(self.fromText)
		page2.addStuff(self.fromDate)
		page2.addStuff(self.tillText)
		page2.addStuff(self.toDate)
		
		self.add_page(page2)

	def onPageChanged(self, evt):
		'Executed after the page has changed.'
		pass

	def onPageChanging(self, evt):
		'Executed before the page changes, so we might veto it.'
		pass

	def onCancel(self, evt):
		'Cancel button has been pressed.  Clean up and exit without continuing.'
		pass

	def onFinished(self, evt):
		'Finish button has been pressed.  Clean up and exit.'
		self.export()
		
	def export(self):
		exportFormat = self.methodPanel.GetSelection()
		
		if self.redNotebook.testing:
			exportFileName = os.path.join(os.path.expanduser('~'), 'rn-export.' + \
										self.formatExtensionMap.get(exportFormat))
		else:
			exportFileName = self.getExportFileName(exportFormat)
		
		if not exportFileName:
			return
		
		if exportFormat == 'PDF':
			exportString = self.getExportString('Latex')
			pdfExportFileName = exportFileName
			exportFileName = os.path.splitext(exportFileName)[0] + '.' + \
								self.formatExtensionMap.get('Latex')
		else:
			exportString = self.getExportString(exportFormat)
		
		with codecs.open(exportFileName, 'w', 'utf-8') as exportFile:
			try:
				exportFile.write(exportString)
				exportFile.flush()
				if exportFormat == 'PDF':
					print 'Creating PDF'
					outputDir = os.path.dirname(exportFileName)
					pdfCommand = 'pdflatex -interaction=nonstopmode '
					outputDirCommand = '-output-directory "' + outputDir + '" '
					completeCommand = pdfCommand + outputDirCommand + '"' + exportFileName + '"'
					print 'Executing Command', completeCommand
					process = subprocess.Popen(completeCommand, shell=True, stdout=subprocess.PIPE)
					processOut = process.stdout
					returnCode = process.wait()
					#print processOut.read()
					#print returnCode
					if returnCode == 0:
						self.redNotebook.showMessage('Content exported to ' + pdfExportFileName)
					else:
						message = 'There were errors exporting the content. '
						if os.path.exists(pdfExportFileName):
							message += 'Better check the pdf.'
						else:
							message += 'No output file created. See Help.'
						self.redNotebook.showMessage(message)
						print 'pdflatex returned', returnCode
						print '***************** PDFLATEX OUTPUT *****************'
						print processOut.read()
				else:
					self.redNotebook.showMessage('Content exported to ' + exportFileName)
			except:
				self.redNotebook.showMessage('Exporting to ' + exportFileName + ' failed')
				
		'''
		htmldoc --toctitle "RedNotebook" --no-title --toclevels 2 -t htmlsep -d htmloutput2/ rn.html
		'''
		
		
		
		
	def getExportFileName(self, exportFormat):
		'''Returns output fileName or None, if user aborted exporting'''
		proposedFileName = 'RedNotebook-Export_' + str(datetime.date.today()) + \
							'.' + self.formatExtensionMap.get(exportFormat)
		dlg = wx.FileDialog(self, "Choose Export Filename", '', proposedFileName, \
							'*.' + self.formatExtensionMap.get(exportFormat), wx.SAVE)
		returnValue = dlg.ShowModal()
		dlg.Destroy()
		if not returnValue == wx.ID_OK:
			return
		
		exportFileName = dlg.GetPath()
		
		'Stop, if file exists and user does not want to override it'
		if os.path.exists(exportFileName):
			dialog = wx.MessageDialog(self, "File already exists. Are you sure you want to override it?", 
			"File Exists", wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
			if not dialog.ShowModal() == wx.ID_YES:
				return
			
		return exportFileName
	
	def getExportString(self, exportFormat):
		if not self.entryPanel.allEntriesRadioButton.GetValue():
			fromDateWX = self.fromDate.GetValue()
			fromDate = dates.getPyDateFromWXDateTime(fromDateWX)
			toDateWX = self.toDate.GetValue()
			toDate = dates.getPyDateFromWXDateTime(toDateWX)
		
			exportDays = self.redNotebook.getDaysInDateRange((fromDate, toDate))
		else:
			exportDays = self.redNotebook.sortedDays
		
		markupStringHeader = 'RedNotebook'
		markupStringsForEachDay = map(markup.getMarkupForDay, exportDays)
		markupString = reduce(operator.add, markupStringsForEachDay)
		
		target = self.formatExtensionMap.get(exportFormat)
		
		return markup.convertMarkupToTarget(markupString, target, markupStringHeader)
			
		
		
		
class RadioButtonPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, wx.ID_ANY)
		
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		
		#self.sizer.AddWindow(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, padding)
		self.SetSizer(self.sizer)
		
		self.options = []
	
	def addOption(self, title):
		if len(self.options) == 0:
			newRadioButton = wx.RadioButton(self, wx.ID_ANY, title, (10, 10), style=wx.RB_GROUP)
		else:
			newRadioButton = wx.RadioButton(self, wx.ID_ANY, title, (10, 10))
		#self.rb2 = wx.RadioButton(panel, -1, 'Value B', (10, 30))
		self.sizer.Add(newRadioButton, 0, wx.ALIGN_LEFT|wx.ALL, padding)
		#self.rb3 = wx.RadioButton(panel, -1, 'Value C', (10, 50))

		#self.Bind(wx.EVT_RADIOBUTTON, self.SetVal, id=newRadioButton.GetId())
		
		self.options.append(newRadioButton)
		
		return newRadioButton

	def GetSelection(self):
		for button in self.options:
			if button.GetValue():
				return button.GetLabelText()
			
class EntryPanel(RadioButtonPanel):
	def __init__(self, *args, **kargs):
		RadioButtonPanel.__init__(self, *args, **kargs)
		
		self.allEntriesRadioButton = self.addOption('All entries')
		self.selectedEntriesRadioButton = self.addOption('Only the entries in the\nselected time range')

		self.Bind(wx.EVT_RADIOBUTTON, self.onCheckBox, id=self.allEntriesRadioButton.GetId())
		self.Bind(wx.EVT_RADIOBUTTON, self.onCheckBox, id=self.selectedEntriesRadioButton.GetId())
		
		self.allEntriesRadioButton.Enable(True)
		self.enableDatePickers(False)
		
	def onCheckBox(self, event):
		allEntries = event.GetId() == self.allEntriesRadioButton.GetId()
		self.enableDatePickers(not allEntries)
		
	def enableDatePickers(self, enabled):
		wizard = self.Parent.Parent
		wizard.fromDate.Enable(enabled)
		wizard.toDate.Enable(enabled)
		wizard.fromText.Enable(enabled)
		wizard.tillText.Enable(enabled)

	
	
