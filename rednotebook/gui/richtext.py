import sys
import os
#sys.path.insert(0, '/home/jendrik/projects/RedNotebook/ref/keepnote-0.5.2')


sys.path.insert(0, '/home/jendrik/projects/RedNotebook/rednotebook/gui')

import gtk
import pango
import StringIO

#import keepnote

'''
No ol's anymore: Let txt2tags produce ol's, but only convert back to ul's
h3 already works
line: works
link: should work
picture: local pictures work, remote ones now also do
'''


from keepnote_gui.editor import KeepNoteEditor
from keepnote_gui.richtext import RichTextView, RichTextModTag, RichTextIO, HtmlError, RichTextError, RichTextImage, is_relative_file
from keepnote_gui.richtext.richtext_html import HtmlBuffer, HtmlTagReader, HtmlTagWriter, unnest_indent_tags
from keepnote_gui.richtext.textbuffer_tools import TagNameDom
from keepnote_gui.richtext.textbuffer_tools import iter_buffer_contents, TextBufferDom
from keepnote_gui.richtext.richtext_tags import RichTextTag, RichTextIndentTag
#from keepnote_gui.richtext.richtextbuffer import ignore_tag



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
		#print '?' * 200
		HtmlTagReader.__init__(self, io, "h3")

	def parse_starttag(self, htmltag, attrs):
		# self._io is RedNotebookHtmlBuffer instance
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
    	# Only insert a newline after a paragraph
    	if self.paragraphs > 0:
			self._io.append_text("\n")
    	self.paragraphs += 1
    	#print 'self.paragraphs', self.paragraphs
        
        

    def parse_endtag(self, htmltag):
    	#print 'O' * 20
        self._io.append_text("\n")
		
#class HtmlTagH3Writer(HtmlTagWriter):
	#def __init__(self, io):
		#HtmlTagWriter.__init__(self, io, RichTextH3Tag)

	#def write_tag_begin(self, out, dom, xhtml):
		#out.write("<h3>")
	#def write_tag_end(self, out, dom, xhtml):
		#out.write("</h3>")
		
#class HtmlTagOrderedListWriter(HtmlTagWriter):

    #def __init__(self, io):
        #HtmlTagWriter.__init__(self, io, RichTextIndentTag)
        
    #def write_tag_begin(self, out, dom, xhtml):
        #out.write("<ol>")

    #def write_tag_end(self, out, dom, xhtml):
        #out.write("</ol>\n")
		


class RedNotebookHtmlBuffer(HtmlBuffer):
	def __init__(self):
		HtmlBuffer.__init__(self)
		
		print 'HTMLBUFFER INIT'
		
		self.add_tag_reader(HtmlTagH3Reader(self))
		
		# overwrite keepnote par reader
		self.parReader = HtmlTagParReader(self)
		self.add_tag_reader(self.parReader)
		#self.add_tag_writer(HtmlTagH3Writer(self))
		
		#self.add_tag_writer(HtmlTagOrderedListWriter(self))
		
	def read(self, html, partial=False, ignore_errors=False):
		"""Read from stream infile to populate textbuffer"""
		
		##
		self.parReader.paragraphs = 0
		
		#self._text_queue = []
		self._within_body = False
		self._partial = partial
		
		self._dom = TextBufferDom()
		self._dom_ptr = self._dom
		self._tag_stack = [(None, self._dom)]

		try:
			self.feed(html)
			##for line in html.split('\n'):
			##	self.feed(line)                
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
		tag_table.tag_class_add("h3", RichTextModTag("h3", weight=pango.WEIGHT_BOLD, size_points=14))
		
		#tag_table.new_tag_class("ul", RichTextH3Tag)
		#tag_table.tag_class_add("ul", RichTextModTag("ul", weight=pango.WEIGHT_BOLD))
		
		self.connect("visit-url", self._on_visit_url)
		
		self._html_buffer = RedNotebookHtmlBuffer()
		
		self.enable_spell_check(False)
		#self.set_editable(False)
		
	def get_buffer(self):
		return self._textbuffer
		
	def _on_visit_url(self, textview, url):
		print 'clicked', url
		import webbrowser
		try:
			webbrowser.open(url)
		except webbrowser.Error:
			print 'Failed to open web browser'
		
class HtmlIO(RichTextIO):
	def __init__(self):
		RichTextIO.__init__(self)
		
		self._html_buffer = RedNotebookHtmlBuffer()
		
	'''
	get_data_file() returns absolute html filename
	'''
		
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
			print 'NORMAL'
			#from rasmus import util
			#util.tic("read")
			buffer_contents = list(self._html_buffer.read(html))
			##print buffer_contents
			#util.toc()
			
			#util.tic("read2")            
			textbuffer.insert_contents(buffer_contents,
								textbuffer.get_start_iter())
			#util.toc()

			# put cursor at begining
			textbuffer.place_cursor(textbuffer.get_start_iter())
			
		except IOError:
			pass
			
		#except (HtmlError, IOError, Exception), e:
			#print 'ERROR', e
			#err = e
			
			## TODO: turn into function
			#textbuffer.clear()
			#textview.set_buffer(textbuffer)
			#ret = False
		else:
			# finish loading
			path = os.path.dirname(os.path.abspath(__file__))#filename)
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

		##path = os.path.dirname(filename)
		##self._save_images(textbuffer, path)
        
		try:
			buffer_contents = iter_buffer_contents(textbuffer, None, None, ignore_tag)
            
			out = sys.stdout##safefile.open(filename, "wb", codec="utf-8")
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
		
		print 'LOADING IMAGES'

		for kind, it, param in iter_buffer_contents(textbuffer,
													None, None,
													ignore_tag):
			if kind == "anchor":
				child, widgets = param
				
				if isinstance(child, RichTextImage):
					filename = child.get_filename()
					if is_relative_file(filename):
						filename = os.path.join(path, filename)
					
					print 'Path', path, 'filename', filename
					##
					if filename.startswith("http:") or \
							filename.startswith("file:"):
						child.set_from_url(filename, os.path.basename(filename)) 
					else:
						child.set_from_file(filename)
	
class HtmlEditor(KeepNoteEditor):
	def __init__(self):
		##KeepNoteEditor.__init__(self, None)
		
		gtk.VBox.__init__(self, False, 0)
		
		# state
		self._textview = HtmlView()    # textview
		#self._page = None                  # current NoteBookPage
		#self._page_scrolls = {}            # remember scroll in each page
		#self._page_cursors = {}
		self._textview_io = HtmlIO()

		
		self._sw = gtk.ScrolledWindow()
		self._sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self._sw.set_shadow_type(gtk.SHADOW_IN)
		self._sw.add(self._textview)
		self.pack_start(self._sw)
		
		self._textview.connect("font-change", self._on_font_callback)
		##self._textview.connect("modified", self._on_modified_callback)
		self._textview.connect("child-activated", self._on_child_activated)
		self._textview.connect("visit-url", self._on_visit_url)
		self._textview.disable()
		
		self.load_html('<html></html>')
		self.show_all()
		
	def load_html(self, html):
		#print html
		html = html.replace('\n', '')
		self._textview_io.load(self._textview, self._textview.get_buffer(), \
								html)
								
	def get_html(self):
		self._textview_io.save(self._textview.get_buffer())
		
		return
		output = StringIO.StringIO()
		self.set_output(output)
		textbuffer = textview.get_buffer()
		buffer_contents = iter_buffer_contents(textbuffer, None, None, ignore_tag)
		self.write(buffer_contents, textbuffer.tag_table, title=None)
		#self.set_output(sys.stdout)
		#self._write_footer()
		self._out.flush()
		return output.getvalue()
	
	def set_editable(self, editable):
		self._textview.set_editable(editable)
		self._textview.set_cursor_visible(editable)
                                       
      
		
	
		
if __name__ == '__main__':
	txt2tagshtmlfile = '/home/jendrik/projects/Tests/completeTxt2tagsTest.html'
	keepnotehtmlfile = '/home/jendrik/test/testpage/page.html'
	knhtml = open(keepnotehtmlfile).read()
	t2thtml = open(txt2tagshtmlfile).read()

	#html = html.split()
	html = t2thtml
	print html
	
	#html = str(BeautifulSoup(html))
	html = html.replace('\n', '')
	print html
	
	frame = gtk.Window()
	
	#keepnote = keepnote.KeepNote('/home/jendrik/projects/RedNotebook/ref/keepnote-0.5.2/keepnote')
	#editor = KeepNoteEditor(keepnote)
	
	
	editor = HtmlEditor()
	#editor.view_pages([])
	
	
	
	
	#tv = editor.get_textview()
	#tv = HtmlView()
	#tv.insert_html('<html><b>H</b>allo</html>')
	#tv._html_buffer = RedNotebookHtmlBuffer()
	
	#tv.insert_html(html)
	#htmlio.load(tv, tv.get_buffer(), txt2tagshtmlfile)
	
	#tv.enable_spell_check(False)
	
	
	print 'A\n' * 4
	#html = tv._html_buffer.get_html(tv)
	#editor.get_html()
	#print 'B\n' * 4
	#html = BeautifulSoup(html).prettify()
	#print html
	
	frame.add(editor)
	
	frame.resize(600, 400)
	
	frame.show()
	editor.show_all()
	#tv.show()
	
	# First draw everything, then add the content
	editor.load_html(t2thtml)
	
	
	#frame2 = gtk.Window()
	#frame2.set_title('Parsed')
	#tv2 = HtmlView()
	#tv2._html_buffer = RedNotebookHtmlBuffer()
	#tv2.insert_html(html)
	#tv2.enable_spell_check(False)
	
	#frame2.add(tv2)
	
	#frame2.resize(600, 400)
	
	##frame2.show()
	#tv2.show()
	
	
	import gtkmozembed
	win = gtk.Window() # Create a new GTK window called 'win'
	
	win.set_title("Simple Web Browser") # Set the title of the window
	win.set_position(gtk.WIN_POS_CENTER) # Position the window in the centre of the screen
	
	#win.connect("destroy", CloseWindow) # Connect the 'destroy' event to the 'CloseWindow' function, so that the app will quit properly when we press the close button
	
	# Create the browser widget
	gtkmozembed.set_profile_path("/tmp", "simple_browser_user") # Set a temporary Mozilla profile (works around some bug)
	mozbrowser = gtkmozembed.MozEmbed() # Create the browser widget
	
	# Set-up the browser widget before we display it
	win.add(mozbrowser) # Add the 'mozbrowser' widget to the main window 'win'
	mozbrowser.load_url('file:///home/jendrik/projects/Tests/completeTxt2tagsTest.html') # Load a web page
	mozbrowser.set_size_request(600,400) # Attempt to set the size of the browser widget to 600x400 pixels
	mozbrowser.show() # Try to show the browser widget before we show the window, so that the window appears at the correct size (600x400)
	
	win.show()
	
	
	
	gtk.main()


