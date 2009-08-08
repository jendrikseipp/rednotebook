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
import logging



def delete_comment(line):
	'''
	delete comment, do not alter the line, 
	if no comment sign is found
	'''
	comment_pos = line.find('#')
	if comment_pos >= 0:
		return line[:comment_pos]
	else:
		return line


class Config(dict):
	
	def __init__(self, dirs):
		dict.__init__(self)
		
		self.dirs = dirs
		
		self.obsoleteKeys = ['useGTKMozembed', 'LD_LIBRARY_PATH', 'MOZILLA_FIVE_HOME']
		
		default_config_file = os.path.join(dirs.filesDir, 'default.cfg')
		default_config = self._read_file(default_config_file)
		
		user_config = self._read_file(dirs.configFile)
		
		#Add the defaults
		if default_config:
			self.update(default_config)
		
		#Overwrite existing values with user options
		if user_config:
			self.update(user_config)
			
		self.set_default_values()
		
		
	def set_default_values(self):
		'''
		Sets some default values that are not automatically set so that
		they appear in the config file
		'''
		#self.read('exportDateFormat', '%A, %x')
		
						
	def _read_file(self, file):
		
		keyValuePairs = []
		
		try:
			with open(file, 'r') as configFile:
				keyValuePairs = configFile.readlines()
				logging.info('The config file %s was read' % file)
		except IOError:
			return {}
			
		if keyValuePairs:
			#something could be read
		
			# delete comments
			keyValuePairs = map(lambda line: delete_comment(line), keyValuePairs)
			
			#delete whitespace
			keyValuePairs = map(str.strip, keyValuePairs)
			
			#delete empty lines
			keyValuePairs = filter(lambda line: len(line) > 0, keyValuePairs)
			
			dictionary = {}
			
			#read keys and values
			for keyValuePair in keyValuePairs:
				if '=' in keyValuePair:
					try:
						# Delete whitespace around =
						pair = keyValuePair.split('=')
						key, value = map(str.strip, pair)
						
						# Do not add obsolete keys -> they will not be rewritten
						# to disk
						if key in self.obsoleteKeys:
							continue
						
						try:
							#Save value as int if possible
							valueInt = int(value)
							dictionary[key] = valueInt
						except ValueError:
							dictionary[key] = value
							
					except Exception:
						logging.error('The line "' + keyValuePair + \
										'" in the config file contains errors')
						
			return dictionary
		
						
	def read(self, key, default):
		if self.has_key(key):
			return self.get(key)
		else:
			self[key] = default
			return default
		
	def read_list(self, key, default):
		'''
		Reads the string corresponding to key and converts it to a list
		
		alpha,beta gamma;delta -> ['alpha', 'beta', 'gamma', 'delta']
		
		default should be of the form 'alpha,beta gamma;delta'
		'''
		string = self.read(key, default)
		string = str(string)
		if not string:
			return []
		
		# Try to convert the string to a list
		separators = [',', ';']
		for separator in separators:
			string = string.replace(separator, ' ')
		
		list = string.split(' ')
		
		# Remove whitespace
		list = map(str.strip, list)
		
		# Remove empty items
		list = filter(lambda item: len(item) > 0, list)
		
		return list
	
	def write_list(self, key, list):
		self[key] = ', '.join(list)
						
	def saveToDisk(self):
		try:
			with open(self.dirs.configFile, 'w') as configFile:
				for key, value in self.iteritems():
					configFile.write('%s=%s\n' % (key, value))
				logging.info('Configuration has been saved')
		except IOError:
			logging.error('Configuration could not be saved')
        

