#!/usr/bin/env python
#
# (C) Copyright 2009 Eitan Isaacson <eitan@monotonous.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License Version
# 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

'''A non-interactive tool for converting any given website to PDF'''

# For Python 2.5 compatability.
from __future__ import with_statement

import gtk

## Jendrik:
## Fix for pywebkitgtk 1.1.5
gtk.gdk.threads_init()

import webkit, glib
import warnings
import sys
import os

VERSION = '0.1'

class UrlPrinter(object):
    PAPER_SIZES = {'a3'        : gtk.PAPER_NAME_A3,
                   'a4'        : gtk.PAPER_NAME_A4,
                   'a5'        : gtk.PAPER_NAME_A5,
                   'b5'        : gtk.PAPER_NAME_B5,
                   'executive' : gtk.PAPER_NAME_EXECUTIVE,
                   'legal'     : gtk.PAPER_NAME_LEGAL,
                   'letter'    : gtk.PAPER_NAME_LETTER}
    def __init__(self, paper, verbose=True):
        self._webview = webkit.WebView()
        webkit_settings = self._webview.get_settings()
        webkit_settings.set_property('enable-plugins', False)
        self._webview.connect('load-error', self._load_error_cb)
        self._verbose = verbose
        self._loop = glib.MainLoop()
        self._paper_size = gtk.PaperSize(self.PAPER_SIZES[paper])

    def print_url(self, url, outfile):
        self._webview.open(url)
        handler = self._webview.connect(
            'load-finished', self._load_finished_cb, outfile)

        self._print_status('Loading URL... ')

        if hasattr(warnings, 'catch_warnings'):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._loop.run()
        else:
            self._loop.run()

        self._webview.disconnect(handler)

    def _load_finished_cb(self, view, frame, outfile):
        self._print_status('Done.\n')
        print_op = gtk.PrintOperation()
        print_settings = print_op.get_print_settings() or gtk.PrintSettings()
        print_settings.set_paper_size(self._paper_size)
        print_op.set_print_settings(print_settings)
        print_op.set_export_filename(os.path.abspath(outfile))
        self._print_status('Exporting PDF... ')
        print_op.connect('end-print', self._end_print_cb)
        try:
            frame.print_full(print_op, gtk.PRINT_OPERATION_ACTION_EXPORT)
        except glib.GError, e:
            self._print_error(e.message+'\n')
            self._loop.quit()

    def _load_error_cb(self, view, frame, url, gp):
        self._print_error("Error loading %s\n" % url)
        self._loop.quit()
    
    def _end_print_cb(self, *args):
        self._print_status('Done.\n')
        self._loop.quit()

    def _print_error(self, status):
        sys.stderr.write(status)
        sys.stderr.flush()
        
    def _print_status(self, status):
        if self._verbose:
            sys.stdout.write(status)
            sys.stdout.flush()

if __name__ == "__main__":
    from optparse import OptionParser
    from urllib import quote_plus
    from urlparse import urljoin

    gtk.gdk.threads_init()

    parser = OptionParser(usage="usage: %prog [options] URL [outfile]",
                          version="%prog "+VERSION)
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")
    parser.add_option("-p", "--paper",
                      action="store", dest="paper", 
                      default=gtk.paper_size_get_default().split('_')[-1],
                      help="paper type, one of: %s" % \
                          ", ".join(UrlPrinter.PAPER_SIZES.keys()))
    
    (options, args) = parser.parse_args()

    if not args:
        parser.error("need a URL")

    if not UrlPrinter.PAPER_SIZES.has_key(options.paper.lower()):
        parser.error("unknown paper type, possible options:\n %s" % \
                         '\n '.join(UrlPrinter.PAPER_SIZES.keys()))

    if len(args) < 2:
        args.append(quote_plus(args[0])+'.pdf')

    url, outfile = args[:2]

    if os.path.exists(url):
        # It's a local file.
        url = urljoin('file://', os.path.abspath(url))

    url_printer = UrlPrinter(options.paper, options.verbose)
    
    url_printer.print_url(url, outfile)
