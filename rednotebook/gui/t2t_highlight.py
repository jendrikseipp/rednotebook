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

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath("./../../"))

from rednotebook.external import gtkcodebuffer
from rednotebook.external import txt2tags
#from rednotebook.gui.richtext import HtmlEditor
from rednotebook.gui.browser import HtmlView
from rednotebook.util import markup

logging.getLogger('').setLevel(logging.DEBUG)


txt = """
=== Header ===
ä **bold**.*, //italic//,/italic/__underlined__, --strikethrough--

	 [""/home/user/Desktop/RedNotebook pic"".png]

	 [hs error.log ""file:///home/user/hs error.log""]

	 [heise ""http://heise.de""]

	 www.heise.de

	 http://www.heise.de

====================

% list-support
- a simple list item
- an other

1. An ordered list
2. other item

"""



class MultiPattern(gtkcodebuffer.Pattern):
	'''
	Extension of the Pattern class that allows a pattern to have
	subgroups with different formatting
	'''
	def __init__(self, regexp, group_tag_pairs, **kwargs):
		gtkcodebuffer.Pattern.__init__(self, regexp, **kwargs)

		self.group_tag_pairs = group_tag_pairs

	def __call__(self, txt, start, end):
		m = self._regexp.search(txt)
		if not m: return None

		iter_pairs = []

		for group, tag_name in self.group_tag_pairs:
			mstart, mend = m.start(group), m.end(group)
			s = start.copy(); s.forward_chars(mstart)
			e = start.copy(); e.forward_chars(mend)
			iter_pairs.append([s, e, tag_name])

		return iter_pairs


class OverlapLanguageDefinition(gtkcodebuffer.LanguageDefinition):

	def __call__(self, buf, start, end):
		mstart = mend = end
		mtag   = None
		txt = buf.get_slice(start, end)

		selected_pairs = None

		# search min match
		#logging.debug('Testing %s rules' % len(self._successful_rules))
		for rule in self._successful_rules[:]:
			# search pattern
			iter_pairs = rule(txt, start, end)
			if not iter_pairs:
				## This rule will not find anything in the next round either
				self._successful_rules.remove(rule)
				continue

			key = lambda iter: iter.get_offset()

			min_start = min([start_iter for start_iter, end_iter, tag_name in iter_pairs], key=key)
			max_end = max([end_iter for start_iter, end_iter, tag_name in iter_pairs], key=key)

			# prefer match with smallest start-iter
			if min_start.compare(mstart) < 0:
				mstart, mend = min_start, max_end
				#mtag = rule.tag_name
				selected_pairs = iter_pairs
				continue

			##if m[0].compare(mstart)==0 and m[1].compare(mend)>0:
			if min_start.compare(mstart) == 0 and max_end.compare(mend) > 0:
				mstart, mend = min_start, max_end
				#mtag = rule.tag_name
				selected_pairs = iter_pairs
				continue

		return selected_pairs#(mstart, mend, mtag)


class OverlapCodeBuffer(gtkcodebuffer.CodeBuffer):

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
		
	def _on_apply_tag(self, buf, tag, start, end):
		'''
		We want to allow applying tags for spellchecking
		'''
		return False
		
	def remove_all_syntax_tags(self, start, end):
		'''
		Do not remove the gtkspell highlighting
		'''
		for style in styles:
			self.remove_tag_by_name(style, start, end)

	def update_syntax(self, start, end):
		""" More or less internal used method to update the
			syntax-highlighting. """
			
		# Just update from the start of the first edited line 
		# to the end of the last edited line, because we can
		# guarantee that there's no multiline rule
		start_line_number = start.get_line()
		start_line_iter = self.get_iter_at_line(start_line_number)
		start = start_line_iter
		
		end.forward_to_line_end()

		# We can omit those rules without occurrences in later searches

		# Reset rules
		self._lang_def._successful_rules = self._lang_def._grammar[:]

		# We do not use recursion -> long files exceed rec-limit!
		finished = False
		while not finished:
			# search first rule matching txt[start..end]
			group_iters_and_tags = self._lang_def(self, start, end)

			if not group_iters_and_tags:
				self.remove_all_syntax_tags(start, end)
				#self.apply_tag_by_name("DEFAULT", start, end)
				return

			key = lambda iter: iter.get_offset()

			min_start = min([start_iter for start_iter, end_iter, tag_name \
										in group_iters_and_tags], key=key)
			max_end = max([end_iter for start_iter, end_iter, tag_name \
										in group_iters_and_tags], key=key)

			# remove all tags from start..end (mend == buffer-end if no match)
			self.remove_all_syntax_tags(start, end)

			for mstart, mend, tagname in group_iters_and_tags:
				# apply tag
				self.apply_tag_by_name(tagname, mstart, mend)

			# Set new start
			start = max_end

			if start == end:
				return


def get_pattern(markup_symbols, style, allow_whitespace=False):
	if allow_whitespace:
		regex = r"(%s)(.+?)(%s)" % ((markup_symbols, ) * 2)
	else:
		# original strikethrough in txt2tags: r'--([^\s](|.*?[^\s])-*)--'
		# txt2tags docs say that format markup is greedy, but
		# that doesn't seem to be the case
		fill_ins = (markup_symbols, markup_symbols)
		# Either one char, or two chars with (maybe empty) content
		# between them
		# In both cases no whitespaces between chars and markup
		regex = r'(%s)([^\s]|[^\s].*?[^\s])(%s)' % fill_ins
	group_style_pairs = [(1, 'grey'), (2, style), (3, 'grey')]
	return MultiPattern(regex, group_style_pairs)


# additional style definitions:
# the update_syntax() method of CodeBuffer allows you to define new and modify
# already defined styles. Think of it like CSS.
styles = {	'DEFAULT':   		{},#{'font': 'serif'},
			'bold':	  			{'weight': pango.WEIGHT_BOLD},
			'comment':   		{'foreground': 'gray'},
			'underlined':   	{'underline': pango.UNDERLINE_SINGLE},
			'grey':				{'foreground': 'gray'},
			'red':				{'foreground': 'red'},
			'italic':			{'style': pango.STYLE_ITALIC},
			'strikethrough':	{'strikethrough': True},
			'header':			{'weight': pango.WEIGHT_ULTRABOLD,
								'scale': pango.SCALE_XX_LARGE,
								'variant': pango.VARIANT_SMALL_CAPS},
			'raw':				{},
			'link':				{'foreground': 'blue',
								'underline': pango.UNDERLINE_SINGLE,},
			}

# Syntax definition

list = MultiPattern(r"^ *(- )[^\s].*$", [(1, 'bold')])

comment = MultiPattern(r'^(\%.*)$', [(1, 'comment')])

line = MultiPattern(r'^[\s]*([_=-]{20,})[\s]*$', [(1, 'bold')])

# Whitespace is allowed, but nothing else
header = MultiPattern(r'^[\s]*(===)([^=]|[^=].*[^=])(===)[\s]*$', \
						[(1, 'grey'), (2, 'header'), (3, 'grey')])

linebreak = MultiPattern(r'(\\\\)', [(1, 'bold')])

# pic [""/home/user/Desktop/RedNotebook pic"".png]
# \w = [a-zA-Z0-9_]
# Added ":-" for "file://5-5.jpg"
# filename = One char or two chars with possibly whitespace in the middle
#filename = r'\S[\w\s_,.+%$#@!?+~/-:-\(\)]*\S|\S'
filename = r'\S.*\S|\S'
ext = r'png|jpe?g|gif|eps|bmp'
pic = MultiPattern(r'(\["")(%s)("")\.(%s)(\?\d+)?(\])' % (filename, ext), \
		[(1, 'grey'), (2, 'bold'), (3, 'grey'), (4, 'bold'), (5, 'grey')], flags='LI')

# named link on hdd [hs err_pid9204.log ""file:///home/jendrik/hs err_pid9204.log""]
# named link in web [heise ""http://heise.de""]
named_link = MultiPattern(r'(\[)(.*)[\s]("")([^\s].*[^\s])(""\])', \
		[(1, 'grey'), (2, 'link'), (3, 'grey'), (4, 'grey'), (5, 'grey')], flags='LI')

# link http://heise.de
# Use txt2tags link guessing mechanism
regexes = txt2tags.getRegexes()
link_regex = regexes['link']
link = MultiPattern(r'overwritten', [(0, 'link')])
link._regexp = link_regex


rules = [
		get_pattern('\*\*', 'bold'),
		get_pattern('__', 'underlined'),
		get_pattern('//', 'italic'),
		get_pattern('--', 'strikethrough'),
		#get_pattern('===', 'header', allow_whitespace=True), # not correct
		header,
		list,
		comment,
		line,
		get_pattern('""', 'raw', allow_whitespace=False), # verified in RedNotebook
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

	win.set_default_size(800,600)
	win.set_position(gtk.WIN_POS_CENTER)
	win.show_all()
	win.connect("destroy", lambda w: gtk.main_quit())

	buff.set_text(txt)

	gtk.main()
