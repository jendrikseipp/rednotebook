import yaml, wx

import datetime, os, zipfile

from gui import wxGladeGui
from util import filesystem, unicode, dates


class RedNotebook(wx.App):
    
    version = '0.1'
    homedir = os.path.expanduser('~')
    dataDir = os.path.join(homedir, "data/")
    fileNameExtension = '.txt'
    
    minDate = datetime.date(1970, 1, 1)
    maxDate = datetime.date(2020, 1, 1)
    
    def OnInit(self):
        mainFrame = wxGladeGui.MainFrame(self, None, -1, "")
        mainFrame.Show()
        self.SetTopWindow(mainFrame)
        self.frame = mainFrame

        
        filesystem.makeDirectory(self.dataDir)
           
        actualDate = datetime.date.today()
        
        self.month = None
        self.date = None
        self.loadedMonths = {}
        
         #Nothing to save before first day change
        self.loadDay(actualDate)

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
            
            archive = zipfile.ZipFile(archiveFileName, "w")
            for root, dirs, files in os.walk(self.dataDir):
                for file in files:
                    archive.write(os.path.join(root,file))

    
    def saveToDisk(self):
        self.saveOldDay()
        
        for yearAndMonth, month in self.loadedMonths.iteritems():
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
    
    def loadMonth(self, date):
        
        yearAndMonth = dates.getYearAndMonthFromDate(date)
        
        #Selected month has not been loaded
        if not self.loadedMonths.has_key(yearAndMonth):
            monthFileString = self.dataDir + yearAndMonth + self.fileNameExtension
            if not os.path.isfile(monthFileString):
                #File not found
                #Create new month
                print 'not found', monthFileString
                self.loadedMonths[yearAndMonth] = Month()
                 
            else:
                #File found
                monthFile = open(monthFileString, 'r')
                monthContents = yaml.load(monthFile)
                self.loadedMonths[yearAndMonth] = Month(monthContents)
            
        return self.loadedMonths[yearAndMonth]
    
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
            

class Day(object):
    def __init__(self, dayNumber, dayContent = None):
        if dayContent == None:
            dayContent = {}
    
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

class Month(object):
    def __init__(self, monthContent = None):
        if monthContent == None:
            monthContent = {}
        
        self.days = {}
        for dayNumber, dayContent in monthContent.iteritems():
            self.days[dayNumber] = Day(dayNumber, dayContent)
    
    def getDay(self, dayNumber):
        if self.days.has_key(dayNumber):
            #print 'Key found', dayNumber
            return self.days[dayNumber]
        else:
            #print 'Key not found', dayNumber
            newDay = Day(dayNumber)
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
    
    def sameMonth(date1, date2):
        if date1 == None or date2 == None:
            return False
        return date1.month == date2.month and date1.year == date2.year
    sameMonth = staticmethod(sameMonth)
    
        
    
def main():
    app = RedNotebook()
    wx.InitAllImageHandlers()    
    app.MainLoop()

if __name__ == '__main__':
    main()
    
