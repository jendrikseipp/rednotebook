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

import sys
import os
import StringIO
import logging

import gtk
import pango

'''
Notes:
This module makes use of the keepnote gui module and especially its richtext 
submodule.
It provides the HtmlEditor class which is used for previewing a day's text.
Later the richtext editing feature will be added.

Some code in this module has been taken from keepnote modules and was altered 
to fit RedNotebook's needs. The original keepnote modules have not been altered
in any significant way. Only some imports where changed or commented out.
'''


from rednotebook.gui.keepnote.gui.editor import KeepNoteEditor
from rednotebook.gui.keepnote.gui.richtext import RichTextView, RichTextModTag, RichTextIO, \
					HtmlError, RichTextError, RichTextImage, is_relative_file
from rednotebook.gui.keepnote.gui.richtext.richtext_html import HtmlBuffer, HtmlTagReader, \
											HtmlTagWriter, unnest_indent_tags
from rednotebook.gui.keepnote.gui.richtext.textbuffer_tools import TagNameDom, TextBufferDom, \
													iter_buffer_contents
from rednotebook.gui.keepnote.gui.richtext.richtext_tags import RichTextTag
from rednotebook.gui.keepnote.gui.richtext.richtextbuffer import ignore_tag

from rednotebook.util import filesystem



# these tags will not be enumerated by iter_buffer_contents
IGNORE_TAGS = set(["gtkspell-misspelled"])

def ignore_tag(tag):
	return tag.get_property("name") in IGNORE_TAGS
   
	
class RichTextH3Tag(RichTextTag):
	def __init__(self, kind):
		RichTextTag.__init__(self, "h3")
		self.kind = kind


class HtmlTagH3Reader(HtmlTagReader):
	def __init__(self, io):
		HtmlTagReader.__init__(self, io, "h3")

	def parse_starttag(self, htmltag, attrs):
		# self._io is a RedNotebookHtmlBuffer instance
		self._io.append_text("\n")
		self._io.append_child(TagNameDom('h3'), True)
		
	def parse_endtag(self, htmltag):
		self._io.append_text("\n")
		
		
class HtmlTagParReader(HtmlTagReader):
	# paragraph
	# NOTE: this tag is currently not used by KeepNote, but if pasting
	# text from another HTML source, KeepNote will interpret it as
	# a newline char

	def __init__(self, io):
		HtmlTagReader.__init__(self, io, "p")
		
		self.paragraphs = 0

	def parse_starttag(self, htmltag, attrs):
		# Don't insert a newline at the beginning of a document
		if self.paragraphs > 0:
			self._io.append_text("\n")
		self.paragraphs += 1

	def parse_endtag(self, htmltag):
		self._io.append_text("\n")


class RedNotebookHtmlBuffer(HtmlBuffer):
	def __init__(self):
		HtmlBuffer.__init__(self)
		
		self.add_tag_reader(HtmlTagH3Reader(self))
		
		# overwrite keepnote par reader
		self.par_reader = HtmlTagParReader(self)
		self.add_tag_reader(self.par_reader)
		
	def read(self, html, partial=False, ignore_errors=False):
		"""Read from stream infile to populate textbuffer"""
		
		# Enable check if we're at the top of a document
		self.par_reader.paragraphs = 0
		
		#self._text_queue = []
		self._within_body = False
		self._partial = partial
		
		self._dom = TextBufferDom()
		self._dom_ptr = self._dom
		self._tag_stack = [(None, self._dom)]

		try:
			self.feed(html)		
			self.close()
		
		except Exception, e:
			# reraise error if not ignored
			if not ignore_errors:
				raise
		
		self.process_dom_read(self._dom)
		return unnest_indent_tags(self._dom.get_contents())
		
	
class HtmlView(RichTextView):
	def __init__(self):
		RichTextView.__init__(self)
		
		tag_table = self._textbuffer.get_tag_table()
		tag_table.new_tag_class("h3", RichTextH3Tag)
		
		# 14pt corresponds to h3
		tag_table.tag_class_add("h3", RichTextModTag("h3", weight=pango.WEIGHT_BOLD, size_points=16))
		
		self.connect("visit-url", self._on_visit_url)
		
		self._html_buffer = RedNotebookHtmlBuffer()
		
		self.enable_spell_check(False)
		#print 'self.is_spell_check_enabled()', self.is_spell_check_enabled()
		#self.set_editable(False)
		
		
	def get_buffer(self):
		return self._textbuffer
		
	def _on_visit_url(self, textview, url):
		logging.info('clicked %s' % url)
		
		filesystem.open_url(url)
		
	def highlight(self, text):
		iter_start = self.get_buffer().get_start_iter()
		
		# Hack: Ignoring the case is not supported for the search so we search
		# for the most common variants, but do not search identical ones
		variants = set([text, text.capitalize(), text.lower(), text.upper()])
		
		for search_text in variants:
			iter_tuple = iter_start.forward_search(search_text, gtk.TEXT_SEARCH_VISIBLE_ONLY)
			
			# When we find one variant, highlight it and quit
			if iter_tuple:
				self.set_selection(*iter_tuple)
				return
			
	def set_selection(self, iter1, iter2):
		'''
		Sort the two iters and select the text between them
		'''		
		sort_by_position = lambda iter: iter.get_offset()
		iter1, iter2 = sorted([iter1, iter2], key=sort_by_position)
		assert iter1.get_offset() <= iter2.get_offset()
		self.get_buffer().select_range(iter1, iter2)
		
		
class HtmlIO(RichTextIO):
	def __init__(self):
		RichTextIO.__init__(self)
		
		self._html_buffer = RedNotebookHtmlBuffer()
		
	def load(self, textview, textbuffer, html):
		"""Load buffer with data from file"""
		
		# unhook expensive callbacks
		textbuffer.block_signals()
		spell = textview.is_spell_check_enabled()
		textview.enable_spell_check(False)
		textview.set_buffer(None)

		# clear buffer		
		textbuffer.clear()
		
		err = None
		try:
			#from rasmus import util
			#util.tic("read")
			buffer_contents = list(self._html_buffer.read(html))
			#util.toc()
			
			#util.tic("read2")			
			textbuffer.insert_contents(buffer_contents,
								textbuffer.get_start_iter())
			#util.toc()

			# put cursor at begining
			textbuffer.place_cursor(textbuffer.get_start_iter())
			
		except IOError:
			pass
			
		except (HtmlError, IOError, Exception), e:
			logging.error(e)
			err = e
			
			# TODO: turn into function
			textbuffer.clear()
			textview.set_buffer(textbuffer)
			ret = False
		else:
			# finish loading
			path = os.path.dirname(os.path.abspath(__file__))
			self._load_images(textbuffer, path)
			textview.set_buffer(textbuffer)
			textview.show_all()
			ret = True
		
		# rehook up callbacks
		textbuffer.unblock_signals()
		textview.enable_spell_check(spell)
		textview.enable()
		
		textbuffer.set_modified(False)
		
		# reraise error
		if not ret:
			raise RichTextError("Error loading '%s'." % 'html', e)
	
	def save(self, textbuffer):
		"""Save buffer contents to file"""
		
		try:
			buffer_contents = iter_buffer_contents(textbuffer, None, None, ignore_tag)
			
			out = sys.stdout
			self._html_buffer.set_output(out)
			self._html_buffer.write(buffer_contents,
									textbuffer.tag_table,)
									##title=title)
			out.flush()
		except IOError, e:
			raise RichTextError("Could not save '%s'." % filename, e)
		
		textbuffer.set_modified(False)
		
	def _load_images(self, textbuffer, path):
		"""Load images present in textbuffer"""

		for kind, it, param in iter_buffer_contents(textbuffer, None, None,
													ignore_tag):
			if kind == "anchor":
				child, widgets = param
				
				if isinstance(child, RichTextImage):
					filename = child.get_filename()
					if is_relative_file(filename):
						filename = os.path.join(path, filename)
					
					## For absolute windows filenames
					if filename.startswith('file://'):
						filename = filename[7:]
						
					## Modified
					if filename.startswith("http:") or \
							filename.startswith("file:"):
						child.set_from_url(filename, os.path.basename(filename)) 
					else:
						child.set_from_file(filename)
	
	
class HtmlEditor(KeepNoteEditor):
	def __init__(self):
		'''
		Do not call the KeepNoteEditor constructor, because we need our own
		classes here.
		'''
		##KeepNoteEditor.__init__(self, None)
		
		gtk.VBox.__init__(self, False, 0)
		
		# state
		self._textview = HtmlView()	# textview
		#self._page = None				  # current NoteBookPage
		#self._page_scrolls = {}			# remember scroll in each page
		#self._page_cursors = {}
		self._textview_io = HtmlIO()

		self._sw = gtk.ScrolledWindow()
		self._sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self._sw.set_shadow_type(gtk.SHADOW_IN)
		self._sw.add(self._textview)
		self.pack_start(self._sw)
		
		##self._textview.connect("font-change", self._on_font_callback)
		##self._textview.connect("modified", self._on_modified_callback)
		self._textview.connect("child-activated", self._on_child_activated)
		##self._textview.connect("visit-url", self._on_visit_url)
		self._textview.disable()
		
		self.load_html('<html></html>')
		self.show_all()
		
	def load_html(self, html):
		html = html.replace('\n', '')
		self._textview_io.load(self._textview, self._textview.get_buffer(), \
								html)
		
	def _on_child_activated(self, textview, child):
		if isinstance(child, RichTextImage):
			filesystem.open_url(child.get_filename())
								
	def get_html(self):
		self._textview_io.save(self._textview.get_buffer())
		
		return
		output = StringIO.StringIO()
		self.set_output(output)
		textbuffer = textview.get_buffer()
		buffer_contents = iter_buffer_contents(textbuffer, None, None, ignore_tag)
		self.write(buffer_contents, textbuffer.tag_table, title=None)
		self._out.flush()
		return output.getvalue()
	
	def set_editable(self, editable):
		self._textview.set_editable(editable)
		self._textview.set_cursor_visible(editable)
		
	def set_font_size(self, size):
		self._textview.modify_font(pango.FontDescription(str(size)))
		
	def highlight(self, string):
		self._textview.highlight(string)
		
									   
	  
		
	
		
if __name__ == '__main__':
	txt2tagshtmlfile = '/home/jendrik/projects/Tests/complete_txt2tags_test.html'
	keepnotehtmlfile = '/home/jendrik/test/testpage/page.html'
	knhtml = open(keepnotehtmlfile).read()
	t2thtml = open(txt2tagshtmlfile).read()

	html = t2thtml
	print html
	
	html = html.replace('\n', '')
	print html
	
	frame = gtk.Window()
	
	editor = HtmlEditor()
	frame.add(editor)
	frame.resize(600, 400)
	frame.show()
	editor.show_all()
	
	# First draw everything, then add the content
	editor.load_html(t2thtml)
	
	
	import gtkmozembed
	win = gtk.Window() # Create a new GTK window called 'win'
	
	win.set_title("Simple Web Browser") # Set the title of the window
	win.set_position(gtk.WIN_POS_CENTER) # Position the window in the centre of the screen
	
	#win.connect("destroy", CloseWindow) # Connect the 'destroy' event to the 
	#'CloseWindow' function, so that the app will quit properly when we press the close button
	
	# Create the browser widget
	gtkmozembed.set_profile_path("/tmp", "simple_browser_user") # Set a temporary Mozilla profile (works around some bug)
	mozbrowser = gtkmozembed.MozEmbed() # Create the browser widget
	
	# Set-up the browser widget before we display it
	win.add(mozbrowser) # Add the 'mozbrowser' widget to the main window 'win'
	mozbrowser.load_url('file:///home/jendrik/projects/Tests/complete_txt2tags_test.html') # Load a web page
	mozbrowser.set_size_request(600,400) # Attempt to set the size of the browser widget to 600x400 pixels
	mozbrowser.show() # Try to show the browser widget before we show the window, 
	#so that the window appears at the correct size (600x400)
	
	win.show()
	
	gtk.main()
