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

import gtk
import pango

from rednotebook.util import markup
from rednotebook import undo

class CategoriesTreeView(object):
	def __init__(self, treeView, mainWindow):
		self.treeView = treeView
		
		self.mainWindow = mainWindow
		self.undo_redo_manager = mainWindow.undo_redo_manager
		
		# Maintain a list of all entered categories. Initialized by rn.__init__()
		self.categories = None
		
		self.statusbar = self.mainWindow.statusbar
		
		# create a TreeStore with one string column to use as the model
		self.treeStore = gtk.TreeStore(str)

		# create the TreeView using treeStore
		self.treeView.set_model(self.treeStore)

		# create the TreeViewColumn to display the data
		self.tvcolumn = gtk.TreeViewColumn('Categories')

		# add tvcolumn to treeView
		self.treeView.append_column(self.tvcolumn)

		# create a CellRendererText to render the data
		self.cell = gtk.CellRendererText()
		
		self.cell.set_property('editable', True)
		self.cell.connect('edited', self.edited_cb, self.treeStore)
		self.cell.connect('editing-started', self.on_editing_started)

		# add the cell to the tvcolumn and allow it to expand
		self.tvcolumn.pack_start(self.cell, True)

		''' set the cell "text" attribute to column 0 - retrieve text
			from that column in treeStore'''
		#self.tvcolumn.add_attribute(self.cell, 'text', 0)
		self.tvcolumn.add_attribute(self.cell, 'markup', 0)

		# make it searchable
		self.treeView.set_search_column(0)

		# Allow sorting on the column
		self.tvcolumn.set_sort_column_id(0)
		
		# Enable a context menu
		self.context_menu = self._get_context_menu()
		
		self.treeView.connect('button-press-event', self.on_button_press_event)
		
		# Wrap lines
		self.cell.props.wrap_mode = pango.WRAP_WORD
		self.cell.props.wrap_width = 200
		self.treeView.connect_after("size-allocate", self.on_size_allocate, self.tvcolumn, self.cell)
		
		
	def node_on_top_level(self, iter):
		if not type(iter) == gtk.TreeIter:
			# iter is a path -> convert to iter
			iter = self.treeStore.get_iter(iter)
		assert self.treeStore.iter_is_valid(iter)
		return self.treeStore.iter_depth(iter) == 0
		
		
	def on_editing_started(self, cell, editable, path):		
		# Let the renderer use text not markup temporarily
		self.tvcolumn.clear_attributes(self.cell)
		self.tvcolumn.add_attribute(self.cell, 'text', 0)
		
		# Fetch the markup
		pango_markup = self.treeStore[path][0]
		
		# Reset the renderer to use markup
		self.tvcolumn.clear_attributes(self.cell)
		self.tvcolumn.add_attribute(self.cell, 'markup', 0)
		
		# We want to show txt2tags markup and not pango markup
		editable.set_text(markup.convert_from_pango(pango_markup))
		
		
	def edited_cb(self, cell, path, new_text, user_data):
		'''
		Called when text in a cell is changed
		
		new_text is txt2tags markup
		'''
		if new_text == 'text' and self.node_on_top_level(path):
			self.statusbar.showText('"text" is a reserved keyword', error=True)
			return
		if len(new_text) < 1:
			self.statusbar.showText(_('Empty nodes are not allowed'), error=True)
			return
		
		liststore = user_data
		pango_markup = markup.convert_to_pango(new_text)
		liststore[path][0] = pango_markup
		
		# Category name changed
		if self.node_on_top_level(path):
			if new_text not in self.categories:
				self.categories.insert(0, new_text)
		
		# Tag name changed
		else:
			iter = self.treeStore.get_iter(path)
			iter_parent = self.treeStore.iter_parent(iter)
			tags_iter = self._get_category_iter('Tags')
			
			tags_node_is_parent = self.get_iter_value(iter_parent).capitalize() == 'Tags'
			if tags_node_is_parent and self.node_on_top_level(iter_parent):
				self.mainWindow.redNotebook.saveOldDay()
				
		# Update cloud
		self.mainWindow.cloud.update()
		
		
	def check_category(self, category):
		if category == 'text':
			self.statusbar.showText('"text" is a reserved keyword', error=True)
			return False
		if len(category) < 1:
			self.statusbar.showText(_('Empty category names are not allowed'), error=True)
			return False
		
		return True
		
		
	def check_entry(self, text):
		if len(text) < 1:
			self.statusbar.showText(_('Empty entries are not allowed'), error=True)
			return False
		
		return True

	
	def add_element(self, parent, elementContent):
		'''Recursive Method for adding the content'''
		for key, value in elementContent.iteritems():
			if key is not None:
				key_pango = markup.convert_to_pango(key)
			newChild = self.treeStore.append(parent, [key_pango])
			if not value == None:
				self.add_element(newChild, value)
			
		
	def set_day_content(self, day):
		for key, value in day.content.iteritems():
			if not key == 'text':
				self.add_element(None, {key: value})
		self.treeView.expand_all()
				
				
	def get_day_content(self):
		if self.empty():
			return {}
		
		content = self._get_element_content(None)
		
		return content
		   
		   
	def _get_element_content(self, element):
		model = self.treeStore
		if self.treeStore.iter_n_children(element) == 0:
			return None
		else:
			content = {}
				
			for i in range(model.iter_n_children(element)):
				child = model.iter_nth_child(element, i)
				txt2tags_markup = self.get_iter_value(child)				
				content[txt2tags_markup] = self._get_element_content(child)
			
			return content
		
		
	def empty(self, category_iter=None):
		'''
		Tests whether a category has children
		
		If no category is given, test whether there are any categories
		'''
		return self.treeStore.iter_n_children(category_iter) == 0
		
		
	def clear(self):
		self.treeStore.clear()
		assert self.empty(), self.treeStore.iter_n_children(None)
		
		
	def get_iter_value(self, iter):
		# Let the renderer use text not markup temporarily
		self.tvcolumn.clear_attributes(self.cell)
		self.tvcolumn.add_attribute(self.cell, 'text', 0)
		
		pango_markup = self.treeStore.get_value(iter, 0).decode('utf-8')
		
		# Reset the renderer to use markup
		self.tvcolumn.clear_attributes(self.cell)
		self.tvcolumn.add_attribute(self.cell, 'markup', 0)
				
		# We want to have txt2tags markup and not pango markup
		text = markup.convert_from_pango(pango_markup)
		return text
	
	
	def set_iter_value(self, iter, txt2tags_markup):
		'''
		text is txt2tags markup
		'''
		pango_markup = markup.convert_to_pango(txt2tags_markup)
		self.treeStore.set_value(iter, 0, pango_markup)
	
	def find_iter(self, category, entry):
		logging.debug('Looking for iter: "%s", "%s"' % (category, entry))
		category_iter = self._get_category_iter(category)
		
		if not category_iter:
			# If the category was not found, return None
			return None
		
		for iterIndex in range(self.treeStore.iter_n_children(category_iter)):
			current_entry_iter = self.treeStore.iter_nth_child(category_iter, iterIndex)
			current_entry = self.get_iter_value(current_entry_iter)
			if str(current_entry) == str(entry):
				return current_entry_iter
		
		# If the entry was not found, return None
		logging.debug('Iter not found: "%s", "%s"' % (category, entry))
		return None
		
		
		
	def _get_category_iter(self, categoryName):
		for iterIndex in range(self.treeStore.iter_n_children(None)):
			currentCategoryIter = self.treeStore.iter_nth_child(None, iterIndex)
			currentCategoryName = self.get_iter_value(currentCategoryIter)
			if str(currentCategoryName).lower() == str(categoryName).lower():
				return currentCategoryIter
		
		# If the category was not found, return None
		logging.debug('Category not found: "%s"' % categoryName)
		return None
	
	
	def addEntry(self, category, entry, undoing=False):
		if category not in self.categories and category is not None:
			self.categories.insert(0, category)
			
		categoryIter = self._get_category_iter(category)
			
		entry_pango = markup.convert_to_pango(entry)
		category_pango = markup.convert_to_pango(category)	
		
		if categoryIter is None:
			# If category does not exist add new category
			categoryIter = self.treeStore.append(None, [category_pango])
			entry_node = self.treeStore.append(categoryIter, [entry_pango])
		else:
			# If category exists add entry to existing category
			entry_node = self.treeStore.append(categoryIter, [entry_pango])
			
		if not undoing:
			undo_func = lambda: self.delete_node(self.find_iter(category, entry), undoing=True)
			redo_func = lambda: self.addEntry(category, entry, undoing=True)
			action = undo.Action(undo_func, redo_func, 'categories_tree_view')
			self.undo_redo_manager.add_action(action)
		
		self.treeView.expand_all()
			
	
	def get_selected_node(self):
		'''
		Returns selected node or None if none is selected
		'''
		treeSelection = self.treeView.get_selection()
		model, selectedIter = treeSelection.get_selected()
		return selectedIter
	
	
	def delete_node(self, iter, undoing=False):
		if not iter:
			# The user has changed the text of the node or deleted it
			return
		
		# Save for undoing ------------------------------------
		
		# An entry is deleted
		# We want to delete empty categories too
		if not self.node_on_top_level(iter):
			deleting_entry = True
			category_iter = self.treeStore.iter_parent(iter)
			category = self.get_iter_value(category_iter)
			entries = [self.get_iter_value(iter)]
		
		# A category is deleted
		else:
			deleting_entry = False
			category_iter = iter
			category = self.get_iter_value(category_iter)
			entries = self._get_element_content(category_iter).keys()
			
			
		# Delete ---------------------------------------------
			
		self.treeStore.remove(iter)
		
		# Delete empty category
		if deleting_entry and self.empty(category_iter):
			self.treeStore.remove(category_iter)
		
		# ----------------------------------------------------
			
			
		
		if not undoing:
				
			def undo_func():
				for entry in entries:
					self.addEntry(category, entry, undoing=True)
					
			def redo_func():
				for entry in entries:
					delete_iter = self.find_iter(category, entry)
					self.delete_node(delete_iter, undoing=True)
				
			action = undo.Action(undo_func, redo_func, 'categories_tree_view')
			self.undo_redo_manager.add_action(action)
		
		# Update cloud
		self.mainWindow.cloud.update()
		
		
	def delete_selected_node(self):
		'''
		This method used to show a warning dialog. This has become obsolete
		with the addition of undo functionality for the categories
		'''
		selectedIter = self.get_selected_node()
		if selectedIter:
			self.delete_node(selectedIter)
			return
		
		
			message = _('Do you really want to delete this node?')
			sortOptimalDialog = gtk.MessageDialog(parent=self.mainWindow.mainFrame, \
									flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_QUESTION, \
									buttons=gtk.BUTTONS_YES_NO, message_format=message)
			response = sortOptimalDialog.run()
			sortOptimalDialog.hide()
			
			if response == gtk.RESPONSE_YES:
				self.delete_node(selectedIter)
				
				
				
				
	def on_button_press_event(self, widget, event):
		"""
		@param widget - gtk.TreeView - The Tree View
		@param event - gtk.gdk.event - Event information
		"""
		#Get the path at the specific mouse position
		path = widget.get_path_at_pos(int(event.x), int(event.y))
		if (path == None):
			"""If we didn't get a path then we don't want anything
			to be selected."""
			selection = widget.get_selection()
			selection.unselect_all()
			
		# Do not show change and delete options, if nothing is selected
		something_selected = (path is not None)
		uimanager = self.mainWindow.uimanager
		change_entry_item = uimanager.get_widget('/ContextMenu/ChangeEntry')
		change_entry_item.set_sensitive(something_selected)
		delete_entry_item = uimanager.get_widget('/ContextMenu/Delete')
		delete_entry_item.set_sensitive(something_selected)
			
		if (event.button == 3):
			#This is a right-click
			self.context_menu.popup(None, None, None, event.button, event.time)
			
	def _get_context_menu(self):
		context_menu_xml = '''
		<ui>
		<popup action="ContextMenu">
			<menuitem action="ChangeEntry"/>
			<menuitem action="AddEntry"/>
			<menuitem action="Delete"/>
		</popup>
		</ui>'''
			
		uimanager = self.mainWindow.uimanager

		# Create an ActionGroup
		actiongroup = gtk.ActionGroup('ContextMenuActionGroup')
		
		new_entry_dialog = self.mainWindow.newEntryDialog
		
		# Create actions
		actiongroup.add_actions([
			('ChangeEntry', gtk.STOCK_EDIT, \
				_('Change this text'), \
				None, None, self._on_change_entry_clicked
			),
			('AddEntry', gtk.STOCK_NEW, \
				_('Add a new entry'), \
				None, None, self._on_add_entry_clicked
			),
			('Delete', gtk.STOCK_DELETE, \
				_('Delete this node'), \
				None, None, self._on_delete_entry_clicked
			),
			])

		# Add the actiongroup to the uimanager
		uimanager.insert_action_group(actiongroup, 0)

		# Add a UI description
		uimanager.add_ui_from_string(context_menu_xml)

		# Create a Menu
		menu = uimanager.get_widget('/ContextMenu')
		return menu
	
	def _on_change_entry_clicked(self, action):
		iter = self.get_selected_node()
		self.treeView.set_cursor(self.treeStore.get_path(iter), \
								focus_column=self.tvcolumn, start_editing=True)
		self.treeView.grab_focus()
	
	def _on_add_entry_clicked(self, action):
		iter = self.get_selected_node()
		
		dialog = self.mainWindow.newEntryDialog
		
		# Either nothing was selected -> show normal newEntryDialog
		if iter is None:
			dialog.show_dialog()
		# or a category was selected
		elif self.node_on_top_level(iter):
			category = self.get_iter_value(iter)
			dialog.show_dialog(category=category)
		# or an entry was selected
		else:
			parent_iter = self.treeStore.iter_parent(iter)
			category = self.get_iter_value(parent_iter)
			dialog.show_dialog(category=category)
			
	def _on_delete_entry_clicked(self, action):
		self.delete_selected_node()
		
	
	def on_size_allocate(self, treeview, allocation, column, cell):
		'''
		Code from pychess project
		(http://code.google.com/p/pychess/source/browse/trunk/lib/pychess/
		System/uistuff.py?r=1025#62)
		
		Allows dynamic line wrapping in a treeview
		'''
		otherColumns = (c for c in treeview.get_columns() if c != column)
		newWidth = allocation.width - sum(c.get_width() for c in otherColumns)
		newWidth -= treeview.style_get_property("horizontal-separator") * 2
		
		## Customize for treeview with expanders
		## The behaviour can only be fitted to one depth -> take the second one
		newWidth -= treeview.style_get_property('expander-size') * 3
		
		if cell.props.wrap_width == newWidth or newWidth <= 0:
			return
		cell.props.wrap_width = newWidth
		store = treeview.get_model()
		iter = store.get_iter_first()
		while iter and store.iter_is_valid(iter):
			store.row_changed(store.get_path(iter), iter)
			iter = store.iter_next(iter)
		treeview.set_size_request(0,-1)
		
		## The heights may have changed
		column.queue_resize()
