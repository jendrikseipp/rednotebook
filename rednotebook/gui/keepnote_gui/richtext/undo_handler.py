# default maximum undo levels
MAX_UNDOS = 100


# keepnote imports
from keepnote.undo import UndoStack
from keepnote.listening import Listeners

# import textbuffer tools
from keepnote.gui.richtext.textbuffer_tools import \
     iter_buffer_contents, \
     buffer_contents_iter_to_offset, \
     normalize_tags, \
     insert_buffer_contents, \
     buffer_contents_apply_tags

# richtext imports
from keepnote.gui.richtext.richtextbase_tags import \
     RichTextTag



def add_child_to_buffer(textbuffer, it, anchor):
    textbuffer.add_child(it, anchor)


#=============================================================================
# RichTextBaseBuffer undoable actions

class Action (object):
    """A base class for undoable actions in RichTextBuffer"""
    
    def __init__(self):
        pass
    
    def do(self):
        pass
    
    def undo(self):
        pass


class InsertAction (Action):
    """Represents the act of inserting text"""
    
    def __init__(self, textbuffer, pos, text, length, cursor_insert=False):
        Action.__init__(self)
        self.textbuffer = textbuffer
        self.current_tags = list(textbuffer.get_current_tags())
        self.pos = pos
        self.text = text
        self.length = length
        self.cursor_insert = cursor_insert
        #assert len(self.text) == self.length

        
    def do(self):
        start = self.textbuffer.get_iter_at_offset(self.pos)
        self.textbuffer.place_cursor(start)

        # set current tags and insert text
        self.textbuffer.set_current_tags(self.current_tags)
        self.textbuffer.insert(start, self.text)
    
    def undo(self):
        start = self.textbuffer.get_iter_at_offset(self.pos)
        end = self.textbuffer.get_iter_at_offset(self.pos + self.length)
        self.textbuffer.place_cursor(start)

        #assert start.get_slice(end) == self.text, \
        #       (start.get_slice(end), self.text)
        self.textbuffer.delete(start, end)



class DeleteAction (Action):
    """Represents the act of deleting a region in a RichTextBuffer"""
    
    def __init__(self, textbuffer, start_offset, end_offset, text,
                 cursor_offset):
        Action.__init__(self)
        self.textbuffer = textbuffer
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.text = text
        self.cursor_offset = cursor_offset
        self.contents = []        
        self._record_range()


    def do(self):
        start = self.textbuffer.get_iter_at_offset(self.start_offset)
        end = self.textbuffer.get_iter_at_offset(self.end_offset)
        self.textbuffer.place_cursor(start)
        self._record_range()
        self.textbuffer.delete(start, end)


    def undo(self):
        start = self.textbuffer.get_iter_at_offset(self.start_offset)
        
        self.textbuffer.begin_user_action()
        insert_buffer_contents(self.textbuffer, start, self.contents,
                               add_child=add_child_to_buffer)
        cursor = self.textbuffer.get_iter_at_offset(self.cursor_offset)
        self.textbuffer.place_cursor(cursor)
        self.textbuffer.end_user_action()

    
    def _record_range(self):
        start = self.textbuffer.get_iter_at_offset(self.start_offset)
        end = self.textbuffer.get_iter_at_offset(self.end_offset)
        self.contents = list(buffer_contents_iter_to_offset(
            iter_buffer_contents(self.textbuffer, start, end)))



class InsertChildAction (Action):
    """Represents the act of inserting a child object into a RichTextBuffer"""
    
    def __init__(self, textbuffer, pos, child):
        Action.__init__(self)
        self.textbuffer = textbuffer
        self.pos = pos
        self.child = child
        
    
    def do(self):
        it = self.textbuffer.get_iter_at_offset(self.pos)

        # NOTE: this is RichTextBuffer specific
        self.child = self.child.copy()
        self.textbuffer.add_child(it, self.child)
        

    
    def undo(self):
        it = self.textbuffer.get_iter_at_offset(self.pos)
        self.child = it.get_child_anchor()
        it2 = it.copy()
        it2.forward_char()
        self.textbuffer.delete(it, it2)
        


class TagAction (Action):
    """Represents the act of applying a tag to a region in a RichTextBuffer"""
    
    def __init__(self, textbuffer, tag, start_offset, end_offset, applied):
        Action.__init__(self)
        self.textbuffer = textbuffer
        self.tag = tag
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.applied = applied
        self.contents = []
        self._record_range()
        
    
    def do(self):
        start = self.textbuffer.get_iter_at_offset(self.start_offset)
        end = self.textbuffer.get_iter_at_offset(self.end_offset)
        self._record_range()
        if self.applied:
            self.textbuffer.apply_tag(self.tag, start, end)
        else:
            self.textbuffer.remove_tag(self.tag, start, end)

    
    def undo(self):
        start = self.textbuffer.get_iter_at_offset(self.start_offset)
        end = self.textbuffer.get_iter_at_offset(self.end_offset)
        
        if self.applied:
            self.textbuffer.remove_tag(self.tag, start, end)
        # undo for remove tag is simply to restore old tags
        buffer_contents_apply_tags(self.textbuffer, self.contents)
        
    
    def _record_range(self):
        start = self.textbuffer.get_iter_at_offset(self.start_offset)
        end = self.textbuffer.get_iter_at_offset(self.end_offset)

        # TODO: I can probably discard iter's.  Maybe make argument to
        # iter_buffer_contents
        self.contents = filter(lambda (kind, it, param): 
            kind in ("begin", "end") and param == self.tag,
            buffer_contents_iter_to_offset(
                iter_buffer_contents(self.textbuffer, start, end)))


#=============================================================================
# handler class



class UndoHandler (object):
    """TextBuffer Handler that provides undo/redo functionality"""

    def __init__(self, textbuffer):
        self.undo_stack = UndoStack(MAX_UNDOS)
        self._next_action = None
        self._buffer = textbuffer
        self.after_changed = Listeners()
        

    def on_insert_text(self, textbuffer, it, text, length):
        """Callback for text insert"""

        # NOTE: GTK does not give us a proper UTF string, so fix it
        text = unicode(text, "utf_8")
        length = len(text)

        # setup next action
        offset = it.get_offset()
        self._next_action = InsertAction(
            textbuffer, offset, text, length,
            cursor_insert= (offset == 
                            textbuffer.get_iter_at_mark(
                                textbuffer.get_insert()).get_offset()))
        
        
    def on_delete_range(self, textbuffer, start, end):
        """Callback for delete range"""
        # setup next action
        self._next_action = DeleteAction(textbuffer, start.get_offset(), 
                                         end.get_offset(),
                                         start.get_slice(end),
                                         textbuffer.get_iter_at_mark(
                                             textbuffer.get_insert()).get_offset())

    
    def on_insert_pixbuf(self, textbuffer, it, pixbuf):
        """Callback for inserting a pixbuf"""
        pass
    
    
    def on_insert_child_anchor(self, textbuffer, it, anchor):
        """Callback for inserting a child anchor"""
        # setup next action
        self._next_action = InsertChildAction(textbuffer, it.get_offset(),
                                              anchor)

    
    def on_apply_tag(self, textbuffer, tag, start, end):
        """Callback for tag apply"""

        if not isinstance(tag, RichTextTag):
            # do not process tags that are not rich text
            # i.e. gtkspell tags (ignored by undo/redo)
            return
        
        action = TagAction(textbuffer, tag, start.get_offset(), 
                           end.get_offset(), True)
        self.undo_stack.do(action.do, action.undo, False)
        textbuffer.set_modified(True)

    
    def on_remove_tag(self, textbuffer, tag, start, end):
        """Callback for tag remove"""

        if not isinstance(tag, RichTextTag):
            # do not process tags that are not rich text
            # i.e. gtkspell tags (ignored by undo/redo)
            return
        
        action = TagAction(textbuffer, tag, start.get_offset(), 
                           end.get_offset(), False)
        self.undo_stack.do(action.do, action.undo, False)
        textbuffer.set_modified(True)

    
    
    def on_changed(self, textbuffer):
        """Callback for buffer change"""
        
        # process actions that have changed the buffer
        if not self._next_action:
            return
        
        
        textbuffer.begin_user_action()

        # add action to undo stack
        action = self._next_action
        self._next_action = None
        self.undo_stack.do(action.do, action.undo, False)
                
        # perfrom additional "clean-up" actions
        # note: only if undo/redo is not currently in progress
        if not self.undo_stack.is_in_progress():
            self.after_changed.notify(action)
        
        textbuffer.end_user_action()
