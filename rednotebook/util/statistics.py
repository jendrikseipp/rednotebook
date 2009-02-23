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

class Statistics(object):
	def __init__(self, redNotebook):
		self.redNotebook = redNotebook
		
	def get_number_of_entries(self):
		pass
	
	def _getHTMLRow(self, key, value):
		return '<tr align="left">' +\
				'<td bgcolor="#e7e7e7">&nbsp;&nbsp;' + key + '</td>' +\
				'<td bgcolor="#aaaaaa">&nbsp;&nbsp;<b>' + str(value) + '</b></td>' + \
				'</tr>'
		
	
	def getStatsHTML(self):
		page = '<html><body bgcolor="#8e8e95"><table cellspacing="5" border="0" width="250">\n'
		stats = {
				'Number of Entries': self.redNotebook.getNumberOfEntries(),
				'Number of Words': self.redNotebook.getNumberOfWords(),
				}
		for key, value in stats.iteritems():
			page += self._getHTMLRow(key, value)
			
		page += '</body></table></html>'
		return page

		