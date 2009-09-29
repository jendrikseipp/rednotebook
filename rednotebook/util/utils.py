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
from optparse import IndentedHelpFormatter
import textwrap

import filesystem


def getHtmlDocFromWordCountDict(wordCountDict, type, ignore_list, include_list):
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
		redNotebook.exit()

	
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
	

class IndentedHelpFormatterWithNL(IndentedHelpFormatter):
	'''
	Code taken from "Dan"
	http://groups.google.com/group/comp.lang.python/browse_frm/thread/e72deee779d9989b/
	
	This class preserves newlines in the optparse help
	'''
	def format_description(self, description):
		if not description: return ""
		desc_width = self.width - self.current_indent
		indent = " "*self.current_indent
		# the above is still the same
		bits = description.split('\n')
		formatted_bits = [
			textwrap.fill(bit,
				desc_width,
				initial_indent=indent,
				subsequent_indent=indent)
			for bit in bits]
		result = "\n".join(formatted_bits) + "\n"
		return result

	def format_option(self, option):
		# The help for each option consists of two parts:
		#	 * the opt strings and metavars
		#	 eg. ("-x", or "-fFILENAME, --file=FILENAME")
		#	 * the user-supplied help string
		#	 eg. ("turn on expert mode", "read data from FILENAME")
		#
		# If possible, we write both of these on the same line:
		#	 -x		turn on expert mode
		#
		# But if the opt string list is too long, we put the help
		# string on a second line, indented to the same column it would
		# start in if it fit on the first line.
		#	 -fFILENAME, --file=FILENAME
		#			 read data from FILENAME
		result = []
		opts = self.option_strings[option]
		opt_width = self.help_position - self.current_indent - 2
		if len(opts) > opt_width:
			opts = "%*s%s\n" % (self.current_indent, "", opts)
			indent_first = self.help_position
		else: # start help on same line as opts
			opts = "%*s%-*s	" % (self.current_indent, "", opt_width, opts)
			indent_first = 0
		result.append(opts)
		if option.help:
			help_text = option.help
			# Everything is the same up through here
			help_lines = []
			help_text = "\n".join([x.strip() for x in
								help_text.split("\n")])
			for para in help_text.split("\n\n"):
				help_lines.extend(textwrap.wrap(para, self.help_width))
				if len(help_lines):
					# for each paragraph, keep the double newlines..
					help_lines[-1] += "\n"
					# Everything is the same after here
			result.append("%*s%s\n" % (
				indent_first, "", help_lines[0]))
			result.extend(["%*s%s\n" % (self.help_position, "", line)
				for line in help_lines[1:]])
		elif opts[-1] != "\n":
			result.append("\n")
		return "".join(result) 
