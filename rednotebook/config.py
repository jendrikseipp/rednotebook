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

from rednotebook.util import filesystem
from rednotebook.util import utils

class Config(dict):
	
	def __init__(self):
		dict.__init__(self)
		
		default_config_file = os.path.join(filesystem.filesDir, 'default.cfg')
		default_config = self._read_file(default_config_file)
		
		user_config = self._read_file(filesystem.configFile)
		
		#Add the defaults
		if default_config:
			self.update(default_config)
		
		#Overwrite existing values with user options
		if user_config:
			self.update(user_config)
		
						
	def _read_file(self, file):
		
		keyValuePairs = []
		
		try:
			with open(file, 'r') as configFile:
				keyValuePairs = configFile.readlines()
				print 'The config file ' + file + ' was read'
		except IOError:
			return {}
			
		if keyValuePairs:
			#something could be read
			
			#delete comments
			keyValuePairs = map(lambda line: line[:line.find('#')], keyValuePairs)
			
			#delete whitespace
			keyValuePairs = map(lambda line: line.strip(), keyValuePairs)
			
			#delete empty lines
			keyValuePairs = filter(lambda line: len(line) > 0, keyValuePairs)
			
			dictionary = {}
			
			#read keys and values
			for keyValuePair in keyValuePairs:
				if '=' in keyValuePair:
					try:
						key, value = keyValuePair.split('=')
						
						try:
							#Save value as int if possible
							valueInt = int(value)
							dictionary[key] = valueInt
						except ValueError:
							dictionary[key] = value
							
					except Exception:
						utils.printError('The line "' + keyValuePair + \
										'" in the config file contains errors')
						
			return dictionary
		
						
	def read(self, key, default):
		if self.has_key(key):
			return self.get(key)
		else:
			self[key] = default
			return default
						
	def saveToDisk(self):
		with open(filesystem.configFile, 'w') as configFile:
			for key, value in self.iteritems():
				configFile.write(key + '=' + str(value) + '\n')
			print 'Configuration has been saved'
        

