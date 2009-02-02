#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import with_statement

import sys
import datetime
import os
import zipfile
import operator


if hasattr(sys, "frozen"):
	from rednotebook.util import filesystem
	from rednotebook.util import utils
else:
	from util import filesystem
	from util import utils

try:
	import gtk
except ImportError:
	utils.printError('Please install PyGTK (python-gtk2)')
	sys.exit(1)

try:
	import yaml
except ImportError:
	utils.printError('Yaml is not installed (install python-yaml)')
	sys.exit(1)

	

print 'AppDir:', filesystem.appDir
baseDir = os.path.abspath(os.path.join(filesystem.appDir, '../'))
print 'BaseDir:', baseDir
if baseDir not in sys.path:
	print 'Adding BaseDir to sys.path'
	sys.path.insert(0, baseDir)
	



'This version of import is needed for win32 to work'
from rednotebook.util import unicode
from rednotebook.util import dates
from rednotebook import info
from rednotebook import config

from rednotebook.gui.mainWindow import MainWindow
from rednotebook.util.statistics import Statistics



class RedNotebook:
	
	def __init__(self):
		self.testing = False
		if 'testing' in sys.argv:
			self.testing = True
			print 'Testing Mode'
			filesystem.dataDir = os.path.join(filesystem.redNotebookUserDir, "data-test/")
		
		self.month = None
		self.date = None
		self.months = {}
		
		'show instructions at first start or if testing'
		self.firstTimeExecution = not os.path.exists(filesystem.dataDir) or self.testing
		
		filesystem.makeDirectories([filesystem.redNotebookUserDir, filesystem.dataDir, \
								filesystem.templateDir, filesystem.tempDir])
		self.makeEmptyTemplateFiles()
		filesystem.makeFiles([(filesystem.configFile, '')])
		
		#self.config = config.redNotebookConfig(localFilename=filesystem.configFile)
		
		mainFrame = MainWindow(self)
		self.frame = mainFrame
		   
		self.actualDate = datetime.date.today()
		
		self.loadAllMonthsFromDisk()
		
		'Nothing to save before first day change'
		self.loadDay(self.actualDate)
		
		self.stats = Statistics(self)
		
		self.frame.categoriesTreeView.categories = self.nodeNames
		
		if self.firstTimeExecution is True:
			self.addInstructionContent()
			
		'Show cloud tab'
		self.frame.searchNotebook.set_current_page(1)
		
		'Check for a new version'
		utils.check_new_version(self.frame, info.version)
		
	
	
	def getDaysInDateRange(self, range):
		startDate, endDate = range
		assert startDate <= endDate
		
		sortedDays = self.sortedDays
		daysInDateRange = []
		for day in sortedDays:
			if day.date < startDate:
				continue
			elif day.date >= startDate and day.date <= endDate:
				daysInDateRange.append(day)
			elif day.date > endDate:
				break
		return daysInDateRange
		
		
	def _getSortedDays(self):
		return sorted(self.days, dates.compareTwoDays)
	sortedDays = property(_getSortedDays)
	
	
	def getEditDateOfEntryNumber(self, entryNumber):
		sortedDays = self.sortedDays
		if len(self.sortedDays) == 0:
			return datetime.date.today()
		return dates.getDateFromDay(self.sortedDays[entryNumber % len(sortedDays)])
	
	   
	def makeEmptyTemplateFiles(self):
		def getInstruction(dayNumber):
			return 'The template for this weekday has not been edited. ' + \
					'If you want to have some text that you can add to that day every week, ' + \
					'edit the file "' + filesystem.getTemplateFile(dayNumber) + \
					'" in a text editor.'
					
		fileContentPairs = []
		for dayNumber in range(1, 8):
			fileContentPairs.append((filesystem.getTemplateFile(dayNumber), getInstruction(dayNumber)))
		
		filesystem.makeFiles(fileContentPairs)
	
	
	def backupContents(self):
		self.saveToDisk()
		backupFile = self.frame.get_backup_file()
		
		if backupFile:
			
			archiveFiles = []
			for root, dirs, files in os.walk(filesystem.dataDir):
				for file in files:
					archiveFiles.append(os.path.join(root, file))
			
			filesystem.writeArchive(backupFile, archiveFiles, filesystem.dataDir)

	
	def saveToDisk(self, exitImminent=False):
		self.saveOldDay()
		
		for yearAndMonth, month in self.months.iteritems():
			if not month.empty:
				monthFileString = os.path.join(filesystem.dataDir, yearAndMonth + \
											filesystem.fileNameExtension)
				with open(monthFileString, 'w') as monthFile:
					monthContent = {}
					for dayNumber, day in month.days.iteritems():
						'do not add empty days'
						if not day.empty:
							monthContent[dayNumber] = day.content
					#month.prettyPrint()
					yaml.dump(monthContent, monthFile)
		
		self.showMessage('The content has been saved', error=False)
		
		if not exitImminent:
			'Update clouds'
		
		
	def loadAllMonthsFromDisk(self):
		for root, dirs, files in os.walk(filesystem.dataDir):
			for file in files:
				self.loadMonthFromDisk(os.path.join(root, file))
	
	
	def loadMonthFromDisk(self, path):
		fileName = os.path.basename(path)
		
		try:
			'Get Year and Month from /something/somewhere/2009-01.txt'
			yearAndMonth, extension = os.path.splitext(fileName)
			yearNumber, monthNumber = yearAndMonth.split('-')
			yearNumber = int(yearNumber)
			monthNumber = int(monthNumber)
			assert monthNumber in range(1,13)
		except Exception:
			print 'Error:', fileName, 'is an incorrect filename.'
			print 'filenames have to have the following form: 2009-01.txt ' + \
					'for January 2009 (yearWith4Digits-monthWith2Digits.txt)'
			return
		
		monthFileString = path
		
		try:
			'Try to read the contents of the file'
			with open(monthFileString, 'r') as monthFile:
				monthContents = yaml.load(monthFile)
				self.months[yearAndMonth] = Month(yearNumber, monthNumber, monthContents)
		except:
			'If that fails there is nothing to load, so just display an error message'
			print 'An Error occured while loading', fileName
		
		
	def loadMonth(self, date):
		
		yearAndMonth = dates.getYearAndMonthFromDate(date)
		
		'Selected month has not been loaded or created yet'
		if not self.months.has_key(yearAndMonth):
			self.months[yearAndMonth] = Month(date.year, date.month)
			
		return self.months[yearAndMonth]
	
	
	def saveOldDay(self):
		'Order is important'
		self.day.content = self.frame.categoriesTreeView.get_day_content()
		
		self.day.text = self.frame.get_day_text()
		self.frame.calendar.setDayEdited(self.date.day, not self.day.empty)
	
	
	def loadDay(self, newDate):
		oldDate = self.date
		self.date = newDate
		
		if not Month.sameMonth(newDate, oldDate):
			self.month = self.loadMonth(self.date)
		self.frame.set_date(self.month, self.date, self.day)
		
		
	def _getCurrentDay(self):
		return self.month.getDay(self.date.day)
	day = property(_getCurrentDay)
	
	
	def changeDate(self, newDate):
		if newDate == self.date:
			return
		
		self.saveOldDay()
		self.loadDay(newDate)
		
		
	def goToNextDay(self):
		self.changeDate(self.date + dates.oneDay)
		
		
	def goToPrevDay(self):
		self.changeDate(self.date - dates.oneDay)
			
			
	def showMessage(self, messageText, error=False, countdown=True):
		self.frame.statusbar.showText(messageText, error, countdown)
		print messageText
		
		
	def _getNodeNames(self):
		nodeNames = set([])
		for month in self.months.values():
			nodeNames |= set(month.nodeNames)
		return list(nodeNames)
	nodeNames = property(_getNodeNames)
	
	
	def _getTags(self):
		tags = set([])
		for month in self.months.values():
			tags |= set(month.tags)
		return list(tags)
	tags = property(_getTags)
	
	
	def search(self, text=None, category=None, tag=None):
		results = []
		for day in self.days:
			result = None
			if text:
				result = day.search_text(text)
			elif category:
				result = day.search_category(category)
			elif tag:
				result = day.search_tag(tag)
			
			if result:
				if category:
					results.extend(result)
				else:
					results.append(result)
					
		return results
	
	
	def _getAllEditedDays(self):
		days = []
		for month in self.months.values():
			daysInMonth = month.days.values()
			
			'Filter out days without content'
			daysInMonth = filter(lambda day: not day.empty, daysInMonth)
			days.extend(daysInMonth)
		return days
	days = property(_getAllEditedDays)
	
	
	def getTemplateEntry(self, date=None):
		if date is None:
			date = self.date
		weekDayNumber = date.weekday() + 1
		templateFileString = filesystem.getTemplateFile(weekDayNumber)
		try:
			with open(templateFileString, 'r') as templateFile:
				 lines = templateFile.readlines()
				 templateText = reduce(operator.add, lines, '')
		except IOError, Error:
			print 'Template File', weekDayNumber, 'not found'
			templateText = ''
		return templateText
		
	
	def getNumberOfWords(self):
		#def countWords(day1, day2):
		#	return day1.getNumberOfWords() + day2.getNumberOfWords()
		#return reduce(countWords, self.days, 0)
		numberOfWords = 0
		for day in self.days:
			numberOfWords += day.getNumberOfWords()
		return numberOfWords
	
	
	def getNumberOfEntries(self):
		return len(self.days)
	
	
	def getWordCountDict(self, type):
		wordDict = utils.ZeroBasedDict()
		for day in self.days:
			if type == 'word':
				words = day.words
			if type == 'category':
				words = day.nodeNames
			if type == 'tag':
				words = day.tags
			
			for word in words:
				wordDict[word.lower()] += 1
		return wordDict
			
	
	def addInstructionContent(self):
		instructionDayContent = {u'Cool Stuff': {u'Went to see the pope': None}, 
								 u'Ideas': {u'Invent Anti-Hangover-Machine': None},
								 u'Tags': {u'Work': None, u'Projects': None},
								 }
		
		self.day.content = instructionDayContent
		self.day.text = info.completeWelcomeText
		
		self.frame.set_date(self.month, self.date, self.day)

			

class Day(object):
	def __init__(self, month, dayNumber, dayContent = None):
		if dayContent == None:
			dayContent = {}
			
		self.month = month
		self.dayNumber = dayNumber
		self.content = dayContent
		
		self.searchResultLength = 50
	
	
	'Text'
	def _getText(self):
		if self.content.has_key('text'):
			return self.content['text']
		else:
		   return ''
		
	def _setText(self, text):
		self.content['text'] = text
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
		
		
	def _getTree(self):
		tree = self.content.copy()
		if tree.has_key('text'):
			del tree['text']
		return tree
	tree = property(_getTree)
	
	
	def _getNodeNames(self):
		return self.tree.keys()
	nodeNames = property(_getNodeNames)
		
		
	def _getTags(self):
		tags = []
		for category, listContent in self.getCategoryContentPairs().iteritems():
			if category.upper() == 'TAGS':
				tags.extend(listContent)
		return set(tags)
	tags = property(_getTags)
	
	
	def getCategoryContentPairs(self):
		'''
		Returns a list of (category, contentInCategoryAsList) pairs.
		contentInCategoryAsList can be empty
		'''
		originalTree = self.tree.copy()
		pairs = {}
		for category, content in originalTree.iteritems():
			entryList = []
			if content is not None:
				for entry, nonetype in content.iteritems():
					entryList.append(entry)
			pairs[category] = entryList
		return pairs
	
	
	def _getWords(self, withSpecialChars=False):
		if withSpecialChars:
			return self.text.split()
		
		wordList = self.text.split()
		realWords = []
		for word in wordList:
			word = word.strip(u'.|-!"/()=?*+~#_:;,<>^°´`{}[]')
			if len(word) > 0:
				realWords.append(word)
		return realWords
	words = property(_getWords)
	
	
	def getNumberOfWords(self):
		return len(self._getWords(withSpecialChars=True))
	
	
	def search_text(self, searchText):
		'''Case-insensitive search'''
		upCaseSearchText = searchText.upper()
		upCaseDayText = self.text.upper()
		occurence = upCaseDayText.find(upCaseSearchText)
		
		if occurence > -1:
			'searchText is in text'
			
			searchedStringInText = self.text[occurence:occurence + len(searchText)]
			
			spaceSearchLeftStart = max(0, occurence - self.searchResultLength/2)
			spaceSearchRightEnd = min(len(self.text), \
									occurence + len(searchText) + self.searchResultLength/2)
				
			resultTextStart = self.text.find(' ', spaceSearchLeftStart, occurence)
			resultTextEnd = self.text.rfind(' ', occurence + len(searchText), spaceSearchRightEnd)
			if resultTextStart == -1:
				resultTextStart = occurence - self.searchResultLength/2
			if resultTextEnd == -1:
				resultTextEnd = occurence + len(searchText) + self.searchResultLength/2
				
			'Add leading and trailing ... if appropriate'
			resultText = ''
			if resultTextStart > 0:
				resultText += '... '
				
			resultText += unicode.substring(self.text, resultTextStart, resultTextEnd).strip()
			
			'Make the searchedText bold'
			resultText = resultText.replace(searchedStringInText, '<b>' + searchedStringInText + '</b>')
			
			if resultTextEnd < len(self.text) - 1:
				resultText += ' ...'
				
			'Delete newlines'
			resultText = resultText.replace('\n', '')
				
			return (str(self), resultText)
		else:
			return None
		
		
	def search_category(self, searchCategory):
		results = []
		for category, content in self.getCategoryContentPairs().iteritems():
			if content:
				if searchCategory.upper() in category.upper():
					for entry in content:
						results.append((str(self), entry))
		return results
	
	
	def search_tag(self, searchTag):
		for category, contentList in self.getCategoryContentPairs().iteritems():
			if category.upper() == 'TAGS' and contentList:
				if searchTag.upper() in map(lambda x: x.upper(), contentList):
					firstWhitespace = self.text.find(' ', self.searchResultLength)
					
					if firstWhitespace == -1:
						'No whitespace found'
						textStart = self.text
					else:
						textStart = self.text[:firstWhitespace + 1]
						
					textStart = textStart.replace('\n', '')
					
					if len(textStart) < len(self.text):
						textStart += ' ...'
					return (str(self), textStart)
		return None
		
		
	def _date(self):
		return dates.getDateFromDay(self)
	date = property(_date)
	
	
	def __str__(self):
		dayNumberString = str(self.dayNumber).zfill(2)
		monthNumberString = str(self.month.monthNumber).zfill(2)
		yearNumberString = str(self.month.yearNumber)
			
		return yearNumberString + '-' + monthNumberString + '-' + dayNumberString

			

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
			return self.days[dayNumber]
		else:
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
	
	
	def _getTags(self):
		tags = set([])
		for day in self.days.values():
			tags |= set(day.tags)
		return tags
	tags = property(_getTags)
	
	
	def sameMonth(date1, date2):
		if date1 == None or date2 == None:
			return False
		return date1.month == date2.month and date1.year == date2.year
	sameMonth = staticmethod(sameMonth)
		
	
	
def main():
	utils.set_environment_vaiables()
	
	redNotebook = RedNotebook()
	utils.setup_signal_handlers(redNotebook)
	
	try:
		gtk.main()
	except KeyboardInterrupt:
		#print 'Interrupt'
		#redNotebook.saveToDisk()
		sys.exit()
		

main()
	
