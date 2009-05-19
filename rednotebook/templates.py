#!/usr/bin/env python
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

import gtk


from rednotebook.util import filesystem

class TemplateManager(object):
	def __init__(self, mainWindow):
		self.mainWindow = mainWindow
		
		self.merge_id = None
		
	
	def on_insert(self, action):
		title = action.get_name()
		
		if title == 'Weekday':
			text = self.get_weekday_text()
		else:
			text = self.get_text(title)
		self.mainWindow.dayTextField.insert_template(text)
		
		
	def get_text(self, title):
		filename = self.titles_to_files.get(title, None)
		if not filename:
			return ''
		
		try:
			with open(filename, 'r') as templateFile:
				 text = templateFile.read()
		except IOError, Error:
			print 'Error: Template File', name, 'not found'
			text = ''
		return text
		
		
	def get_weekday_text(self, date=None):
		if date is None:
			date = self.mainWindow.redNotebook.date
		weekDayNumber = date.weekday() + 1
		return self.get_text(str(weekDayNumber))
		
	
	def get_available_template_files(self):
		dir = filesystem.templateDir
		files = os.listdir(dir)
		files = map(lambda basename: os.path.join(dir, basename), files)
		
		# No directories allowed
		files = filter(lambda file:os.path.isfile(file), files)
		
		#textfiles = []
		#for file in files:
		#	type, encoding = mimetypes.guess_type(file)
		#	if type == 'text/plain':
		#		textfiles.append(file)
		#print 'TPL Files', files
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
		
		menu_xml = '''
		<ui>
		<popup action="TemplateMenu">
			<menuitem action="Weekday"/>
			<separator name="sep1"/>
		'''
		
		sorted_titles = sorted(self.titles_to_files.keys())
			
		for title in sorted_titles:
			if title not in map(str, range(1,8)):
				menu_xml += '<menuitem action="%s"/>\n' % title
				#<menuitem action="BulletList"/>
			
		menu_xml += '''\
		</popup>
		</ui>'''
			
		uimanager = self.mainWindow.uimanager

		# Create an ActionGroup
		actiongroup = gtk.ActionGroup('TemplateActionGroup')

		
		actions = []
		
		actions.append(('Weekday', None, 'For This Weekday', None, None, \
					lambda widget: self.on_insert(widget)))
			
		
		for title in self.titles_to_files:
			action = (title, None, title, None, None, \
					lambda widget: self.on_insert(widget))
			actions.append(action)
		
		
		# Create actions
		actiongroup.add_actions(actions)

		# Add the actiongroup to the uimanager
		uimanager.insert_action_group(actiongroup, 0)

		# Remove the lasts ui description
		if self.merge_id:
			uimanager.remove_ui(self.merge_id)

		# Add a UI description
		self.merge_id = uimanager.add_ui_from_string(menu_xml)

		# Create a Menu
		menu = uimanager.get_widget('/TemplateMenu')
		
		return menu
		
		
	
	def make_empty_template_files(self):
		def getInstruction(dayNumber):
			file = filesystem.getTemplateFile(dayNumber)
			text = '''\
The template for this weekday has not been edited. 
If you want to have some text that you can add to that day every week, \
edit the file [%s ""%s""] in a text editor.

To do so, you can switch to "Preview" and click on the link to that file.
			''' % (os.path.basename(file), file)
			return text
					
		fileContentPairs = []
		for dayNumber in range(1, 8):
			fileContentPairs.append((filesystem.getTemplateFile(dayNumber), getInstruction(dayNumber)))
		
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
		''' % (filesystem.templateDir, filesystem.templateDir)
		
		template_help_filename = filesystem.getTemplateFile('Help')
		fileContentPairs.append((template_help_filename, template_help_text))
		
		
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
		
		template_meeting_filename = filesystem.getTemplateFile('Meeting')
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
		
		template_journey_filename = filesystem.getTemplateFile('Journey')
		fileContentPairs.append((template_journey_filename, template_journey_text))
		
		
		filesystem.makeFiles(fileContentPairs)
