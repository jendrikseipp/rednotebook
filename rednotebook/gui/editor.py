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

# Try to import gtkspell
gtkspell = None
try:
    import gtkspell
except ImportError:
    pass

from rednotebook.gui import t2t_highlight
from rednotebook import undo
from rednotebook.util import filesystem


class Editor(object):
    def __init__(self, day_text_view, undo_redo_manager):
        self.day_text_view = day_text_view
        self.day_text_buffer = t2t_highlight.get_highlight_buffer()
        self.day_text_view.set_buffer(self.day_text_buffer)

        self.undo_redo_manager = undo_redo_manager

        self.changed_connection = self.day_text_buffer.connect('changed', self.on_text_change)

        self.old_text = ''
        self.search_text = ''

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
        self.font = pango.FontDescription(font_name)
        self.default_size = self.font.get_size() / pango.SCALE
        logging.debug('Default font: %s' % self.font.to_string())
        logging.debug('Default size: %s' % self.default_size)

    def set_text(self, text, undoing=False):
        self.insert(text, overwrite=True, undoing=undoing)

    def get_text(self, iter_start=None, iter_end=None):
        iter_start = iter_start or self.day_text_buffer.get_start_iter()
        iter_end = iter_end or self.day_text_buffer.get_end_iter()
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

    def replace_selection(self, text):
        self.force_adding_undo_point = True

        self.day_text_buffer.delete_selection(interactive=False,
                                              default_editable=True)
        self.day_text_buffer.insert_at_cursor(text)

    def replace_selection_and_highlight(self, p1, p2, p3):
        """
        Insert all three parts and highlight the middle part.
        """
        self.replace_selection(p1 + p2 + p3)
        # Get the mark at the end of the insertion.
        insert_mark = self.day_text_buffer.get_insert()
        insert_iter = self.day_text_buffer.get_iter_at_mark(insert_mark)
        start = insert_iter.copy()
        end = insert_iter.copy()
        start.backward_chars(len(p3) + len(p2))
        end.backward_chars(len(p3))
        self.day_text_buffer.select_range(start, end)

    def highlight(self, text):
        self.search_text = text
        self.day_text_buffer.set_search_text(text)

    def scroll_to_text(self, text):
        iter_start = self.day_text_buffer.get_start_iter()

        # Hack: Ignoring the case is not supported for the search so we search
        # for the most common variants, but do not search identical ones
        variants = set([text, text.capitalize(), text.lower(), text.upper()])

        for search_text in variants:
            iter_tuple = iter_start.forward_search(search_text,
                                                gtk.TEXT_SEARCH_VISIBLE_ONLY)

            # When we find one variant, scroll to it and quit
            if iter_tuple:
                # It is safer to scroll to a mark than an iter
                mark = self.day_text_buffer.create_mark('highlight_query',
                                            iter_tuple[0], left_gravity=False)
                self.day_text_view.scroll_to_mark(mark, 0)
                self.day_text_buffer.delete_mark(mark)
                return

    def get_selected_text(self):
        bounds = self.day_text_buffer.get_selection_bounds()
        if bounds:
            return self.get_text(*bounds)
        else:
            return ''

    def get_text_around_selected_text(self, length):
        bounds = self.get_selection_bounds()
        start1 = bounds[0].copy()
        start1.backward_chars(length)
        start2 = bounds[0]
        end1 = bounds[1]
        end2 = bounds[1].copy()
        end2.forward_chars(length)
        return (self.get_text(start1, start2), self.get_text(end1, end2))

    @staticmethod
    def sort_iters(*iters):
        return sorted(iters, key=lambda iter: iter.get_offset())

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
        return self.sort_iters(iter1, iter2)

    def get_text_parts(self):
        """
        Return text before the selection, the selected text itself and
        the text after the selection.
        """
        start = self.day_text_buffer.get_start_iter()
        end = self.day_text_buffer.get_end_iter()
        sel_start, sel_end = self.get_selection_bounds()
        return (self.get_text(start, sel_start),
                self.get_text(sel_start, sel_end),
                self.get_text(sel_end, end))

    def apply_format(self, markup):
        text_around_selection = self.get_text_around_selected_text(2)
        # Apply formatting only once if a format button is clicked multiple times
        if text_around_selection == (unicode(markup), unicode(markup)):
            return

        text = self.get_selected_text() or ' '
        self.replace_selection_and_highlight(markup, text, markup)

    def set_font_size(self, size):
        if size <= 0:
            size = self.default_size
        self.font.set_size(size * pango.SCALE)
        self.day_text_view.modify_font(self.font)

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
                except gobject.GError as err:
                    logging.error('Spell checking could not be enabled: "%s"' % err)
                    self._spell_checker = None
                if self._spell_checker:
                    try:
                        self._spell_checker.set_language(filesystem.LANGUAGE)
                    except RuntimeError as err:
                        logging.error('Spellchecking could not be enabled for %s: %s' %
                                      (filesystem.LANGUAGE, err))
                        logging.error('Consult built-in help for instructions '
                                      'on how to add custom dictionaries.')
        else:
            if self._spell_checker is not None:
                self._spell_checker.detach()
                self._spell_checker = None

    def is_spell_check_enabled(self):
        """Returns True if spell check is enabled"""
        return self._spell_checker is not None

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
        uris = uris.split()  # we may have more than one file dropped
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
