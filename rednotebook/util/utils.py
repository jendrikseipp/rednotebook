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

from __future__ import with_statement
import sys
import signal
import random
import operator
import os
from threading import Thread
from urllib2 import urlopen, URLError
import webbrowser
import unicode


import filesystem

def printError(message):
	print '\nERROR:', message

def floatDiv(a, b):
	return float(float(a)/float(b))

#-----------DICTIONARY-----------------------------

class ZeroBasedDict(dict):
	def __getitem__(self, key):
		if key in self:
			return dict.__getitem__(self, key)
		else:
			return 0

def getSortedDictByKeys(adict):
	'''Returns a sorted list of (key, value) pairs, sorted by key'''
	items = adict.items()
	items.sort()
	return items
   
def sortDictByKeys(adict, sortFunction=None):
	'''Returns a sorted list of values, sorted by key'''
	keys = adict.keys()
	if sortFunction is None:
		keys.sort()
	else:
		keys.sort(key=sortFunction)
	return map(adict.get, keys)

def sortDictByValues(adict):
	'''
	Returns a sorted list of (key, value) pairs, sorted by value
	'''
	
	'''items returns a list of (key, value) pairs'''
	items = adict.items()
	items.sort(lambda (key1, value1), (key2, value2): cmp(value1, value2))
	return items

def sort_pair_list_by_keys(aList, sortFunction=None):
	'''Returns a sorted list of values, sorted by key'''
	def compare_two_pairs(pair1, pair2):
		key1, value1 = pair1
		key2, value2 = pair2
		
	#return sort(lambda)
	keys = adict.keys()
	if sortFunction is None:
		keys.sort()
	else:
		keys.sort(key=sortFunction)
	return map(adict.get, keys)


def restrain(valueToRestrain, range):
	rangeStart, rangeEnd = range
	if valueToRestrain < rangeStart:
		valueToRestrain = rangeStart
	if valueToRestrain > rangeEnd:
		entryNumber = rangeEnd
	return valueToRestrain


def getHtmlDocFromWordCountDict(wordCountDict, type):
	sortedDict = sortDictByValues(wordCountDict)
	
	if type == 'word':
		'filter short words'
		sortedDict = filter(lambda x: len(x[0]) > 4, sortedDict)
	
	oftenUsedWords = []
	numberOfWords = 42
	
	'''
	only take the longest words. If there are less words than n, 
	len(longWords) words are returned
	'''
	tagCloudWords = sortedDict[-numberOfWords:]
	if len(tagCloudWords) < 1:
		return [], ''
	
	minCount = tagCloudWords[0][1]
	maxCount = tagCloudWords[-1][1]
	
	deltaCount = maxCount - minCount
	if deltaCount == 0:
		deltaCount = 1
	
	minFontSize = 10
	maxFontSize = 50
	
	fontDelta = maxFontSize - minFontSize
	
	'delete count information from word list'
	tagCloudWords = map(lambda (word, count): word, tagCloudWords)
	
	'search words with unicode sort function'
	tagCloudWords.sort(key=unicode.coll)
	
	htmlElements = []
	
	htmlHead = 	'<body><div style="text-align:center; font-family: sans-serif">'
	htmlTail = '</div></body>'
	
	for wordIndex in range(len(tagCloudWords)):
		count = wordCountDict.get(tagCloudWords[wordIndex])
		fontFactor = floatDiv((count - minCount), (deltaCount))
		fontSize = int(minFontSize + fontFactor * fontDelta)
		
		htmlElements.append('<a href="search/' + str(wordIndex) + '">' + \
								'<span style="font-size:' + str(int(fontSize)) + 'px">' + \
									tagCloudWords[wordIndex] + \
								'</span>' + \
							'</a>' + \
							#Add some whitespace
							'<span style="font-size:5px; color:white"> _ </span>' + \
							#'&nbsp;'*3 + 
							'\n')
		
	#random.shuffle(htmlElements)	
	
	htmlDoc = htmlHead 
	htmlDoc += reduce(operator.add, htmlElements, '')
	htmlDoc += htmlTail
	
	return (tagCloudWords, htmlDoc)


def set_environment_variables(config):
	variables = {	'LD_LIBRARY_PATH': '/usr/lib/xulrunner-1.9',
					 'MOZILLA_FIVE_HOME': '/usr/lib/xulrunner-1.9',
				}
	
	for variable, value in variables.iteritems():
		if not os.environ.has_key(variable) and config.has_key(variable):
			# Only add environment variable if it does not exist yet
			os.environ[variable] = config.read(variable, default=value)
			print variable, 'set to', value
			
	for variable in variables.keys():
		if os.environ.has_key(variable):
			print 'The environment variable', variable, 'has value', os.environ.get(variable)
		else:
			print 'There is no environment variable called', variable


def setup_signal_handlers(redNotebook):
	'''
	Catch abnormal exits of the program and save content to disk
	Look in signal man page for signal names
	
	SIGKILL cannot be caught
	SIGINT is caught again by KeyboardInterrupt
	'''
	
	signals = []
	
	try:
		signals.append(signal.SIGHUP)  #Terminal closed, Parent process dead
	except AttributeError: 
		pass
	try:
		signals.append(signal.SIGINT)  #Interrupt from keyboard (CTRL-C)
	except AttributeError: 
		pass
	try:
		signals.append(signal.SIGQUIT) #Quit from keyboard
	except AttributeError: 
		pass
	try:
		signals.append(signal.SIGABRT) #Abort signal from abort(3)
	except AttributeError: 
		pass
	try:
		signals.append(signal.SIGTERM) #Termination signal
	except AttributeError: 
		pass
	try:
		signals.append(signal.SIGTSTP) #Stop typed at tty
	except AttributeError: 
		pass
	
	
	def signal_handler(signum, frame):
		print 'Program was abnormally aborted with signal', signum
		redNotebook.saveToDisk()
		sys.exit()

	
	print 'Connected Signals:',
	
	for signalNumber in signals:
		try:
			print signalNumber,
			signal.signal(signalNumber, signal_handler)
		except RuntimeError:
			print '\nFalse Signal Number:', signalNumber
	print
				

def get_new_version_number(currentVersion):
	newVersion = None
	
	try:
		projectXML = urlopen('http://freshmeat.net/projects-xml/rednotebook/rednotebook.xml').read()
		tag = '<latest_release_version>'
		position = projectXML.find(tag)
		newVersion = projectXML[position + len(tag):position + len(tag) + 5]
		print newVersion, 'is newest version'
	except URLError:
		print 'New version info could not be read'
	
	if newVersion:
		if newVersion > currentVersion:
			return newVersion
	
	return None


def check_new_version(mainFrame, currentVersion, startup=False):
	if get_new_version_number(currentVersion):
		mainFrame.show_new_version_dialog()
	elif not startup:
		mainFrame.show_no_new_version_dialog()
		
		
def write_file(content, filename):
	filename = os.path.join(filesystem.tempDir, filename)
	with open(filename, 'w') as file:
		file.write(content)
		

def show_html_in_browser(html, filename='tmp.html'):
	write_file(html, filename)
	filename = os.path.join(filesystem.tempDir, filename)
	
	html_file = os.path.abspath(filename)
	html_file = 'file://' + html_file
	webbrowser.open(html_file)
	
	