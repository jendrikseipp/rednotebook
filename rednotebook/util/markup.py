# -*- coding: utf-8 -*-
from __future__ import with_statement

import os

from rednotebook import txt2tags
from rednotebook.util import filesystem

def _convertCategoriesToMarkup(categories, with_category_title=True):
	'Only add Category title if the text is displayed'
	if with_category_title:
		markup = '== Categories ==\n'
	else:
		markup = ''
		
	for category, entryList in categories.iteritems():
		markup += '- ' + category + '\n'
		for entry in entryList:
			markup += '  - ' + entry + '\n'
		markup += '\n\n'
	return markup

def getMarkupForDay(day, with_text=True, selected_categories=None, with_date=True):
	exportString = ''
	
	'Add date'
	if with_date:
		exportString += '= ' + str(day.date) + ' =\n\n'
		
	'Add text'
	if with_text:
		exportString += day.text
	
	'Add Categories'
	categoryContentPairs = day.getCategoryContentPairs()
	
	categories_of_this_day = map(lambda category: category.upper(), categoryContentPairs.keys())
	
	if selected_categories:
		export_categories = {}
		for selected_category in selected_categories:
			if selected_category.upper() in categories_of_this_day:
				export_categories[selected_category] = categoryContentPairs[selected_category]
	else:
		export_categories = categoryContentPairs
	
	
	if len(export_categories) > 0:
		exportString += '\n\n\n' + _convertCategoriesToMarkup(export_categories, \
															with_category_title=with_text)
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