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

# For Python 2.5 compatibility.
from __future__ import with_statement

import os
import sys
import logging
import re

try:
	import yaml
except ImportError:
	logging.error('PyYAML not found. Please install python-yaml or PyYAML')
	sys.exit(1)

# The presence of the yaml module has been checked
try:
	from yaml import CLoader as Loader
	from yaml import CDumper as Dumper
	#logging.info('Using libyaml for loading and dumping')
except ImportError:
	from yaml import Loader, Dumper
	logging.info('Using pyyaml for loading and dumping')
	
from rednotebook.data import Month
	
	
	
class Storage(object):
	def __init__(self):
		pass
		
	def load_all_months_from_disk(self, data_dir):
		'''
		Load all months and return a directory mapping year-month values
		to month objects
		'''
		# Format: 2010-05.txt
		date_exp = re.compile(r'(\d{4})-(\d{2})\.txt')
		
		months = {}
		
		logging.debug('Starting to load files in dir "%s"' % data_dir)
		files = sorted(os.listdir(data_dir))
		for file in files:
			match = date_exp.match(file)
			if match:
				year_string = match.group(1)
				month_string = match.group(2)
				year_month = year_string + '-' + month_string
				
				path = os.path.join(data_dir, file)
				
				month = self._load_month_from_disk(path)
				if month:
					months[year_month] = month
		logging.debug('Finished loading files in dir "%s"' % data_dir)
		return months
	
	
	def _load_month_from_disk(self, path):
		'''
		Load the month file at path and return a month object
		
		If an error occurs, return None
		'''
		# path: /something/somewhere/2009-01.txt
		# fileName: 2009-01.txt
		fileName = os.path.basename(path)
		
		try:
			# Get Year and Month from filename
			yearAndMonth, extension = os.path.splitext(fileName)
			yearNumber, monthNumber = yearAndMonth.split('-')
			yearNumber = int(yearNumber)
			monthNumber = int(monthNumber)
			assert monthNumber in range(1,13)
		except Exception:
			msg = 'Error: %s is an incorrect filename. ' \
				'Filenames have to have the following form: ' \
				'2009-01.txt for January 2009 ' \
				'(yearWith4Digits-monthWith2Digits.txt)' % fileName
			logging.error(msg)
			return
		
		monthFileString = path
		
		try:
			# Try to read the contents of the file
			with open(monthFileString, 'r') as monthFile:
				logging.debug('Start loading file "%s"' % monthFileString)
				monthContents = yaml.load(monthFile, Loader=Loader)
				logging.debug('Finished loading file "%s"' % monthFileString)
				month = Month(yearNumber, monthNumber, monthContents)
				return month
		except yaml.YAMLError, exc:
			logging.error('Error in file %s:\n%s' % (monthFileString, exc))
		except IOError:
			#If that fails, there is nothing to load, so just display an error message
			logging.error('Error: The file %s could not be read' % monthFileString)
		except Exception, err:
			logging.error('An error occured while reading %s:' % monthFileString)
			logging.error('%s' % err)
		
	def saveToDisk(self, months, frame, exitImminent=False, changing_journal=False, saveas=False):
		'''
		Do the actual saving
		'''
		for yearAndMonth, month in months.items():
			# We always need to save everything when we are "saving as"
			if (not month.empty and month.edited) or saveas:
				something_saved = True
				monthFileString = os.path.join(self.dirs.dataDir, yearAndMonth + \
											filesystem.fileNameExtension)
				with open(monthFileString, 'w') as monthFile:
					monthContent = {}
					for dayNumber, day in month.days.iteritems():
						# do not add empty days
						if not day.empty:
							monthContent[dayNumber] = day.content
					
					try:
						# yaml.dump(monthContent, monthFile, Dumper=Dumper)
						# This version produces readable unicode and no python directives
						yaml.safe_dump(monthContent, monthFile, allow_unicode=True)
						month.edited = False
					except OSError, err:
						frame.show_save_error_dialog(exitImminent)
						return True
					except IOError, err:
						frame.show_save_error_dialog(exitImminent)
						return True	
