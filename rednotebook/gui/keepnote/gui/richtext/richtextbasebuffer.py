
# pygtk imports
import pygtk
pygtk.require('2.0')
import gtk, gobject, pango
from gtk import gdk


# import textbuffer tools
from keepnote.gui.richtext.textbuffer_tools import \
     iter_buffer_contents, \
     buffer_contents_iter_to_offset, \
     normalize_tags, \
     insert_buffer_contents, \
     buffer_contents_apply_tags

from keepnote.gui.richtext.undo_handler import \
     UndoHandler, \
     Action, \
     InsertAction, \
     DeleteAction, \
     InsertChildAction, \
     TagAction

# richtext imports
from keepnote.gui.richtext.richtextbase_tags import \
     RichTextBaseTagTable, \
     RichTextTagClass, \
     RichTextTag



def add_child_to_buffer(textbuffer, it, anchor):
    textbuffer.add_child(it, anchor)


#=============================================================================
# buffer paragraph navigation

# TODO: this might go into textbuffer_tools

def move_to_start_of_line(it):
    """Move a TextIter it to the start of a paragraph"""
    
    if not it.starts_line():
        if it.get_line() > 0:
            it.backward_line()
            it.forward_line()
        else:
            it = it.get_buffer().get_start_iter()
    return it

def move_to_end_of_line(it):
    """Move a TextIter it to the start of a paragraph"""
    it.forward_line()
    return it

def get_paragraph(it):
    """Get iters for the start and end of the paragraph containing 'it'"""
    start = it.copy()
    end = it.copy()

    start = move_to_start_of_line(start)
    end.forward_line()
    return start, end

class paragraph_iter (object):
    """Iterate through the paragraphs of a TextBuffer"""

    def __init__(self, buf, start, end):
        self.buf = buf
        self.pos = start
        self.end = end
    
        # create marks that survive buffer edits
        self.pos_mark = buf.create_mark(None, self.pos, True)
        self.end_mark = buf.create_mark(None, self.end, True)

    def __del__(self):
        if self.pos_mark is not None:
            self.buf.delete_mark(self.pos_mark)
            self.buf.delete_mark(self.end_mark)

    def __iter__(self):
        while self.pos.compare(self.end) == -1:
            self.buf.move_mark(self.pos_mark, self.pos)
            yield self.pos

            self.pos = self.buf.get_iter_at_mark(self.pos_mark)
            self.end = self.buf.get_iter_at_mark(self.end_mark)
            if not self.pos.forward_line():
                break

        # cleanup marks
        self.buf.delete_mark(self.pos_mark)
        self.buf.delete_mark(self.end_mark)

        self.pos_mark = None
        self.end_mark = None

        
def get_paragraphs_selected(buf):
    """Get start and end of selection rounded to nears paragraph boundaries"""
    sel = buf.get_selection_bounds()
    
    if not sel:
        start, end = get_paragraph(buf.get_iter_at_mark(buf.get_insert()))
    else:
        start = move_to_start_of_line(sel[0])
        end = move_to_end_of_line(sel[1])
    return start, end




#=============================================================================

class RichTextAnchor (gtk.TextChildAnchor):
    """Base class of all anchor objects in a RichTextView"""
    
    def __init__(self):
        gtk.TextChildAnchor.__init__(self)
        self._widget = None
        self._buffer = None
    
    def get_widget(self):
        return self._widget

    def set_buffer(self, buf):
        self._buffer = buf

    def get_buffer(self):
        return self._buffer
    
    def copy(self):
        anchor = RichTextAnchor()
        anchor.set_buffer(self._buffer)
        return anchor
    
    def highlight(self):
        if self._widget:
            self._widget.highlight()
    
    def unhighlight(self):
        if self._widget:
            self._widget.unhighlight()

gobject.type_register(RichTextAnchor)
gobject.signal_new("selected", RichTextAnchor, gobject.SIGNAL_RUN_LAST, 
                   gobject.TYPE_NONE, ())
gobject.signal_new("activated", RichTextAnchor, gobject.SIGNAL_RUN_LAST, 
                   gobject.TYPE_NONE, ())
gobject.signal_new("popup-menu", RichTextAnchor, gobject.SIGNAL_RUN_LAST,
                   gobject.TYPE_NONE, (int, object))
gobject.signal_new("init", RichTextAnchor, gobject.SIGNAL_RUN_LAST, 
                   gobject.TYPE_NONE, ())



class RichTextBaseFont (object):
    """Class for representing a font in a simple way"""
    
    def __init__(self):
        pass


    def set_font(self, attr, tags, current_tags, tag_table):
        pass



class RichTextBaseBuffer2 (gtk.TextBuffer):
    """Basic RichTextBuffer with the following features
    
        - maintains undo/redo stacks
        - manages "current font" behavior
    """

    def __init__(self, tag_table=RichTextBaseTagTable()):
        gtk.TextBuffer.__init__(self, tag_table)
        self._undo_handler = UndoHandler(self)
        self._undo_handler.after_changed.add(self.on_after_changed)
        self.undo_stack = self._undo_handler.undo_stack

        # insert mark tracking
        self._insert_mark = self.get_insert()
        self._old_insert_mark = self.create_mark(
            None, self.get_iter_at_mark(self._insert_mark), True)

        
        self._current_tags = []
        
        self._user_action_ending = False
        self._noninteractive = 0

        # setup signals
        self._signals = [

            # local events            
            self.connect("begin_user_action", self._on_begin_user_action),
            self.connect("end_user_action", self._on_end_user_action),
            self.connect("mark-set", self._on_mark_set),
            self.connect("insert-text", self._on_insert_text),
            self.connect("insert-child-anchor", self._on_insert_child_anchor),
            self.connect("apply-tag", self._on_apply_tag),
            self.connect("remove-tag", self._on_remove_tag),

            # undo handler events
            self.connect("insert-text", self._undo_handler.on_insert_text),
            self.connect("delete-range", self._undo_handler.on_delete_range),
            self.connect("insert-pixbuf", self._undo_handler.on_insert_pixbuf),
            self.connect("insert-child-anchor", self._undo_handler.on_insert_child_anchor),
            self.connect("apply-tag", self._undo_handler.on_apply_tag),
            self.connect("remove-tag", self._undo_handler.on_remove_tag),
            self.connect("changed", self._undo_handler.on_changed)
            
            ]

        self._default_attr = gtk.TextAttributes()


    def block_signals(self):
        """Block all signal handlers"""
        for signal in self._signals:
            self.handler_block(signal)
        self.undo_stack.suppress()

    
    def unblock_signals(self):
        """Unblock all signal handlers"""
        for signal in self._signals:
            self.handler_unblock(signal)
        self.undo_stack.resume()
        self.undo_stack.reset()

    def set_default_attr(self, attr):
        self._default_attr = attr

    def get_default_attr(self):
        return self._default_attr
    

    def clear(self, clear_undo=False):
        """Clear buffer contents"""
        
        start = self.get_start_iter()
        end = self.get_end_iter()

        if clear_undo:
            self.undo_stack.suppress()

        self.begin_user_action()
        self.remove_all_tags(start, end)
        self.delete(start, end)
        self.end_user_action()

        if clear_undo:
            self.undo_stack.resume()
            self.undo_stack.reset()

    #==========================================================
    # restrict cursor and insert

    def is_insert_allowed(self, it, text=""):
        """Check that insert is allowed at TextIter 'it'"""
        return it.can_insert(True)


    def is_cursor_allowed(self, it):
        """Returns True if cursor is allowed at TextIter 'it'"""
        return True
    

    #======================================
    # child widgets

    def add_child(self, it, child):
        """Add TextChildAnchor to buffer"""
        pass

    def update_child(self, action):
        
        if isinstance(action, InsertChildAction):
            # set buffer of child
            action.child.set_buffer(self)
        

    #======================================
    # selection callbacks
    
    def on_selection_changed(self):
        pass


    #=========================================================
    # paragraph change callbacks
    
    def on_paragraph_split(self, start, end):
        pass

    def on_paragraph_merge(self, start, end):
        pass

    def on_paragraph_change(self, start, end):
        pass


    def update_paragraphs(self, action):

        if isinstance(action, InsertAction):

            # detect paragraph spliting
            if "\n" in action.text:
                par_start = self.get_iter_at_offset(action.pos)
                par_end = par_start.copy()
                par_start.backward_line()
                par_end.forward_chars(action.length)
                par_end.forward_line()
                self.on_paragraph_split(par_start, par_end)


        elif isinstance(action, DeleteAction):

            # detect paragraph merging
            if "\n" in action.text:
                par_start, par_end = get_paragraph(
                    self.get_iter_at_offset(action.start_offset))
                self.on_paragraph_merge(par_start, par_end)

     

    #===========================================================
    # callbacks
    
    def _on_mark_set(self, textbuffer, it, mark):
        """Callback for mark movement"""

        if mark is self._insert_mark:

            # if cursor is not allowed here, move it back
            old_insert = self.get_iter_at_mark(self._old_insert_mark)
            if not self.get_iter_at_mark(mark).equal(old_insert) and \
               not self.is_cursor_allowed(it):
                self.place_cursor(old_insert)
                return
            
            # if cursor startline pick up opening tags,
            # otherwise closing tags
            opening = it.starts_line()
            self._current_tags = [x for x in it.get_toggled_tags(opening)
                                  if isinstance(x, RichTextTag) and
                                  x.can_be_current()]

            # when cursor moves, selection changes
            self.on_selection_changed()

            # keep track of cursor position
            self.move_mark(self._old_insert_mark, it)
            
            # update UI for current fonts
            self.emit("font-change", self.get_font())
    


    def _on_insert_text(self, textbuffer, it, text, length):
        """Callback for text insert"""

        # NOTE: GTK does not give us a proper UTF string, so fix it
        text = unicode(text, "utf_8")
        length = len(text)
        
        # check to see if insert is allowed
        if textbuffer.is_interactive() and \
           not self.is_insert_allowed(it, text):
            textbuffer.stop_emission("insert_text")
            

    def _on_insert_child_anchor(self, textbuffer, it, anchor):
        """Callback for inserting a child anchor"""

        if not self.is_insert_allowed(it, ""):
            self.stop_emission("insert_child_anchor")
        
    def _on_apply_tag(self, textbuffer, tag, start, end):
        """Callback for tag apply"""

        if not isinstance(tag, RichTextTag):
            # do not process tags that are not rich text
            # i.e. gtkspell tags (ignored by undo/redo)
            return

        if tag.is_par_related():
            self.on_paragraph_change(start, end)

    
    def _on_remove_tag(self, textbuffer, tag, start, end):
        """Callback for tag remove"""

        if not isinstance(tag, RichTextTag):
            # do not process tags that are not rich text
            # i.e. gtkspell tags (ignored by undo/redo)
            return
        
        if tag.is_par_related():
            self.on_paragraph_change(start, end)


    def on_after_changed(self, action):
        """
        Callback after content change has occurred

        Fix up textbuffer to restore consistent state (paragraph tags,
        current font application)
        """
        
        
        self.begin_user_action()
        
        self.update_current_tags(action)
        self.update_paragraphs(action)
        self.update_child(action)
        
        self.end_user_action()


    #==================================================================
    # records whether text insert is currently user interactive, or is
    # automated
        

    def begin_noninteractive(self):
        """Begins a noninteractive mode"""
        self._noninteractive += 1

    def end_noninteractive(self):
        """Ends a noninteractive mode"""
        self._noninteractive -= 1

    def is_interactive(self):
        """Returns True when insert is currently interactive"""
        return self._noninteractive == 0


    #=====================================================================
    # undo/redo methods
    
    def undo(self):
        """Undo the last action in the RichTextView"""
        self.begin_noninteractive()
        self.undo_stack.undo()
        self.end_noninteractive()
        
    def redo(self):
        """Redo the last action in the RichTextView"""
        self.begin_noninteractive()        
        self.undo_stack.redo()
        self.end_noninteractive()
    
    def _on_begin_user_action(self, textbuffer):
        """Begin a composite undo/redo action"""

        #self._user_action = True
        self.undo_stack.begin_action()

    def _on_end_user_action(self, textbuffer):
        """End a composite undo/redo action"""
        
        if not self.undo_stack.is_in_progress() and \
           not self._user_action_ending:
            self._user_action_ending = True
            self.on_ending_user_action()
            self._user_action_ending = False
        self.undo_stack.end_action()


    def on_ending_user_action(self):
        """
        Callback for when user action is about to end
        Convenient for implementing extra actions that should be included
        in current user action
        """
        pass



class RichTextBaseBuffer (RichTextBaseBuffer2):
    """Basic RichTextBuffer with the following features
    
        - manages "current font" behavior
    """
    
    def __init__(self, tag_table=RichTextBaseTagTable()):
        RichTextBaseBuffer2.__init__(self, tag_table)

        self._current_tags = []

    #==============================================================
    # Tag manipulation    

    def update_current_tags(self, action):
        """Check if current tags need to be applited due to action"""

        self.begin_user_action()

        if isinstance(action, InsertAction):

            # apply current style to inserted text if inserted text is
            # at cursor            
            if action.cursor_insert and \
               len(self._current_tags) > 0:

                it = self.get_iter_at_offset(action.pos)
                it2 = it.copy()
                it2.forward_chars(action.length)

                for tag in action.current_tags:
                    self.apply_tag(tag, it, it2)

        self.end_user_action()

    
    def get_current_tags(self):
        """Returns the currently active tags"""
        return self._current_tags

    def set_current_tags(self, tags):
        """Sets the currently active tags"""
        self._current_tags = list(tags)
        self.emit("font-change", self.get_font())
    

    def can_be_current_tag(self, tag):
        return isinstance(tag, RichTextTag) and tag.can_be_current()
        

    def toggle_tag_selected(self, tag, start=None, end=None):
        """Toggle tag in selection or current tags"""

        self.begin_user_action()

        if start is None:
            it = self.get_selection_bounds()
        else:
            it = [start, end]

        # toggle current tags
        if self.can_be_current_tag(tag):
            if tag not in self._current_tags:
                self.clear_current_tag_class(tag)
                self._current_tags.append(tag)
            else:
                self._current_tags.remove(tag)            

        # update region
        if len(it) == 2:
            if not it[0].has_tag(tag):
                self.clear_tag_class(tag, it[0], it[1])
                self.apply_tag(tag, it[0], it[1])
            else:
                self.remove_tag(tag, it[0], it[1])
        
        self.end_user_action()

        self.emit("font-change", self.get_font())


    def apply_tag_selected(self, tag, start=None, end=None):
        """Apply tag to selection or current tags"""
        
        self.begin_user_action()

        if start is None:
            it = self.get_selection_bounds()
        else:
            it = [start, end]
        
        # update current tags
        if self.can_be_current_tag(tag):
            if tag not in self._current_tags:
                self.clear_current_tag_class(tag)
                self._current_tags.append(tag)        

        # update region
        if len(it) == 2:
            self.clear_tag_class(tag, it[0], it[1])
            self.apply_tag(tag, it[0], it[1])
        self.end_user_action()

        self.emit("font-change", self.get_font())


    def remove_tag_selected(self, tag, start=None, end=None):
        """Remove tag from selection or current tags"""

        self.begin_user_action()

        if start is None:
            it = self.get_selection_bounds()
        else:
            it = [start, end]
        
        # no selection, remove tag from current tags
        if tag in self._current_tags:
            self._current_tags.remove(tag)

        # update region
        if len(it) == 2:
            self.remove_tag(tag, it[0], it[1])
        self.end_user_action()

        self.emit("font-change", self.get_font())


    def remove_tag_class_selected(self, tag, start=None, end=None):
        """Remove all tags of a class from selection or current tags"""

        self.begin_user_action()

        if start is None:
            it = self.get_selection_bounds()
        else:
            it = [start, end]
        
        # no selection, remove tag from current tags
        self.clear_current_tag_class(tag)        

        # update region
        if len(it) == 2:
            self.clear_tag_class(tag, it[0], it[1])
        self.end_user_action()

        self.emit("font-change", self.get_font())

    
    def clear_tag_class(self, tag, start, end):
        """Remove all tags of the same class as 'tag' in region (start, end)"""

        # TODO: is there a faster way to do this?
        #   make faster mapping from tag to class

        cls = self.tag_table.get_class_of_tag(tag)
        if cls is not None and cls.exclusive:
            for tag2 in cls.tags:
                self.remove_tag(tag2, start, end)

        self.emit("font-change", self.get_font())



    def clear_current_tag_class(self, tag):
        """Remove all tags of the same class as 'tag' from current tags"""
        
        cls = self.tag_table.get_class_of_tag(tag)
        if cls is not None and cls.exclusive:
            self._current_tags = [x for x in self._current_tags
                                  if x not in cls.tags]
            

    
    #===========================================================
    # Font management
    
    def get_font(self, font=None):
        """Returns the active font under the cursor"""
        
        # get iter for retrieving font
        it2 = self.get_selection_bounds()
        
        if len(it2) == 0:
            it = self.get_iter_at_mark(self.get_insert())
        else:
            it = it2[0]
            it.forward_char()
        
        # create a set that is fast for quering the existance of tags
        current_tags = set(self._current_tags)        
        
        # get the text attributes and font at the iter
        attr = gtk.TextAttributes()
        self._default_attr.copy_values(attr)
        it.get_attributes(attr)
        tags = it.get_tags()

        # create font object and return
        if font is None:
            font = RichTextFont()
        font.set_font(attr, tags, current_tags, self.tag_table)
        return font





gobject.type_register(RichTextBaseBuffer)
gobject.signal_new("font-change", RichTextBaseBuffer, gobject.SIGNAL_RUN_LAST, 
                   gobject.TYPE_NONE, (object,))
