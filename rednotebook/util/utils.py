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

from __future__ import with_statement, division

import sys
import signal
import random
import operator
from operator import itemgetter
import os
from urllib2 import urlopen, URLError
import webbrowser
import unicode
import logging

import filesystem


def getHtmlDocFromWordCountDict(wordCountDict, type, ignore_list):
	logging.debug('Turning the wordCountDict into html')
	logging.debug('Length wordCountDict: %s' % len(wordCountDict))
	
	sortedDict = sorted(wordCountDict.items(), key=lambda (word, freq): freq)
	
	if type == 'word':
		# filter short words
		sortedDict = filter(lambda (word, freq): len(word) > 4, sortedDict)
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
	
	htmlHead = 	'<body><div style="text-align:center; font-family: sans-serif">\n'
	htmlTail = '</div></body>'
	
	for index, (word, count) in enumerate(cloud_words):
		fontFactor = (count - minCount) / deltaCount
		fontSize = int(minFontSize + fontFactor * fontDelta)
		
		htmlElements.append('<a href="search/%s">' 
								'<span style="font-size:%spx">%s</span></a>' \
								% (index, fontSize, word) + \
									
							#Add some whitespace (previously &#xA0;)
							'<span> </span>')
		
	#random.shuffle(htmlElements)
	
	htmlDoc = htmlHead
	htmlDoc += '\n'.join(htmlElements) + '\n'
	htmlDoc += htmlTail
	
	return (cloud_words, htmlDoc)


def set_environment_variables(config):
	variables = {}
	
	for variable, value in variables.iteritems():
		if not os.environ.has_key(variable): #and config.has_key(variable):
			# Only add environment variable if it does not exist yet
			os.environ[variable] = config.read(variable, default=value)
			logging.info('%s set to %s' % (variable, value))
			
	for variable in variables.keys():
		if os.environ.has_key(variable):
			logging.info('The environment variable %s has value %s' % (variable, os.environ.get(variable)))
		else:
			logging.info('There is no environment variable called %s' % variable)
	
			
def redirect_output_to_file(logfile_path):
	'''
	Changes stdout and stderr to a file.
	Disables both streams if logfile_path is None or cannot be opened.
	
	This is necessary to suppress the error messages on Windows when closing 
	the application.
	'''
	assert sys.platform == 'win32'
	
	if logfile_path is None:
		logfile = None
	else:
		try:
			logfile = open(logfile_path, 'w')
		except IOError:
			logging.info('logfile %s could not be found, disabling output' % logfile_path)
			logfile = None
	
	sys.stdout = logfile
	sys.stderr = logfile


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
		logging.info('Program was abnormally aborted with signal %s' % signum)
		redNotebook.saveToDisk()
		sys.exit()

	
	msg = 'Connected Signals: '
	
	for signalNumber in signals:
		try:
			msg += str(signalNumber) + ' '
			signal.signal(signalNumber, signal_handler)
		except RuntimeError:
			msg += '\nFalse Signal Number: ' + signalNumber
	
	logging.info(msg)
				

def get_new_version_number(currentVersion):
	newVersion = None
	
	try:
		projectXML = urlopen('http://www.gnomefiles.org/app.php/RedNotebook').read()
		tag = 'version '
		position = projectXML.upper().find(tag.upper())
		newVersion = projectXML[position + len(tag):position + len(tag) + 5]
		logging.info('%s is newest version. You have version %s' % (newVersion, currentVersion))
	except URLError:
		logging.error('New version info could not be read')
	
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
	assert os.path.isabs(filename)
	with open(filename, 'w') as file:
		file.write(content)
		

def show_html_in_browser(html, filename):
	write_file(html, filename)
	
	html_file = os.path.abspath(filename)
	html_file = 'file://' + html_file
	webbrowser.open(html_file)
	
class StreamDuplicator(object):
	def __init__(self, default, duplicates):
		if not type(duplicates) == list:
			duplicates = [duplicates]
		self.duplicates = duplicates
		self.default = default
		
	@property
	def streams(self):
		return [self.default] + self.duplicates
	
	def write(self, str):
		#print 'write', self.default, self.duplicates, self.streams
		for stream in self.streams:
			#print stream
			stream.write(str)
		
	def flush(self):
		for stream in self.streams:
			stream.flush()
			
	#def close(self):
	#	for stream in self.streams():
	#		self.stream.close()
	


