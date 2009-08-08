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

from rednotebook import txt2tags
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


def getMarkupForDay(day, with_text=True, categories=None, date=None):#with_date=True):
	exportString = ''
	
	'Add date'
	if date:
		exportString += '= ' + date + ' =\n\n'
		
	'Add text'
	if with_text:
		exportString += day.text
	
	'Add Categories'
	categoryContentPairs = day.getCategoryContentPairs()
	
	categories_of_this_day = map(lambda category: category.upper(), categoryContentPairs.keys())
	
	if categories is not None:
		export_categories = {}
		for selected_category in categories:
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


#def get_toc_html(days):
#	
#	html = '''\
#<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
#<HTML>
#<HEAD>
#<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
#
#<STYLE TYPE="text/css">
#body {
#	font-family: sans-serif;
#}
#</STYLE>
#
#</HEAD><BODY BGCOLOR="white" TEXT="black">
#<FONT SIZE="4">
#</FONT></CENTER>
#
#<P>
#<B>Contents</B>
#
#</P>
#<UL>
#'''
#		
#	for day in days:
#		html += '<LI><A HREF="' + str(day) + '.html" TARGET="Content">' + str(day) + '</A>\n'
#		
#	html += '</UL></BODY></HTML>'
#	
#	return html
#
#
#def get_frameset_html(current_day):
#	return '''\
#<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Frameset//EN"
#   "http://www.w3.org/TR/html4/frameset.dtd">
#<html>
#<head>
#<title>RedNotebook</title>
#</head>
#
#<frameset cols="200,*">
#  <frame src="toc.html" name="navigation">
#  <frame src="%s.html" name="Content">
#</frameset>
#</html>
#''' % str(current_day)
#
#
#def preview_in_browser(days, current_day):
#	'''write the html to files in tmp dir'''
#	
#	if current_day not in days:
#		days.append(current_day)
#		
#	for day in days:
#		date_string = str(day)
#		markupText = getMarkupForDay(day, with_date=False)
#		headers = [dates.get_date_string(day.date), '', '']
#		html = convert(markupText, 'xhtml', headers)
#		utils.write_file(html, date_string + '.html')
#	
#	utils.write_file(get_toc_html(days), 'toc.html')
#		
#	utils.show_html_in_browser(get_frameset_html(current_day), 'RedNotebook.html')
	

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
				