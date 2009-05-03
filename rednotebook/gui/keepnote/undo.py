"""

    KeepNote
    Matt Rasmussen 2008

    UndoStack for maintaining undo and redo actions

"""

import sys

from keepnote.linked_list import LinkedList




def cat_funcs(funcs):
    """Concatenate a list of functions [f,g,h,...] that take no arguments
       into one function: cat = { lambda: f(); g(); h(); }
    """

    funcs = list(funcs)

    if len(funcs) == 1:
        return funcs[0]
    
    def f():
        for func in funcs:
            func()
    return f


class UndoStack (object):
    """UndoStack for maintaining undo and redo actions"""
    
    def __init__(self, maxsize=sys.maxint):
        """maxsize -- maximum size of undo list"""

        # stacks maintaining (undo,redo) pairs
        self._undo_actions = LinkedList()
        self._redo_actions = []

        # grouping several actions into one
        self._group_counter = 0
        self._pending_actions = []

        # suppress undo/redo while counter > 0
        self._suppress_counter = 0

        # maximum size undo stack
        self._maxsize = maxsize

        self._in_progress = False
    
    
    def do(self, action, undo, execute=True):
        """Perform action() (if execute=True) and place (action,undo) pair
           on stack"""

        if self._suppress_counter > 0:
            return    
    
        if self._group_counter == 0:
            # grouping is not active, push action pair and clear redo stack
            self._undo_actions.append((action, undo))
            self._redo_actions = []

            # TODO: should stack be suppressed at this time?
            if execute:
                action()

            # maintain proper undo size
            while len(self._undo_actions) > self._maxsize:
                self._undo_actions.pop_front()
        else:
            # grouping is active, place action pair on pending stack
            self._pending_actions.append((action, undo))
            self._redo_actions = []
            if execute:
                action()

    
    def undo(self):
        """Undo last action on stack"""
        assert self._group_counter == 0
        
        if len(self._undo_actions) > 0:
            action, undo = self._undo_actions.pop()
            self.suppress()
            self._in_progress = True
            undo()
            self._in_progress = False
            self.resume()
            self._redo_actions.append((action, undo))
    
    def redo(self):
        """Redo last action on stack"""
        assert self._group_counter == 0
    
        if len(self._redo_actions) > 0:
            action, undo = self._redo_actions.pop()
            self.suppress()
            self._in_progress = True
            action()
            self._in_progress = False
            self.resume()
            self._undo_actions.append((action, undo))

            while len(self._undo_actions) > self._maxsize:
                self._undo_actions.pop_front()
    
    def begin_action(self):
        """Start grouping actions
           Can be called recursively.  Must have corresponding end_action() call
        """
        self._group_counter += 1
    
    def end_action(self):
        """Stop grouping actions
           Can be called recursively.
        """
        self._group_counter -= 1
        assert self._group_counter >= 0

        if self._group_counter == 0:
            if len(self._pending_actions) > 0:
                actions, undos = zip(*self._pending_actions)
                
                self._undo_actions.append((cat_funcs(actions), 
                                           cat_funcs(reversed(undos))))
                self._pending_actions = []

                while len(self._undo_actions) > self._maxsize:
                    self._undo_actions.pop_front()


    def abort_action(self):
        """
        Stop grouping actions and throw away actions collected so far
        """
        
        self._group_counter = 0
        self._pending_actions = []
        

    def suppress(self):
        """Suppress pushing actions on stack
           Can be called recursively.  Must have corresponding resume() call"""
        self._suppress_counter += 1
    
    def resume(self):
        """Resume pushing actions on stack
           Can be called recursively.
        """
        self._suppress_counter -= 1
        assert self._suppress_counter >= 0
    
    def is_suppressed(self):
        """Returns True if UndoStack is being suprressed"""
        return self._suppress_counter > 0
    
    def reset(self):
        """Clear UndoStack of all actions"""
        self._undo_actions.clear()
        self._redo_actions = []
        self._group_counter = 0
        self._pending_actions = []
        self._suppress_counter = 0


    def is_in_progress(self):
        """Returns True if undo or redo is in progress"""
        return self._in_progress

