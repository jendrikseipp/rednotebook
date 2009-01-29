# -*- coding: utf-8 -*-
from __future__ import with_statement

import os

from rednotebook import txt2tags
from rednotebook.util import filesystem

def _convertCategoriesToMarkup(categories):
	markup = '== Categories ==\n'
	for category, entryList in categories.iteritems():
		markup += '- ' + category + '\n'
		for entry in entryList:
			markup += '  - ' + entry + '\n'
		markup += '\n\n'
	return markup

def getMarkupForDay(day, withDate=True):
	'Add date and text'
	if withDate:
		exportString = '= ' + str(day.date) + ' =\n\n' + day.text
	else:
		exportString = day.text
	
	'Add Categories'
	categoryContentPairs = day.getCategoryContentPairs()
	
	if len(categoryContentPairs) > 0:
		exportString += '\n\n\n' + _convertCategoriesToMarkup(categoryContentPairs)
	else:
		exportString += '\n\n'
	
	exportString += '\n\n\n'
	return exportString

def convertMarkupToTarget(markup, target, title):
	markup = title + '\n\n\n' + markup #no author provided
	markup = markup.splitlines()
	
	source = txt2tags.process_source_file(contents=markup)			
	
	full_parsed, headConfBody = source
	
	parameters = {'target': target,}
	
	'Important: do not forget ":" after preproc'
	
	'''
	Euro signs do not work in Latex, but they also cannot be
	substituted by txt2tags
	'''
	
	if target == 'tex':
		parameters.update({'encoding': 'utf8',	
							#'preproc': [('€', 'Euro'), ('w', 'WWWW'), ('a', 'AAAA'),],
							})
	elif target == 'html':
		parameters.update({'encoding': 'UTF-8',
						'style': [os.path.join(filesystem.filesDir, 'stylesheet.css')],
						'css-inside': 1,
						})
		
	
	full_parsed.update(parameters)
	
	source = txt2tags.convert_this_files([source])[0]
	
	output = ''
	for line in source:
		output += line + '\n'
	
	return output