

# pygtk imports
import pygtk
pygtk.require('2.0')
from gtk import gdk
import gtk.glade
import gobject



class FontSelector (gtk.ComboBox):
    """ComboBox for selection Font family"""
    
    def __init__(self):
        gtk.ComboBox.__init__(self)

        self._list = gtk.ListStore(str)
        self.set_model(self._list)
        
        self._families = sorted(f.get_name()
            for f in self.get_pango_context().list_families())
        self._lookup = [x.lower() for x in self._families]

        for f in self._families:
            self._list.append([f])

        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        
        fam = self.get_pango_context().get_font_description().get_family()
        self.set_family(fam)

        
    def set_family(self, family):
        try:
            index = self._lookup.index(family.lower())
            self.set_active(index)
        except:
            pass
        

    def get_family(self):
        return self._families[self.get_active()]
