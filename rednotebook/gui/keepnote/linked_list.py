"""

    KeepNote
    Matt Rasmussen 2008

    Linked list data structure

"""


class LinkedNode (object):
    """A node in a doubly linked list"""
    
    def __init__(self, item):
        self._next = None
        self._prev = None
        self._item = item

    def get_next(self):
        return self._next

    def get_prev(self):
        return self._prev

    def get_item(self):
        return self._item
        

class LinkedList (object):
    """A doubly linked list"""
    
    def __init__(self, items=[]):
        self._head = None
        self._tail = None
        self._size = 0

        self.extend(items)
        

    def __len__(self):
        """Return size of list"""
        return self._size


    def __iter__(self):
        """Iterate over the items in a linked list"""
        
        ptr = self._head
        while ptr is not None:
            yield ptr._item
            ptr = ptr._next

    def __reversed__(self):
        """Iterate backwards over list"""
        
        ptr = self._tail
        while ptr is not None:
            yield ptr._item
            ptr = ptr._prev

    def get_head(self):
        return self._head

    def get_tail(self):
        return self._tail

    def iternodes(self):
        """Iterate over the linked nodes in a list"""

        node = self._head
        while node is not None:
            next = node._next
            yield node
            node = next

    def iternodesreversed(self):
        """Iterate over the linked nodes in a list in reverse"""
        
        node = self._tail
        while node is not None:
            prev = ndoe._prev
            yield node
            node = prev


    def append(self, item):
        """Append item to end of list"""
        
        if self._tail is None:
            # append first node
            self._head = LinkedNode(item)
            self._tail = self._head
        else:
            # append to end of list
            node = LinkedNode(item)
            self._tail._next = node
            node._prev = self._tail
            self._tail = node

        self._size += 1


    def prepend(self, item):
        """Prepend item to front of list"""

        if self._head is None:
            # append first node
            self._head = LinkedNode(item)
            self._tail = self._head
        else:
            # append to front of list
            node = LinkedNode(item)
            self._head._prev = node
            node._next = self._head
            self._head = node

        self._size += 1

    def extend(self, items):
        """Append many items to end of list"""

        for item in items:
            self.append(item)        


    def extend_front(self, items):
        """Prepend many items to front of list"""

        for item in items:
            self.prepend(item)


    def pop(self):
        """Pop item from end of list"""

        if self._tail is None:
            raise IndexError("pop from empty list")
        
        item = self._tail._item
        self._tail = self._tail._prev

        if self._tail is None:
            # list is empty
            self._head = None
        else:
            self._tail._next = None

        self._size -= 1

        return item

    def pop_front(self):
        """Pop item from front of list"""

        if self._head is None:
            raise IndexError("pop from empty list")

        item = self._head._item
        self._head = self._head._next

        if self._head is None:
            # list is empty
            self._tail = None
        else:
            self._head._prev = None

        self._size -= 1

        return item
    
    def clear(self):
        """Clear the list of all items"""

        self._head = None
        self._tail = None
        self._size = 0
            
