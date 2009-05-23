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
else:
	appDir = get_main_dir()
	


imageDir = os.path.join(appDir, 'images/')
frameIconDir = os.path.join(imageDir, 'redNotebookIcon/')
userHomeDir = os.path.expanduser('~')
redNotebookUserDir = os.path.join(userHomeDir, ".rednotebook/")
defaultDataDir = os.path.join(redNotebookUserDir, "data/")
dataDir = defaultDataDir
tempDir = os.path.join(redNotebookUserDir, "tmp/")
templateDir = os.path.join(redNotebookUserDir, "templates/")
configFile = os.path.join(redNotebookUserDir, 'configuration.cfg')
filesDir = os.path.join(appDir, 'files/')
fileNameExtension = '.txt'
guiDir = os.path.join(appDir, 'gui')

last_pic_dir = userHomeDir
last_file_dir = userHomeDir
#last_journal_dir = dataDir

class Filenames(dict):
	'''
	Dictionary for dirnames and filenames
	'''
	def __init__(self):
		self.test = 'aha'
		print locals()
		for key, value in globals().items():
			# Exclude "get_main_dir()"
			if key.lower().endswith('dir') and type(value) is str:
				self[key] = value
				setattr(self, key, value)
		print locals()
		print self, len(self.keys())


def makeDirectory(dir):
	if not os.path.exists(dir):
		os.makedirs(dir)
		
def makeDirectories(dirs):
	for dir in dirs:
		makeDirectory(dir)
		
def makeFile(file, content=''):
	if not os.path.exists(file):
		with open(file, 'w') as f:
			f.write(content)
			
def makeFiles(fileContentPairs):
	for file, content in fileContentPairs:
		if len(content) > 0:
			makeFile(file, content)
		else:
			makeFile(file)
		
def getAbsPathFromAbsFileAndRelFile(absFilePath, relFilePath):
	absDir = os.path.abspath(os.path.dirname(absFilePath))
	absPath = os.path.join(absDir, relFilePath)
	return os.path.abspath(absPath)

def getAbsPathFromDirAndFilename(dir, fileName):
	return os.path.abspath(os.path.join(dir, fileName))

def dirExistsOrCanBeCreated(dir):
	if os.path.exists(dir):
		return os.path.isdir(dir)
	elif dir.endswith(os.sep) and os.path.exists(dir[:-1]):
		return False
	else:
		return True
	
def writeArchive(archiveFileName, files, baseDir='', arcBaseDir=''):
	"""
	use baseDir for relative filenames, in case you don't 
	want your archive to contain '/home/...'
	"""
	archive = zipfile.ZipFile(archiveFileName, "w")
	for file in files:
		archive.write(file, os.path.join(arcBaseDir, file[len(baseDir):]))
	archive.close()
	
def getTemplateFile(basename):
	return os.path.join(templateDir, str(basename) + fileNameExtension)

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
	


def open_url(url):
	'''
	Opens a file with the platform's preferred method 
	'''
		
	# Try opening the file locally
	if sys.platform == 'win32':
		try:
			print 'Trying to open %s with "open"' % url
			os.startfile(os.path.normpath(url))
			return
		except OSError:
			print 'Opening %s with "open" failed' % url
	else:
		
		try:
			subprocess.check_call(['xdg-open', '--version'])
			print 'Trying to open %s with xdg-open' % url
			subprocess.call(['xdg-open', url])
			return
		except OSError, subprocess.CalledProcessError:
			print 'Opening %s with xdg-open failed' % url
		
	# If everything failed, try the webbrowser
	import webbrowser
	try:
		print 'Trying to open %s with webbrowser' % url
		webbrowser.open(url)
	except webbrowser.Error:
		print 'Failed to open web browser'
