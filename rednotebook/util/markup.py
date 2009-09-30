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

from __future__ import with_statement

import os
import logging

import pango
import gobject

# TODO: REMOVE
import sys
sys.path.insert(0, '/home/jendrik/projects/RedNotebook')

from rednotebook.external import txt2tags
from rednotebook.util import filesystem
from rednotebook.util import dates
from rednotebook.util import utils



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


def getMarkupForDay(day, with_text=True, categories=None, date=None):
	'''
	Used for exporting days
	'''
	exportString = ''
	
	# Add date
	if date:
		exportString += '= ' + date + ' =\n\n'
		
	# Add text
	if with_text:
		exportString += day.text
	
	# Add Categories
	categoryContentPairs = day.getCategoryContentPairs()
	
	if categories:
		categories = map(lambda string: str(string).lower(), categories)
		export_categories = dict((x,y) for (x, y) in categoryContentPairs.items()
						if x.lower() in categories)
	elif categories is None:
		# No restrictions
		export_categories = categoryContentPairs
	else:
		# "Export no categories" selected
		export_categories = []
	
	
	if export_categories:
		exportString += '\n\n\n' + _convertCategoriesToMarkup(export_categories, \
															with_category_title=with_text)
	elif with_text:
		exportString += '\n\n'
		
	# Only return the string, when there is text or there are categories
	# We don't want to list empty dates
	if export_categories or with_text:
		exportString += '\n\n\n'
		return exportString
	
	return ''
	

def _get_config(type):
	
	config = {}
	
	# Set the configuration on the 'config' dict.
	config = txt2tags.ConfigMaster()._get_defaults()
	
	# The Pre (and Post) processing config is a list of lists:
	# [ [this, that], [foo, bar], [patt, replace] ]
	config['postproc'] = []
	config['preproc'] = []
	
	if type == 'xhtml' or type == 'html':
		config['encoding'] = 'UTF-8'	   # document encoding
		config['toc'] = 0
		config['style'] = [os.path.join(filesystem.filesDir, 'stylesheet.css')]
		config['css-inside'] = 1
	
		# keepnote only recognizes "<strike>"
		config['postproc'].append(['(?i)(</?)s>', '\\1strike>'])
		
		# Allow line breaks, r'\\\\' are 2 \ for regexes
		config['postproc'].append([r'\\\\', '<BR>'])
		
	elif type == 'tex':
		config['encoding'] = 'utf8'
		config['preproc'].append(['€', 'Euro'])
		
		# Latex only allows whitespace and underscores in filenames if
		# the filename is surrounded by "...". This is in turn only possible
		# if the extension is omitted
		config['preproc'].append([r'\[""', r'["""'])
		config['preproc'].append([r'""\.', r'""".'])
		
		# Allow line breaks, r'\\\\' are 2 \ for regexes
		config['postproc'].append([r'\$\\backslash\$\$\\backslash\$', r'\\\\'])
		
	elif type == 'txt':
		# Allow line breaks, r'\\\\' are 2 \ for regexes
		config['postproc'].append([r'\\\\', '\n'])
		
	
	
	return config
	

def convert(txt, target, headers=None, options=None, append_whitespace=False):
	'''
	Code partly taken from txt2tags tarball
	'''
	
	# Here is the marked body text, it must be a list.
	txt = txt.split('\n')
	
	'''
	Without this HACK "First Line\nSecond Line" is rendered to
	"First LineSecond Line", but we want "First Line Second Line"
	
	We only need this for the keepnote input, the exports work fine
	'''
	if append_whitespace:
		def add_whitespace(line):
			if line.rstrip().endswith(r'\\'):
				return line.rstrip()
			else:
				return line + ' '
		txt = map(add_whitespace, txt)
	
	# Set the three header fields
	if headers is None:
		headers = ['', '', '']
	
	config = _get_config(target)
	
	config['outfile'] = txt2tags.MODULEOUT  # results as list
	config['target'] = target
	
	if options is not None:
		config.update(options)
	
	# Let's do the conversion
	try:
		headers   = txt2tags.doHeader(headers, config)
		body, toc = txt2tags.convert(txt, config)
		footer	= txt2tags.doFooter(config)
		toc = txt2tags.toc_tagger(toc, config)
		toc = txt2tags.toc_formatter(toc, config)
		full_doc  = headers + toc + body + footer
		finished  = txt2tags.finish_him(full_doc, config)
		result = '\n'.join(finished)
	
	# Txt2tags error, show the messsage to the user
	except txt2tags.error, msg:
		logging.error(msg)
		result = msg
	
	# Unknown error, show the traceback to the user
	except:
		result = txt2tags.getUnknownErrorMessage()
		logging.error(result)
		
	return result

def convert_to_pango(txt, headers=None, options=None):
	'''
	Code partly taken from txt2tags tarball
	'''
	original_txt = txt
	
	# Here is the marked body text, it must be a list.
	txt = txt.split('\n')
	
	# Set the three header fields
	if headers is None:
		headers = ['', '', '']
	
	config = txt2tags.ConfigMaster()._get_defaults()
	
	config['outfile'] = txt2tags.MODULEOUT  # results as list
	config['target'] = 'xhtml'
	
	# Allow line breaks, r'\\\\' are 2 \ for regexes
	config['postproc'] = []
	config['postproc'].append([r'\\\\', '\n'])
	
	if options is not None:
		config.update(options)
	
	# Let's do the conversion
	try:
		body, toc = txt2tags.convert(txt, config)
		full_doc  = body
		finished  = txt2tags.finish_him(full_doc, config)
		result = ''.join(finished)
	
	# Txt2tags error, show the messsage to the user
	except txt2tags.error, msg:
		logging.error(msg)
		result = msg
	
	# Unknown error, show the traceback to the user
	except:
		result = txt2tags.getUnknownErrorMessage()
		logging.error(result)
		
	# remove unwanted paragraphs
	result = result.replace('<p>', '').replace('</p>', '')
	
	logging.log(5, 'Converted "%s" text to "%s" txt2tags markup' % (original_txt, result))

	try:
		attr_list, plain, accel = pango.parse_markup(result)
		
		# result is valid pango markup, return the markup
		return result
	except gobject.GError:
		# There are unknown tags in the markup, return the original text
		logging.debug('There are unknown tags in the markup: %s' % result)
		return original_txt
	
	
def convert_from_pango(pango_markup):
	original_txt = pango_markup
	replacements = dict((('<b>', '**'), ('</b>', '**'),
						('<i>', '//'), ('</i>', '//'),
						('<s>', '--'), ('</s>', '--'),
						('<u>', '__'), ('</u>', '__'),
						('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'),
						))
	for orig, repl in replacements.items():
		pango_markup = pango_markup.replace(orig, repl)
		
	logging.log(5, 'Converted "%s" pango to "%s" txt2tags' % \
				(original_txt, pango_markup))
	return pango_markup


def get_table_markup(table):
	'''
	table is a list of lists
	
	return the txt2tags markup for that table
	'''
	table = map(lambda row: (str(cell) for cell in row), table)
	table = map(lambda row: '| ' + ' | '.join(row) + ' |', table)
	table[0] = '|' + table[0]
	return '\n'.join(table)


if __name__ == '__main__':
	markup = '''\
normal text, normal_text_with_underscores and ""raw_text_with_underscores""

[Link ""http://www.co.whatcom.wa.us/health/environmental/site_hazard/sitehazard.jsp""]

[hs_err_pid13673.log ""file:///home/jendrik/hs_err_pid13673.log""]

[""/home/jendrik/Desktop/desktop pics/bg8_karte_s1_rgb"".jpg]'''

	latex = convert(markup, 'tex')
	print latex
	
	html = convert(markup, 'xhtml')
	#print html
	
	
				
