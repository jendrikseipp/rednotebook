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

# Testing
if __name__ == '__main__':
	sys.path.insert(0, '../../')
	
import os
import logging
import warnings

import gtk
import gobject
	
#from rednotebook.external import interwibble

#try:
#	import webkit
#except ImportError:
#	webkit = None
	
	
def can_print_pdf():
	return False
	
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
	

class HtmlPrinter(object):#interwibble.UrlPrinter):
	'''
	Takes an html string and writes a PDF file to the disk
	Idea and code mostly taken from http://github.com/eeejay/interwibble
	'''
		
	def print_html(self, html, outfile):
		with open('tmpfile.html', 'w') as tmpfile:
			tmpfile.write(html)
		self.print_url('file://' + 'tmpfile.html', outfile)
		#self._webview.load_html_string(html, 'http://www.heise.de')
		
	def _print_status(self, status):
		logging.info(status)
		
	def _print_error(self, status):
		logging.error(status)
	

def print_pdf(html, filename):
	printer = HtmlPrinter('a4')
	printer.print_html(html, filename)
	return printer._webview
	
if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath("./../../"))
	from rednotebook.util import markup
	text = 'Hello PDF'
	html = markup.convert(text, 'html')#'<html><body></body></html>'
	print html
	print_pdf(html, '/tmp/export-test.pdf')
	
