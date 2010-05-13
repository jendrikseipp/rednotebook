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
	def __init__(self, month, day_number, day_content = None):
		if day_content == None:
			day_content = {}
			
		self.date = datetime.date(month.year_number, month.month_number, day_number)
			
		self.month = month
		self.day_number = day_number
		self.content = day_content
		
		self.search_result_length = 50
		
	#def __getattr__(self, name):
	#	return getattr(self.date, name)
	
	
	# Text
	def _get_text(self):
		'''
		Returns the day's text encoded as UTF-8
		decode means "decode from the standard ascii representation"
		'''
		if self.content.has_key('text'):
			return self.content['text'].decode('utf-8')
		else:
		   return ''
		
	def _set_text(self, text):
		self.content['text'] = text
	text = property(_get_text, _set_text)
	
	def _has_text(self):
		return len(self.text.strip()) > 0
	has_text = property(_has_text)
	
	
	def _is_empty(self):
		if len(self.content.keys()) == 0:
			return True
		elif len(self.content.keys()) == 1 and self.content.has_key('text') and not self.has_text:
			return True
		else:
			return False
	empty = property(_is_empty)
		
		
	def _get_tree(self):
		tree = self.content.copy()
		if tree.has_key('text'):
			del tree['text']
		return tree
	tree = property(_get_tree)
	
	
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
		for category, entries in same_day.get_category_content_pairs().items():
			for entry in entries:
				self.add_category_entry(category, entry)
	
	
	def _get_node_names(self):
		return self.tree.keys()
	node_names = property(_get_node_names)
		
		
	def _get_tags(self):
		tags = []
		for category, list_content in self.get_category_content_pairs().iteritems():
			if category.upper() == 'TAGS':
				tags.extend(list_content)
		return set(tags)
	tags = property(_get_tags)
	
	
	def get_category_content_pairs(self):
		'''
		Returns a dict of (category: content_in_category_as_list) pairs.
		content_in_category_as_list can be empty
		'''
		original_tree = self.tree.copy()
		pairs = {}
		for category, content in original_tree.iteritems():
			entry_list = []
			if content is not None:
				for entry, nonetype in content.iteritems():
					entry_list.append(entry)
			pairs[category] = entry_list
		return pairs
	
	
	def _get_words(self, with_special_chars=False):
		if with_special_chars:
			return self.text.split()
		
		word_list = self.text.split()
		real_words = []
		for word in word_list:
			word = word.strip(u'.|-!"/()=?*+~#_:;,<>^°´`{}[]')
			if len(word) > 0:
				real_words.append(word)
		return real_words
	words = property(_get_words)
	
	
	def get_number_of_words(self):
		return len(self._get_words(with_special_chars=True))
	
	
	def search_text(self, search_text):
		'''Case-insensitive search'''
		up_case_search_text = search_text.upper()
		up_case_day_text = self.text.upper()
		occurence = up_case_day_text.find(up_case_search_text)
		
		if occurence > -1:
			# search_text is in text
			
			searched_string_in_text = self.text[occurence:occurence + len(search_text)]
			
			space_search_left_start = max(0, occurence - self.search_result_length/2)
			space_search_right_end = min(len(self.text), \
									occurence + len(search_text) + self.search_result_length/2)
				
			result_text_start = self.text.find(' ', space_search_left_start, occurence)
			result_text_end = self.text.rfind(' ', \
						occurence + len(search_text), space_search_right_end)
			if result_text_start == -1:
				result_text_start = occurence - self.search_result_length/2
			if result_text_end == -1:
				result_text_end = occurence + len(search_text) + self.search_result_length/2
				
			# Add leading and trailing ... if appropriate
			result_text = ''
			if result_text_start > 0:
				result_text += '... '
				
			result_text += unicode.substring(self.text, result_text_start, result_text_end).strip()
			
			# Make the searched_text bold
			result_text = result_text.replace(searched_string_in_text, \
									'<b>' + searched_string_in_text + '</b>')
			
			if result_text_end < len(self.text) - 1:
				result_text += ' ...'
				
			# Delete newlines
			result_text = result_text.replace('\n', '')
				
			return (str(self), result_text)
		else:
			return None
		
		
	def search_category(self, search_category):
		results = []
		for category, content in self.get_category_content_pairs().iteritems():
			if content:
				if search_category.upper() in category.upper():
					for entry in content:
						results.append((str(self), entry))
		return results
	
	
	def search_tag(self, search_tag):
		for category, content_list in self.get_category_content_pairs().iteritems():
			if category.upper() == 'TAGS' and content_list:
				if search_tag.upper() in map(lambda x: x.upper(), content_list):
					first_whitespace = self.text.find(' ', self.search_result_length)
					
					if first_whitespace == -1:
						# No whitespace found
						text_start = self.text
					else:
						text_start = self.text[:first_whitespace + 1]
						
					text_start = text_start.replace('\n', '')
					
					if len(text_start) < len(self.text):
						text_start += ' ...'
					return (str(self), text_start)
		return None
	
	
	def __str__(self):
		day_number_string = str(self.day_number).zfill(2)
		month_number_string = str(self.month.month_number).zfill(2)
		year_number_string = str(self.month.year_number)
			
		return year_number_string + '-' + month_number_string + '-' + day_number_string

	
	def __cmp__(self, other):
		return cmp(self.date, other.date)
			

class Month(object):
	def __init__(self, year_number, month_number, month_content = None):
		if month_content == None:
			month_content = {}
		
		self.year_number = year_number
		self.month_number = month_number
		self.days = {}
		for day_number, day_content in month_content.iteritems():
			self.days[day_number] = Day(self, day_number, day_content)
			
		self.edited = False
	
	
	def get_day(self, day_number):
		if self.days.has_key(day_number):
			return self.days[day_number]
		else:
			new_day = Day(self, day_number)
			self.days[day_number] = new_day
			return new_day
		
		
	def set_day(self, day_number, day):
		self.days[day_number] = day
		
		
	def __str__(self):
		res = 'Month %s %s\n' % (self.year_number, self.month_number)
		for day_number, day in self.days.iteritems():
			res += '%s: %s\n' % (day_number, day.text)
		return res
		
		
	def _is_empty(self):
		for day in self.days.values():
			if not day.empty:
				return False
		return True
	empty = property(_is_empty)
	
	
	def _get_node_names(self):
		node_names = set([])
		for day in self.days.values():
			node_names |= set(day.node_names)
		return node_names
	node_names = property(_get_node_names)
	
	
	def _get_tags(self):
		tags = set([])
		for day in self.days.values():
			tags |= set(day.tags)
		return tags
	tags = property(_get_tags)
	
	
	def same_month(date1, date2):
		if date1 == None or date2 == None:
			return False
		return date1.month == date2.month and date1.year == date2.year
	same_month = staticmethod(same_month)
	
	def __cmp__(self, other):
		return cmp((self.year_number, self.month_number), \
					(other.year_number, other.month_number))
