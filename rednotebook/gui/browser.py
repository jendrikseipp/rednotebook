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
import os.path
import sys

from gi.repository import GObject
from gi.repository import Gtk

from rednotebook.util import filesystem
from rednotebook.util import markup

try:
    from gi.repository import WebKit2
except ImportError as err:
    logging.error(
        'WebKit2Gtk+ not found. Please install it (gir1.2-webkit2-4.0): %s' % err)
    sys.exit(1)


MAX_HITS = 10**6


class Browser(WebKit2.WebView):
    def __init__(self):
        WebKit2.WebView.__init__(self)
        webkit_settings = self.get_settings()
        webkit_settings.set_property('enable-plugins', False)

    def load_html(self, html):
        WebKit2.WebView.load_html(self, content=html, base_uri='file:///')


class HtmlPrinter(object):
    def __init__(self):
        self._webview = Browser()
        self._webview.connect('load-failed', self._on_load_failed)
        self._webview.connect('notify::title', self._on_title_changed)
        self._webview.connect('load-changed', self._on_load_changed)
        self._paper_size = Gtk.PaperSize(Gtk.PAPER_NAME_A4)
        self.outfile = None

    def print_html(self, html, outfile):
        self.outfile = outfile
        self.contains_mathjax = 'MathJax' in html
        logging.info('Loading URL...')
        self._webview.load_html(html)

        while Gtk.events_pending():
            Gtk.main_iteration()

    def _print(self):
        """
        Print HTML document to PDF.

        To print the PDF without a dialog, we need to set the
        "Print to File" printer name. While we can set the printer by
        localized name, this obviously only works if the two
        translations match, which is brittle. If they don't match,
        calling `print_op.print_()` exits without an error, but does
        nothing. We therefore, set the localized printer name as a hint,
        but don't depend on it. Instead, we display the print dialog and
        let the user make adjustments.

        see gtk/modules/printbackends/file/gtkprintbackendfile.c shows
        that the non-translated printer name is "Print to File".

        """
        print_settings = Gtk.PrintSettings()
        print_settings.set_paper_size(self._paper_size)
        print_settings.set_printer(_('Print to File'))
        print_settings.set(
            Gtk.PRINT_SETTINGS_OUTPUT_URI,
            filesystem.get_local_url(os.path.abspath(self.outfile)))
        print_settings.set(Gtk.PRINT_SETTINGS_OUTPUT_FILE_FORMAT, 'pdf')

        print_op = WebKit2.PrintOperation.new(self._webview)
        print_op.set_page_setup(Gtk.PageSetup())
        print_op.set_print_settings(print_settings)
        print_op.connect('finished', self._on_end_print)

        logging.info('Exporting PDF...')
        try:
            print_op.run_dialog(None)
            while Gtk.events_pending():
                Gtk.main_iteration()
        except GObject.GError as e:
            logging.error(e.message)

    def _on_title_changed(self, view, _gparamstring):
        title = view.get_title()
        logging.info('Title changed: {}'.format(title))
        # MathJax changes the title once it has typeset all formulas.
        if title == markup.MATHJAX_FINISHED:
            self._print()

    def _on_load_changed(self, _view, event):
        if event == WebKit2.LoadEvent.FINISHED:
            logging.info('Loading done')
            # Formulas are typeset after this signal is emitted.
            if not self.contains_mathjax:
                self._print()

    def _on_load_failed(self, _view, event, uri, error):
        logging.error("Error loading %s" % uri)
        # Stop propagating the error.
        return True

    def _on_end_print(self, *args):
        logging.info('Exporting done')


def print_pdf(html, filename):
    printer = HtmlPrinter()
    printer.print_html(html, filename)


class HtmlView(Gtk.ScrolledWindow):
    def __init__(self, *args, **kargs):
        Gtk.ScrolledWindow.__init__(self, *args, **kargs)
        self.webview = Browser()
        self.add(self.webview)

        self.search_text = ''
        self.webview.connect('load-changed', self.on_load_changed)
        self.show_all()

    def load_html(self, html):
        self.webview.load_html(html)

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
        self.webview.get_find_controller().search(
            self.search_text, WebKit2.FindOptions.CASE_INSENSITIVE, MAX_HITS)

    def on_load_changed(self, webview, event):
        '''
        We use this method to highlight searched text.
        Whenever new searched text is entered it is saved in the HtmlView
        instance and highlighted, when the html is loaded.

        Trying to highlight text while the page is still being loaded
        does not work.
        '''
        if event == WebKit2.LoadEvent.FINISHED:
            if self.search_text:
                self.highlight(self.search_text)
            else:
                webview.get_find_controller().search_finish()
