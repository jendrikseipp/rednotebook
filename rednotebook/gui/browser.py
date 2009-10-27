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
	
import logging

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
	#if not has_attribute(frame
	return hasattr(frame, 'print_full')	
		
	return True
		
print can_print_pdf()
