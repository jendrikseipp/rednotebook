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

import gtk
import sys
import os.path
import pango
import logging
import re

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath("./../../"))
	logging.getLogger('').setLevel(logging.DEBUG)

from rednotebook.external import gtkcodebuffer
from rednotebook.external import txt2tags
#from rednotebook.gui.richtext import HtmlEditor
from rednotebook.gui.browser import HtmlView
from rednotebook.util import markup




class MultiPattern(gtkcodebuffer.Pattern):
	'''
	Extension of the Pattern class that allows a pattern to have
	subgroups with different formatting
	'''
	def __init__(self, pattern_or_regex, group_tag_pairs, **kwargs):
		if type(pattern_or_regex) == str:
			pattern = pattern_or_regex
		else:
			pattern = pattern_or_regex.pattern
		gtkcodebuffer.Pattern.__init__(self, pattern, **kwargs)

		self.group_tag_pairs = group_tag_pairs

	def __call__(self, txt, start, end):
		m = self._regexp.search(txt)
		if not m: return None

		iter_pairs = []

		for group, tag_name in self.group_tag_pairs:
			group_matched = bool(m.group(group))
			if not group_matched:
				continue
			mstart, mend = m.start(group), m.end(group)
			s = start.copy(); s.forward_chars(mstart)
			e = start.copy(); e.forward_chars(mend)
			iter_pairs.append([s, e, tag_name])
		print 'GROUP', m.group(0)

		return iter_pairs
		
		
class Rule(object):
	'''
	Extension of the Pattern class that allows a pattern to have
	subgroups with different formatting
	'''
	def __init__(self, regex, group_tag_pairs, **kwargs):
		#gtkcodebuffer.Pattern.__init__(self, regexp, **kwargs)
		self.regex = regex
		self.group_tag_pairs = group_tag_pairs

	def __call__(self, txt, start, end):
		m = self.regex.search(txt)
		if not m: return None

		iter_pairs = []
		
		groups = len(m.groups()) + 1#[m.group(0)] + m.groups()

		for group, tag_name in self.group_tag_pairs:
			print 'GROUP', group, m.group(group)
			mstart, mend = m.start(group), m.end(group)
			s = start.copy(); s.forward_chars(mstart)
			e = start.copy(); e.forward_chars(mend)
			#tag_name = self.group_tag_pairs[group]
			iter_pairs.append([s, e, tag_name])

		return iter_pairs


class OverlapLanguageDefinition(object):
	
	def __init__(self, rules):
		self.rules = rules
		self.styles = dict()
		
	def get_styles(self):
		return self.styles

	def __call__(self, buf, start, end):
		mstart = end.copy()
		mend = end.copy()
		#mtag   = None
		txt = buf.get_slice(start, end)

		selected_pairs = None

		# search min match
		#logging.debug('Testing %s rules' % len(self._successful_rules))
		for rule in self._successful_rules[:]:
			print rule._regexp.pattern
			# search pattern
			iter_pairs = rule(txt, start, end)
			if not iter_pairs:
				## This rule will not find anything in the next round either
				self._successful_rules.remove(rule)
				continue
				
			print 'FOUND'
			for s, e, tag in iter_pairs:
				print buf.get_slice(s, e), '->', tag

			key = lambda iter: iter.get_offset()

			min_start = min([start_iter for start_iter, end_iter, tag_name in iter_pairs], key=key)
			iters = [start_iter for start_iter, end_iter, tag_name in iter_pairs]
			print 'ITERS', map(key, iters)
			iters = sorted(iters, key=key)
			print 'ITERS', map(key, iters)
			min_start2 = sorted([start_iter for start_iter, end_iter, tag_name in iter_pairs], key=key)[0]
			assert min_start.equal(min_start2)
			max_end = end#max([end_iter for start_iter, end_iter, tag_name in iter_pairs], key=key)
			
			print 'FOUND2'
			for s, e, tag in iter_pairs:
				print buf.get_slice(s, e), '->', tag
			
			#min_start_end = min_start.copy()
			#min_start_end.forward_to_line_end()
			print 'MIN_START', buf.get_slice(min_start, buf.get_end_iter())
			
			mstart_end = mstart.copy()
			mstart_end.forward_to_line_end()
			print 'MSTART', buf.get_slice(mstart, mstart_end)

			# prefer match with smallest start-iter
			if min_start.compare(mstart) == -1:
				print 'SMALLER'
				for s, e, tag in iter_pairs:
					print buf.get_slice(s, e), '->', tag
				mstart, mend = min_start.copy(), max_end.copy()
				#mtag = rule.tag_name
				selected_pairs = iter_pairs
				continue

			##if m[0].compare(mstart)==0 and m[1].compare(mend)>0:
			if min_start.equal(mstart) and max_end.compare(mend) > 0:
				print 'EQUAL'
				mstart, mend = min_start, max_end
				#mtag = rule.tag_name
				selected_pairs = iter_pairs
				continue
		#print 'SELECTED'
		#for s, e, tag in selected_pairs:
		#	print buf.get_slice(s, e), '->', tag
		return selected_pairs#(mstart, mend, mtag)


class OverlapCodeBuffer(gtkcodebuffer.CodeBuffer):
	
	def __init__(self, table=None, lang=None, styles={}):
		""" The constructor takes 3 optional arguments. 
		
			table specifies a tag-table associated with the TextBuffer-instance.
			This argument will be passed directly to the constructor of the 
			TextBuffer-class. 
			
			lang specifies the language-definition. You have to load one using
			the SyntaxLoader-class or you may hard-code your syntax-definition 
			using the LanguageDefinition-class. 
			
			styles is a dictionary used to extend or overwrite the default styles
			provided by this module (DEFAULT_STYLE) and any language specific 
			styles defined by the LanguageDefinition. """
		gtk.TextBuffer.__init__(self, table)
					   			   
		# update styles with user-defined
		self.styles = styles
		
		# create tags
		for name, props in self.styles.items():
			style = {}#dict(self.styles['DEFAULT'])	# take default
			style.update(props)					 # and update with props
			self.create_tag(name, **style)
		
		# store lang-definition
		self._lang_def = lang
		
		self.connect_after("insert-text", self._on_insert_text)
		self.connect_after("delete-range", self._on_delete_range)
		#self.connect('apply-tag', self._on_apply_tag)

	def get_slice(self, start, end):
		'''
		We have to search for the regexes in utf-8 text
		'''
		slice_text = gtkcodebuffer.CodeBuffer.get_slice(self, start, end)
		slice_text = slice_text.decode('utf-8')
		return slice_text

	def _on_insert_text(self, buf, it, text, length):
		end = it.copy()
		start = it.copy()
		start.backward_chars(length)

		self.update_syntax(start, end)

	def _on_delete_range(self, buf, start, end):
		start = start.copy()

		self.update_syntax(start, start)
		
	def remove_all_syntax_tags(self, start, end):
		'''
		Do not remove the gtkspell highlighting
		'''
		for style in self.styles:
			self.remove_tag_by_name(style, start, end)

	def update_syntax(self, start, end):
		""" More or less internal used method to update the
			syntax-highlighting. """
		'''
		Use two categories of rules: one-line and multiline
		
		Before running multiline rules: Check if e.g. - is present in changed string
		'''
			
		# Just update from the start of the first edited line 
		# to the end of the last edited line, because we can
		# guarantee that there's no multiline rule
		start_line_number = start.get_line()
		start_line_iter = self.get_iter_at_line(start_line_number)
		start = start_line_iter
		
		end.forward_to_line_end()
		
		text = self.get_text(start, end)
		logging.debug('Update \n"%s"' % text)

		# We can omit those rules without occurrences in later searches

		# Reset rules
		self._lang_def._successful_rules = self._lang_def.rules[:]
		
		# remove all tags from start to end
		self.remove_all_syntax_tags(start, end)

		# We do not use recursion -> long files exceed rec-limit!
		#finished = False
		while not start == end:#not finished:
			
			# search first rule matching txt[start..end]
			group_iters_and_tags = self._lang_def(self, start, end)

			if not group_iters_and_tags:
				return

			key = lambda iter: iter.get_offset()

			#min_start = min([start_iter for start_iter, end_iter, tag_name \
			#							in group_iters_and_tags], key=key)
			max_end = max([end_iter for start_iter, end_iter, tag_name \
										in group_iters_and_tags], key=key)

			for mstart, mend, tagname in group_iters_and_tags:
				# apply tag
				self.apply_tag_by_name(tagname, mstart, mend)
				#self.apply_tag_by_name('red', mstart, mend)
				#print 'APPLYING', tagname, 'to', self.get_text(mstart, mend)

			# Set new start
			start = max_end





# additional style definitions:
# the update_syntax() method of CodeBuffer allows you to define new and modify
# already defined styles. Think of it like CSS.
styles = {	'DEFAULT':   		{'font': 'sans'},#{'font': 'serif'},
			'bold':	  			{'weight': pango.WEIGHT_BOLD},
			'comment':   		{'foreground': 'gray'},
			'underlined':   	{'underline': pango.UNDERLINE_SINGLE},
			'grey':				{'foreground': 'gray'},
			'red':				{'foreground': 'red'},
			'italic':			{	# Just to be sure we live this in
									'style': pango.STYLE_ITALIC,
									# The font:Italic is actually needed
									'font': 'Italic'},
			'strikethrough':	{'strikethrough': True},
			'header':			{'weight': pango.WEIGHT_ULTRABOLD,
								'scale': pango.SCALE_XX_LARGE,
								# causes PangoWarnings on Windows
								#'variant': pango.VARIANT_SMALL_CAPS,
								},
			'raw':				{'font': 'Oblique'},
			'verbatim':			{'font': 'monospace'},
			'tagged':			{},
			'link':				{'foreground': 'blue',
								'underline': pango.UNDERLINE_SINGLE,},
			}

# Syntax definition

bank = txt2tags.getRegexes()
bold = MultiPattern(bank['fontBold'], [(0, 'grey'), (1, 'bold'),])

def get_pattern(char, style):
	# original strikethrough in txt2tags: r'--([^\s](|.*?[^\s])-*)--'
	# txt2tags docs say that format markup is greedy, but
	# that doesn't seem to be the case
	
	# Either one char, or two chars with (maybe empty) content
	# between them
	# In both cases no whitespaces between chars and markup
	#regex = r'(%s)(\S.*\S)(%s)' % ((markup_symbols, ) * 2)
	regex = r'(%s%s)(\S|.*?\S%s*)(%s%s)' % ((char, ) * 5)
	group_style_pairs = [(1, 'grey'), (2, style), (3, 'grey')]
	return MultiPattern(regex, group_style_pairs)


list    = MultiPattern(r"^ *(- )[^ ].*$",  [(1, 'red'), (1, 'bold')])
numlist = MultiPattern(r"^ *(\+ )[^ ].*$", [(1, 'red'), (1, 'bold')])

comment = MultiPattern(r'^(\%.*)$', [(1, 'comment')])

line = MultiPattern(r'^[\s]*([_=-]{20,})[\s]*$', [(1, 'bold')])

# Whitespace is allowed, but nothing else
#header = MultiPattern(r'^[\s]*(===)([^=]|[^=].*[^=])(===)[\s]*$', \
#						[(1, 'grey'), (2, 'header'), (3, 'grey')])

title_style = [(1, 'grey'), (2, 'header'), (3, 'grey'), (4, 'grey')]
titskel = r'^ *(%s)(%s)(\1)(\[[\w-]*\])?\s*$'
title_pattern    = titskel % ('[=]{1,5}','[^=]|.*[^=]')
numtitle_pattern = titskel % ('[+]{1,5}','[^+]|.*[^+]')
title = MultiPattern(title_pattern, title_style)
numtitle = MultiPattern(numtitle_pattern, title_style)

linebreak = MultiPattern(r'(\\\\)', [(1, 'grey')])

# pic [""/home/user/Desktop/RedNotebook pic"".png]
# \w = [a-zA-Z0-9_]
# Added ":-" for "file://5-5.jpg"
# filename = One char or two chars with possibly whitespace in the middle
#filename = r'\S[\w\s_,.+%$#@!?+~/-:-\(\)]*\S|\S'
filename = r'\S.*\S|\S'
ext = r'png|jpe?g|gif|eps|bmp'
pic = MultiPattern(r'(\["")(%s)("")(\.%s)(\?\d+)?(\])' % (filename, ext), \
		[(1, 'grey'), (2, 'bold'), (3, 'grey'), (4, 'bold'), (5, 'grey'), (6, 'grey')], flags='I')

# named link on hdd [hs err_pid9204.log ""file:///home/jendrik/hs err_pid9204.log""]
# named link in web [heise ""http://heise.de""]
named_link = MultiPattern(r'(\[)(.*)\s("")(\S.*\S)(""\])', \
		[(1, 'grey'), (2, 'link'), (3, 'grey'), (4, 'grey'), (5, 'grey')], flags='LI')

# link http://heise.de
# Use txt2tags link guessing mechanism
link_regex = bank['link']
link = MultiPattern(r'overwritten', [(0, 'link')])
link._regexp = link_regex

# We do not support multiline regexes
#blockverbatim = MultiPattern(r'^(```)\s*$\n(.*)$\n(```)\s*$', [(1, 'grey'), (2, 'verbatim'), (3, 'grey')])


rules = [
		get_pattern('\*', 'bold'),
		get_pattern('_', 'underlined'),
		get_pattern('/', 'italic'),
		get_pattern('-', 'strikethrough'),
		title,
		numtitle,
		list,
		numlist,
		comment,
		line,
		get_pattern('"', 'raw'),
		get_pattern('`', 'verbatim'),
		get_pattern("'", 'tagged'),
		linebreak,
		pic,
		named_link,
		link,
		]


def get_highlight_buffer():
	# create lexer:
	lang = OverlapLanguageDefinition(rules)

	# create buffer and update style-definition
	buff = OverlapCodeBuffer(lang=lang, styles=styles)

	return buff

# Testing
if __name__ == '__main__':
	
	txt = """== Main==[oho] 
=== Header ===
 **bold**, //italic//,/italic/__underlined__, --strikethrough--

[""/home/user/Desktop/RedNotebook pic"".png]

[hs error.log ""file:///home/user/hs error.log""]
```
[heise ""http://heise.de""]
```
www.heise.de, alex@web.de

''$a^2$''  ""über oblique""  ``code mit python``

====================

% list-support
- a simple list item
- an other


+ An ordered list
+ other item


"""

	buff = get_highlight_buffer()

	win = gtk.Window(gtk.WINDOW_TOPLEVEL)
	scr = gtk.ScrolledWindow()

	html_editor = HtmlView()

	def change_text(widget):
		html = markup.convert(widget.get_text(widget.get_start_iter(), \
								widget.get_end_iter()), \
							  'xhtml', append_whitespace=True)

		html_editor.load_html(html)

	buff.connect('changed', change_text)

	vbox = gtk.VBox()
	vbox.pack_start(scr)
	vbox.pack_start(html_editor)
	win.add(vbox)
	scr.add(gtk.TextView(buff))

	win.set_default_size(900,1000)
	win.set_position(gtk.WIN_POS_CENTER)
	win.show_all()
	win.connect("destroy", lambda w: gtk.main_quit())

	buff.set_text(txt)

	gtk.main()
