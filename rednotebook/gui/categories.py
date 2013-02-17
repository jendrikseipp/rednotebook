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
from rednotebook.util import utils
from rednotebook import undo


class CategoriesTreeView(object):
    def __init__(self, tree_view, main_window):
        self.tree_view = tree_view

        self.main_window = main_window
        self.undo_redo_manager = main_window.undo_redo_manager

        # Maintain a list of all entered categories. Initialized by rn.__init__()
        self.categories = []
        self.last_category = ''

        self.statusbar = self.main_window.statusbar

        # create a TreeStore with one string column to use as the model
        self.tree_store = gtk.TreeStore(str)

        # create the TreeView using tree_store
        self.tree_view.set_model(self.tree_store)

        # create the TreeViewColumn to display the data
        self.tvcolumn = gtk.TreeViewColumn()
        label = gtk.Label()
        label.set_markup('<b>' + _('Tags') + '</b>')
        label.show()
        self.tvcolumn.set_widget(label)

        # add tvcolumn to tree_view
        self.tree_view.append_column(self.tvcolumn)

        # create a CellRendererText to render the data
        self.cell = gtk.CellRendererText()

        self.cell.set_property('editable', True)
        self.cell.connect('edited', self.edited_cb, self.tree_store)
        self.cell.connect('editing-started', self.on_editing_started)

        # add the cell to the tvcolumn and allow it to expand
        self.tvcolumn.pack_start(self.cell, True)

        """ set the cell "text" attribute to column 0 - retrieve text
            from that column in tree_store"""
        #self.tvcolumn.add_attribute(self.cell, 'text', 0)
        self.tvcolumn.add_attribute(self.cell, 'markup', 0)

        # make it searchable
        self.tree_view.set_search_column(0)

        # Allow sorting on the column
        self.tvcolumn.set_sort_column_id(0)

        # Enable a context menu
        self.context_menu = self._get_context_menu()
        self.context_menu.attach_to_widget(self.tree_view, lambda x, y: None)

        self.tree_view.connect('button-press-event', self.on_button_press_event)
        self.tree_view.connect('key-press-event', self.on_key_press_event)

        # Wrap lines
        self.cell.props.wrap_mode = pango.WRAP_WORD
        self.cell.props.wrap_width = 200
        self.tree_view.connect_after("size-allocate", self.on_size_allocate, self.tvcolumn, self.cell)

    def _show_error_msg(self, text):
        self.main_window.journal.show_message(text, error=True)

    def add_category(self, category):
        """Add a new category name and sort all categories."""
        if category:
            self.last_category = category
        if category is None or category in self.categories:
            return
        self.categories.append(category)
        self.categories.sort(key=utils.sort_asc)

    def node_on_top_level(self, iter):
        if not type(iter) == gtk.TreeIter:
            # iter is a path -> convert to iter
            iter = self.tree_store.get_iter(iter)
        assert self.tree_store.iter_is_valid(iter)
        return self.tree_store.iter_depth(iter) == 0

    def on_editing_started(self, cell, editable, path):
        # Let the renderer use text not markup temporarily
        self.tvcolumn.clear_attributes(self.cell)
        self.tvcolumn.add_attribute(self.cell, 'text', 0)

        # Fetch the markup
        pango_markup = self.tree_store[path][0]

        # Tell the renderer NOT to use markup
        self.tvcolumn.clear_attributes(self.cell)
        self.tvcolumn.add_attribute(self.cell, 'markup', 0)

        # We want to show txt2tags markup and not pango markup
        editable.set_text(markup.convert_from_pango(pango_markup))

    def edited_cb(self, cell, path, new_text, liststore):
        """
        Called when text in a cell is changed

        new_text is txt2tags markup
        """
        if new_text == 'text' and self.node_on_top_level(path):
            self._show_error_msg('"text" is a reserved keyword')
            return
        if len(new_text) < 1:
            self._show_error_msg(_('Empty entries are not allowed'))
            return

        liststore[path][0] = markup.convert_to_pango(new_text)

        # Category name changed
        if self.node_on_top_level(path):
            self.add_category(new_text)

        # Update cloud
        self.main_window.cloud.update()

    def check_category(self, category):
        if category == 'text':
            self._show_error_msg('"text" is a reserved keyword')
            return False
        assert category
        return True

    def add_element(self, parent, element_content):
        """
        Recursive Method for adding the content
        """
        # We want to order the entries ascendingly
        ascending = lambda (key, value): key.lower()

        for key, value in sorted(element_content.iteritems(), key=ascending):
            if key is not None:
                key_pango = markup.convert_to_pango(key)
            new_child = self.tree_store.append(parent, [key_pango])
            if not value is None:
                self.add_element(new_child, value)

    def set_day_content(self, day):
        # We want to order the categories ascendingly
        sorted_keys = sorted(day.content.keys(), key=lambda x: x.lower())

        for key in sorted_keys:
            value = day.content[key]
            if not key == 'text':
                self.add_element(None, {key: value})
        self.tree_view.expand_all()

    def get_day_content(self):
        if self.empty():
            return {}

        content = self._get_element_content(None)

        return content

    def _get_element_content(self, element):
        model = self.tree_store
        if self.tree_store.iter_n_children(element) == 0:
            return None
        else:
            content = {}

            for i in range(model.iter_n_children(element)):
                child = model.iter_nth_child(element, i)
                txt2tags_markup = self.get_iter_value(child)
                content[txt2tags_markup] = self._get_element_content(child)

            return content

    def empty(self, category_iter=None):
        """
        Tests whether a category has children

        If no category is given, test whether there are any categories
        """
        return self.tree_store.iter_n_children(category_iter) == 0

    def clear(self):
        self.tree_store.clear()
        assert self.empty(), self.tree_store.iter_n_children(None)

    def get_iter_value(self, iter):
        # Let the renderer use text not markup temporarily
        self.tvcolumn.clear_attributes(self.cell)
        self.tvcolumn.add_attribute(self.cell, 'text', 0)

        pango_markup = self.tree_store.get_value(iter, 0).decode('utf-8')

        # Reset the renderer to use markup
        self.tvcolumn.clear_attributes(self.cell)
        self.tvcolumn.add_attribute(self.cell, 'markup', 0)

        # We want to have txt2tags markup and not pango markup
        text = markup.convert_from_pango(pango_markup)
        return text

    def set_iter_value(self, iter, txt2tags_markup):
        pango_markup = markup.convert_to_pango(txt2tags_markup)
        self.tree_store.set_value(iter, 0, pango_markup)

    def find_iter(self, category, entry=None):
        logging.debug('Looking for iter: "%s", "%s"' % (category, entry))
        category_iter = self._get_category_iter(category)

        if category_iter:
            # If we only search the category, return it.
            if not entry:
                return category_iter
        else:
            # If the category was not found, return None
            return None

        for iter_index in range(self.tree_store.iter_n_children(category_iter)):
            current_entry_iter = self.tree_store.iter_nth_child(category_iter, iter_index)
            current_entry = self.get_iter_value(current_entry_iter)
            if str(current_entry) == str(entry):
                return current_entry_iter

        # If the entry was not found, return None
        logging.debug('Iter not found: "%s", "%s"' % (category, entry))
        return None

    def _get_category_iter(self, category_name):
        for iter_index in range(self.tree_store.iter_n_children(None)):
            current_category_iter = self.tree_store.iter_nth_child(None, iter_index)
            current_category_name = self.get_iter_value(current_category_iter)
            if str(current_category_name).lower() == str(category_name).lower():
                return current_category_iter

        # If the category was not found, return None
        logging.debug('Category not found: "%s"' % category_name)
        return None

    def add_entry(self, category, entry, undoing=False):
        self.add_category(category)

        category_iter = self._get_category_iter(category)

        entry_pango = markup.convert_to_pango(entry)
        category_pango = markup.convert_to_pango(category)

        # If category exists add entry to existing category, else add new category
        if category_iter is None:
            category_iter = self.tree_store.append(None, [category_pango])

        # Only add entry if there is one
        if entry_pango:
            self.tree_store.append(category_iter, [entry_pango])

        if not undoing:
            undo_func = lambda: self.delete_node(self.find_iter(category, entry), undoing=True)
            redo_func = lambda: self.add_entry(category, entry, undoing=True)
            action = undo.Action(undo_func, redo_func, 'categories_tree_view')
            self.undo_redo_manager.add_action(action)

        self.tree_view.expand_all()

    def get_selected_node(self):
        """
        Returns selected node or None if none is selected
        """
        tree_selection = self.tree_view.get_selection()
        model, selected_iter = tree_selection.get_selected()
        return selected_iter

    def delete_node(self, iter, undoing=False):
        if not iter:
            # The user has changed the text of the node or deleted it
            return

        # Save for undoing ------------------------------------

        # An entry is deleted
        if not self.node_on_top_level(iter):
            category_iter = self.tree_store.iter_parent(iter)
            category = self.get_iter_value(category_iter)
            entries = [self.get_iter_value(iter)]

        # A category is deleted
        else:
            category_iter = iter
            category = self.get_iter_value(category_iter)
            content = self._get_element_content(category_iter)
            if content:
                entries = content.keys()
            else:
                entries = []

        # Delete ---------------------------------------------

        self.tree_store.remove(iter)

        # ----------------------------------------------------

        if not undoing:

            def undo_func():
                for entry in entries:
                    self.add_entry(category, entry, undoing=True)

            def redo_func():
                for entry in entries:
                    delete_iter = self.find_iter(category, entry)
                    self.delete_node(delete_iter, undoing=True)

            action = undo.Action(undo_func, redo_func, 'categories_tree_view')
            self.undo_redo_manager.add_action(action)

        # Update cloud
        self.main_window.cloud.update()

    def delete_selected_node(self):
        selected_iter = self.get_selected_node()
        if selected_iter:
            self.delete_node(selected_iter)
            return

    def on_key_press_event(self, widget, event):
        """
        @param widget - gtk.TreeView - The Tree View
        @param event - gtk.gdk.event - Event information

        Delete an annotation node when user hits "Delete"
        """
        keyname = gtk.gdk.keyval_name(event.keyval)
        logging.info('Pressed key: %s' % keyname)

        if keyname == 'Delete':
            self._on_delete_entry_clicked(None)
        elif keyname == 'Menu':
            # Does not work
            logging.info('Context Menu does not work')
            self.context_menu.popup(None, None, None, 0, event.time)

    def on_button_press_event(self, widget, event):
        """
        @param widget - gtk.TreeView - The Tree View
        @param event - gtk.gdk.event - Event information
        """
        #Get the path at the specific mouse position
        path = widget.get_path_at_pos(int(event.x), int(event.y))
        if (path is None):
            """If we didn't get a path then we don't want anything
            to be selected."""
            selection = widget.get_selection()
            selection.unselect_all()

        # Do not show change and delete options, if nothing is selected
        something_selected = (path is not None)
        uimanager = self.main_window.uimanager
        change_entry_item = uimanager.get_widget('/ContextMenu/ChangeEntry')
        change_entry_item.set_sensitive(something_selected)
        delete_entry_item = uimanager.get_widget('/ContextMenu/Delete')
        delete_entry_item.set_sensitive(something_selected)

        if (event.button == 3):
            #This is a right-click
            self.context_menu.popup(None, None, None, event.button, event.time)

    def _get_context_menu(self):
        context_menu_xml = """
        <ui>
        <popup action="ContextMenu">
            <menuitem action="ChangeEntry"/>
            <menuitem action="AddEntry"/>
            <menuitem action="Delete"/>
        </popup>
        </ui>"""

        uimanager = self.main_window.uimanager

        # Create an ActionGroup
        actiongroup = gtk.ActionGroup('ContextMenuActionGroup')

        # Create actions
        actiongroup.add_actions([
            ('ChangeEntry', gtk.STOCK_EDIT, _('Change this text'),
             None, None, self._on_change_entry_clicked),
            ('AddEntry', gtk.STOCK_NEW, _('Add a new entry'),
             None, None, self._on_add_entry_clicked),
            ('Delete', gtk.STOCK_DELETE, _('Delete this entry'),
             None, None, self._on_delete_entry_clicked),
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
        self.tree_view.set_cursor(self.tree_store.get_path(iter),
                                focus_column=self.tvcolumn, start_editing=True)

    def _on_add_entry_clicked(self, action):
        iter = self.get_selected_node()

        dialog = self.main_window.new_entry_dialog

        # Either nothing was selected -> show normal new_entry_dialog
        if iter is None:
            dialog.show_dialog()
        # or a category was selected
        elif self.node_on_top_level(iter):
            category = self.get_iter_value(iter)
            dialog.show_dialog(category=category)
        # or an entry was selected
        else:
            parent_iter = self.tree_store.iter_parent(iter)
            category = self.get_iter_value(parent_iter)
            dialog.show_dialog(category=category)

    def _on_delete_entry_clicked(self, action):
        self.delete_selected_node()

    def on_size_allocate(self, treeview, allocation, column, cell):
        """
        Code from pychess project
        (http://code.google.com/p/pychess/source/browse/trunk/lib/pychess/
        System/uistuff.py?r=1025#62)

        Allows dynamic line wrapping in a treeview
        """
        other_columns = (c for c in treeview.get_columns() if c != column)
        new_width = allocation.width - sum(c.get_width() for c in other_columns)
        new_width -= treeview.style_get_property("horizontal-separator") * 2

        ## Customize for treeview with expanders
        ## The behaviour can only be fitted to one depth -> take the second one
        new_width -= treeview.style_get_property('expander-size') * 3

        if cell.props.wrap_width == new_width or new_width <= 0:
            return
        cell.props.wrap_width = new_width
        store = treeview.get_model()
        iter = store.get_iter_first()
        while iter and store.iter_is_valid(iter):
            store.row_changed(store.get_path(iter), iter)
            iter = store.iter_next(iter)
        treeview.set_size_request(0, -1)

        ## The heights may have changed
        column.queue_resize()
