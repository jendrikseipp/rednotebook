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

import os
import zipfile
import subprocess
import logging
import codecs



#from http://www.py2exe.org/index.cgi/HowToDetermineIfRunningFromExe
import imp, os, sys

def main_is_frozen():
	return (hasattr(sys, "frozen") or # new py2exe
		hasattr(sys, "importers") # old py2exe
		or imp.is_frozen("__main__")) # tools/freeze

def get_main_dir():
	if main_is_frozen():
		return os.path.dirname(sys.executable)
	return os.path.dirname(sys.argv[0])
#--------------------------------------------------------------------------------------------------------


if not main_is_frozen():
	appDir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
	appDir = os.path.normpath(appDir)
else:
	appDir = get_main_dir()
	


imageDir = os.path.join(appDir, 'images')
frameIconDir = os.path.join(imageDir, 'redNotebookIcon')
filesDir = os.path.join(appDir, 'files')
guiDir = os.path.join(appDir, 'gui')

userHomeDir = os.path.expanduser('~')

#redNotebookUserDir = os.path.join(userHomeDir, '.rednotebook')
#templateDir = os.path.join(redNotebookUserDir, 'templates')

#defaultDataDir = os.path.join(redNotebookUserDir, 'data')
#dataDir = defaultDataDir

fileNameExtension = '.txt'

#configFile = os.path.join(redNotebookUserDir, 'configuration.cfg')
#logFile = os.path.join(redNotebookUserDir, 'rednotebook.log')

#last_pic_dir = userHomeDir
#last_file_dir = userHomeDir


class Filenames(dict):
	'''
	Dictionary for dirnames and filenames
	'''
	def __init__(self, config):
		for key, value in globals().items():
			# Exclude "get_main_dir()"
			if key.lower().endswith('dir') and type(value) is str:
				value = os.path.abspath(value)
				self[key] = value
				setattr(self, key, value)
		
		self.portable = bool(config.read('portable', 0))
		
		self.redNotebookUserDir = self.get_user_dir(config)
		
		self.dataDir = self.defaultDataDir
		
		# Is this the first run of RedNotebook?
		self.is_first_start = not os.path.exists(self.redNotebookUserDir)
			
		# Assert that all dirs and files are in place so that logging can take start
		makeDirectories([self.redNotebookUserDir, self.dataDir, self.templateDir,
						self.tempDir])
		makeFiles([(self.configFile, ''), (self.logFile, '')])
		
		self.last_pic_dir = self.userHomeDir
		self.last_file_dir = self.userHomeDir
		
	def get_user_dir(self, config):
		custom = config.read('userDir', '')
		
		if custom:
			# If a custom user dir has been set,
			# construct the absolute path (if not absolute already) 
			# and use it
			if not os.path.isabs(custom):
				custom = os.path.join(self.appDir, custom)
			user_dir = custom
		else:
			if self.portable:
				user_dir = os.path.join(self.appDir, 'user')
			else:
				user_dir = os.path.join(self.userHomeDir, '.rednotebook')
		
		return user_dir
		
		

		
	def __getattribute__(self, attr):
		user_paths = dict((('templateDir', 'templates'),
						('tempDir', 'tmp'),
						('defaultDataDir', 'data'),
						('configFile', 'configuration.cfg'),
						('logFile', 'rednotebook.log'),
						))
							
		if attr in user_paths:
			return os.path.join(self.redNotebookUserDir, user_paths.get(attr))
		
		return dict.__getattribute__(self, attr)
	


def makeDirectory(dir):
	if not os.path.exists(dir):
		os.makedirs(dir)
		
def makeDirectories(dirs):
	for dir in dirs:
		makeDirectory(dir)
		
def makeFile(file, content=''):
	if not os.path.exists(file):
		with codecs.open(file, 'w', encoding='utf-8') as f:
			f.write(content)
			
def makeFiles(fileContentPairs):
	for file, content in fileContentPairs:
		if len(content) > 0:
			makeFile(file, content)
		else:
			makeFile(file)
			
def make_file_with_dir(file, content):
	dir = os.path.dirname(file)
	makeDirectory(dir)
	makeFile(file, content)
	
def get_relative_path(from_dir, to_dir):
	'''
	Try getting the relative path from from_dir to to_dir
	The relpath method is only available in python >= 2.6
	if we run python <= 2.5, return the absolute path to to_dir
	'''
	if getattr(os.path, 'relpath', None):
		return os.path.relpath(to_dir, from_dir)
	else:
		return to_dir
	
def writeArchive(archiveFileName, files, baseDir='', arcBaseDir=''):
	"""
	use baseDir for relative filenames, in case you don't 
	want your archive to contain '/home/...'
	"""
	archive = zipfile.ZipFile(archiveFileName, "w")
	for file in files:
		archive.write(file, os.path.join(arcBaseDir, file[len(baseDir):]))
	archive.close()

def get_icons():
	iconFiles = []
	for base, dirs, files in os.walk(frameIconDir):
		for file in files:
			if file.endswith(".png"):
				file = os.path.join(base, file)
				iconFiles.append(file)
	return iconFiles

def uri_is_local(uri):
	return uri.startswith('file://')


def get_journal_title(dir):
	'''
	returns the last dir name in path
	'''
	# Remove double slashes and last slash
	dir = os.path.normpath(dir)
	dir = os.path.abspath(dir)
	
	upper_dir = os.path.join(dir, '../')
	upper_dir = os.path.abspath(upper_dir)
	
	upper_dir_length = len(upper_dir)
	if upper_dir_length > 1:
		title = dir[upper_dir_length+1:]
	else:
		title = dir[upper_dir_length:]
	return title


def get_platform_info():
	import platform
	import gtk
	import yaml
	
	functions = [platform.machine, platform.platform, platform.processor, \
				platform.python_version, platform.release, platform.system,]
	values = map(lambda function: function(), functions)
	functions = map(lambda function: function.__name__, functions)
	names_values = zip(functions, values)
	
	lib_values = [('GTK version', gtk, 'gtk_version'),
					('PyGTK version', gtk, 'pygtk_version'),
					('Yaml version', yaml, '__version__'),]
	
	for name, object, value in lib_values:
		try:
			names_values.append((name, getattr(object, value)))
		except AttributeError, err:
			logging.info('%s could not be determined' % name)
			
	strings = []
	for name, value in names_values:
		strings.extend([name, value])
	strings = tuple(strings)
	return 'System info: ' + '%s: %s, '*(len(strings)/2) % strings
	

def system_call(args):
	'''
	Asynchronous system call
	
	subprocess.call runs synchronously
	'''
	subprocess.Popen(args)
	


def open_url(url):
	'''
	Opens a file with the platform's preferred method
	'''
		
	# Try opening the file locally
	if sys.platform == 'win32':
		try:
			logging.info('Trying to open %s with "os.startfile"' % url)
			# os.startfile is only available on windows
			os.startfile(os.path.normpath(url))
			return
		except OSError:
			logging.exception('Opening %s with "os.startfile" failed' % url)
	
	elif sys.platform == 'darwin':
		try:
			logging.info('Trying to open %s with "open"' % url)
			system_call(['open', url])
			return
		except OSError, subprocess.CalledProcessError:
			logging.exception('Opening %s with "open" failed' % url)
	
	else:
		try:
			subprocess.check_call(['xdg-open', '--version'])
			logging.info( 'Trying to open %s with xdg-open' % url)
			system_call(['xdg-open', url])
			return
		except OSError, subprocess.CalledProcessError:
			logging.exception('Opening %s with xdg-open failed' % url)
		
	# If everything failed, try the webbrowser
	import webbrowser
	try:
		logging.info('Trying to open %s with webbrowser' % url)
		webbrowser.open(url)
	except webbrowser.Error:
		logging.exception('Failed to open web browser')
		
		
def read_yaml_file(filename, loader=None):
	'''
	Unused
	
	Try to read the contents of the file, if an error occurs, return None
	'''
	import yaml
	if loader is None:
		loader = yaml.Loader
		
	try:
		# Try to read the contents of the file
		with open(filename, 'r') as file:
			logging.debug('Start loading file "%s"' % filename)
			content = yaml.load(file, Loader=loader)
			logging.debug('Finished loading file "%s"' % filename)
			return content
	except yaml.YAMLError, exc:
		logging.error('Error in file "%s":\n%s' % (filename, exc))
	except IOError, err:
		#If that fails, there is nothing to load, so just display an error message
		logging.error('Error: The file "%s" could not be read:' % filename)
		logging.error('%s' % err)
	except Exception, err:
		logging.error('An error occured while reading "%s":' % filename)
		logging.error('%s' % err)
		
	return None
	
def read_file(filename):
	encodings = ['utf-8']#, 'latin1', 'latin2']
	
	try:
		import chardet
	except ImportError:
		logging.info("chardet not found. Let's hope all your files are unicode")
		chardet = None
		
	if chardet:
		with open(filename, 'rb') as file:
			content = file.read()
		guess = chardet.detect(content)
		logging.debug('Chardet guesses %s for %s' % (guess, filename))
		encoding = guess.get('encoding')
		
		#print encoding, encoding == 'MacCyrrilic'
		
		# chardet makes error here sometimes
		if encoding == 'MacCyrillic':
			encoding = 'ISO-8859-2'
			
		if encoding:
			encodings.insert(0, encoding)
		
		
	import codecs
	
	for encoding in encodings:
		try:
			file = codecs.open(filename, 'rb', encoding=encoding, errors='replace')
			data = file.read()
			file.close()
			return data
		except ValueError, err:
			logging.info(err)
		except Exception, e:
			logging.error(e)
	return None
