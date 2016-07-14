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
import os
import sys

import gobject
import gtk

from rednotebook.util import markup

try:
    import webkit
except ImportError as err:
    logging.error(
        'pywebkitgtk not found. Please install it (python-webkit): %s' % err)
    sys.exit(1)


class Browser(webkit.WebView):
    def __init__(self):
        webkit.WebView.__init__(self)
        webkit_settings = self.get_settings()
        webkit_settings.set_property('enable-plugins', False)

    def load_html(self, html):
        self.load_html_string(html, 'file:///')


class HtmlPrinter(object):
    """
    Idea and code-snippets taken from interwibble,
    "A non-interactive tool for converting any given website to PDF"
    (http://github.com/eeejay/interwibble/)
    """
    PAPER_SIZES = {'a3': gtk.PAPER_NAME_A3,
                   'a4': gtk.PAPER_NAME_A4,
                   'a5': gtk.PAPER_NAME_A5,
                   'b5': gtk.PAPER_NAME_B5,
                   'executive': gtk.PAPER_NAME_EXECUTIVE,
                   'legal': gtk.PAPER_NAME_LEGAL,
                   'letter': gtk.PAPER_NAME_LETTER}

    def __init__(self, paper='a4'):
        self._webview = Browser()
        try:
            self._webview.connect('load-error', self._load_error_cb)
            self._webview.connect('title-changed', self._title_changed_cb)
            self._webview.connect('load-finished', self._load_finished_cb)
        except TypeError, err:
            logging.info(err)
        self._paper_size = gtk.PaperSize(self.PAPER_SIZES[paper])
        self.outfile = None

    def print_html(self, html, outfile):
        self.outfile = outfile
        self.contains_mathjax = 'MathJax' in html
        logging.info('Loading URL...')
        self._webview.load_html(html)

        while gtk.events_pending():
            gtk.main_iteration()

    def _print(self, frame):
        print_op = gtk.PrintOperation()
        print_settings = print_op.get_print_settings() or gtk.PrintSettings()
        print_settings.set_paper_size(self._paper_size)
        print_op.set_print_settings(print_settings)
        print_op.set_export_filename(os.path.abspath(self.outfile))
        logging.info('Exporting PDF...')
        print_op.connect('end-print', self._end_print_cb)
        try:
            frame.print_full(print_op, gtk.PRINT_OPERATION_ACTION_EXPORT)
            while gtk.events_pending():
                gtk.main_iteration()
        except gobject.GError, e:
            logging.error(e.message)

    def _title_changed_cb(self, _view, frame, title):
        logging.info('Title changed: %s' % title)
        # MathJax changes the title once it has typeset all formulas.
        if title == markup.MATHJAX_FINISHED:
            self._print(frame)

    def _load_finished_cb(self, _view, frame):
        logging.info('Loading done')
        # If there's a formula, it is typeset after the load-finished signal.
        if not self.contains_mathjax:
            self._print(frame)

    def _load_error_cb(self, _view, frame, url, _gp):
        logging.error("Error loading %s" % url)

    def _end_print_cb(self, *args):
        logging.info('Exporting done')


try:
    printer = HtmlPrinter()
except TypeError, err:
    printer = None
    logging.info('UrlPrinter could not be created: "%s"' % err)


def can_print_pdf():
    if not printer:
        return False

    frame = printer._webview.get_main_frame()

    can_print_full = hasattr(frame, 'print_full')

    if not can_print_full:
        msg = 'For direct PDF export, please install pywebkitgtk version 1.1.5 or later.'
        logging.info(msg)

    return can_print_full


def print_pdf(html, filename):
    assert can_print_pdf()
    printer.print_html(html, filename)


class HtmlView(gtk.ScrolledWindow):
    def __init__(self, *args, **kargs):
        gtk.ScrolledWindow.__init__(self, *args, **kargs)
        self.webview = Browser()
        self.add(self.webview)

        self.search_text = ''
        self.loading_html = False

        self.webview.connect('button-press-event', self.on_button_press)
        self.webview.connect('load-finished', self.on_load_finished)

        self.show_all()

    def load_html(self, html):
        self.loading_html = True
        self.webview.load_html(html)
        self.loading_html = False

    def set_editable(self, editable):
        self.webview.set_editable(editable)

    def set_font_size(self, size):
        if size <= 0:
            zoom = 1.0
        else:
            zoom = size / 10.0
        # It seems webkit shows text a little bit bigger
        zoom *= 0.90
        self.webview.set_zoom_level(zoom)

    def highlight(self, string):
        # Tell the webview which text to highlight after the html is loaded
        self.search_text = string

        # Not possible for all versions of pywebkitgtk
        try:
            # Remove results from last highlighting
            self.webview.unmark_text_matches()

            # Mark all occurences of "string", case-insensitive, no limit
            self.webview.mark_text_matches(string, False, 0)
            self.webview.set_highlight_text_matches(True)
        except AttributeError, err:
            logging.info(err)

    def on_button_press(self, webview, event):
        # Right mouse click
        if event.button == 3:
            # We don't want the context menus, so stop processing that event.
            return True

    def on_load_finished(self, webview, frame):
        '''
        We use this method to highlight searched text.
        Whenever new searched text is entered it is saved in the HtmlView
        instance and highlighted, when the html is loaded.

        Trying to highlight text while the page is still being loaded
        does not work.
        '''
        if self.search_text:
            self.highlight(self.search_text)
        else:
            self.webview.set_highlight_text_matches(False)
