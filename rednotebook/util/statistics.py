

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

		