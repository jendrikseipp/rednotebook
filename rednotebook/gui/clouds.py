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

import logging

import gtk

from rednotebook.gui.browser import HtmlView
from rednotebook.util import unicode


def word_count_dict_to_html(wordCountDict, type, ignore_list, include_list):
	logging.debug('Turning the wordCountDict into html')
	logging.debug('Length wordCountDict: %s' % len(wordCountDict))
	
	sortedDict = sorted(wordCountDict.items(), key=lambda (word, freq): freq)
	
	if type == 'word':
		# filter short words
		include_list = map(str.lower, include_list)
		get_long_words = lambda (word, freq): len(word) > 4 or word.lower() in include_list
		sortedDict = filter(get_long_words, sortedDict)
		logging.debug('Filtered short words. Length wordCountDict: %s' % len(sortedDict))
		
	# filter words in ignore_list
	sortedDict = filter(lambda (word, freq): word.lower() not in ignore_list, sortedDict)
	logging.debug('Filtered blacklist words. Length wordCountDict: %s' % len(sortedDict))
	
	oftenUsedWords = []
	numberOfWords = 42
	
	'''
	only take the longest words. If there are less words than n, 
	len(sortedDict) words are returned
	'''
	cloud_words = sortedDict[-numberOfWords:]
	logging.debug('Selected most frequent words. Length CloudWords: %s' % len(cloud_words))
	
	if len(cloud_words) < 1:
		return [], ''
	
	minCount = cloud_words[0][1]
	maxCount = cloud_words[-1][1]
	
	logging.debug('Min word count: %s, Max word count: %s' % (minCount, maxCount))
	
	deltaCount = maxCount - minCount
	if deltaCount == 0:
		deltaCount = 1
	
	minFontSize = 10
	maxFontSize = 50
	
	fontDelta = maxFontSize - minFontSize
	
	# sort words with unicode sort function
	cloud_words.sort(key=lambda (word, count): unicode.coll(word))
	
	logging.debug('Sorted cloud words. Length CloudWords: %s' % len(cloud_words))
	
	htmlElements = []
	
	
	css = '''\
	<style type="text/css">
		body {
			font-family: sans-serif;
			text-align: center;
		}
		a:link { color:black; text-decoration:none; }
		a:visited { color:black; text-decoration:none; }
		a:focus { color:black; text-decoration:none; }
		a:hover { color:black; text-decoration:none; }
		a:active { color:black; text-decoration:none; }
	</style>'''
	
	for index, (word, count) in enumerate(cloud_words):
		fontFactor = (count - minCount) / deltaCount
		fontSize = int(minFontSize + fontFactor * fontDelta)
		
		htmlElements.append('<a href="search/%s">' 
							'<span style="font-size:%spx">%s</span></a>' \
							% (index, fontSize, word) + \
							#Add some whitespace
							'&#xA0;')
		
	#random.shuffle(htmlElements)
	
	htmlBody = '<body>' + '\n'.join(htmlElements) + '\n</body>\n'
	htmlDoc = '<html><head>' + css + '</head>' + htmlBody + '</html>'
	
	return (cloud_words, htmlDoc)



class Cloud(HtmlView):
	def __init__(self, redNotebook):
		HtmlView.__init__(self)
		
		self.redNotebook = redNotebook
		
		self.update_lists()
		
		self.webview.connect("hovering-over-link", self.on_hovering_over_link)
		self.webview.connect('populate-popup', self.on_populate_popup)
		
		self.set_type(0, init=True)
		self.last_hovered_word = None
		
	def set_type(self, type_int, init=False):
		self.type_int = type_int
		self.type = ['word', 'category', 'tag'][type_int]
		if not init:
			self.update(force_update=True)
			
	def update_lists(self):
		config = self.redNotebook.config
		
		default_ignore_list = _('filter, these, comma, separated, words')
		self.ignore_list = config.read_list('cloudIgnoreList', default_ignore_list)
		self.ignore_list = map(str.lower, self.ignore_list)
		logging.info('Cloud ignore list: %s' % self.ignore_list)
		
		default_include_list = _('mtv, spam, work, job, play')
		self.include_list = config.read_list('cloudIncludeList', default_include_list)
		self.include_list = map(str.lower, self.include_list)
		logging.info('Cloud include list: %s' % self.include_list)
		
		
	def update(self, force_update=False):
		if self.redNotebook.frame is None:
			return
		
		logging.debug('Update the cloud (Type: %s, Force: %s)' % (self.type, force_update))
		
		# Do not update the cloud with words as it requires a lot of searching		
		if self.type == 'word' and not force_update:
			return
		
		self.redNotebook.saveOldDay()
		
		wordCountDict = self.redNotebook.getWordCountDict(self.type)
		logging.debug('Retrieved WordCountDict. Length: %s' % len(wordCountDict))
		
		self.tagCloudWords, html = \
			word_count_dict_to_html(wordCountDict, self.type, \
									self.ignore_list, self.include_list)
		logging.debug('%s cloud words found' % len(self.tagCloudWords))
		
		self.load_html(html)
		self.last_hovered_word = None
		
		logging.debug('Cloud updated')
		
		
	def on_navigate(self, webview, frame, request):
		'''
		Called when user clicks on a cloud word
		'''
		if self.loading_html:
			# Keep processing
			return False
			
		uri = request.get_uri()
		logging.info('Clicked URI "%s"' % uri)
		
		self.redNotebook.saveOldDay()
		
		# uri has the form "something/somewhere/search/searchIndex"
		if 'search' in uri:
			# searchIndex is the part after last slash
			searchIndex = int(uri.split('/')[-1])
			searchText, count = self.tagCloudWords[searchIndex]
			
			self.redNotebook.frame.searchTypeBox.set_active(self.type_int)
			self.redNotebook.frame.searchBox.set_active_text(searchText)
			self.redNotebook.frame.searchNotebook.set_current_page(0)
			
			# returning True here stops loading the document
			return True
			
			
	def on_button_press(self, webview, event):
		'''
		Here we want the context menus
		'''
		# keep processing
		return False
		
	
	def on_hovering_over_link(self, webview, title, uri):
		'''
		We want to save the last hovered link to be able to add it
		to the context menu when the user right-clicks the next time
		'''
		if uri:
			searchIndex = int(uri.split('/')[-1])
			searchText, count = self.tagCloudWords[searchIndex]
			self.last_hovered_word = searchText
			
			
	def on_populate_popup(self, webview, menu):
		'''
		Called when the cloud's popup menu is created
		'''
		
		# remove normal menu items
		children = menu.get_children()
		for child in children:
			menu.remove(child)
			
		if self.last_hovered_word:
			label = _('Hide "%s" from clouds') % self.last_hovered_word
			ignore_menu_item = gtk.MenuItem(label)
			ignore_menu_item.show()
			menu.prepend(ignore_menu_item)
			ignore_menu_item.connect('activate', self.on_ignore_menu_activate, self.last_hovered_word)
		
	def on_ignore_menu_activate(self, menu_item, selected_word):
		logging.info('"%s" will be hidden from clouds' % selected_word)
		self.ignore_list.append(selected_word)
		self.redNotebook.config.write_list('cloudIgnoreList', self.ignore_list)
		self.update(force_update=True)
