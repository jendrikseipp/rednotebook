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

from __future__ import division

from rednotebook.util import dates

class Statistics(object):
	def __init__(self, redNotebook):
		self.redNotebook = redNotebook
		
	def getNumberOfWords(self):
		numberOfWords = 0
		for day in self.redNotebook.days:
			numberOfWords += day.getNumberOfWords()
		return numberOfWords
	
	def get_number_of_distinct_words(self):
		word_count_dict = self.redNotebook.getWordCountDict('word')
		number_of_distinct_words = len(word_count_dict)
		return number_of_distinct_words
	
	def getNumberOfChars(self):
		numberOfChars = 0
		for day in self.redNotebook.days:
			numberOfChars += len(day.text)
		return numberOfChars
	
	def get_number_of_usage_days(self):
		'''Returns the timespan between the first and last entry'''
		sorted_days = self.redNotebook.sortedDays
		if len(sorted_days) <= 1:
			return len(sorted_days)
		first_day = sorted_days[0]
		last_day = sorted_days[-1]
		timespan = last_day.date - first_day.date
		return abs(timespan.days) + 1
	
	def getNumberOfEntries(self):
		return len(self.redNotebook.days)
	
	def get_edit_percentage(self):
		total = self.get_number_of_usage_days()
		edited = self.getNumberOfEntries()
		if total == 0:
			return 0
		percent = round(100 * edited / total, 2) 
		return '%s%%' % percent
	
	def get_average_number_of_words(self):
		if self.getNumberOfEntries() == 0:
			return 0
		return round(self.getNumberOfWords() / self.getNumberOfEntries(), 2)
	
	def _getHTMLRow(self, key, value):
		return '<tr align="left">' +\
				'<td bgcolor="#e7e7e7">&nbsp;&nbsp;' + key + '</td>' +\
				'<td bgcolor="#aaaaaa">&nbsp;&nbsp;<b>' + str(value) + '</b></td>' + \
				'</tr>'
		
	@property
	def overall_pairs(self):
		return [
				['Words', self.getNumberOfWords()],
				['Distinct Words', self.get_number_of_distinct_words()],
				['Entries', self.getNumberOfEntries()],
				['Letters', self.getNumberOfChars()],
				['Days between first and last Entry', self.get_number_of_usage_days()],
				['Average number of Words', self.get_average_number_of_words()],
				['Percentage of edited Days', self.get_edit_percentage()],
				]
		
	@property
	def day_pairs(self):
		day = self.redNotebook.day
		return [
				['Words', day.getNumberOfWords()],
				['Lines', len(day.text.splitlines())],
				['Letters', len(day.text)],
				]
	
	def getStatsHTML(self):
		self.redNotebook.saveOldDay()
		page = '<html><body bgcolor="#8e8e95"><table cellspacing="5" border="0" width="400">\n'
		stats = self.pairs
		for key, value in stats:
			page += self._getHTMLRow(key, value)
			
		page += '</body></table></html>'
		return page
	
	def show_dialog(self, dialog):
		self.redNotebook.saveOldDay()
		
		day_store = dialog.day_list.get_model()
		day_store.clear()
		for pair in self.day_pairs:
			day_store.append(pair)
		
		overall_store = dialog.overall_list.get_model()
		overall_store.clear()
		for pair in self.overall_pairs:
			overall_store.append(pair)
			
		dialog.show_all()
		dialog.run()
		dialog.hide()

		