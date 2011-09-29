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

import os
import urllib
import logging

import gtk
import gobject
import pango

# try to import gtkspell
try:
    import gtkspell
except ImportError:
    gtkspell = None

from rednotebook.gui import t2t_highlight
from rednotebook import undo


class Editor(object):
    def __init__(self, day_text_view, undo_redo_manager):
        self.day_text_view = day_text_view
        #self.day_text_buffer = gtk.TextBuffer()
        self.day_text_buffer = t2t_highlight.get_highlight_buffer()
        self.day_text_view.set_buffer(self.day_text_buffer)

        self.undo_redo_manager = undo_redo_manager

        self.changed_connection = self.day_text_buffer.connect('changed', self.on_text_change)

        self.old_text = ''

        # Some actions should get a break point even if not much text has been
        # changed
        self.force_adding_undo_point = False

        # spell checker
        self._spell_checker = None
        self.enable_spell_check(False)

        # Enable drag&drop
        #self.day_text_view.connect('drag-drop', self.on_drop) # unneeded
        self.day_text_view.connect('drag-data-received', self.on_drag_data_received)

        # Sometimes making the editor window very small causes the program to freeze
        # So we forbid that behaviour, by setting a minimum width
        self.day_text_view.set_size_request(1, -1)

        font_name = gtk.settings_get_default().get_property('gtk-font-name')
        self.default_family, self.default_size = font_name.split()
        self.default_size = int(self.default_size)

        logging.debug('Default font: %s %s' % (self.default_family, self.default_size))

    def set_text(self, text, undoing=False):
        self.insert(text, overwrite=True, undoing=undoing)

    def get_text(self):
        iter_start = self.day_text_buffer.get_start_iter()
        iter_end = self.day_text_buffer.get_end_iter()
        return self.day_text_buffer.get_text(iter_start, iter_end).decode('utf-8')

    def insert(self, text, iter=None, overwrite=False, undoing=False):
        self.force_adding_undo_point = True

        self.day_text_buffer.handler_block(self.changed_connection)

        if overwrite:
            self.day_text_buffer.set_text('')
            iter = self.day_text_buffer.get_start_iter()

        if iter is None:
            self.day_text_buffer.insert_at_cursor(text)
        else:
            if type(iter) == gtk.TextMark:
                iter = self.day_text_buffer.get_iter_at_mark(iter)
            self.day_text_buffer.insert(iter, text)

        self.day_text_buffer.handler_unblock(self.changed_connection)
        self.on_text_change(self.day_text_buffer, undoing=undoing)

    def highlight(self, text):
        self.day_text_buffer.set_search_text(text)
        return
        iter_start = self.day_text_buffer.get_start_iter()

        # Hack: Ignoring the case is not supported for the search so we search
        # for the most common variants, but do not search identical ones
        variants = set([text, text.capitalize(), text.lower(), text.upper()])

        for search_text in variants:
            iter_tuple = iter_start.forward_search(search_text,
                                gtk.TEXT_SEARCH_VISIBLE_ONLY
                                #| gtk.SEARCH_CASE_INSENSITIVE # non-existent
                                )

            # When we find one variant, highlight it, scroll to it and quit
            if iter_tuple:
                self.set_selection(*iter_tuple)

                # It is safer to scroll to a mark than an iter
                mark = self.day_text_buffer.create_mark('highlight', iter_tuple[0], left_gravity=False)
                #self.day_text_view.scroll_to_iter(iter_tuple[0], 0)
                self.day_text_view.scroll_to_mark(mark, 0)
                self.day_text_buffer.delete_mark(mark)
                return

    def get_selected_text(self):
        bounds = self.day_text_buffer.get_selection_bounds()
        if bounds:
            return self.day_text_buffer.get_text(*bounds).decode('utf-8')
        else:
            return None

    def set_selection(self, iter1, iter2):
        '''
        Sort the two iters and select the text between them
        '''
        sort_by_position = lambda iter: iter.get_offset()
        iter1, iter2 = sorted([iter1, iter2], key=sort_by_position)
        assert iter1.get_offset() <= iter2.get_offset()
        self.day_text_buffer.select_range(iter1, iter2)

    def get_selection_bounds(self):
        '''
        Return sorted iters

        Do not mix this method up with the textbuffer's method of the same name
        That method returns an empty tuple, if there is no selection
        '''
        mark1 = self.day_text_buffer.get_insert()
        mark2 = self.day_text_buffer.get_selection_bound()

        iter1 = self.day_text_buffer.get_iter_at_mark(mark1)
        iter2 = self.day_text_buffer.get_iter_at_mark(mark2)

        sort_by_position = lambda iter: iter.get_offset()
        iter1, iter2 = sorted([iter1, iter2], key=sort_by_position)

        assert iter1.get_offset() <= iter2.get_offset()
        return (iter1, iter2)

    def apply_format(self, format, markup):
        selected_text = self.get_selected_text()

        # If no text has been selected add example text and select it
        if not selected_text:
            selected_text = ' '  #'%s text' % format
            self.insert(selected_text)

            # Set the selection to the new text

            # get_insert() returns the position of the cursor (after 2nd markup)
            insert_mark = self.day_text_buffer.get_insert()
            insert_iter = self.day_text_buffer.get_iter_at_mark(insert_mark)
            markup_start_iter = insert_iter.copy()
            markup_end_iter = insert_iter.copy()
            markup_start_iter.backward_chars(len(selected_text))
            markup_end_iter.backward_chars(0)
            self.set_selection(markup_start_iter, markup_end_iter)

        # Check that there is a selection
        assert self.day_text_buffer.get_selection_bounds()

        # Add the markup around the selected text
        insert_bound = self.day_text_buffer.get_insert()
        selection_bound = self.day_text_buffer.get_selection_bound()
        self.insert(markup, insert_bound)
        self.insert(markup, selection_bound)

        # Set the selection to the formatted text
        iter1, iter2 = self.get_selection_bounds()
        selection_start_iter = iter2.copy()
        selection_end_iter = iter2.copy()
        selection_start_iter.backward_chars(len(selected_text) + len(markup))
        selection_end_iter.backward_chars(len(markup))
        self.set_selection(selection_start_iter, selection_end_iter)

    def set_font_size(self, size):
        if size <= 0:
            size = self.default_size
        font = pango.FontDescription('%s %s' % (self.default_family, size))
        self.day_text_view.modify_font(font)

    def hide(self):
        self.day_text_view.hide()

    def on_text_change(self, textbuffer, undoing=False):
        # Do not record changes while undoing or redoing
        if undoing:
            self.old_text = self.get_text()
            return

        new_text = self.get_text()
        old_text = self.old_text[:]

        #Determine whether to add a save point
        much_text_changed = abs(len(new_text) - len(old_text)) >= 5

        if much_text_changed or self.force_adding_undo_point:

            def undo_func():
                self.set_text(old_text, undoing=True)

            def redo_func():
                self.set_text(new_text, undoing=True)

            action = undo.Action(undo_func, redo_func, 'day_text_field')
            self.undo_redo_manager.add_action(action)

            self.old_text = new_text
            self.force_adding_undo_point = False

    #===========================================================
    # Spell check code taken from KeepNote project

    def can_spell_check(self):
        """Returns True if spelling is available"""
        return gtkspell is not None

    def enable_spell_check(self, enabled=True):
        """Enables/disables spell check"""
        if not self.can_spell_check():
            return

        if enabled:
            if self._spell_checker is None:
                try:
                    self._spell_checker = gtkspell.Spell(self.day_text_view)
                except gobject.GError, err:
                    logging.error('Spell checking could not be enabled: "%s"' % err)
                    self._spell_checker = None
        else:
            if self._spell_checker is not None:
                self._spell_checker.detach()
                self._spell_checker = None

    def is_spell_check_enabled(self):
        """Returns True if spell check is enabled"""
        return self._spell_checker != None

    #===========================================================

    #def on_drop(self, widget, drag_context, x, y, timestamp):
        #logging.info('Drop occured')
        #self.day_text_view.emit_stop_by_name('drag-drop')
        #return True

    def on_drag_data_received(self, widget, drag_context, x, y, selection, info, timestamp):
        # We do not want the default behaviour
        self.day_text_view.emit_stop_by_name('drag-data-received')

        iter = self.day_text_view.get_iter_at_location(x, y)

        def is_pic(uri):
            head, ext = os.path.splitext(uri)
            return ext.lower().strip('.') in 'png jpeg jpg gif eps bmp'.split()

        uris = selection.data.strip('\r\n\x00')
        logging.debug('URIs: "%s"' % uris)
        uris = uris.split() # we may have more than one file dropped
        uris = map(lambda uri: uri.strip(), uris)
        for uri in uris:
            uri = urllib.url2pathname(uri)
            dirs, filename = os.path.split(uri)
            uri_without_ext, ext = os.path.splitext(uri)
            if is_pic(uri):
                self.insert('[""%s""%s]\n' % (uri_without_ext, ext), iter)
            else:
                # It is always safer to add the "file://" protocol and the ""s
                self.insert('[%s ""%s""]\n' % (filename, uri), iter)

        drag_context.finish(True, False, timestamp)
        # No further processing
        return True
