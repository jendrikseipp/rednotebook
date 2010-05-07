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
import datetime

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath("./../../"))

from rednotebook.redNotebook import Day, Month

class ImportDay(Day):
	'''
	text is set and retrieved with the property "text"
	'''
	def __init__(self, year, month, day):
		import_month = Month(year, month)
		Day.__init__(self, import_month, day)
		
		
class Importer(object):
	def __init__():
		pass
		
	def get_days(self):
		pass
		
		
if __name__ == '__main__':
	'''
	Run some tests
	'''
	a = ImportDay(2010,5,7)
	a.text = 'a_text'
	a.add_category_entry('c1', 'e1')
	a.add_category_entry('c2', 'e2')
	a.add_category_entry('c4', 'e5')

	print a.content
	
	b = ImportDay(2010,5,7)
	b.text = 'b_text'
	b.add_category_entry('c1', 'e1')
	b.add_category_entry('c2', 'e3')
	b.add_category_entry('c3', 'e4')
	
	a.merge(b)
	
	assert a.text == 'a_text\n\nb_text'
	assert a.tree == {'c1': {'e1': None}, 'c2': {'e2': None, 'e3':None}, \
			'c4': {'e5': None}, 'c3': {'e4': None},}, a.tree
			
	print 'ALL TESTS SUCCEEDED'
	

plaintext_module = __import__('plaintext')
print dir(plaintext_module)
p = getattr(plaintext_module, 'aha')
p = plaintext_module.PlainTextImporter()
	

		
	
