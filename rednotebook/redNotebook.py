#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import with_statement

import yaml
import wxversion
wxversion.select("2.8")
import wx
import sys
import datetime
import os
import zipfile



from util import filesystem
print 'AppDir:', filesystem.appDir
baseDir = os.path.abspath(os.path.join(filesystem.appDir, '../'))
print 'BaseDir:', baseDir
if baseDir not in sys.path:
    print 'Adding BaseDir to sys.path'
    sys.path.insert(0, baseDir)




#from gui import wxGladeGui
from gui import wxGladeGui
from util import unicode, dates
import info


class RedNotebook(wx.App):
    
    version = info.version
    appDir = filesystem.appDir
    imageDir = filesystem.imageDir
    userHomedir = os.path.expanduser('~')
    redNotebookUserDir = os.path.join(userHomedir, ".rednotebook/")
    dataDir = os.path.join(redNotebookUserDir, "data/")
    fileNameExtension = '.txt'
    
    minDate = datetime.date(1970, 1, 1)
    maxDate = datetime.date(2020, 1, 1)
    
    def OnInit(self):
        self.month = None
        self.date = None
        self.months = {}
        
        mainFrame = wxGladeGui.MainFrame(self, None, -1, "")
        mainFrame.Show()
        self.SetTopWindow(mainFrame)
        self.frame = mainFrame

        #show instructions at first start
        self.firstTimeExecution = not os.path.exists(self.dataDir)
        
        filesystem.makeDirectories((self.redNotebookUserDir, self.dataDir))
           
        self.actualDate = datetime.date.today()
        
        self.loadAllMonthsFromDisk()
        
         #Nothing to save before first day change
        self.loadDay(self.actualDate)
        
        if self.firstTimeExecution is True:
            self.addInstructionContent()

        return True
    
    def backupContents(self):
        proposedFileName = 'RedNotebook-Backup_' + str(datetime.date.today()) + ".zip"
        dlg = wx.FileDialog(self.frame, "Choose Backup File", '', proposedFileName, "*.zip", wx.SAVE)
        returnValue = dlg.ShowModal()
        dlg.Destroy()
        if returnValue == wx.ID_OK:            
            archiveFileName = dlg.GetPath()
            
            if os.path.exists(archiveFileName):
                dialog = wx.MessageDialog(self.frame, "File already exists. Are you sure you want to override it?", 
                "File Exists", wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION) # Create a message dialog box
                if not dialog.ShowModal() == wx.ID_YES:
                    return
            
            archiveFiles = []
            for root, dirs, files in os.walk(self.dataDir):
                for file in files:
                    archiveFiles.append(os.path.join(root,file))
            
            filesystem.writeArchive(archiveFileName, archiveFiles, self.dataDir)

    
    def saveToDisk(self):
        self.saveOldDay()
        
        for yearAndMonth, month in self.months.iteritems():
            if not month.empty:
                monthFile = open(self.dataDir + yearAndMonth + self.fileNameExtension, 'w')
                monthContent = {}
                for dayNumber, day in month.days.iteritems():
                    #do not add empty days
                    if not day.empty:
                        monthContent[dayNumber] = day.content
                #month.prettyPrint()
                yaml.dump(monthContent, monthFile)
        
        #TODO: Uncomment
        #savedDialog = wx.MessageDialog(None, message='The content has been saved.', caption='Saved', style=wx.OK)
        self.showMessage('The content has been saved')
        print 'The content has been saved'
        #savedDialog.ShowModal()
        #savedDialog.Destroy()
        
    def loadAllMonthsFromDisk(self):
        for root, dirs, files in os.walk(self.dataDir):
            for file in files:
                self.loadMonthFromDisk(os.path.join(root, file))
    
    def loadMonthFromDisk(self, file):
        
        yearAndMonth = file[-11:-4] #dates.getYearAndMonthFromDate(date)
        yearNumber = yearAndMonth[:4]
        monthNumber = yearAndMonth[-2:]
        
        #Selected month has not been loaded
        #if not self.months.has_key(yearAndMonth):
        monthFileString = file #self.dataDir + yearAndMonth + self.fileNameExtension
        if not os.path.isfile(monthFileString):
            #File not found
            #Create new month
            print 'not found', monthFileString
            self.months[yearAndMonth] = Month(yearNumber, monthNumber)
             
        else:
            #File found
            monthFile = open(monthFileString, 'r')
            monthContents = yaml.load(monthFile)
            self.months[yearAndMonth] = Month(yearNumber, monthNumber, monthContents)
            
        return self.months[yearAndMonth]
    
    def loadMonth(self, date):
        
        yearAndMonth = dates.getYearAndMonthFromDate(date)
        
        #Selected month has not been loaded
        if not self.months.has_key(yearAndMonth):
            #monthFileString = self.dataDir + yearAndMonth + self.fileNameExtension
            #if not os.path.isfile(monthFileString):
                #File not found
                #Create new month
                #print 'not found', monthFileString
            self.months[yearAndMonth] = Month(date.year, date.month)
                 
            #else:
                #File found
                #monthFile = open(monthFileString, 'r')
                #monthContents = yaml.load(monthFile)
                #self.months[yearAndMonth] = Month(monthContents)
            
        return self.months[yearAndMonth]
    
    def saveOldDay(self):  
        #Order important
        self.day.content = self.frame.contentTree.getDayContent()
        self.day.text = self.frame.getDayText()
        self.frame.calendar.setDayEdited(self.date.day, not self.day.empty)
    
    def loadDay(self, newDate):
        oldDate = self.date
        self.date = newDate
        
        if not Month.sameMonth(newDate, oldDate):
            self.month = self.loadMonth(self.date)
            self.frame.calendar.setMonth(self.month)
        
        self.frame.calendar.PySetDate(self.date)
        self.frame.showDay(self.day)
        self.frame.contentTree.categories = self.nodeNames
        
    def _getCurrentDay(self):
        return self.month.getDay(self.date.day)
    day = property(_getCurrentDay)
    
    def changeDate(self, date):
        self.saveOldDay()
        self.loadDay(date)
        
    def goToNextDay(self):
        self.changeDate(self.date + dates.oneDay)
        
    def goToPrevDay(self):
        self.changeDate(self.date - dates.oneDay)
        
    def goToNextEditedDay(self):
        oldDate = self.date
        self.goToNextDay()
        while self.day.empty and not self.date > self.maxDate:
            self.goToNextDay()
        if self.date > self.maxDate:
            print 'No edited day exists after this one'
            self.changeDate(oldDate)
        
        
    def goToPrevEditedDay(self):
        oldDate = self.date    
        self.goToPrevDay()
        while not self.day.empty and not self.date < self.minDate:
            self.goToPrevDay()
        if self.date < self.minDate:
            print 'No edited day exists before this one'
            self.changeDate(oldDate)
            
    def showMessage(self, messageText):
        self.frame.showMessageInStatusBar(messageText)
        
    def _getNodeNames(self):
        nodeNames = set([])
        for month in self.months.values():
            nodeNames |= set(month.nodeNames)
        return list(nodeNames)
    nodeNames = property(_getNodeNames)
    
    def search(self, text):
        results = []
        for day in self.days:
            if not day.search(text) == None:
                results.append(day.search(text))
        return results
    
    def _getAllEditedDays(self):
        days = []
        for month in self.months.values():
            days.extend(month.days.values())
        return days
    days = property(_getAllEditedDays)
    
    def getNumberOfWords(self):
        #def countWords(day1, day2):
        #    return day1.getNumberOfWords() + day2.getNumberOfWords()
        #return reduce(countWords, self.days, 0)
        numberOfWords = 0
        for day in self.days:
            numberOfWords += day.getNumberOfWords()
        return numberOfWords
    
    def getNumberOfEntries(self):
        return len(self.days)
    
    def addInstructionContent(self):
        instructionDayContent = {u'Cool Stuff': {u'Went to see the pope': None}, 
                                 u'Ideas': {u'Found a way to end all wars. (More on that tomorrow.)': None}}
        
        #Dates don't matter as only the categories are shown
        instructionDay = Day(self.actualDate.month, self.actualDate.day, dayContent = instructionDayContent)
        
        self.frame.contentTree.addDayContent(instructionDay)
        self.frame.contentTree.ExpandAll()
        
        instructionText = """\
Hello, 
this is the RedNotebook, a simple diary. This program helps you to keep track of your activities and thoughts. \
Thank you very much for giving it a try.
The text field in which you are reading this text is the container for your normal diary entries: 

Today I went to a pet shop and bought myself a tiger. Then we went to the park and had a nice time playing \
ultimate frisbee together. After that we watched the Flying Circus.

The usual stuff.
On the right there is space for extra entries. Things that can easily be sorted into categories. Those entries \
are shown in a tree. For example you could add the category Ideas and then add an entry which reminds you of \
what your idea was about:

> Ideas
  Found a way to end all wars. (More on that tomorrow.)
  
In addition you could add:

> Cool Stuff
  Went to see the pope
  
For the really cool things you did that day. On the right panel you control everything with right-clicks. Either \
on the white space or on existing categories.

Everything you enter will be saved automatically when you exit the program. If you want to double check you can save \
pressing "Strg-S" or using the menu entry under "File" in the top left corner. "Backup" saves all your entered data in a \
zip file. After pressing the button you can select a location for that.

There are many features I have planned to add in the future so stay tuned.
I hope you enjoy the program!
            """
        self.frame.mainTextField.SetValue(instructionText)
        
        
        
class Label(object):
    def __init__(self, name):
        self.name = name
        
            

class Day(object):
    def __init__(self, month, dayNumber, dayContent = None):
        if dayContent == None:
            dayContent = {}
            
        self.month = month
        self.dayNumber = dayNumber
        self.content = dayContent
    
    #Text
    def _getText(self):
        if self.content.has_key('text'):
            return self.content['text']
        else:
           return ''
        #self.getContent('text')
    def _setText(self, text):
        self.content['text'] = text
        #self.setContent('text', text)
    text = property(_getText, _setText)
    
    def _hasText(self):
        return len(self.text.strip()) > 0
    hasText = property(_hasText)
    
    def _isEmpty(self):
        if len(self.content.keys()) == 0:
            return True
        elif len(self.content.keys()) == 1 and self.content.has_key('text') and not self.hasText:
            return True
        else:
            return False
    empty = property(_isEmpty)
    
    def getContent(self, key):
        if self.content.has_key(key):
            return self.content[key]
        else:
            return ''
    def setContent(self, key, value):
        self.content[key] = value
        
    def _getTree(self):
        tree = self.content.copy()
        if tree.has_key('text'):
            del tree['text']
        return tree
    tree = property(_getTree)
        
    def _getNodeNames(self):
        return self.tree.keys()
    nodeNames = property(_getNodeNames)
    
    def getNumberOfWords(self):
        return len(self.text.split())
    
    
    def search(self, searchText):
        '''Case-insensitive search'''
        upCaseSearchText = searchText.upper()
        upCaseDayText = self.text.upper()
        occurence = upCaseDayText.find(upCaseSearchText)
        
        if occurence > -1:
            spaceSearchLeftStart = occurence-15
            if spaceSearchLeftStart < 0:
                spaceSearchLeftStart = 0
            spaceSearchRightEnd = occurence + len(searchText) + 15
            if spaceSearchRightEnd > len(self.text):
                spaceSearchRightEnd = len(self.text)
                
            resultTextStart = self.text.find(' ', spaceSearchLeftStart, occurence)
            resultTextEnd = self.text.rfind(' ', occurence + len(searchText), spaceSearchRightEnd)
            if resultTextStart == -1:
                resultTextStart = occurence - 10
            if resultTextEnd == -1:
                resultTextEnd = occurence + len(searchText) + 10
                
            return (self, '... ' + unicode.substring(self.text, resultTextStart, resultTextEnd).strip() + ' ...')
        else:
            return None
            

class Month(object):
    def __init__(self, yearNumber, monthNumber, monthContent = None):
        if monthContent == None:
            monthContent = {}
        
        self.yearNumber = yearNumber
        self.monthNumber = monthNumber
        self.days = {}
        for dayNumber, dayContent in monthContent.iteritems():
            self.days[dayNumber] = Day(self, dayNumber, dayContent)
    
    def getDay(self, dayNumber):
        if self.days.has_key(dayNumber):
            #print 'Key found', dayNumber
            return self.days[dayNumber]
        else:
            #print 'Key not found', dayNumber
            newDay = Day(self, dayNumber)
            self.days[dayNumber] = newDay
            return newDay
        
    def setDay(self, dayNumber, day):
        self.days[dayNumber] = day
        
    def prettyPrint(self):
        print '***'
        for dayNumber, day in self.days.iteritems():
            print dayNumber, 
            unicode.printUnicode(day.text)
        print '---'
        
    def _isEmpty(self):
        for day in self.days.values():
            if not day.empty:
                return False
        return True
    empty = property(_isEmpty)
    
    def _getNodeNames(self):
        nodeNames = set([])
        for day in self.days.values():
            nodeNames |= set(day.nodeNames)
        return nodeNames
    nodeNames = property(_getNodeNames)
    
    def sameMonth(date1, date2):
        if date1 == None or date2 == None:
            return False
        return date1.month == date2.month and date1.year == date2.year
    sameMonth = staticmethod(sameMonth)
        
    
    
        
    
def main():
    app = RedNotebook(redirect=False)
    wx.InitAllImageHandlers()
    app.MainLoop()

#if __name__ == '__main__':
main()
    
