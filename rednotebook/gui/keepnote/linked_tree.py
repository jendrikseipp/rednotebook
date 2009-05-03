"""
   A tree implemented with linked lists
"""

class LinkedTreeNode (object):
    """A node in a linked list tree"""

    def __init__(self):
        self._parent = None
        self._next = None
        self._prev = None
        self._child = None

        # NOTE: if first self == self._parent._child, then
        # self._prev == last sibling

    def get_parent(self):
        """Returns parent"""
        return self._parent

    def __iter__(self):
        """Iterate over children"""
        node = self._child
        while node:
            yield node
            node = node._next

    def get_children_list(self):
        """Returns a list of the children"""
        return list(self)

    def num_children(self):
        """Returns the number of children"""
        n = 0
        for child in self:
            n += 1
        return n

    def first_child(self):
        """Return first child or None"""
        return self._child

    def is_leaf(self):
        """Returns True if node has no children"""
        return self._child is None

    def last_child(self):
        """Returns last child or None"""
        if not self._child:
            return None
        else:
            return self._child._prev

    def next_sibling(self):
        """Returns next sibling or None"""
        return self._next

    def prev_sibling(self):
        """Returns previous sibling or None"""
        if self._parent and self._parent._child is not self:
            return self._prev
        else:
            return None
            

    def append_child(self, child):
        """Append child to end of sibling list"""

        if self._child is None:
            # add first child
            self._child = child
            child._prev = child
        else:
            # append child to end of sibling list
            last = self._child._prev
            last._next = child
            child._prev = last
            self._child._prev = child

        child._next = None
        child._parent = self

    def prepend_child(self, child):
        """Prepend child to begining of sibling list"""

        if self._child is None:
            # add first child
            self._child = child
            child._prev = child
            child._next = None
        else:
            # prepend to begining of sibling list
            first = self._child
            child._next = first
            child._prev = first._prev            
            first._prev = child
            self._child = child

        child._parent = self

    def remove_child(self, child):
        """Remove child from Node"""
        assert child._parent is self
        self.child.remove()


    def replace_child(self, old_child, new_child):
        """Replace the old_child with a new_child"""

        assert old_child._parent == self

        # set parent child link
        if self._child == old_child:
            self._child = new_child
        else:
            old_child._prev._next = new_child

        # copy over old links
        new_child._next = old_child._next
        if old_child._prev == old_child:
            new_child._prev = new_child
        else:
            new_child._prev = old_child._prev
        new_child._parent = self

        # notify siblings
        if new_child._next is not None:
            new_child._next._prev = new_child
        else:
            # notify first child
            new_child._parent._child._prev = new_child
        
        

        # clear old links
        old_child._next = None
        old_child._prev = None
        old_child._parent = None


    def insert_before(self, child, new_child):
        """Insert new_child before child"""

        new_child._prev = child._prev
        if self._child != child:
            child._prev._next = new_child
        else:
            self._child = new_child
        child._prev = new_child
        new_child._next = child
        new_child._parent = self
        
    

    def remove(self):
        """Remove from parent"""
        
        if self._next:
            # setup next sibling
            self._next._prev = self._prev
        else:
            # notify first child
            self._parent._child._prev = self._prev
        if self._parent._child is not self:
            # setup prev sibling, if they exist
            self._prev._next = self._next
        else:
            # find new first child
            self._parent._child = self._next

        # remove old links
        self._parent = None
        self._next = None
        self._prev = None
    
        

