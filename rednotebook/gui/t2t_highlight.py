#!/usr/bin/python
import gtk
import sys
import os.path
import pango

import time

# if you don't have pygtkcodebuffer installed...
sys.path.insert(0, os.path.abspath("./../external/pygtkcodebuffer"))
sys.path.insert(0, os.path.abspath("./../../"))

from gtkcodebuffer import CodeBuffer, Pattern, String, LanguageDefinition 
from gtkcodebuffer import SyntaxLoader, add_syntax_path, _log_debug


from rednotebook.gui.richtext import HtmlEditor
from rednotebook.util import markup

txt = """
=== Header ===
**bold**.*, //italic//,/italic/__underlined__, __aakaroaa__, --stricken--

====================

# About 
This example shows you a hard-coded\\ markdown 
syntax-definition. Supporting `code-segments`, 
**emphasized text**, **2nd** or *emphasized text*.

## list-support
## 2list-support
- a simple list item
- an other

1. A ordered list
2. other item

#### n-th order heading
"""



class MultiPattern(Pattern):
	def __init__(self, regexp, group_tag_pairs, **kwargs):
		Pattern.__init__(self, regexp, **kwargs)
		
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
	
class OverlapLanguageDefinition(LanguageDefinition):
	
	def __call__(self, buf, start, end=None):
		# if no end given -> end of buffer
		if not end: end = buf.get_end_iter()
	
		mstart = mend = end
		mtag   = None
		txt = buf.get_slice(start, end)
		
		selected_pairs = None
		
		##self.min_start
		
		# search min match
		for rule in self._grammar:
			# search pattern
			iter_pairs = rule(txt, start, end)
			if not iter_pairs: continue
			
			key = lambda iter: iter.get_offset()
			
			min_start = min([start_iter for start_iter, end_iter, tag_name in iter_pairs], key=key)
			max_end = max([end_iter for start_iter, end_iter, tag_name in iter_pairs], key=key)
			
			#for start_iter, end_iter, tag_name in iter_pairs:
			
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
			
		#assert selected_pairs, txt

		return selected_pairs#(mstart, mend, mtag)
	

class OverlapCodeBuffer(CodeBuffer):
	
	def update_syntax(self, start, end=None):
		""" More or less internal used method to update the 
			syntax-highlighting. """
			
		## Force renewal of complete text
		start = self.get_start_iter()	
		
		# if no lang set	
		if not self._lang_def: return			 
		_log_debug("Update syntax from %i"%start.get_offset())
			
		# if not end defined
		if not end: 
			#print 'Update'
			end = self.get_end_iter()
		
		# We do not use recursion -> long files exceed rec-limit!
		finished = False
		while not finished: 
			# search first rule matching txt[start..end]			
			##mstart, mend, tagname = self._lang_def(self, start, end)
			group_iters_and_tags = self._lang_def(self, start, end)
			
			#print 'group_iters_and_tags', group_iters_and_tags
			
			if not group_iters_and_tags:
				finished = True
				continue
			
			key = lambda iter: iter.get_offset()
			
			min_start = min([start_iter for start_iter, end_iter, tag_name in group_iters_and_tags], key=key)
			max_end = max([end_iter for start_iter, end_iter, tag_name in group_iters_and_tags], key=key)
			
			#print max_end.get_offset(), map(lambda (siter, enditer, tag): enditer.get_offset(), group_iters_and_tags)
			#time.sleep(1)
			# remove all tags from start..mend (mend == buffer-end if no match)		
			##self.remove_all_tags(start, max_end)
			self.remove_all_tags(start, end)
			#time.sleep(1)
			# make start..mstart = DEFAUL (mstart == buffer-end if no match)
			if not start.equal(min_start):
				_log_debug("Apply DEFAULT")
				##self.apply_tag_by_name("DEFAULT", start, min_start)
				self.apply_tag_by_name("DEFAULT", start, end)
			
			for index, (mstart, mend, tagname) in enumerate(group_iters_and_tags):
				
				
				#print 'slice', self.get_slice(mstart, mend)
				
				all_groups_done = (index == len(group_iters_and_tags) - 1)
				
				# optimisation: if mstart-mend is allready tagged with tagname 
				#   -> finished
#				if tagname:	 #if something found
#					tag = self.get_tag_table().lookup(tagname)
#					if mstart.begins_tag(tag) and mend.ends_tag(tag) and not mstart.equal(start):
#						self.remove_all_tags(start,mstart)
#						self.apply_tag_by_name("DEFAULT", start, mstart)
#						_log_debug("Optimized: Found old tag at %i (%s)"%(mstart.get_offset(), mstart.get_char()))
#						# finish
#						
#						if all_groups_done:
#							finished = True
#						continue
						
				
			
				# nothing found -> finished
				if not tagname: 
					if all_groups_done:
						finished = True
						continue
			
				# apply tag
				_log_debug("Apply %s"%tagname)
				self.apply_tag_by_name(tagname, mstart, mend)
			
			#print 'set new start', self.get_slice(self.get_start_iter(), max_end)
			#print '*'*30
			start = max_end
			
			if start == end: 
				finished = True
				continue

def get_pattern(markup_symbols, style, allow_whitespace=False):
	if allow_whitespace:
		regex = r"(%s)(.+?)(%s)" % ((markup_symbols, ) * 2)
	else:
		# original stricken in txt2tags: r'--([^\s](|.*?[^\s])-*)--'
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
#   the update_syntax() method of CodeBuffer allows you to define new and modify
#   already defined styles. Think of it like CSS.
styles = { 'DEFAULT':   {},#{'font': 'serif'},
		   'bold':	  {'weight': pango.WEIGHT_BOLD},
		   'comment':   {'foreground': 'gray',
						 #'weight': 700
						 },
		   #'heading':   {'variant': pango.VARIANT_SMALL_CAPS,
			#			 'underline': pango.UNDERLINE_DOUBLE},
		   'underlined':   {#'variant': pango.VARIANT_SMALL_CAPS,
						 'underline': pango.UNDERLINE_SINGLE},
			'grey':		{'foreground': 'gray'},
			'red':		{'foreground': 'red'},
			'italic':	{'style': pango.STYLE_ITALIC, # does not work
						#'foreground': 'green'
						},
			'stricken':	{'strikethrough': True},
			'header':	{'weight': pango.WEIGHT_ULTRABOLD,
						'scale': pango.SCALE_XX_LARGE,
						'variant': pango.VARIANT_SMALL_CAPS},
			'raw':		{},
			}

# Syntax definition

list = MultiPattern(r"^ *(- ).+$", [(1, 'bold')])
#list = MultiPattern(r"^ *(- )(?=[^ ])$", [(1, 'bold')])
comment = MultiPattern(r'^(\%.*)$', [(1, 'comment')])
#line = MultiPattern(r'^(\s*)([_=-]{20,})\s*$', [(2, 'bold')])
line = MultiPattern(r'^\s*([_=-]{20,})\s*$', [(1, 'bold')])

header = MultiPattern(r'^[\s]*(===)([^=]|[^=].*[^=])(===)[\s]*$', \
						[(1, 'grey'), (2, 'header'), (3, 'grey')])

rules = [
		get_pattern('\*\*', 'bold'),
		get_pattern('__', 'underlined'),
		get_pattern('//', 'italic'),
		get_pattern('--', 'stricken'),
		#get_pattern('===', 'header', allow_whitespace=True),
		header,
		list,
		comment,
		line,
		get_pattern('""', 'raw', allow_whitespace=False) # verified in RedNotebook
		]




# create lexer: 
lang = OverlapLanguageDefinition(rules)

# create buffer and update style-definition 
buff = OverlapCodeBuffer(lang=lang, styles=styles)

win = gtk.Window(gtk.WINDOW_TOPLEVEL)
scr = gtk.ScrolledWindow()

html_editor = HtmlEditor()

def change_text(widget):
	html = markup.convert(widget.get_text(widget.get_start_iter(), widget.get_end_iter()), \
						  'xhtml', append_whitespace=True)
			
	html_editor.load_html(html)
	
buff.connect('changed', change_text)

vbox = gtk.VBox()
vbox.pack_start(scr)
vbox.pack_start(html_editor)
win.add(vbox)
scr.add(gtk.TextView(buff))
		
win.set_default_size(600,400)
win.set_position(gtk.WIN_POS_CENTER)
win.show_all()
win.connect("destroy", lambda w: gtk.main_quit())

buff.set_text(txt)
		
gtk.main()		
