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

import gi
from gi.repository import Gtk

from rednotebook.util import filesystem
from rednotebook.util import markup

try:
    gi.require_version('WebKit2', '4.0')
    from gi.repository import WebKit2
except (ImportError, ValueError) as err:
    WebKit2 = None
    if not filesystem.IS_WIN:
        logging.info(
            'WebKit2Gtk+ 4.0 (gir1.2-webkit2-4.0) not found. Please install'
            ' it if you want in-app previews. Error message: "{}"'.format(err))


MAX_HITS = 10**6


if WebKit2:
    class Browser(WebKit2.WebView):
        def __init__(self):
            WebKit2.WebView.__init__(self)
            webkit_settings = self.get_settings()
            webkit_settings.set_property('enable-plugins', False)

        def load_html(self, html):
            WebKit2.WebView.load_html(self, content=html, base_uri='file:///')

    class HtmlView(Browser):
        def __init__(self):
            Browser.__init__(self)
            self.search_text = ''
            self.connect('load-changed', self.on_load_changed)
            self.show_all()

        def set_font_size(self, size):
            if size <= 0:
                zoom = 1.0
            else:
                zoom = size / 10.0
            # It seems webkit shows text a little bit bigger.
            zoom *= 0.90
            self.set_zoom_level(zoom)

        def highlight(self, search_text):
            # Tell the webview which text to highlight after the html is loaded
            self.search_text = search_text
            self.get_find_controller().search(
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


class HtmlPrinter:
    """
    Print HTML document to PDF.
    """
    def __init__(self):
        self._webview = Browser()
        self._webview.get_settings().set_enable_write_console_messages_to_stdout(True)
        self._webview.connect('print', self._on_print)
        self._webview.connect('load-failed', self._on_load_failed)
        self._webview.connect('load-changed', self._on_load_changed)
        self._paper_size = Gtk.PaperSize(Gtk.PAPER_NAME_A4)
        self.outfile = None

    def print_html(self, html, outfile):
        """
        TODO: Pages with formulas are often not loaded at all. The same
        HTML works in Epiphany and Chrome so it's hard to say where the
        error is coming from. We should revisit this when formulas
        become officially supported. One solution is to recommend
        exporting to HTML and printing from there.

        """
        self.outfile = outfile
        if 'MathJax' in html:
            print_function = '<script>MathJax.Hub.Queue(function() {window.print();});</script>'
        else:
            print_function = '<script>window.onload = function() {window.print();};</script>'
        html = html.replace(markup.PRINT_FUNCTION, print_function)
        logging.info('Loading HTML...')
        self._webview.load_html(html)

    def _on_print(self, _view, print_op):
        """
        To print the PDF without a dialog, we would need to set the
        "Print to File" printer name. While we can set the printer by
        localized name, this obviously only works if the two
        translations match, which is brittle. If they don't match,
        calling `print_op.print_()` exits without an error, but does
        nothing. We therefore set the localized printer name as a hint,
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

        print_op.set_page_setup(Gtk.PageSetup())
        print_op.set_print_settings(print_settings)
        print_op.connect('finished', self._on_end_print)

        logging.info('Exporting PDF...')

        # Show print dialog.
        return False

    def _on_load_changed(self, _view, event):
        logging.info('Load changed: {}'.format(event))

    def _on_load_failed(self, _view, event, uri, error):
        logging.error("Error loading %s" % uri)
        # Stop propagating the error.
        return True

    def _on_end_print(self, *args):
        logging.info('Exporting done')


def print_pdf(html, filename):
    printer = HtmlPrinter()
    printer.print_html(html, filename)
