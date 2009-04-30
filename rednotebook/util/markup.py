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


def getMarkupForDay(day, with_text=True, selected_categories=None, with_date=True):
	exportString = ''
	
	'Add date'
	if with_date:
		exportString += '= ' + dates.get_date_string(day.date) + ' =\n\n'
		
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


def convertMarkupToTarget(markup, target, title=''):
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
	elif target == 'html' or target == 'xhtml':
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


def get_toc_html(days):
	
	html = '''\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<HEAD>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">

<STYLE TYPE="text/css">
body {
	font-family: sans-serif;
}
</STYLE>

</HEAD><BODY BGCOLOR="white" TEXT="black">
<FONT SIZE="4">
</FONT></CENTER>

<P>
<B>Contents</B>

</P>
<UL>
'''
		
	for day in days:
		html += '<LI><A HREF="' + str(day) + '.html" TARGET="Content">' + str(day) + '</A>\n'
		
	html += '</UL></BODY></HTML>'
	
	return html


def get_frameset_html(current_day):
	return '''\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Frameset//EN"
   "http://www.w3.org/TR/html4/frameset.dtd">
<html>
<head>
<title>RedNotebook</title>
</head>

<frameset cols="200,*">
  <frame src="toc.html" name="navigation">
  <frame src="%s.html" name="Content">
</frameset>
</html>
''' % str(current_day)


def preview_in_browser(days, current_day):
	'''write the html to files in tmp dir'''
	
	if current_day not in days:
		days.append(current_day)
		
	for day in days:
		date_string = str(day)
		markupText = getMarkupForDay(day, with_date=False)
		html = convertMarkupToTarget(markupText, 'xhtml', \
									title=dates.get_date_string(day.date))
		utils.write_file(html, date_string + '.html')
	
	utils.write_file(get_toc_html(days), 'toc.html')
		
	utils.show_html_in_browser(get_frameset_html(current_day), 'RedNotebook.html')
	

def convert_markup_to_html(txt, headers=None):
	'''
	Code partly taken from txt2tags tarball
	'''
	
	# Here is the marked body text, it must be a list.
	txt = txt.split('\n')
	
	# Set the three header fields
	if headers is None:
		headers = ['', '', '']
	
	# Set the configuration on the 'config' dict.
	config = txt2tags.ConfigMaster()._get_defaults()
	config['outfile'] = txt2tags.MODULEOUT  # results as list
	config['target'] = 'html'			   # target type: HTML
	config['encoding'] = 'UTF-8'	   # document encoding
	config['toc'] = 1	   # document encoding
	#config['css-sugar'] = 1                 # CSS flag
	
	# The Pre (and Post) processing config is a list of lists:
	# [ [this, that], [foo, bar], [patt, replace] ]
	#config['preproc'] = []
	#config['preproc'].append(['nice','VERY NICE'])
	#config['preproc'].append(['day','life'])
	
	# Let's do the conversion
	try:
		headers   = txt2tags.doHeader(headers, config)
		body, toc = txt2tags.convert(txt, config)
		footer	= txt2tags.doFooter(config)
		toc = txt2tags.toc_tagger(toc, config)
		toc = txt2tags.toc_formatter(toc, config)
		full_doc  = headers + toc + body + footer
		finished  = txt2tags.finish_him(full_doc, config)
		html = '\n'.join(finished)
	
	# Txt2tags error, show the messsage to the user
	except txt2tags.error, msg:
		print msg
		html = msg
	
	# Unknown error, show the traceback to the user
	except:
		html = txt2tags.getUnknownErrorMessage()
		print html
		
	return html
				