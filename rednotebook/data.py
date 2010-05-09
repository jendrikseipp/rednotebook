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

import datetime
import logging

class Day(object):
	def __init__(self, month, dayNumber, dayContent = None):
		if dayContent == None:
			dayContent = {}
			
		self.date = datetime.date(month.yearNumber, month.monthNumber, dayNumber)
			
		self.month = month
		self.dayNumber = dayNumber
		self.content = dayContent
		
		self.searchResultLength = 50
		
	#def __getattr__(self, name):
	#	return getattr(self.date, name)
	
	
	# Text
	def _getText(self):
		'''
		Returns the day's text encoded as UTF-8
		decode means "decode from the standard ascii representation"
		'''
		if self.content.has_key('text'):
			return self.content['text'].decode('utf-8')
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
	
	
	def add_category_entry(self, category, entry):
		if self.content.has_key(category):
			self.content[category][entry] = None
		else:
			self.content[category] = {entry: None}
			
	
	def merge(self, same_day):
		assert self.date == same_day.date
		
		# Merge texts
		text1 = self.text.strip() 
		text2 = same_day.text.strip()
		if text2 in text1:
			# self.text contains the other text
			pass
		elif text1 in text2:
			# The other text contains contains self.text
			self.text = same_day.text
		else:
			self.text += '\n\n' + same_day.text
			
		# Merge categories
		for category, entries in same_day.getCategoryContentPairs().items():
			for entry in entries:
				self.add_category_entry(category, entry)
	
	
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
		Returns a dict of (category: contentInCategoryAsList) pairs.
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
			# searchText is in text
			
			searchedStringInText = self.text[occurence:occurence + len(searchText)]
			
			spaceSearchLeftStart = max(0, occurence - self.searchResultLength/2)
			spaceSearchRightEnd = min(len(self.text), \
									occurence + len(searchText) + self.searchResultLength/2)
				
			resultTextStart = self.text.find(' ', spaceSearchLeftStart, occurence)
			resultTextEnd = self.text.rfind(' ', \
						occurence + len(searchText), spaceSearchRightEnd)
			if resultTextStart == -1:
				resultTextStart = occurence - self.searchResultLength/2
			if resultTextEnd == -1:
				resultTextEnd = occurence + len(searchText) + self.searchResultLength/2
				
			# Add leading and trailing ... if appropriate
			resultText = ''
			if resultTextStart > 0:
				resultText += '... '
				
			resultText += unicode.substring(self.text, resultTextStart, resultTextEnd).strip()
			
			# Make the searchedText bold
			resultText = resultText.replace(searchedStringInText, \
									'<b>' + searchedStringInText + '</b>')
			
			if resultTextEnd < len(self.text) - 1:
				resultText += ' ...'
				
			# Delete newlines
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
						# No whitespace found
						textStart = self.text
					else:
						textStart = self.text[:firstWhitespace + 1]
						
					textStart = textStart.replace('\n', '')
					
					if len(textStart) < len(self.text):
						textStart += ' ...'
					return (str(self), textStart)
		return None
	
	
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
			
		self.edited = False
	
	
	def getDay(self, dayNumber):
		if self.days.has_key(dayNumber):
			return self.days[dayNumber]
		else:
			newDay = Day(self, dayNumber)
			self.days[dayNumber] = newDay
			return newDay
		
		
	def setDay(self, dayNumber, day):
		self.days[dayNumber] = day
		
		
	def __str__(self):
		res = 'Month %s %s\n' % (self.yearNumber, self.monthNumber)
		for dayNumber, day in self.days.iteritems():
			res += '%s: %s\n' % (dayNumber, day.text)
		return res
		
		
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
