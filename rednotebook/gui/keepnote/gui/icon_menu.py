"""

   Change Node Icon Sub Menu

"""


# pygtk imports
import pygtk
pygtk.require('2.0')
import gobject
import gtk

import keepnote.gui

default_menu_icons = [x for x in keepnote.gui.builtin_icons
                      if "-open." not in x][:20]



class IconMenu (gtk.Menu):
    """Icon picker menu"""

    def __init__(self):
        gtk.Menu.__init__(self)

        # default icon
        self.default_icon = gtk.MenuItem("_Default Icon")
        self.default_icon.connect("activate",
                                  lambda w: self.emit("set-icon", ""))
        self.default_icon.show()

        # new icon
        self.new_icon = gtk.MenuItem("_New Icon...")
        self.new_icon.show()


        self.width = 4
        self.posi = 0
        self.posj = 0
        
        self.setup_menu(None)


    def set_notebook(self, notebook):
        self._notebook = notebook
        

    def clear(self):
        """clear menu"""
        
        self.foreach(lambda item: self.remove(item))        
        self.posi = 0
        self.posj = 0
        

    def setup_menu(self, notebook):

        self.clear()       

        self.set_notebook(notebook)

        if notebook is None:
            for iconfile in default_menu_icons:                    
                self.add_icon(iconfile)
        else:
            for iconfile in notebook.pref.quick_pick_icons:                
                self.add_icon(iconfile)

        # separator
        item = gtk.SeparatorMenuItem()
        item.show()
        self.append(item)

        # default icon               
        self.append(self.default_icon)

        # new icon        
        self.append(self.new_icon)

        # make changes visible
        self.unrealize()
        self.realize()
        

    def append_grid(self, item):
        self.attach(item, self.posj, self.posj+1, self.posi, self.posi+1)
        
        self.posj += 1
        if self.posj >= self.width:
            self.posj = 0
            self.posi += 1

    def append(self, item):
        
        # reset posi, posj
        if self.posj > 0:
            self.posi += 1
            self.posj = 0

        gtk.Menu.append(self, item)

    def add_icon(self, iconfile):

        child = gtk.MenuItem("")
        child.remove(child.child)
        img = gtk.Image()
        iconfile2 = keepnote.gui.lookup_icon_filename(self._notebook, iconfile)
        img.set_from_file(iconfile2)
        child.add(img)
        child.child.show()
        child.show()
        child.connect("activate",
                      lambda w: self.emit("set-icon", iconfile))
        self.append_grid(child)


gobject.type_register(IconMenu)
gobject.signal_new("set-icon", IconMenu, gobject.SIGNAL_RUN_LAST, 
           gobject.TYPE_NONE, (object,))

