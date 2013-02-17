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

import sys
import os
import logging
import tempfile

import gtk
import gobject

# Testing
if __name__ == '__main__':
    sys.path.insert(0, '../../')

from rednotebook.util import markup


try:
    import webkit
except ImportError as err:
    logging.error('Webkit was not found. It can be found in a package '
                  'with the name python-webkit or pywebkitgtk.\n'
                  '%s' % err)
    sys.exit(1)


LOAD_HTML_FROM_FILE = False


class Browser(webkit.WebView):
    def __init__(self):
        webkit.WebView.__init__(self)
        webkit_settings = self.get_settings()
        webkit_settings.set_property('enable-plugins', False)

        if LOAD_HTML_FROM_FILE:
            self.tmp_file = tempfile.NamedTemporaryFile(suffix='.html', prefix='rn-tmp', delete=False)
            self.tmp_uri = 'file://' + self.tmp_file.name

        #self.connect('notify::load-status', self._on_load_status_changed)

    #def _on_load_status_changed(self, *args):
    #    print 'LOAD STATUS CHANGED', self.get_property('load-status')

    def load_html_from_file(self, html):
        self.tmp_file.truncate(0)
        self.tmp_file.write(html)
        self.tmp_file.flush()
        self.load_uri(self.tmp_uri)

    def load_html(self, html):
        if LOAD_HTML_FROM_FILE:
            self.load_html_from_file(html)
        else:
            self.load_html_string(html, 'file:///')
            #self.load_string(html, content_mimetype='text/html',
            #                 content_encoding='UTF-8', base_uri='file:///')

    def get_html(self):
        self.execute_script("document.title=document.document_element.innerHTML;")
        return self.get_main_frame().get_title()


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

    def _title_changed_cb(self, view, frame, title):
        logging.info('Title changed: %s' % title)
        # MathJax changes the title once it has typeset all formulas.
        if title == markup.MATHJAX_FINISHED:
            self._print(frame)

    def _load_finished_cb(self, view, frame):
        logging.info('Loading done')
        # If there's a formula, it is typeset after the load-finished signal.
        if not self.contains_mathjax:
            self._print(frame)

    def _load_error_cb(self, view, frame, url, gp):
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

        #self.webview.connect('populate-popup', self.on_populate_popup)
        self.webview.connect('button-press-event', self.on_button_press)

        self.search_text = ''
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

    def on_populate_popup(self, webview, menu):
        '''
        Unused
        '''

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


if __name__ == '__main__':
    logging.getLogger('').setLevel(logging.DEBUG)
    sys.path.insert(0, os.path.abspath("./../../"))
    text = 'PDF export works 1 www.heise.de $\\sum i^2$'
    html = markup.convert(text, 'xhtml', '/tmp')

    win = gtk.Window()
    win.connect("destroy", lambda w: gtk.main_quit())
    win.set_default_size(600, 400)

    vbox = gtk.VBox()

    def test_export():
        pdf_file = '/tmp/export-test.pdf'
        print_pdf(html, pdf_file)
        #os.system("evince " + pdf_file)

    button = gtk.Button("Export")
    button.connect('clicked', lambda button: test_export())
    vbox.pack_start(button, False, False)

    html_view = HtmlView()

    def high(view, frame):
        html_view.highlight("work")
    html_view.webview.connect('load-finished', high)

    html_view.load_html(html)

    html_view.set_editable(True)
    vbox.pack_start(html_view)

    win.add(vbox)
    win.show_all()

    gtk.main()
