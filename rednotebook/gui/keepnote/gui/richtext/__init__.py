"""
    KeepNote
    Copyright Matt Rasmussen 2008
    
    General rich text editor that saves to HTML
"""



# python imports
import sys, os, tempfile, re
import urllib2, StringIO

# pygtk imports
import pygtk
pygtk.require('2.0')
import gtk, gobject, pango
from gtk import gdk

# try to import spell check
try:
    import gtkspell
except ImportError:
    gtkspell = None


# textbuffer_tools imports
from keepnote.gui.richtext.textbuffer_tools import \
     iter_buffer_contents

# richtextbuffer imports
from keepnote.gui.richtext.richtextbuffer import \
     ignore_tag, \
     add_child_to_buffer, \
     RichTextBuffer, \
     RichTextImage, \
     RichTextIndentTag

# tag imports
from keepnote.gui.richtext.richtext_tags import \
     RichTextModTag, \
     RichTextJustifyTag, \
     RichTextFamilyTag, \
     RichTextSizeTag, \
     RichTextFGColorTag, \
     RichTextBGColorTag, \
     RichTextIndentTag, \
     RichTextBulletTag, \
     RichTextLinkTag

# richtext io
from keepnote.gui.richtext.richtext_html import HtmlBuffer, HtmlError

from keepnote import safefile


#=============================================================================
# constants
DEFAULT_FONT = "Sans 10"
TEXTVIEW_MARGIN = 5
CLIPBOARD_NAME = "CLIPBOARD"
RICHTEXT_ID = -3    # application defined integer for the clipboard


# mime types
MIME_KEEPNOTE = "application/x-keepnote"
MIME_IMAGES = ["image/png",
               "image/bmp",
               "image/jpeg",
               "image/xpm"]

# TODO: add more text MIME types?
MIME_TEXT = ["text/plain",
             "text/plain;charset=utf-8",
             "text/plain;charset=UTF-8",
             "UTF8_STRING",
             "STRING",
             "COMPOUND_TEXT",
             "TEXT"]


def parse_font(fontstr):
    """Parse a font string from the font chooser"""
    tokens = fontstr.split(" ")
    size = int(tokens.pop())
    mods = []
        
    # NOTE: underline is not part of the font string and is handled separately
    while tokens[-1] in ["Bold", "Italic"]:
        mods.append(tokens.pop().lower())
        
    return " ".join(tokens), mods, size


def parse_utf(text):

    # TODO: lookup the standard way to do this
    
    if text[:2] in ('\xff\xfe', '\xfe\xff') or (
        len(text) > 1 and text[1] == '\x00') or (
        len(text) > 3 and text[3] == '\x00'):
        return text.decode("utf16")
    else:
        return unicode(text, "utf8")



def is_relative_file(filename):
    """Returns True if filename is relative"""
    
    return (not re.match("[^:/]+://", filename) and 
            not os.path.isabs(filename))
        


#=============================================================================


class RichTextError (StandardError):
    """Class for errors with RichText"""

    # NOTE: this is only used for saving and loading in textview
    # should this stay here?
    
    def __init__(self, msg, error):
        StandardError.__init__(self, msg)
        self.msg = msg
        self.error = error
    
    def __str__(self):
        if self.error:
            return str(self.error) + "\n" + self.msg
        else:
            return self.msg


class RichTextMenu (gtk.Menu):
    """A popup menu for child widgets in a RichTextView"""
    def __inti__(self):
        gkt.Menu.__init__(self)
        self._child = None

    def set_child(self, child):
        self._child = child

    def get_child(self):
        return self._child


class RichTextIO (object):
    """Read/Writes the contents of a RichTextBuffer to disk"""

    def __init__(self):
        self._html_buffer = HtmlBuffer()

    
    def save(self, textbuffer, filename, title=None):
        """Save buffer contents to file"""
        
        path = os.path.dirname(filename)
        self._save_images(textbuffer, path)
        
        try:
            buffer_contents = iter_buffer_contents(textbuffer,
                                                   None,
                                                   None,
                                                   ignore_tag)
            
            out = safefile.open(filename, "wb", codec="utf-8")
            self._html_buffer.set_output(out)
            self._html_buffer.write(buffer_contents,
                                    textbuffer.tag_table,
                                    title=title)
            out.close()
        except IOError, e:
            raise RichTextError("Could not save '%s'." % filename, e)
        
        textbuffer.set_modified(False)
    
    
    def load(self, textview, textbuffer, filename):
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
            buffer_contents = list(self._html_buffer.read(
                safefile.open(filename, "r", codec="utf-8")))
            #util.toc()
            
            #util.tic("read2")            
            textbuffer.insert_contents(buffer_contents,
                                       textbuffer.get_start_iter())
            #util.toc()

            # put cursor at begining
            textbuffer.place_cursor(textbuffer.get_start_iter())
            
        except (HtmlError, IOError, Exception), e:
            err = e
            
            # TODO: turn into function
            textbuffer.clear()
            textview.set_buffer(textbuffer)
            ret = False            
        else:
            # finish loading
            path = os.path.dirname(filename)
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
            raise RichTextError("Error loading '%s'." % filename, e)
        

    
    def _load_images(self, textbuffer, path):
        """Load images present in textbuffer"""

        for kind, it, param in iter_buffer_contents(textbuffer,
                                                    None, None,
                                                    ignore_tag):
            if kind == "anchor":
                child, widgets = param
                    
                if isinstance(child, RichTextImage):
                    filename = child.get_filename()
                    if is_relative_file(filename):
                        filename = os.path.join(path, filename)
                    
                    child.set_from_file(filename)

    
    def _save_images(self, textbuffer, path):
        """Save images present in text buffer"""
        
        for kind, it, param in iter_buffer_contents(textbuffer,
                                                    None, None,
                                                    ignore_tag):
            if kind == "anchor":
                child, widgets = param
                    
                if isinstance(child, RichTextImage):
                    filename = child.get_filename()
                    if is_relative_file(filename):
                        filename = os.path.join(path, filename)
                        
                    if child.save_needed():
                        child.write(filename)
                    



class RichTextView (gtk.TextView):
    """A RichText editor widget"""

    def __init__(self):
        gtk.TextView.__init__(self, None)
        
        self._textbuffer = None
        self._buffer_callbacks = []
        self._clipboard_contents = None
        self._blank_buffer = RichTextBuffer(self)
        self._popup_menu = None
        self._html_buffer = HtmlBuffer()
        
        self.set_buffer(RichTextBuffer(self))
        self.set_default_font(DEFAULT_FONT)
        
        
        # spell checker
        self._spell_checker = None
        self.enable_spell_check(True)
        
        # signals        
        self.set_wrap_mode(gtk.WRAP_WORD)
        self.set_property("right-margin", TEXTVIEW_MARGIN)
        self.set_property("left-margin", TEXTVIEW_MARGIN)

        self.connect("key-press-event", self.on_key_press_event)
        #self.connect("insert-at-cursor", self.on_insert_at_cursor)
        self.connect("backspace", self.on_backspace)
        self.connect("button-press-event", self.on_button_press)

        # drag and drop
        self.connect("drag-data-received", self.on_drag_data_received)
        self.connect("drag-motion", self.on_drag_motion)
        self.drag_dest_add_image_targets()

        # clipboard
        self.connect("copy-clipboard", lambda w: self._on_copy())
        self.connect("cut-clipboard", lambda w: self._on_cut())
        self.connect("paste-clipboard", lambda w: self._on_paste())

        #self.connect("button-press-event", self.on_button_press)
        self.connect("populate-popup", self.on_popup)
        
        # popup menus
        self.init_menus()
        
        # requires new pygtk
        #self._textbuffer.register_serialize_format(MIME_TAKENOTE, 
        #                                          self.serialize, None)
        #self._textbuffer.register_deserialize_format(MIME_TAKENOTE, 
        #                                            self.deserialize, None)


    def init_menus(self):
        """Initialize popup menus"""
        
        # image menu
        self._image_menu = RichTextMenu()
        self._image_menu.attach_to_widget(self, lambda w,m:None)

        item = gtk.ImageMenuItem(gtk.STOCK_CUT)
        item.connect("activate", lambda w: self.emit("cut-clipboard"))
        self._image_menu.append(item)
        item.show()
        
        item = gtk.ImageMenuItem(gtk.STOCK_COPY)
        item.connect("activate", lambda w: self.emit("copy-clipboard"))
        self._image_menu.append(item)
        item.show()

        item = gtk.ImageMenuItem(gtk.STOCK_DELETE)
        def func(widget):
            if self._textbuffer:
                self._textbuffer.delete_selection(True, True)
        item.connect("activate", func)
        self._image_menu.append(item)
        item.show()

    
    
    def set_buffer(self, textbuffer):
        """Attach this textview to a RichTextBuffer"""
        
        # tell current buffer we are detached
        if self._textbuffer:
            for callback in self._buffer_callbacks:
                self._textbuffer.disconnect(callback)

        
        # change buffer
        if textbuffer:
            gtk.TextView.set_buffer(self, textbuffer)            
        else:
            gtk.TextView.set_buffer(self, self._blank_buffer)
        self._textbuffer = textbuffer


        # tell new buffer we are attached
        if self._textbuffer:
            self._textbuffer.set_default_attr(self.get_default_attributes())
            self._modified_id = self._textbuffer.connect(
                "modified-changed", self._on_modified_changed)

            self._buffer_callbacks = [
                self._textbuffer.connect("font-change",
                                        self._on_font_change),
                self._textbuffer.connect("child-added",
                                         self._on_child_added),
                self._textbuffer.connect("child-activated",
                                        self._on_child_activated),
                self._textbuffer.connect("child-menu",
                                        self._on_child_popup_menu),
                self._modified_id
                ]
            
            # add all deferred anchors
            self._textbuffer.add_deferred_anchors(self)

    #======================================================
    # keyboard callbacks


    def on_key_press_event(self, textview, event):
        """Callback from key press event"""

        if self._textbuffer is None:
            return

        if event.keyval == gtk.gdk.keyval_from_name("ISO_Left_Tab"):
            # shift+tab is pressed

            it = self._textbuffer.get_iter_at_mark(self._textbuffer.get_insert())

            # indent if there is a selection
            if self._textbuffer.get_selection_bounds():
                # tab at start of line should do unindentation
                self.unindent()
                return True

        if event.keyval == gtk.gdk.keyval_from_name("Tab"):
            # tab is pressed
            
            it = self._textbuffer.get_iter_at_mark(self._textbuffer.get_insert())

            # indent if cursor at start of paragraph or if there is a selection
            if self._textbuffer.starts_par(it) or \
               self._textbuffer.get_selection_bounds():
                # tab at start of line should do indentation
                self.indent()
                return True


        if event.keyval == gtk.gdk.keyval_from_name("Delete"):
            # delete key pressed

            # TODO: make sure selection with delete does not fracture
            # unedititable regions.
            it = self._textbuffer.get_iter_at_mark(self._textbuffer.get_insert())

            if not self._textbuffer.get_selection_bounds() and \
               self._textbuffer.starts_par(it) and \
               not self._textbuffer.is_insert_allowed(it) and \
               self._textbuffer.get_indent(it)[0] > 0:
                # delete inside bullet phrase, removes bullet
                self.toggle_bullet("none")
                self.unindent()
                return True



    def on_backspace(self, textview):
        """Callback for backspace press"""

        if not self._textbuffer:
            return

        it = self._textbuffer.get_iter_at_mark(self._textbuffer.get_insert())

        if self._textbuffer.starts_par(it):
            # look for indent tags
            indent, par_type = self._textbuffer.get_indent()
            if indent > 0:
                self.unindent()
                self.stop_emission("backspace")
                        

    #==============================================
    # callbacks


    def on_button_press(self, widget, event):
        """Process context popup menu"""

        
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            # double left click
            
            x, y = self.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT,
                                                int(event.x), int(event.y))
            it = self.get_iter_at_location(x, y)

            if self.click_iter(it):
                self.stop_emission("button-press-event")
            

    def click_iter(self, it):
        """Perfrom click action at TextIter it"""

        if not self._textbuffer:
            return

        for tag in it.get_tags():
            if isinstance(tag, RichTextLinkTag):
                self.emit("visit-url", tag.get_href())
                return True

        return False

    

    #=======================================================
    # Drag and drop

    def on_drag_motion(self, textview, drag_context, x, y, timestamp):
        """Callback for when dragging over textview"""

        if not self._textbuffer:
            return

        # in preference order
        accepted_targets = MIME_IMAGES + \
                           ["text/uri-list",
                            "text/html",
                            "text/plain"]

        for target in accepted_targets:
            if target in drag_context.targets:
                textview.drag_dest_set_target_list([(target, 0, 0)])
                break

        '''
        # check for image targets
        img_target = self.drag_dest_find_target(drag_context, 
                                                [(x, 0, 0)
                                                 for x in MIME_IMAGES])

             
        if img_target is not None and img_target != "NONE":
            textview.drag_dest_set_target_list([(img_target, 0, 0)])
            
        elif "application/pdf" in drag_context.targets:
            textview.drag_dest_set_target_list([("application/pdf", 0, 0)])

        elif "text/html" in drag_context.targets:
            textview.drag_dest_set_target_list([("text/html", 0, 0)])
            
        else:
            textview.drag_dest_set_target_list([("text/plain", 0, 0)])
        '''
    
    
    def on_drag_data_received(self, widget, drag_context, x, y,
                              selection_data, info, eventtime):
        """Callback for when drop event is received"""

        if not self._textbuffer:
            return
        
        img_target = self.drag_dest_find_target(drag_context, 
                                                [(x, 0, 0)
                                                 for x in MIME_IMAGES])

             
        if img_target not in (None, "NONE"):
            # process image drop
            pixbuf = selection_data.get_pixbuf()
            
            if pixbuf != None:
                image = RichTextImage()
                image.set_from_pixbuf(pixbuf)
        
                self.insert_image(image)
            
                drag_context.finish(True, True, eventtime)
                self.stop_emission("drag-data-received")

        elif self.drag_dest_find_target(drag_context, 
            [("text/uri-list", 0, 0)]) not in (None, "NONE"):
            # process URI drop

            uris = parse_utf(selection_data.data)

            # remove empty lines and comments
            uris = [x for x in (uri.strip()
                                for uri in uris.split("\n"))
                    if len(x) > 0 and x[0] != "#"]

            links = ['<a href="%s">%s</a> ' % (uri, uri) for uri in uris]

            # insert links
            self.insert_html("<br />".join(links))
            
                
        #elif self.drag_dest_find_target(drag_context, 
        #    [("application/pdf", 0, 0)]) not in (None, "NONE"):
        #    # process pdf drop
        #    
        #    data = selection_data.data
        #    self.drop_pdf(data)
        #    
        #    drag_context.finish(True, True, eventtime)
        #    self.stop_emission("drag-data-received")

        elif self.drag_dest_find_target(drag_context, 
            [("text/html", 0, 0)]) not in (None, "NONE"):
            # process html drop

            html = parse_utf(selection_data.data)
            #html = 
            self.insert_html(html)
            
        
        elif self.drag_dest_find_target(drag_context, 
            [("text/plain", 0, 0)]) not in (None, "NONE"):
            # process text drop

            #self._textbuffer.begin_user_action()
            self._textbuffer.insert_at_cursor(selection_data.get_text())
            #self._textbuffer.end_user_action()
            

    def drop_pdf(self, data):
        """Drop a PDF into the TextView"""

        if not self._textbuffer:
            return

        # NOTE: requires hardcoded convert
        # TODO: generalize
        
        self._textbuffer.begin_user_action()
        
        try:
            f, imgfile = tempfile.mkstemp(".png", "keepnote")
            os.close(f)

            out = os.popen("convert - %s" % imgfile, "wb")
            out.write(data)
            out.close()
            
            name, ext = os.path.splitext(imgfile)
            imgfile2 = name + "-0" + ext
            
            if os.path.exists(imgfile2):
                i = 0
                while True:
                    imgfile = name + "-" + str(i) + ext
                    if not os.path.exists(imgfile):
                        break
                    self.insert_image_from_file(imgfile)
                    os.remove(imgfile)
                    i += 1
                    
            elif os.path.exists(imgfile):
                
                self.insert_image_from_file(imgfile)
                os.remove(imgfile)
        except:
            if os.path.exists(imgfile):
                os.remove(imgfile)

        self._textbuffer.end_user_action()
        

    
    #==================================================================
    # Copy and Paste

    def _on_copy(self):
        """Callback for copy action"""
        clipboard = self.get_clipboard(selection=CLIPBOARD_NAME)
        self.stop_emission('copy-clipboard')
        self.copy_clipboard(clipboard)

    
    def _on_cut(self):
        """Callback for cut action"""    
        clipboard = self.get_clipboard(selection=CLIPBOARD_NAME)
        self.stop_emission('cut-clipboard')
        self.cut_clipboard(clipboard, self.get_editable())

    
    def _on_paste(self):
        """Callback for paste action"""    
        clipboard = self.get_clipboard(selection=CLIPBOARD_NAME)
        self.stop_emission('paste-clipboard')
        self.paste_clipboard(clipboard, None, self.get_editable())
        

    def copy_clipboard(self, clipboard):
        """Callback for copy event"""

        if not self._textbuffer:
            return
    
        sel = self._textbuffer.get_selection_bounds()

        # do nothing if nothing is selected
        if not sel:
            return
        
        start, end = sel
        contents = list(self._textbuffer.copy_contents(start, end))

        
        if len(contents) == 1 and \
           contents[0][0] == "anchor" and \
           isinstance(contents[0][2][0], RichTextImage):
            # copy image
            targets = [(MIME_KEEPNOTE, gtk.TARGET_SAME_APP, RICHTEXT_ID),
                       ("text/html", 0, RICHTEXT_ID)] + \
                      [(x, 0, RICHTEXT_ID) for x in MIME_IMAGES]
            
            clipboard.set_with_data(targets, self._get_selection_data, 
                                    self._clear_selection_data,
                                    (contents, ""))

        else:
            # copy text
            targets = [(MIME_KEEPNOTE, gtk.TARGET_SAME_APP, RICHTEXT_ID),
                       ("text/html", 0, RICHTEXT_ID)] + \
                      [(x, 0, RICHTEXT_ID) for x in MIME_TEXT]
            
            text = start.get_text(end)
            clipboard.set_with_data(targets, self._get_selection_data, 
                                    self._clear_selection_data,
                                    (contents, text))


    def cut_clipboard(self, clipboard, default_editable):
        """Callback for cut event"""

        if not self._textbuffer:
            return
        
        self.copy_clipboard(clipboard)
        self._textbuffer.delete_selection(True, default_editable)

    
    def paste_clipboard(self, clipboard, override_location, default_editable):
        """Callback for paste event"""

        if not self._textbuffer:
            return
        
        targets = clipboard.wait_for_targets()
        if targets is None:
            # nothing on clipboard
            return
        targets = set(targets)

        
        # check that insert is allowed
        it = self._textbuffer.get_iter_at_mark(self._textbuffer.get_insert())
        if not self._textbuffer.is_insert_allowed(it):            
            return

        
        if MIME_KEEPNOTE in targets:
            # request KEEPNOTE contents object
            clipboard.request_contents(MIME_KEEPNOTE, self._do_paste_object)
            
        elif "text/html" in targets:
            # request HTML
            clipboard.request_contents("text/html", self._do_paste_html)
            
        else:

            # test image formats
            for mime_image in MIME_IMAGES:
                if mime_image in targets:
                    clipboard.request_contents(mime_image,
                                               self._do_paste_image)
                    break
            else:
                # request text
                clipboard.request_text(self._do_paste_text)

    
    def paste_clipboard_as_text(self):
        """Callback for paste action"""    
        clipboard = self.get_clipboard(selection=CLIPBOARD_NAME)
        #self.paste_clipboard(clipboard, None, self.get_editable())

        if not self._textbuffer:
            return
        
        targets = clipboard.wait_for_targets()
        if targets is None:
            # nothing on clipboard
            return
        
        # check that insert is allowed
        it = self._textbuffer.get_iter_at_mark(self._textbuffer.get_insert())
        if not self._textbuffer.is_insert_allowed(it):            
            return

        # request text
        clipboard.request_text(self._do_paste_text)
        
    
    def _do_paste_text(self, clipboard, text, data):
        """Paste text into buffer"""
        
        self._textbuffer.begin_user_action()
        self._textbuffer.delete_selection(False, True)
        self._textbuffer.insert_at_cursor(text)
        self._textbuffer.end_user_action()

        self.scroll_mark_onscreen(self._textbuffer.get_insert())

    def _do_paste_html(self, clipboard, selection_data, data):
        """Paste HTML into buffer"""

        # TODO: figure out right way to parse selection.data
        html = parse_utf(selection_data.data)        
        self._textbuffer.begin_user_action()
        self._textbuffer.delete_selection(False, True)
        self.insert_html(html)
        self._textbuffer.end_user_action()
        
        self.scroll_mark_onscreen(self._textbuffer.get_insert())
    
    def _do_paste_image(self, clipboard, selection_data, data):
        """Paste image into buffer"""

        pixbuf = selection_data.get_pixbuf()
        image = RichTextImage()
        image.set_from_pixbuf(pixbuf)

        self._textbuffer.begin_user_action()
        self._textbuffer.delete_selection(False, True)
        self._textbuffer.insert_image(image)
        self._textbuffer.end_user_action()
        self.scroll_mark_onscreen(self._textbuffer.get_insert())
        
    
    def _do_paste_object(self, clipboard, selection_data, data):
        """Paste a program-specific object into buffer"""
        
        if self._clipboard_contents is None:
            # do nothing
            return

        self._textbuffer.begin_user_action()
        self._textbuffer.delete_selection(False, True)
        self._textbuffer.insert_contents(self._clipboard_contents)
        self._textbuffer.end_user_action()
        self.scroll_mark_onscreen(self._textbuffer.get_insert())        
    
    
    def _get_selection_data(self, clipboard, selection_data, info, data):
        """Callback for when Clipboard needs selection data"""

        contents, text = data
        
        self._clipboard_contents = contents

        
        if MIME_KEEPNOTE in selection_data.target:
            # set rich text
            selection_data.set(MIME_KEEPNOTE, 8, "<keepnote>")
            
        elif "text/html" in selection_data.target:
            # set html
            stream = StringIO.StringIO()
            self._html_buffer.set_output(stream)
            self._html_buffer.write(contents,
                                    self._textbuffer.tag_table,
                                    partial=True,
                                    xhtml=False)
            selection_data.set("text/html", 8, stream.getvalue())

        elif len([x for x in MIME_IMAGES
                  if x in selection_data.target]) > 0:
            # set image
            image = contents[0][2][0]
            selection_data.set_pixbuf(image.get_original_pixbuf())
            
        else:
            # set plain text
            selection_data.set_text(text)

    
    def _clear_selection_data(self, clipboard, data):
        """Callback for when Clipboard contents are reset"""
        self._clipboard_contents = None
                    

    #=============================================
    # State
    
    def is_modified(self):
        """Returns True if buffer is modified"""

        if self._textbuffer:            
            return self._textbuffer.get_modified()
        else:
            return False

    
    def _on_modified_changed(self, textbuffer):
        """Callback for when buffer is modified"""
        
        # propogate modified signal to listeners of this textview
        self.emit("modified", textbuffer.get_modified())


        
    def enable(self):
        self.set_sensitive(True)
    
    
    def disable(self):
        """Disable TextView"""

        if self._textbuffer:
            self._textbuffer.handler_block(self._modified_id)
            self._textbuffer.clear()
            self._textbuffer.set_modified(False)
            self._textbuffer.handler_unblock(self._modified_id)

        self.set_sensitive(False)
        
    
    """
    def serialize(self, register_buf, content_buf, start, end, data):
        print "serialize", content_buf
        self.a = u"SERIALIZED"
        return self.a 
    
    
    def deserialize(self, register_buf, content_buf, it, data, create_tags, udata):
        print "deserialize"
    """

    #=====================================================
    # Popup Menus

    
    def on_popup(self, textview, menu):
        """Popup menu for RichTextView"""

        self._popup_menu = menu

        # insert "paste as plain text" after paste
        item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PASTE,
                                 accel_group=None)        
        item.child.set_text("Paste As Plain Text")
        item.connect("activate", lambda item: self.paste_clipboard_as_text())
        item.show()
        menu.insert(item, 3)

    '''
        menu.foreach(lambda item: menu.remove(item))

        # Create the menu item
        copy_item = gtk.MenuItem("Copy")
        copy_item.connect("activate", self.on_copy)
        menu.add(copy_item)
        
        accel_group = menu.get_accel_group()
        print "accel", accel_group
        if accel_group == None:
            accel_group = gtk.AccelGroup()
            menu.set_accel_group(accel_group)
            print "get", menu.get_accel_group()


        # Now add the accelerator to the menu item. Note that since we created
        # the menu item with a label the AccelLabel is automatically setup to 
        # display the accelerators.
        copy_item.add_accelerator("activate", accel_group, ord("C"),
                                  gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        copy_item.show()
    '''
    

    def _on_child_popup_menu(self, textbuffer, child, button, activate_time):
        """Callback for when child menu should appear"""
        self._image_menu.set_child(child)

        # popup menu based on child widget
        if isinstance(child, RichTextImage):
            # image menu
            self._image_menu.popup(None, None, None, button, activate_time)
            self._image_menu.show()

            
    def get_image_menu(self):
        """Returns the image popup menu"""
        return self._image_menu


    #==========================================
    # child events

    def _on_child_added(self, textbuffer, child):
        """Callback when child added to buffer"""
        self._add_children()
                               

    def _on_child_activated(self, textbuffer, child):
        """Callback for when child has been activated"""
        self.emit("child-activated", child)
        
    
    #===========================================================
    # Actions

    def _add_children(self):
        """Add all deferred children in textbuffer"""        
        self._textbuffer.add_deferred_anchors(self)
        

    def indent(self):
        """Indents selection one more level"""
        if self._textbuffer:
            self._textbuffer.indent()


    def unindent(self):
        """Unindents selection one more level"""        
        if self._textbuffer:
            self._textbuffer.unindent()

    
    def insert_image(self, image, filename="image.png"):
        """Inserts an image into the textbuffer"""
        if self._textbuffer:
            self._textbuffer.insert_image(image, filename)    

    def insert_image_from_file(self, imgfile, filename="image.png"):
        """Inserts an image from a file"""
        
        pixbuf = gdk.pixbuf_new_from_file(imgfile)
        img = RichTextImage()
        img.set_from_pixbuf(pixbuf)
        self.insert_image(img, filename)

    def insert_hr(self):
        """Inserts a horizontal rule"""
        if self._textbuffer:
            self._textbuffer.insert_hr()
        
        
    def insert_html(self, html):
        """Insert HTML content into Buffer"""

        if not self._textbuffer:
            return
        
        contents = list(self._html_buffer.read([html],
                                               partial=True,
                                               ignore_errors=True))

        # scan contents
        for kind, pos, param in contents:
            
            # download images included in html
            if kind == "anchor" and isinstance(param[0], RichTextImage):
                img = param[0]
                if img.get_filename().startswith("http:") or \
                   img.get_filename().startswith("file:"):
                    # TODO: protect this with exceptions
                    img.set_from_url(img.get_filename(), "image.png")
        
        # add to buffer
        self._textbuffer.insert_contents(contents)



    def get_link(self, it=None):

        if self._textbuffer is None:
            return None, None, None
        return self._textbuffer.get_link(it)

    
    def set_link(self, url="", start=None, end=None):
        if self._textbuffer is None:
            return

        if start is None or end is None:
            tagname = RichTextLinkTag.tag_name(url)
            self._apply_tag(tagname)
            return self._textbuffer.tag_table.looku(tagname)
        else:
            return self._textbuffer.set_link(url, start, end)
                

    #==========================================================
    # Find/Replace

    # TODO: add wrapping to search
    
    def forward_search(self, it, text, case_sensitive):
        """Finds next occurrence of 'text' searching forwards"""
        
        it = it.copy()
        text = unicode(text, "utf8")
        if not case_sensitive:
            text = text.lower()
        
        textlen = len(text)
        
        while True:
            end = it.copy()
            end.forward_chars(textlen)
                        
            text2 = it.get_slice(end)
            if not case_sensitive:
                text2 = text2.lower()
            
            if text2 == text:
                return it, end
            if not it.forward_char():
                return None
    
    
    def backward_search(self, it, text, case_sensitive):
        """Finds next occurrence of 'text' searching backwards"""
        
        it = it.copy()
        it.backward_char()
        text = unicode(text, "utf8")
        if not case_sensitive:
            text = text.lower()
        
        textlen = len(text)
        
        while True:
            end = it.copy()
            end.forward_chars(textlen)
                        
            text2 = it.get_slice(end)
            if not case_sensitive:
                text2 = text2.lower()
            
            if text2 == text:
                return it, end
            if not it.backward_char():
                return None

        
    
    def find(self, text, case_sensitive=False, forward=True, next=True):
        """Finds next occurrence of 'text'"""
        
        if not self._textbuffer:
            return
        
        it = self._textbuffer.get_iter_at_mark(self._textbuffer.get_insert())
        
        
        if forward:
            if next:
                it.forward_char()
            result = self.forward_search(it, text, case_sensitive)
        else:
            result = self.backward_search(it, text, case_sensitive)
        
        if result:
            self._textbuffer.select_range(result[0], result[1])
            self.scroll_mark_onscreen(self._textbuffer.get_insert())
            return result[0].get_offset()
        else:
            return -1
        
        
    def replace(self, text, replace_text, 
                case_sensitive=False, forward=True, next=True):
        """Replaces next occurrence of 'text' with 'replace_text'"""

        if not self._textbuffer:
            return
        
        pos = self.find(text, case_sensitive, forward, next)
        
        if pos != -1:
            self._textbuffer.begin_user_action()
            self._textbuffer.delete_selection(True, self.get_editable())
            self._textbuffer.insert_at_cursor(replace_text)
            self._textbuffer.end_user_action()
            
        return pos
        
            
    def replace_all(self, text, replace_text, 
                    case_sensitive=False, forward=True):
        """Replaces all occurrences of 'text' with 'replace_text'"""

        if not self._textbuffer:
            return
        
        found = False
        
        self._textbuffer.begin_user_action()
        while self.replace(text, replace_text, case_sensitive, forward, False) != -1:
            found = True
        self._textbuffer.end_user_action()
        
        return found

    #===========================================================
    # Spell check
    
    def can_spell_check(self):
        """Returns True if spelling is available"""
        return gtkspell is not None
    
    def enable_spell_check(self, enabled=True):
        """Enables/disables spell check"""
        if not self.can_spell_check():
            return
        
        if enabled:
            if self._spell_checker is None:
                self._spell_checker = gtkspell.Spell(self)
        else:
            if self._spell_checker is not None:
                self._spell_checker.detach()
                self._spell_checker = None

    def is_spell_check_enabled(self):
        """Returns True if spell check is enabled"""
        return self._spell_checker != None
        
    #===========================================================
    # font manipulation

    def _apply_tag(self, tag_name):
        if self._textbuffer:
            self._textbuffer.apply_tag_selected(
                self._textbuffer.tag_table.lookup(tag_name))

    def toggle_font_mod(self, mod):
        """Toggle a font modification"""
        if self._textbuffer:
            self._textbuffer.toggle_tag_selected(
                self._textbuffer.tag_table.lookup(RichTextModTag.tag_name(mod)))

    def set_font_mod(self, mod):
        """Sets a font modification"""
        self._apply_tag(RichTextModTag.tag_name(mod))


    def toggle_link(self):
        """Toggles a link tag"""

        tag, start, end = self.get_link()
        if not tag:
            tag = self._textbuffer.tag_table.lookup(
                RichTextLinkTag.tag_name(""))
        
        self._textbuffer.toggle_tag_selected(tag)

    
    def set_font_family(self, family):
        """Sets the family font of the selection"""
        self._apply_tag(RichTextFamilyTag.tag_name(family))
    
    def set_font_size(self, size):
        """Sets the font size of the selection"""
        self._apply_tag(RichTextSizeTag.tag_name(size))
    
    def set_justify(self, justify):
        """Sets the text justification"""
        self._apply_tag(RichTextJustifyTag.tag_name(justify))

    def set_font_fg_color(self, color):
        """Sets the text foreground color"""
        if self._textbuffer:
            if color:
                self._textbuffer.toggle_tag_selected(
                    self._textbuffer.tag_table.lookup(
                        RichTextFGColorTag.tag_name(color)))
            else:
                self._textbuffer.remove_tag_class_selected(
                    self._textbuffer.tag_table.lookup(
                        RichTextFGColorTag.tag_name("#000000")))

        
    def set_font_bg_color(self, color):
        """Sets the text background color"""
        if self._textbuffer:

            if color:
                self._textbuffer.toggle_tag_selected(
                    self._textbuffer.tag_table.lookup(
                        RichTextBGColorTag.tag_name(color)))
            else:
                self._textbuffer.remove_tag_class_selected(
                    self._textbuffer.tag_table.lookup(
                        RichTextBGColorTag.tag_name("#000000")))

    def toggle_bullet(self, par_type=None):
        """Toggle state of a bullet list"""
        if self._textbuffer:
            self._textbuffer.toggle_bullet_list(par_type)


    def set_font(self, font_name):
        """Font change from choose font widget"""

        if not self._textbuffer:
            return
        
        family, mods, size = parse_font(font_name)

        self._textbuffer.begin_user_action()
        
        # apply family and size tags
        self.set_font_family(family)
        self.set_font_size(size)
        
        # apply modifications
        for mod in mods:
            self.set_font_mod(mod)

        # disable modifications not given
        mod_class = self._textbuffer.tag_table.get_tag_class("mod")
        for tag in mod_class.tags:
            if tag.get_property("name") not in mods:
                self._textbuffer.remove_tag_selected(tag)

        self._textbuffer.end_user_action()
    
    #==================================================================
    # UI Updating from changing font under cursor


    def _on_font_change(self, textbuffer, font):
        """Callback for when font under cursor changes"""

        # forward signal along to listeners
        self.emit("font-change", font)
    
    def get_font(self):
        """Get the font under the cursor"""
        if self._textbuffer:
            return self._textbuffer.get_font()
        else:
            return self._blank_buffer.get_font()


    def set_default_font(self, font):
        """Sets the default font of the textview"""
        try:
            f = pango.FontDescription(font)
            self.modify_font(f)
        except:
            # TODO: think about how to handle this error
            pass

    
    
    #=========================================
    # undo/redo methods
    
    def undo(self):
        """Undo the last action in the RichTextView"""
        if self._textbuffer:
            self._textbuffer.undo()
            self.scroll_mark_onscreen(self._textbuffer.get_insert())
        
    def redo(self):
        """Redo the last action in the RichTextView"""
        if self._textbuffer:
            self._textbuffer.redo()
            self.scroll_mark_onscreen(self._textbuffer.get_insert())



# register new signals
gobject.type_register(RichTextView)
gobject.signal_new("modified", RichTextView, gobject.SIGNAL_RUN_LAST, 
    gobject.TYPE_NONE, (bool,))
gobject.signal_new("font-change", RichTextView, gobject.SIGNAL_RUN_LAST, 
    gobject.TYPE_NONE, (object,))
gobject.signal_new("child-activated", RichTextView, gobject.SIGNAL_RUN_LAST, 
    gobject.TYPE_NONE, (object,))
gobject.signal_new("visit-url", RichTextView, gobject.SIGNAL_RUN_LAST, 
    gobject.TYPE_NONE, (str,))

