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

import logging

class Action(object):
	def __init__(self, undo_function, redo_function, tags):
		self.undo_function = undo_function
		self.redo_function = redo_function
		self.tags = tags

class UndoRedoManager(object):
	def __init__(self):
		self.undo_stack = []
		self.redo_stack = []
		
	
	def add_action(self, action):
		'''
		Arguments are functions that encode what there is to to to redo and undo
		the action
		'''
		self.undo_stack.append(action)
		
		del self.redo_stack[:]
		
	def undo(self):
		if not self.can_undo():
			logging.info('There is nothing to undo')
			return
		action = self.undo_stack.pop()
		action.undo_function()
		self.redo_stack.append(action)
		
	def redo(self):
		if not self.can_redo():
			logging.info('There is nothing to redo')
			return
		action = self.redo_stack.pop()
		action.redo_function()
		self.undo_stack.append(action)
		
	def can_undo(self):
		return len(self.undo_stack) > 0
	
	def can_redo(self):
		return len(self.redo_stack) > 0
	
	def delete_actions(self, tag):
		self.undo_stack = filter(lambda action: not tag in action.tags, self.undo_stack)
		self.redo_stack = filter(lambda action: not tag in action.tags, self.redo_stack)
		