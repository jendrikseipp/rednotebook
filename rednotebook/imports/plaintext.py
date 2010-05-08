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
	
from rednotebook.imports import ImportDay, Importer

#from __init__ import Importer

NAME = 'Plain Text'
DESCRIPTION = 'Import Text from plain textfiles'
REQUIREMENTS = []

class PlainTextImporter(Importer):
	def get_days():
		day = Day(2010, 5, 7)
		day.text = 'test text'
		day.add_category_entry('cat', 'dog')
		return [day]
		
	

