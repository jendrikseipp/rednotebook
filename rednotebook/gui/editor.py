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
import urllib.request
import logging

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Pango

from rednotebook.util import filesystem

try:
    from rednotebook.external import spellcheck
except ImportError:
    logging.warning(
        'For spell checking, please install enchant (python3-enchant).')
    spellcheck = None


DEFAULT_FONT = Gtk.Settings.get_default().get_property('gtk-font-name')


class Editor(GObject.GObject):
    __gsignals__ = {
        'can-undo-redo-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self, day_text_view):
        super().__init__()
        self.day_text_view = day_text_view

        self._connect_undo_signals()

        self.search_text = ''

        # spell checker
        self._spell_checker = None
        self.enable_spell_check(False)

        # Enable drag&drop
        self.day_text_view.connect('drag-data-received', self.on_drag_data_received)

        # Sometimes making the editor window very small causes the program to freeze
        # So we forbid that behaviour, by setting a minimum width
        self.day_text_view.set_size_request(1, -1)

        self.font = Pango.FontDescription(DEFAULT_FONT)
        self.default_size = self.font.get_size() / Pango.SCALE
        logging.debug('Default font: %s' % self.font.to_string())
        logging.debug('Default size: %s' % self.default_size)

    def replace_buffer(self, buffer):
        self.day_text_view.set_buffer(buffer)
        # Initialize buffer only if it is new.
        if self._spell_checker and not buffer.get_tag_table().lookup(
                'gtkspellchecker-misspelled'):
            self._spell_checker.buffer_initialize()
        self._connect_undo_signals()
        self._can_undo_redo_changed()

    @property
    def day_text_buffer(self):
        return self.day_text_view.get_buffer()

    def _connect_undo_signals(self):
        undo_mgr = self.day_text_buffer.get_undo_manager()
        undo_mgr.connect('can-undo-changed', self._can_undo_redo_changed)
        undo_mgr.connect('can-redo-changed', self._can_undo_redo_changed)

    def set_text(self, text, undoing=False):
        # We typically don't want to be able to undo/redo a replacement of the
        # whole text, so we mark it as 'not undoable'.
        self.day_text_buffer.begin_not_undoable_action()
        self.insert(text, overwrite=True, undoing=undoing)
        self.day_text_buffer.end_not_undoable_action()

    def get_text(self, iter_start=None, iter_end=None):
        iter_start = iter_start or self.day_text_buffer.get_start_iter()
        iter_end = iter_end or self.day_text_buffer.get_end_iter()
        return self.day_text_buffer.get_text(iter_start, iter_end, True)

    def insert(self, text, iter=None, overwrite=False, undoing=False):
        if overwrite:
            self.day_text_buffer.set_text('')
            iter = self.day_text_buffer.get_start_iter()

        if iter is None:
            self.day_text_buffer.insert_at_cursor(text)
        else:
            if type(iter) == Gtk.TextMark:
                iter = self.day_text_buffer.get_iter_at_mark(iter)
            self.day_text_buffer.insert(iter, text)

    def replace_selection(self, text):
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
        buf = self.day_text_buffer

        # Clear previous highlighting
        start = buf.get_start_iter()
        end = buf.get_end_iter()
        buf.remove_tag_by_name('highlighter', start, end)

        # Highlight matches
        if text:
            for match_start, match_end in self.iter_search_matches(text):
                buf.apply_tag_by_name('highlighter', match_start, match_end)

    search_flags = Gtk.TextSearchFlags.VISIBLE_ONLY | Gtk.TextSearchFlags.CASE_INSENSITIVE

    def iter_search_matches(self, text):
        it = self.day_text_buffer.get_start_iter()
        while True:
            match = it.forward_search(text, self.search_flags)
            if not match:
                return
            yield match
            it = match[1]  # Continue searching from after the match

    def scroll_to_text(self, text):
        for match_start, _ in self.iter_search_matches(text):
            # It is safer to scroll to a mark than an iter
            mark = self.day_text_buffer.create_mark(
                'highlight_query', match_start, left_gravity=False)
            self.day_text_view.scroll_to_mark(mark, 0, False, 0, 0)
            self.day_text_buffer.delete_mark(mark)
            return  # Stop after the first match

    def get_selected_text(self):
        bounds = self.day_text_buffer.get_selection_bounds()
        if bounds:
            return self.get_text(*bounds)
        else:
            return ''

    def get_text_left_of_selection(self, length):
        bounds = self.get_selection_bounds()
        start = bounds[0].copy()
        start.backward_chars(length)
        end = bounds[0]
        return self.get_text(start, end)

    def get_text_right_of_selection(self, length):
        bounds = self.get_selection_bounds()
        start = bounds[1]
        end = bounds[1].copy()
        end.forward_chars(length)
        return self.get_text(start, end)

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

    def _get_markups(self, format, selection):
        format_to_markups = {
            'bold': ('**', '**'),
            'italic': ('//', '//'),
            'monospace': ('``', '``'),
            'underline': ('__', '__'),
            'strikethrough': ('--', '--'),
            'title': ('\n=== ', ' ===\n')
        }
        left_markup, right_markup = format_to_markups[format]
        if format == 'monospace' and '\n' in selection:
            left_markup = '\n```\n'
            right_markup = '\n```\n'
        return left_markup, right_markup

    def apply_format(self, format):
        selection = self.get_selected_text()
        left_markup, right_markup = self._get_markups(format, self.get_selected_text())

        # Apply formatting only once.
        if (self.get_text_left_of_selection(len(left_markup)) == left_markup or
                selection.startswith(left_markup)):
            left_markup = ''
        if (self.get_text_right_of_selection(len(right_markup)) == right_markup or
                selection.endswith(right_markup)):
            right_markup = ''

        # Don't add unneeded newlines.
        if left_markup.startswith('\n') and self.get_text_left_of_selection(1) in ['\n', '']:
            left_markup = left_markup[1:]
        if right_markup.endswith('\n') and self.get_text_right_of_selection(1) in ['\n', '']:
            right_markup = right_markup[:-1]

        text = selection or ' '
        self.replace_selection_and_highlight(left_markup, text, right_markup)
        self.day_text_view.grab_focus()

    def set_font(self, font_name):
        font = Pango.FontDescription(font_name)
        self.day_text_view.modify_font(font)

    def hide(self):
        self.day_text_view.hide()

    # ===========================================================
    # Spell checking.

    def can_spell_check(self):
        """Return True if spell checking is available."""
        return spellcheck is not None

    def is_spell_check_enabled(self):
        return bool(self._spell_checker and self._spell_checker.enabled)

    def _enable_spell_check(self):
        assert self.can_spell_check()
        if self._spell_checker:
            self._spell_checker.enable()
        else:
            try:
                self._spell_checker = spellcheck.SpellChecker(
                    self.day_text_view, filesystem.LANGUAGE)
            except spellcheck.NoDictionariesFound:
                logging.warning('No spell checking dictionaries found.')
                self._spell_checker = None
            except Exception as err:
                logging.error(
                    'Spell checking could not be enabled. %s: %s' %
                    (type(err).__name__, err))
                self._spell_checker = None

    def _disable_spell_check(self):
        if self._spell_checker:
            self._spell_checker.disable()

    def enable_spell_check(self, enable=True):
        """Enable/disable spell check."""
        if not self.can_spell_check():
            return

        if enable:
            self._enable_spell_check()
        else:
            self._disable_spell_check()

    # ===========================================================

    def on_drag_data_received(self, widget, drag_context, x, y, selection, info, timestamp):
        # We do not want the default behaviour
        self.day_text_view.emit_stop_by_name('drag-data-received')

        iter = self.day_text_view.get_iter_at_location(x, y)

        def is_pic(uri):
            _, ext = os.path.splitext(uri)
            return ext.lower().strip('.') in 'png jpeg jpg gif eps bmp svg'.split()

        uris = selection.get_text().split()
        logging.debug('Text: {}'.format(selection.get_text()))
        logging.debug('URIs: {}'.format(uris))
        for uri in uris:
            uri = uri.strip()
            uri = urllib.request.url2pathname(uri)
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

    def _can_undo_redo_changed(self, undo_mgr=None):
        self.emit("can-undo-redo-changed")
