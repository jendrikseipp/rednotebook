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
import sys
import mimetypes
import logging
import time

import gtk


from rednotebook.util import filesystem

class TemplateManager(object):
	def __init__(self, mainWindow):
		self.mainWindow = mainWindow
		
		self.dirs = mainWindow.redNotebook.dirs
		
		self.merge_id = None
		self.actiongroup = None
		
	
	def on_insert(self, action):
		title = action.get_name()
		
		if title == 'Weekday':
			text = self.get_weekday_text()
		else:
			text = self.get_text(title)
		self.mainWindow.dayTextField.insert_template(text)
		
		
	def on_edit(self, action):
		'''
		Open the template file in an editor
		'''
		edit_title = action.get_name()
		title = edit_title[4:]
		
		if title == 'Weekday':
			date = self.mainWindow.redNotebook.date
			weekDayNumber = date.weekday() + 1
			title = str(weekDayNumber)
		
		filename = self.titles_to_files.get(title)
		filesystem.open_url(filename)
		
	def on_new_template(self, action):
		dialog = gtk.Dialog('Choose Template Name')
		dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
		dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
		
		entry = gtk.Entry()
		entry.set_size_request(300, -1)
		dialog.get_content_area().pack_start(entry)
		dialog.show_all()
		response = dialog.run()
		dialog.hide()
		
		example_text = '''\
This is a template file. It can contain any formatting or content that is also \
allowed in normal entries.

Your text can be:

- **bold**
- //italic//
- __underlined__
- --stricken--


You can add images to your template:

**images:** [""/path/to/your/picture"".jpg]

You can link to almost everything:

- **links to files on your computer:** [filename.txt ""/path/to/filename.txt""]
- **links to directories:** [directory name ""/path/to/directory/""]
- **links to websites:** [RedNotebook Homepage ""http://rednotebook.sourceforge.net""]


As you see, **bullet lists** are also available. As always you have to add two \
empty lines to the end of a list.

Additionally you can have **titles** and **horizontal lines**:

===Title===

==================== 

When a template is inserted, every occurence of "$date$" is converted to \
the current date. You can set the date format in the preferences.
		'''
		
		if response == gtk.RESPONSE_OK:
			title = entry.get_text()
			if not title.lower().endswith('.txt'):
				title += '.txt'
			filename = os.path.join(self.dirs.templateDir, title)
			
			filesystem.makeFile(filename, example_text)
			
			filesystem.open_url(filename)
			
	
	def on_open_template_dir(self):
		filesystem.open_url(self.dirs.templateDir)
		
	
	def getTemplateFile(self, basename):
		return os.path.join(self.dirs.templateDir, str(basename) + '.txt')
		
		
	def get_text(self, title):
		filename = self.titles_to_files.get(title, None)
		if not filename:
			return ''
		
		try:
			with open(filename, 'r') as templateFile:
				 text = templateFile.read()
		except IOError, Error:
			logging.error('Template File %s not found' % name)
			text = ''
			
		# convert every "$date$" to the current date
		default_date_string = '%A, %x %X'
		date_string = self.mainWindow.redNotebook.config.read('dateTimeString', default_date_string)
		date = time.strftime(date_string)
		text = text.replace('$date$', date)
		
		return text
		
		
	def get_weekday_text(self, date=None):
		if date is None:
			date = self.mainWindow.redNotebook.date
		weekDayNumber = date.weekday() + 1
		return self.get_text(str(weekDayNumber))
		
	
	def get_available_template_files(self):
		dir = self.dirs.templateDir
		files = os.listdir(dir)
		files = map(lambda basename: os.path.join(dir, basename), files)
		
		# No directories allowed
		files = filter(lambda file:os.path.isfile(file), files)
		
		# No tempfiles
		files = filter(lambda file: not file.endswith('~'), files)
		
		return files
	
	
	def get_menu(self):
		'''
		See http://www.pygtk.org/pygtk2tutorial/sec-UIManager.html for help
		A popup menu cannot show accelerators (HIG).
		'''
		
		# complete paths
		files = self.get_available_template_files()
		
		# 1, 2, 3
		self.titles_to_files = {}
		for file in files:
			root, ext = os.path.splitext(file)
			title = os.path.basename(root)
			self.titles_to_files[title] = file
			
		sorted_titles = sorted(self.titles_to_files.keys())
		
		menu_xml = '''\
		<ui>
		<popup action="TemplateMenu">
		'''
		
		insert_menu_xml = '''\
			<menu action="InsertMenu">
				<menuitem action="Weekday"/>
				<separator name="sep4"/>
		'''
		for title in sorted_titles:
			if title not in map(str, range(1,8)):
				insert_menu_xml += '''\
				<menuitem action="%s"/>
				''' % title
		insert_menu_xml += '''\
			</menu>
		'''
		
		menu_xml += insert_menu_xml
		
		menu_xml += '''\
			<separator name="sep5"/>
			<menuitem action="NewTemplate"/>
		'''
			
		edit_menu_xml = '''\
			<menu action="EditMenu">
				<menuitem action="EditWeekday"/>
				<separator name="sep3"/>
		'''
		for title in sorted_titles:
			if title not in map(str, range(1,8)):
				edit_menu_xml += '''\
				<menuitem action="Edit%s"/>
				''' % title
		edit_menu_xml += '''\
			</menu>
		'''
		
		
		menu_xml += edit_menu_xml
		
		
		
		
		
		menu_xml +='''\
			<menuitem action="OpenTemplateDirectory"/>
		</popup>
		</ui>'''
			
		uimanager = self.mainWindow.uimanager
		
		if self.actiongroup:
			uimanager.remove_action_group(self.actiongroup)

		# Create an ActionGroup
		self.actiongroup = gtk.ActionGroup('TemplateActionGroup')

		
		# Create actions
		actions = []			
		
		for title in sorted_titles:
			insert_action = (title, None, title, None, None, \
					lambda widget: self.on_insert(widget))
			actions.append(insert_action)
			edit_action = ('Edit' + title, None, title, None, None, \
					lambda widget: self.on_edit(widget))
			actions.append(edit_action)
			
		actions.append(('Weekday', gtk.STOCK_HOME, "This Weekday's Template", None, None, \
					lambda widget: self.on_insert(widget)))
		
		actions.append(('EditMenu', gtk.STOCK_EDIT, 'Edit Template', None, None, \
					None))
		
		actions.append(('InsertMenu', gtk.STOCK_ADD, 'Insert Template', None, None, \
					None))
		
		actions.append(('EditWeekday', gtk.STOCK_HOME, 'This Weekday', None, None, \
					lambda widget: self.on_edit(widget)))
		
		actions.append(('NewTemplate', gtk.STOCK_NEW, 'Create New Template', None, None, \
					lambda widget: self.on_new_template(widget)))
		
		actions.append(('OpenTemplateDirectory', gtk.STOCK_DIRECTORY, 'Open Template Directory', None, None, \
					lambda widget: self.on_open_template_dir()))
		
		
		self.actiongroup.add_actions(actions)

		

		# Remove the lasts ui description
		if self.merge_id:
			uimanager.remove_ui(self.merge_id)

		# Add a UI description
		self.merge_id = uimanager.add_ui_from_string(menu_xml)
		
		# Add the actiongroup to the uimanager
		uimanager.insert_action_group(self.actiongroup, 0)

		# Create a Menu
		menu = uimanager.get_widget('/TemplateMenu')
		
		return menu
		
		
	
	def make_empty_template_files(self):
		def getInstruction(dayNumber):
			file = self.getTemplateFile(dayNumber)
			text = '''\
The template for this weekday has not been edited. 
If you want to have some text that you can add to that day every week, \
edit the file [%s ""%s""] in a text editor.

To do so, you can switch to "Preview" and click on the link to that file.
			''' % (os.path.basename(file), file)
			return text
					
		fileContentPairs = []
		for dayNumber in range(1, 8):
			fileContentPairs.append((self.getTemplateFile(dayNumber), getInstruction(dayNumber)))
		
		template_help_text = '''\
Besides templates for weekdays you can also have arbitrary named templates. 
For example you might want to have a template for "Meeting" or "Journey".
All templates must reside in the directory "%s".

To create a new template, just save an ordinary textfile in that directory. \
You can use your favourite text editing program for that task \
(e.g. gedit on Linux or the editor on Win). 
The name of the newly created file will be the template's title.

You can switch to "Preview" mode and click on the link to get to the \
[template directory ""%s""].

If you come up with templates that could be useful for other people as well, \
I would appreciate if you sent me your template file, so others can benefit \
from it.
		''' % (self.dirs.templateDir, self.dirs.templateDir)
		
		template_help_filename = self.getTemplateFile('Help')
		fileContentPairs.append((template_help_filename, template_help_text))
		
		# Only add the example templates the first time and just restore
		# the day templates everytime
		if not self.mainWindow.redNotebook.firstTimeExecution:
			filesystem.makeFiles(fileContentPairs)
			return
		
		
		template_meeting_text = '''\
=== Meeting ===
Group name, date, and place

**Present**

 - Axxxx
 - Bxxxx
 - Cxxx
 - Dxxxxx
 - Exxxx


**Agenda**

 - Xxxx xxxxx xxxxxxx xxxx
 - Xxxxxxx xxxxxxxxx xxxx xxxx
   - Xxxx xxxxx


**Discussion, decisions, assignments**

First agenda item: Xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

Second agenda item: Xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx. Xxxxxxxxxxxxx

Additional items: Xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx. Xxxxxxxxxxxxxxxxxxxxx


**Tentative agenda for the next meeting**

 - Xxxxxxxxxxxxxxx Xxxxx Xxxxxxxxxxx
 - Xxxxxxxxxx Xxxxxxxxxxxx
		'''
		
		template_meeting_filename = self.getTemplateFile('Meeting')
		fileContentPairs.append((template_meeting_filename, template_meeting_text))
		
		
		template_journey_text = '''\
=== Journey ===
**Date:** xx.xx.xxxx

**Location:** 

**Participants:**

**The trip:** 
First we went to xxxxx then we got to yyyyy ...

**Pictures:** [Image folder ""/path/to/the/images/""]
		'''
		
		template_journey_filename = self.getTemplateFile('Journey')
		fileContentPairs.append((template_journey_filename, template_journey_text))
		
		
		filesystem.makeFiles(fileContentPairs)
