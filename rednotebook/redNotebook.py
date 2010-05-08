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
import datetime
import os
import operator
import collections
import time
from optparse import OptionParser, OptionValueError


if hasattr(sys, "frozen"):
	from rednotebook.util import filesystem
	from rednotebook.util import utils
	from rednotebook import info
	from rednotebook import configuration
else:
	from util import filesystem # creates a copy of filesystem module
	#import util.filesystem # imports the original filesystem module
	from util import utils
	import info
	import configuration
	
	

def parse_options():
	parser = OptionParser(usage="usage: %prog [options] [journal-path]",
						  description=info.command_line_help,
						  #option_class=ExtOption,
						  formatter=utils.IndentedHelpFormatterWithNL(),
						  )
#	parser.add_option(
#		'-p', '--portable', dest='portable', default=False,
#		action='store_true', 
#		help='Run in portable mode ' \
#			'(default: False)')
	
	parser.add_option(
		'-d', '--debug', dest='debug', \
		default=False, action='store_true',
		help='Output debugging messages ' \
			'(default: False)')
	
	parser.add_option(
		'-m', '--minimized', dest='minimized', \
		default=False, action='store_true',
		help='Start mimimized to system tray ' \
			'(default: False)')
	
	options, args = parser.parse_args()
		
	return options, args

options, args = parse_options()



## ---------------------- Enable logging -------------------------------

import logging

def setup_logging(log_file):
	loggingLevels = {'debug': logging.DEBUG,
					'info': logging.INFO,
					'warning': logging.WARNING,
					'error': logging.ERROR,
					'critical': logging.CRITICAL}
	
	# File logging
	if sys.platform == 'win32' and hasattr(sys, "frozen"):
		utils.redirect_output_to_file(log_file)
	
	file_logging_stream = open(log_file, 'w')
	
	# We want to have the error messages in the logfile
	sys.stderr = utils.StreamDuplicator(sys.__stderr__, [file_logging_stream])
	
	# Write a log containing every output to a log file
	logging.basicConfig(level=logging.DEBUG,
						format='%(asctime)s %(levelname)-8s %(message)s',
						#filename=filesystem.logFile,
						#filemode='w',
						stream=file_logging_stream,#sys.stdout,
						)
	
	level = logging.INFO
	#if len(sys.argv) > 1:
		#level = loggingLevels.get(sys.argv[1], level)
	if options.debug:
		level = logging.DEBUG
	
	# define a Handler which writes INFO messages or higher to the sys.stdout
	console = logging.StreamHandler(sys.stdout)
	console.setLevel(level)
	# set a format which is simpler for console use
	formatter = logging.Formatter('%(levelname)-8s %(message)s')
	# tell the handler to use this format
	console.setFormatter(formatter)
	# add the handler to the root logger
	logging.getLogger('').addHandler(console)
	
	logging.debug('sys.stdout logging level: %s' % level)
	logging.info('Writing log to file "%s"' % log_file)


default_config_file = os.path.join(filesystem.appDir, 'files', 'default.cfg')
default_config = configuration.Config(default_config_file)

dirs = filesystem.Filenames(default_config)
setup_logging(dirs.logFile)

## ------------------ end Enable logging -------------------------------



## ---------------------- Enable i18n -------------------------------

# set the locale for all categories to the user’s default setting 
# (typically specified in the LANG environment variable)
import locale
lang = os.environ.get('LANG', None)
logging.debug('LANG: %s' % lang)
default_locale = locale.getdefaultlocale()[0]
logging.debug('Default locale: %s' % default_locale)
try:
	locale.setlocale(locale.LC_ALL, '')
	logging.debug('Set default locale: "%s"' % default_locale)
except locale.Error, err:
	# unsupported locale setting
	logging.error('Locale "%s" could not be set: "%s"' % (default_locale, err))
	logging.error('Probably you have to install the appropriate language packs')

# If the default locale could be determined and the LANG env variable
# has not been set externally, set LANG to the default locale
# This is necessary only for windows where program strings are not
# shown in the system language, but in English
if default_locale and not lang:
	logging.debug('Setting LANG to %s' % default_locale)
	os.environ['LANG'] = default_locale
	
LOCALE_PATH = os.path.join(dirs.appDir, 'i18n')

# the name of the gettext domain. because we have our translation files
# not in a global folder this doesn't really matter, setting it to the
# application name is a good idea tough.
GETTEXT_DOMAIN = 'rednotebook'

# set up the gettext system
import gettext

# Adding locale to the list of modules translates gtkbuilder strings
modules = [gettext, locale]

# Sometimes this doesn't work though, 
# so we try to call gtk.glade's function as well if glade is present
try:
	import gtk.glade
	modules.append(gtk.glade)
except ImportError, err:
	pass

for module in modules:
	try:
		# locale.bintextdomain and locale textdomain not available on win
		module.bindtextdomain(GETTEXT_DOMAIN, LOCALE_PATH)
		module.textdomain(GETTEXT_DOMAIN)
	except AttributeError, err:
		logging.info(err)
		
# register the gettext function for the whole interpreter as "_"
import __builtin__
__builtin__._ = gettext.gettext



## ------------------- end Enable i18n -------------------------------




try:
	import pygtk
	if not sys.platform == 'win32':
		pygtk.require("2.0")
except ImportError:
	logging.error('pygtk not found. Please install PyGTK (python-gtk2)')
	sys.exit(1)

try:
	import gtk
	
	import gobject
	# Some notes on threads_init:
	# only gtk.gdk.threads_init(): pdf export works, but gui hangs afterwards
	# only gobject.threads_init(): pdf export works, gui works
	# both: pdf export works, gui hangs afterwards	
	gobject.threads_init() # only initializes threading in the glib/gobject module
	#gtk.gdk.threads_init() # also initializes the gdk threads
except (ImportError, AssertionError), e:
	logging.error(e)
	logging.error('gtk not found. Please install PyGTK (python-gtk2)')
	sys.exit(1)

try:
	import yaml
except ImportError:
	logging.error('PyYAML not found. Please install python-yaml or PyYAML')
	sys.exit(1)

# The presence of the yaml module has been checked
try:
	from yaml import CLoader as Loader
	from yaml import CDumper as Dumper
	logging.info('Using libyaml for loading and dumping')
except ImportError:
	from yaml import Loader, Dumper
	logging.info('Using pyyaml for loading and dumping')

	

logging.info('AppDir: %s' % filesystem.appDir)
baseDir = os.path.abspath(os.path.join(filesystem.appDir, '../'))
logging.info('BaseDir: %s' % baseDir)
if baseDir not in sys.path:
	# Adding BaseDir to sys.path
	sys.path.insert(0, baseDir)
	

# This version of import is needed for win32 to work
from rednotebook.util import unicode
from rednotebook.util import dates
#from rednotebook import info
#from rednotebook import configuration
from rednotebook import backup


from rednotebook.util.statistics import Statistics
from rednotebook.gui.mainWindow import MainWindow



class RedNotebook:
	
	def __init__(self):
		self.dirs = dirs
		
		user_config = configuration.Config(self.dirs.configFile)
		# Apply defaults where no custom values have been set
		for key, value in default_config.items():
			if key not in user_config:
				user_config[key] = value
		self.config = user_config
		self.config.save_state()
		
		logging.info('Running in portable mode: %s' % self.dirs.portable)
		
		self.testing = False
		if options.debug:
			self.testing = True
			logging.debug('Debug Mode is on')
			
		# Allow starting minimized to tray
		# When we start minimized we have to set the tray icon visible
		self.start_minimized = options.minimized
		if self.start_minimized:
			self.config['closeToTray'] = 1
		
		self.month = None
		self.date = None
		self.months = {}
		
		# The dir name is the title
		self.title = ''
		
		# show instructions at first start
		logging.info('First Start: %s' % self.dirs.is_first_start)
		
		logging.info('RedNotebook version: %s' % info.version)
		logging.info(filesystem.get_platform_info())
		
		utils.set_environment_variables(self.config)
		
		self.actualDate = datetime.date.today()
		
		# Let components check if the MainWindow has been created
		self.frame = None
		self.frame = MainWindow(self)
		
		self.open_journal(self.get_journal_path())
		
		self.archiver = backup.Archiver(self)
		
		# Check for a new version
		if self.config.read('checkForNewVersion', default=0) == 1:
			utils.check_new_version(self.frame, info.version, startup=True)
			
		# Automatically save the content after a period of time
		if not self.testing:
			gobject.timeout_add_seconds(600, self.saveToDisk)
			
	
	def get_journal_path(self):
		'''
		Retrieve the path from optional args or return standard value if args
		not present
		'''
		if not args:
			data_dir = self.config.read('dataDir', self.dirs.dataDir)
			if not os.path.isabs(data_dir):
				data_dir = os.path.join(self.dirs.appDir, data_dir)
				data_dir = os.path.normpath(data_dir)
			return data_dir
		
		# path_arg can be e.g. data (under .rednotebook), data (elsewhere), 
		# or an absolute path /home/username/myjournal
		# Try to find the journal under the standard location or at the given
		# absolute or relative location
		path_arg = args[0]
		
		logging.debug('Trying to find journal "%s"' % path_arg)
		
		paths_to_check = [path_arg, os.path.join(self.dirs.redNotebookUserDir, path_arg)]
		
		for path in paths_to_check:
			if os.path.exists(path):
				if os.path.isdir(path):
					return path
				else:
					logging.warning('To open a journal you must specify a '
								'directory, not a file.')
		
		logging.error('The path "%s" is no valid journal directory. ' 
					'Execute "rednotebook -h" for instructions' % path_arg)
		sys.exit(1)
			
			
	
	
	def getDaysInDateRange(self, range):
		startDate, endDate = range
		assert startDate <= endDate
		
		sortedDays = self.sortedDays
		daysInDateRange = []
		for day in sortedDays:
			if day.date < startDate:
				continue
			elif day.date >= startDate and day.date <= endDate:
				daysInDateRange.append(day)
			elif day.date > endDate:
				break
		return daysInDateRange
		
		
	def _getSortedDays(self):
		return sorted(self.days, key=lambda day: day.date)
	sortedDays = property(_getSortedDays)
	
	
	def getEditDateOfEntryNumber(self, entryNumber):
		sortedDays = self.sortedDays
		if len(self.sortedDays) == 0:
			return datetime.date.today()
		return self.sortedDays[entryNumber % len(sortedDays)].date
	
	
	def backupContents(self, backup_file):
		self.saveToDisk()
		
		if backup_file:
			self.archiver.backup(backup_file)
			
		
	def exit(self):
		self.frame.add_values_to_config()
		
		# Make it possible to stop the program from exiting
		# e.g. if the journal could not be saved
		self.is_allowed_to_exit = True
		self.saveToDisk(exitImminent=True)
		
		if self.is_allowed_to_exit:
			logging.info('Goodbye!')
			gtk.main_quit()

	
	def saveToDisk(self, exitImminent=False, changing_journal=False, saveas=False):
		logging.info('Trying to save the journal')
		
		self.saveOldDay()
		
		if not os.path.exists(self.dirs.dataDir):
			logging.error('Save path does not exist')
			self.frame.show_save_error_dialog(exitImminent)
			return True
			
		try:
			filesystem.makeDirectory(self.dirs.dataDir)
		except OSError, err:
			self.frame.show_save_error_dialog(exitImminent)
			return True
		
		something_saved = False
		
		for yearAndMonth, month in self.months.items():
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
						self.frame.show_save_error_dialog(exitImminent)
						return True
					except IOError, err:
						self.frame.show_save_error_dialog(exitImminent)
						return True	
					
		
		if something_saved:
			self.showMessage(_('The content has been saved to %s') % self.dirs.dataDir, error=False)
		else:
			self.showMessage(_('Nothing to save'), error=False)
		
		if self.config.changed():
			try:
				filesystem.makeDirectory(self.dirs.redNotebookUserDir)
				self.config.saveToDisk()
			except IOError, err:
				self.showMessage(_('Configuration could not be saved. Please check your permissions'))
		
		if not (exitImminent or changing_journal) and something_saved:
			# Update cloud
			self.frame.cloud.update(force_update=True)
			
		# tell gobject to keep saving the content in regular intervals
		return True
	
	
	def open_journal(self, data_dir, load_files=True):
		
		if self.months:
			self.saveToDisk(changing_journal=True)
			
		# Password Protection
		#password = self.config.read('password', '')
		
		logging.info('Opening journal at %s' % data_dir)
		
		if not os.path.exists(data_dir):
			logging.warning('The data dir %s does not exist. Select a different dir.' \
						% data_dir)
			
			self.frame.show_dir_chooser('open', dir_not_found=True)
			return
		
		data_dir_empty = not os.listdir(data_dir)
		
		if not load_files and not data_dir_empty:
			msg_part1 = _('The selected folder is not empty.')
			msg_part2 = _('To prevent you from overwriting data, the folder content has been imported into the new journal.')
			self.showMessage('%s %s' % (msg_part1, msg_part2), error=False)
		elif load_files and data_dir_empty:
			self.showMessage(_('The selected folder is empty. A new journal has been created.'), \
								error=False)
		
		self.dirs.dataDir = data_dir
		
		self.month = None
		self.months.clear()
		
		# We always want to load all files
		if load_files or True:
			self.loadAllMonthsFromDisk()
		
		# Nothing to save before first day change
		self.loadDay(self.actualDate)
		
		self.stats = Statistics(self)
		
		sortedCategories = sorted(self.nodeNames, key=lambda category: str(category).lower())
		self.frame.categoriesTreeView.categories = sortedCategories
		
		if self.dirs.is_first_start and data_dir_empty:
			logging.info('Adding example content')
			self.addInstructionContent()
			
		# Notebook is only on page 1 here, if we are opening a journal the second time
		if self.frame.searchNotebook.get_current_page() == 1:
			# We have opened a new journal
			self.frame.cloud.update(force_update=True)
		else:
			# Show cloud tab, cloud is updated automatically
			self.frame.searchNotebook.set_current_page(1)
		
		# Reset Search
		self.frame.searchBox.clear()
		
		self.title = filesystem.get_journal_title(data_dir)
		
		# Set frame title
		if self.title == 'data':
			frame_title = 'RedNotebook'
		else:
			frame_title = 'RedNotebook - ' + self.title
		self.frame.mainFrame.set_title(frame_title)
		
		# Save the folder for next start
		if not self.dirs.portable:
			self.config['dataDir'] = data_dir
		else:
			rel_data_dir = filesystem.get_relative_path(self.dirs.appDir, data_dir)
			self.config['dataDir'] = rel_data_dir
		
		# Set the date range for the export assistant
		start_date = self.getEditDateOfEntryNumber(0)
		self.frame.export_assistant.set_start_date(start_date)

		end_date = self.getEditDateOfEntryNumber(-1)
		self.frame.export_assistant.set_end_date(end_date)
		
		
		
	def loadAllMonthsFromDisk(self):
		logging.debug('Starting to load files in dir "%s"' % self.dirs.dataDir)
		#for root, dirs, files in os.walk(self.dirs.dataDir):
		files = os.listdir(self.dirs.dataDir)
		for file in files:
			if not file.endswith('~'):
				self.loadMonthFromDisk(os.path.join(self.dirs.dataDir, file))
		logging.debug('Finished loading files in dir "%s"' % self.dirs.dataDir)
	
	
	def loadMonthFromDisk(self, path):
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
			msg = '''Error: %s is an incorrect filename. \
Filenames have to have the following form: 2009-01.txt \
'for January 2009 (yearWith4Digits-monthWith2Digits.txt)''' % fileName
			logging.error(msg)
			return
		
		monthFileString = path
		
		try:
			# Try to read the contents of the file
			with open(monthFileString, 'r') as monthFile:
				logging.debug('Start loading file "%s"' % monthFileString)
				monthContents = yaml.load(monthFile, Loader=Loader)
				#print monthContents
				#monthContents = unicode.get_unicode_dict(monthContents)
				#print monthContents
				logging.debug('Finished loading file "%s"' % monthFileString)
				self.months[yearAndMonth] = Month(yearNumber, monthNumber, monthContents)
		except yaml.YAMLError, exc:
			logging.error('Error in file %s:\n%s' % (monthFileString, exc))
		except IOError:
			#If that fails, there is nothing to load, so just display an error message
			logging.error('Error: The file %s could not be read' % monthFileString)
		except Exception, err:
			logging.error('An error occured while reading %s:' % monthFileString)
			logging.error('%s' % err)
		
		
	def loadMonth(self, date):
		'''
		Returns the corresponding month if it has previously been visited,
		otherwise a new month is created and returned
		'''
		
		yearAndMonth = dates.getYearAndMonthFromDate(date)
		
		# Selected month has not been loaded or created yet
		if not self.months.has_key(yearAndMonth):
			self.months[yearAndMonth] = Month(date.year, date.month)
			
		return self.months[yearAndMonth]
	
	
	def saveOldDay(self):
		'''Order is important'''
		old_content = self.day.content
		self.day.content = self.frame.categoriesTreeView.get_day_content()
		self.day.text = self.frame.get_day_text()
		
		content_changed = not (old_content == self.day.content)
		if content_changed:
			self.month.edited = True
		
		self.frame.calendar.setDayEdited(self.date.day, not self.day.empty)
	
	
	def loadDay(self, newDate):
		oldDate = self.date
		self.date = newDate
		
		if not Month.sameMonth(newDate, oldDate) or self.month is None:
			self.month = self.loadMonth(self.date)
			#self.month.visited = True
		
		self.frame.set_date(self.month, self.date, self.day)
		
		
	def merge_days(self, days):
		'''
		Method used by importers
		'''
		self.saveOldDay()
		for new_day in days:
			date = new_day.date
			month = self.loadMonth(date)
			old_day = month.getDay(date.day)
			old_day.merge(new_day)
			month.edited = True
			
		
	def _getCurrentDay(self):
		return self.month.getDay(self.date.day)
	day = property(_getCurrentDay)
	
	
	def changeDate(self, newDate):
		if newDate == self.date:
			return
		
		self.saveOldDay()
		self.loadDay(newDate)
		
		
	def goToNextDay(self):
		self.changeDate(self.date + dates.oneDay)
		
		
	def goToPrevDay(self):
		self.changeDate(self.date - dates.oneDay)
			
			
	def showMessage(self, messageText, error=False, countdown=True):
		self.frame.statusbar.showText(messageText, error, countdown)
		logging.info(messageText)
		
		
	def _getNodeNames(self):
		nodeNames = set([])
		for month in self.months.values():
			nodeNames |= set(month.nodeNames)
		return list(nodeNames)
	nodeNames = property(_getNodeNames)
	
	
	def _getTags(self):
		tags = set([])
		for month in self.months.values():
			tags |= set(month.tags)
		return list(tags)
	tags = property(_getTags)
	
	
	def search(self, text=None, category=None, tag=None):
		results = []
		for day in self.days:
			result = None
			if text:
				result = day.search_text(text)
			elif category:
				result = day.search_category(category)
			elif tag:
				result = day.search_tag(tag)
			
			if result:
				if category:
					results.extend(result)
				else:
					results.append(result)
					
		return results
	
	
	def _getAllEditedDays(self):
		# The day being edited counts too
		if self.frame:
			self.saveOldDay()
			
		days = []
		for month in self.months.values():
			daysInMonth = month.days.values()
			
			# Filter out days without content
			daysInMonth = filter(lambda day: not day.empty, daysInMonth)
			days.extend(daysInMonth)
		return days
	days = property(_getAllEditedDays)
	
	
	def getWordCountDict(self, type):
		'''
		Returns a dictionary mapping the words to their number of appearance
		'''
		wordDict = collections.defaultdict(int)
		for day in self.days:
			if type == 'word':
				words = day.words
			if type == 'category':
				words = day.nodeNames
			if type == 'tag':
				words = day.tags
			
			for word in words:
				wordDict[word.lower()] += 1
		return wordDict
	
	def go_to_first_empty_day(self):
		if len(self.sortedDays) == 0:
			return datetime.date.today()
		
		last_edited_day = self.sortedDays[-1]
		first_empty_date = last_edited_day.date + dates.oneDay
		self.changeDate(first_empty_date)
			
	
	def addInstructionContent(self):
		self.go_to_first_empty_day()
		current_date = self.date
		
		for example_day in info.example_content:
			self.day.content = example_day
			self.frame.set_date(self.month, self.date, self.day)
			self.goToNextDay()
		
		self.changeDate(current_date)
		
		

			

class Day(object):
	def __init__(self, month, dayNumber, dayContent = None):
		if dayContent == None:
			dayContent = {}
			
		self.date = datetime.date(month.yearNumber, month.monthNumber, dayNumber)
			
		self.month = month
		self.dayNumber = dayNumber
		self.content = dayContent
		
		self.searchResultLength = 50
		
	#def __getattr__(self, name):
	#	return getattr(self.date, name)
	
	
	# Text
	def _getText(self):
		'''
		Returns the day's text encoded as UTF-8
		decode means "decode from the standard ascii representation"
		'''
		if self.content.has_key('text'):
			return self.content['text'].decode('utf-8')
		else:
		   return ''
		
	def _setText(self, text):
		self.content['text'] = text
	text = property(_getText, _setText)
	
	def _hasText(self):
		return len(self.text.strip()) > 0
	hasText = property(_hasText)
	
	
	def _isEmpty(self):
		if len(self.content.keys()) == 0:
			return True
		elif len(self.content.keys()) == 1 and self.content.has_key('text') and not self.hasText:
			return True
		else:
			return False
	empty = property(_isEmpty)
		
		
	def _getTree(self):
		tree = self.content.copy()
		if tree.has_key('text'):
			del tree['text']
		return tree
	tree = property(_getTree)
	
	
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
		for category, entries in same_day.getCategoryContentPairs().items():
			for entry in entries:
				self.add_category_entry(category, entry)
	
	
	def _getNodeNames(self):
		return self.tree.keys()
	nodeNames = property(_getNodeNames)
		
		
	def _getTags(self):
		tags = []
		for category, listContent in self.getCategoryContentPairs().iteritems():
			if category.upper() == 'TAGS':
				tags.extend(listContent)
		return set(tags)
	tags = property(_getTags)
	
	
	def getCategoryContentPairs(self):
		'''
		Returns a dict of (category: contentInCategoryAsList) pairs.
		contentInCategoryAsList can be empty
		'''
		originalTree = self.tree.copy()
		pairs = {}
		for category, content in originalTree.iteritems():
			entryList = []
			if content is not None:
				for entry, nonetype in content.iteritems():
					entryList.append(entry)
			pairs[category] = entryList
		return pairs
	
	
	def _getWords(self, withSpecialChars=False):
		if withSpecialChars:
			return self.text.split()
		
		wordList = self.text.split()
		realWords = []
		for word in wordList:
			word = word.strip(u'.|-!"/()=?*+~#_:;,<>^°´`{}[]')
			if len(word) > 0:
				realWords.append(word)
		return realWords
	words = property(_getWords)
	
	
	def getNumberOfWords(self):
		return len(self._getWords(withSpecialChars=True))
	
	
	def search_text(self, searchText):
		'''Case-insensitive search'''
		upCaseSearchText = searchText.upper()
		upCaseDayText = self.text.upper()
		occurence = upCaseDayText.find(upCaseSearchText)
		
		if occurence > -1:
			# searchText is in text
			
			searchedStringInText = self.text[occurence:occurence + len(searchText)]
			
			spaceSearchLeftStart = max(0, occurence - self.searchResultLength/2)
			spaceSearchRightEnd = min(len(self.text), \
									occurence + len(searchText) + self.searchResultLength/2)
				
			resultTextStart = self.text.find(' ', spaceSearchLeftStart, occurence)
			resultTextEnd = self.text.rfind(' ', \
						occurence + len(searchText), spaceSearchRightEnd)
			if resultTextStart == -1:
				resultTextStart = occurence - self.searchResultLength/2
			if resultTextEnd == -1:
				resultTextEnd = occurence + len(searchText) + self.searchResultLength/2
				
			# Add leading and trailing ... if appropriate
			resultText = ''
			if resultTextStart > 0:
				resultText += '... '
				
			resultText += unicode.substring(self.text, resultTextStart, resultTextEnd).strip()
			
			# Make the searchedText bold
			resultText = resultText.replace(searchedStringInText, \
									'<b>' + searchedStringInText + '</b>')
			
			if resultTextEnd < len(self.text) - 1:
				resultText += ' ...'
				
			# Delete newlines
			resultText = resultText.replace('\n', '')
				
			return (str(self), resultText)
		else:
			return None
		
		
	def search_category(self, searchCategory):
		results = []
		for category, content in self.getCategoryContentPairs().iteritems():
			if content:
				if searchCategory.upper() in category.upper():
					for entry in content:
						results.append((str(self), entry))
		return results
	
	
	def search_tag(self, searchTag):
		for category, contentList in self.getCategoryContentPairs().iteritems():
			if category.upper() == 'TAGS' and contentList:
				if searchTag.upper() in map(lambda x: x.upper(), contentList):
					firstWhitespace = self.text.find(' ', self.searchResultLength)
					
					if firstWhitespace == -1:
						# No whitespace found
						textStart = self.text
					else:
						textStart = self.text[:firstWhitespace + 1]
						
					textStart = textStart.replace('\n', '')
					
					if len(textStart) < len(self.text):
						textStart += ' ...'
					return (str(self), textStart)
		return None
	
	
	def __str__(self):
		dayNumberString = str(self.dayNumber).zfill(2)
		monthNumberString = str(self.month.monthNumber).zfill(2)
		yearNumberString = str(self.month.yearNumber)
			
		return yearNumberString + '-' + monthNumberString + '-' + dayNumberString

			

class Month(object):
	def __init__(self, yearNumber, monthNumber, monthContent = None):
		if monthContent == None:
			monthContent = {}
		
		self.yearNumber = yearNumber
		self.monthNumber = monthNumber
		self.days = {}
		for dayNumber, dayContent in monthContent.iteritems():
			self.days[dayNumber] = Day(self, dayNumber, dayContent)
			
		self.edited = False
	
	
	def getDay(self, dayNumber):
		if self.days.has_key(dayNumber):
			return self.days[dayNumber]
		else:
			newDay = Day(self, dayNumber)
			self.days[dayNumber] = newDay
			return newDay
		
		
	def setDay(self, dayNumber, day):
		self.days[dayNumber] = day
		
		
	def __str__(self):
		res = 'Month %s %s\n' % (self.yearNumber, self.monthNumber)
		for dayNumber, day in self.days.iteritems():
			res += '%s: %s\n' % (dayNumber, day.text)
		return res
		
		
	def _isEmpty(self):
		for day in self.days.values():
			if not day.empty:
				return False
		return True
	empty = property(_isEmpty)
	
	
	def _getNodeNames(self):
		nodeNames = set([])
		for day in self.days.values():
			nodeNames |= set(day.nodeNames)
		return nodeNames
	nodeNames = property(_getNodeNames)
	
	
	def _getTags(self):
		tags = set([])
		for day in self.days.values():
			tags |= set(day.tags)
		return tags
	tags = property(_getTags)
	
	
	def sameMonth(date1, date2):
		if date1 == None or date2 == None:
			return False
		return date1.month == date2.month and date1.year == date2.year
	sameMonth = staticmethod(sameMonth)
		
	
	
def main():
	start_time = time.time()
	redNotebook = RedNotebook()
	utils.setup_signal_handlers(redNotebook)
	end_time = time.time()
	logging.debug('Start took %s seconds' % (end_time - start_time))
	
	try:
		logging.debug('Trying to enter the gtk main loop')
		gtk.main()
		#logging.debug('Closing logfile')
		#file_logging_stream.close()
	except KeyboardInterrupt:
		# 'Interrupt'
		#redNotebook.saveToDisk()
		sys.exit()
		

if __name__ == '__main__':
	main()
	
