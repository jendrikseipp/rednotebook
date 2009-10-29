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

# Testing
if __name__ == '__main__':
	import sys
	sys.path.insert(0, '../../')
	
import sys
import os
import logging
import warnings

import gtk
import glib

from rednotebook.external import interwibble

try:
	import webkit
except ImportError:
	webkit = None
	
def can_print_pdf():
	if not webkit:
		logging.info('Importing webkit failed')
		return False
	
	try:
		from rednotebook.external import interwibble
	except ImportError:
		logging.info('Importing interwibble failed')
		return False
		
	try:
		printer = interwibble.UrlPrinter()
	except TypeError, err:
		logging.info('UrlPrinter could not be created: "%s"' % err)
		return False
	
	frame = printer._webview.get_main_frame()
	
	return hasattr(frame, 'print_full')
	

class HtmlPrinter(interwibble.UrlPrinter):
	'''
	Takes an html string and writes a PDF file to the disk
	Idea and code mostly taken from http://github.com/eeejay/interwibble
	'''
	def print_html(self, html, outfile):
		self._webview.load_html_string(html, 'http://www.pseudo.com')
		self.handler = self._webview.connect(
			'load-finished', self._load_finished_cb, outfile)

		self._print_status('Loading HTML... ')

		#self._webview.disconnect(handler)
		
	def _load_finished_cb(self, view, frame, outfile):
		self._webview.disconnect(self.handler)
		self._print_status('Done.')
		print_op = gtk.PrintOperation()
		print_op.set_export_filename(os.path.abspath(outfile))
		self._print_status('Exporting PDF... ')
		print_op.connect('end-print', self._end_print_cb)
		try:
			frame.print_full(print_op, gtk.PRINT_OPERATION_ACTION_EXPORT)
		except glib.GError, e:
			self._print_error(e.message)
			##gtk.main_quit()
			
	def _load_error_cb(self, view, frame, url, gp):
		self._print_error("Error loading %s\n" % url)
		##gtk.main_quit()
			
	def _end_print_cb(self, *args):
		self._print_status('Done.')
		##gtk.main_quit()
		
	def _print_status(self, status):
		logging.info(status)
		
	def _print_error(self, status):
		logging.error(status)
	

def print_pdf(html, filename):
	# TODO: Implement
	printer = HtmlPrinter()
	printer.print_html(html, filename)
	
