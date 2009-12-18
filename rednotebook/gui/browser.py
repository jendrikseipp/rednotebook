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

# For Python 2.5 compatability.
from __future__ import with_statement

import sys

# Testing
if __name__ == '__main__':
	sys.path.insert(0, '../../')
	
import os
import logging
import warnings

import gtk
import gobject

# Fix for pywebkitgtk 1.1.5
#gtk.gdk.threads_init() # only initializes threading in the glib/gobject module
gobject.threads_init() # also initializes the gdk threads
	

try:
	import webkit
except ImportError:
	webkit = None
	
	
def can_print_pdf():	
	if not webkit:
		logging.info('Importing webkit failed')
		return False
		
	try:
		printer = HtmlPrinter()
	except TypeError, err:
		logging.info('UrlPrinter could not be created: "%s"' % err)
		return False
	
	frame = printer._webview.get_main_frame()
	
	return hasattr(frame, 'print_full')
	

def print_pdf(html, filename):
	printer = HtmlPrinter()
	printer.print_html(html, filename)



class HtmlPrinter(object):
	'''
	Idea and some code taken from interwibble, 
	"A non-interactive tool for converting any given website to PDF"
	
	(http://github.com/eeejay/interwibble/)
	'''
	PAPER_SIZES = {'a3'		: gtk.PAPER_NAME_A3,
				   'a4'		: gtk.PAPER_NAME_A4,
				   'a5'		: gtk.PAPER_NAME_A5,
				   'b5'		: gtk.PAPER_NAME_B5,
				   'executive' : gtk.PAPER_NAME_EXECUTIVE,
				   'legal'	 : gtk.PAPER_NAME_LEGAL,
				   'letter'	: gtk.PAPER_NAME_LETTER}
				   
	def __init__(self, paper='a4'):
		self._webview = webkit.WebView()
		webkit_settings = self._webview.get_settings()
		webkit_settings.set_property('enable-plugins', False)
		self._webview.connect('load-error', self._load_error_cb)
		self._paper_size = gtk.PaperSize(self.PAPER_SIZES[paper])
		
	def print_html(self, html, outfile):
		handler = self._webview.connect(
			'load-finished', self._load_finished_cb, outfile)
		self._webview.load_html_string(html, 'http://rednotebook-export.html');
		
		self._print_status('Loading URL...')

		if hasattr(warnings, 'catch_warnings'):
			with warnings.catch_warnings():
				warnings.simplefilter("ignore")
				while gtk.events_pending():
					gtk.main_iteration()
		else:
			while gtk.events_pending():
				gtk.main_iteration()

		self._webview.disconnect(handler)

	def _load_finished_cb(self, view, frame, outfile):
		self._print_status('Loading done')
		print_op = gtk.PrintOperation()
		print_settings = print_op.get_print_settings() or gtk.PrintSettings()
		print_settings.set_paper_size(self._paper_size)
		print_op.set_print_settings(print_settings)
		print_op.set_export_filename(os.path.abspath(outfile))
		self._print_status('Exporting PDF...')
		print_op.connect('end-print', self._end_print_cb)
		try:
			frame.print_full(print_op, gtk.PRINT_OPERATION_ACTION_EXPORT)
			while gtk.events_pending():
				gtk.main_iteration()
		except gobject.GError, e:
			self._print_error(e.message)

	def _load_error_cb(self, view, frame, url, gp):
		self._print_error("Error loading %s" % url)
	
	def _end_print_cb(self, *args):
		self._print_status('Exporting done')

	def _print_error(self, status):
		logging.error(status)
		
	def _print_status(self, status):
		logging.info(status)
	

class HtmlView(gtk.ScrolledWindow):
	def __init__(self, *args, **kargs):
		gtk.ScrolledWindow.__init__(self, *args, **kargs)
		self.webview = webkit.WebView()
		self.add(self.webview)
		self.show_all()
		
	def load_html(self, html):
		html = self.webview.load_html_string(html, 'http://')
								
	def get_html(self):
		pass
	
	def set_editable(self, editable):
		self.webview.set_editable(editable)
		
	def set_font_size(self, size):
		if size <= 0:
			zoom = 1
		else:
			zoom = size / 10.0
		self.webview.set_zoom_level(zoom)
		
	def highlight(self, string):
		# Mark all occurences of "string", case-insensitive, no limit
		print 'Highlight'
		self.webview.mark_text_matches(string, False, 0)
		self.webview.set_highlight_text_matches(True)
	
if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath("./../../"))
	from rednotebook.util import markup
	text = 'PDF export works'
	html = markup.convert(text, 'xhtml')
	
	win = gtk.Window()
	win.connect("destroy", lambda w: gtk.main_quit())
	win.set_default_size(600,400)
	
	vbox = gtk.VBox()
	
	button = gtk.Button("Export")
	button.connect('clicked', lambda button: print_pdf(html, '/tmp/export-test.pdf'))
	vbox.pack_start(button, False, False)
	
	html_view = HtmlView()
	html_view.load_html(html)
	html_view.highlight("work")
	vbox.pack_start(html_view)
	
	win.add(vbox)
	win.show_all()
	
	gtk.main()
	
