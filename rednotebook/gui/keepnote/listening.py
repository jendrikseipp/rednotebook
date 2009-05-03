"""

    KeepNote
    Matt Rasmussen 2008

    Listener (Observer) pattern

"""


class Listeners (object):
    """Maintains a list of listeners (functions) that are called when the 
       notify function is called.
    """

    def __init__(self):
        self._listeners = []
        self._suppress = {}
    
    
    def add(self, listener):
        """Add a listener function to the list"""
        self._listeners.append(listener)
        self._suppress[listener] = 0
    
    
    def remove(self, listener):
        """Remove a listener function from list"""
        self._listeners.remove(listener)
        del self._suppress[listener]
    
    
    def clear(self):
        """Clear listener list"""
        self._listeners = []
        self._suppress = {}
    
    
    def notify(self, *args, **kargs):
        """Notify listeners"""
        for listener in self._listeners:
            if self._suppress[listener] == 0:
                listener(*args, **kargs)


    def suppress(self, listener=None):
        """Suppress notification"""
        
        if listener is not None:
            self._suppress[listener] += 1
        else:
            for l in self._suppress:
                self._suppress[l] += 1
    
    
    def resume(self, listener=None):
        """Resume notification"""
        if listener is not None:
            self._suppress[listener] -= 1
        else:
            for l in self._suppress:
                self._suppress[l] -= 1
    
