# -*- coding: utf-8 -*-

import gtk
import datetime
import os
import codecs
import operator

from rednotebook.util import markup

class ExportAssistant (object):
    def __init__ (self, mainWindow):
        
        self.redNotebook = mainWindow.redNotebook
        self.gladefile = mainWindow.gladefile
        
        self.formatExtensionMap = {'Text': 'txt', 'HTML': 'html', 'Latex': 'tex', 'PDF' : 'pdf'}
        self.assistant = gtk.Assistant()
        self.assistant.connect('close', self.onQuit)
        self.assistant.connect('cancel', self.onCancel)
        self.assistant.connect('delete_event', self.onCancel)

        self.append_first_page()
        self.append_second_page()
        self.append_third_page()
        
        self.assistant.set_forward_page_func(self.prepare_next_page, None)
        
        self.assistant.show()

    def append_first_page (self) :

        cloned_glade = gtk.glade.XML(self.gladefile, 'exportAssistant_1') 
        page1 = cloned_glade.get_widget('exportAssistant_1')
        page1.show()

        self.assistant.append_page(page1)
        self.assistant.set_page_title(page1, 'Export Assistant, step 1')
        self.assistant.set_page_type(page1, gtk.ASSISTANT_PAGE_CONTENT)
        self.assistant.set_page_complete(page1, True)

        self.textButton = cloned_glade.get_widget('text')
        self.htmlButton = cloned_glade.get_widget('html')
        self.latexButton = cloned_glade.get_widget('latex')
        self.pdfButton = cloned_glade.get_widget('pdf')
        if not self.isPDFSupported() :
            self.pdfButton.hide()
        else :
            self.pdfButton.show()
            


    def append_second_page (self) :
        cloned_glade = gtk.glade.XML(self.gladefile, 'exportAssistant_2')
        dic = {
            'changeDateSelectorStatus': self.changeDateSelectorStatus
        }
        cloned_glade.signal_autoconnect(dic)
        
        page2 = cloned_glade.get_widget('exportAssistant_2')
        page2.show()
        self.assistant.append_page(page2)
        self.assistant.set_page_title(page2, 'Export Assistant, step 2')
        self.assistant.set_page_type(page2, gtk.ASSISTANT_PAGE_CONTENT)
        self.assistant.set_page_complete(page2, True)
        
        self.allEntriesButton = cloned_glade.get_widget('allEntries')
        self.selectedRangeButton = cloned_glade.get_widget('selectedRange')
        self.startDate = cloned_glade.get_widget('startDate')
        self.endDate = cloned_glade.get_widget('endDate')
        
        
        startDateValue = self.redNotebook.getEditDateOfEntryNumber(0)
        self.startDate.select_month(startDateValue.month - 1, startDateValue.year)
        self.startDate.select_day (startDateValue.day)

        endDateValue = self.redNotebook.getEditDateOfEntryNumber(-1)
        self.endDate.select_month(endDateValue.month - 1, endDateValue.year)
        self.endDate.select_day (endDateValue.day)
        
        self.changeDateSelectorStatus(self.assistant)

    
    def append_third_page (self) :
        cloned_glade = gtk.glade.XML(self.gladefile, 'exportAssistant_3')
        page3 = cloned_glade.get_widget('exportAssistant_3')
        page3.show()
        
        self.assistant.append_page(page3)
        self.assistant.set_page_title(page3, 'Export Assistant, step 3')
        self.assistant.set_page_type(page3, gtk.ASSISTANT_PAGE_CONFIRM)
        self.assistant.set_page_complete(page3, True)

        self.filnameChooser = cloned_glade.get_widget('filenameChooser')
        
    
    def prepare_next_page (self, currentPage, data):
        if currentPage == 0 :
            proposedFileName = 'RedNotebook-Export_' + str(datetime.date.today()) + \
                                '.' + self.formatExtensionMap.get(self.getSelectedFormat())

            home = os.getenv('USERPROFILE') or os.getenv('HOME')
            self.filnameChooser.set_current_folder(home)
            self.filnameChooser.set_current_name (proposedFileName)
            
        return currentPage + 1
    
    
    def onQuit (self, widget):
        self.fileName = self.filnameChooser.get_filename()
        self.assistant.destroy()
        self.export()
    
    def onCancel (self, widget, other=None):
        self.redNotebook.showMessage('Cancelling export assistant.')
	self.assistant.destroy()

    def changeDateSelectorStatus (self, widget):
        if (self.allEntriesButton.get_active()) :
            self.startDate.set_sensitive(False)
            self.endDate.set_sensitive(False)
        else :
            self.startDate.set_sensitive(True)
            self.endDate.set_sensitive(True)
            
    def getStartDate (self):
        year, month, day = self.startDate.get_date()
        return datetime.date(year, month + 1, day)

    def getEndDate (self):
        year, month, day = self.endDate.get_date()
        return datetime.date(year, month + 1, day)
    
    def getSelectedFormat (self):
        if self.latexButton.get_active():
            return "Latex"
        if self.htmlButton.get_active():
            return "HTML"
        if self.pdfButton.get_active() :
            return "PDF"
        return "Text"
    
    def isAllEntriesSelected (self):
        if self.allEntriesButton.get_active():
            return True
        return False
        
    def isPDFSupported (self):
        #TODO: Implement that
        return False
    
    def export (self):
        #TODO: Implement that
        exportString = self.getExportString(self.getSelectedFormat())
        
        try:
            exportFile = codecs.open(self.fileName, 'w', 'utf-8')
            exportFile.write(exportString)
            exportFile.flush()
            self.redNotebook.showMessage('Content exported to ' + self.fileName)
        except:
            self.redNotebook.showMessage('Exporting to ' + self.fileName + ' failed')

    def getExportString(self, format):
        if self.isAllEntriesSelected() :
            exportDays = self.redNotebook.sortedDays
        else:
            exportDays = self.redNotebook.getDaysInDateRange((self.getStartDate(), self.getEndDate()))

        markupStringHeader = 'RedNotebook'
        markupStringsForEachDay = map(markup.getMarkupForDay, exportDays)
        markupString = reduce(operator.add, markupStringsForEachDay)
        
        target = self.formatExtensionMap.get(self.getSelectedFormat())
        
        return markup.convertMarkupToTarget(markupString, target, markupStringHeader)
    
    
