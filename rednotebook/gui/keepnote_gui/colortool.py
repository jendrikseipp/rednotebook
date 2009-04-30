"""

    KeepNote
    Matt Rasmussen 2008
    
    ColorTool.py

    Color picker for the toolbar

"""


# pygtk imports
import pygtk
pygtk.require('2.0')
from gtk import gdk
import gtk.glade
import gobject
import pango

from keepnote.gui import get_resource_image


FONT_LETTER = "A"

m = 65535
DEFAULT_COLORS = [

            # lights
            (m, .6*m, .6*m),
            (m, .8*m, .6*m),
            (m, m, .6*m),
            (.6*m, m, .6*m),
            (.6*m, m, m),
            (.6*m, .6*m, m),
            (m, .6*m, m),

            # trues
            (m, 0, 0),                    
            (m, m*.64, 0),
            (m, m, 0),                    
            (0, m, 0),
            (0, m, m),
            (0, 0, m),
            (m, 0, m),

            # darks
            (.5*m, 0, 0),
            (.5*m, .32*m, 0),
            (.5*m, .5*m, 0),
            (0, .5*m, 0),
            (0, .5*m, .5*m),
            (0, 0, .5*m),
            (.5*m, 0, .5*m),

            # white, gray, black
            (m, m, m),
            (.9*m, .9*m, .9*m),
            (.75*m, .75*m, .75*m),
            (.5*m, .5*m, .5*m),
            (.25*m, .25*m, .25*m),
            (.1*m, .1*m, .1*m),                    
            (0, 0, 0),                    
        ]

# TODO: share the same pallete between color menus



class ColorTextImage (gtk.Image):
    """Image widget that display a color box with and without text"""

    def __init__(self, width, height, letter, border=True):
        gtk.Image.__init__(self)
        self.width = width
        self.height = height
        self.letter = letter
        self.border = border
        self.marginx = int((width - 10) / 2.0)
        self.marginy = - int((height - 12) / 2.0)
        self._pixmap = None
        self._colormap = None
        self.fg_color = None
        self.bg_color = None
        self._exposed = False

        self.connect("parent-set", self.on_parent_set)
        self.connect("expose-event", self.on_expose_event)
        

    def on_parent_set(self, widget, old_parent):
        self._exposed = False
            
        
    def on_expose_event(self, widget, event):
        """Set up colors on exposure"""

        if not self._exposed:
            self._exposed = True
            self.init_colors()


    def init_colors(self):
        self._pixmap = gdk.Pixmap(self.parent.window,
                                  self.width, self.height, -1)
        self.set_from_pixmap(self._pixmap, None)
        self._colormap = self._pixmap.get_colormap()
        #self._colormap = gtk.gdk.colormap_get_system()
        #gtk.gdk.screen_get_default().get_default_colormap()
        self._gc = self._pixmap.new_gc()

        self._context = self.get_pango_context()
        self._fontdesc = pango.FontDescription("sans bold 10")

        if isinstance(self.fg_color, tuple):
            self.fg_color = self._colormap.alloc_color(*self.fg_color)
        elif self.fg_color is None:
            self.fg_color = self._colormap.alloc_color(
                self.get_style().text[gtk.STATE_NORMAL])

        if isinstance(self.bg_color, tuple):
            self.bg_color = self._colormap.alloc_color(*self.bg_color)
        elif self.bg_color is None:
            self.bg_color = self._colormap.alloc_color(
                self.get_style().bg[gtk.STATE_NORMAL])
        
        self._border_color = self._colormap.alloc_color(0, 0, 0)
        self.refresh()


    def set_fg_color(self, red, green, blue, refresh=True):
        """Set the color of the color chooser"""
        if self._colormap:
            self.fg_color = self._colormap.alloc_color(red, green, blue)
            if refresh:
                self.refresh()
        else:
            self.fg_color = (red, green, blue)


    def set_bg_color(self, red, green, blue, refresh=True):
        """Set the color of the color chooser"""
        if self.bg_color:
            self.bg_color = self._colormap.alloc_color(red, green, blue)
            if refresh:
                self.refresh()
        else:
            self.bg_color = (red, green, blue)        
        

    def refresh(self):
        self._gc.foreground = self.bg_color
        self._pixmap.draw_rectangle(self._gc, True, 0, 0,
                                    self.width, self.height)
        if self.border:
            self._gc.foreground = self._border_color
            self._pixmap.draw_rectangle(self._gc, False, 0, 0,
                                        self.width-1, self.height-1)

        if self.letter:
            self._gc.foreground = self.fg_color
            layout = pango.Layout(self._context)
            layout.set_text(FONT_LETTER)
            layout.set_font_description(self._fontdesc)
            self._pixmap.draw_layout(self._gc, self.marginx,
                                     self.marginy,
                                     layout)

        self.set_from_pixmap(self._pixmap, None)



class ColorMenu (gtk.Menu):
    """Color picker menu"""

    def __init__(self, default_colors=DEFAULT_COLORS):
        gtk.Menu.__init__(self)

        self.width = 7
        self.posi = 4
        self.posj = 0

        no_color = gtk.MenuItem("_Default Color")
        no_color.show()
        no_color.connect("activate", self.on_no_color)
        self.attach(no_color, 0, self.width, 0, 1)

        # new color
        new_color = gtk.MenuItem("_New Color...")
        new_color.show()
        new_color.connect("activate", self.on_new_color)
        self.attach(new_color, 0, self.width, 1, 2)

        # grab color
        #new_color = gtk.MenuItem("_Grab Color")
        #new_color.show()
        #new_color.connect("activate", self.on_grab_color)
        #self.attach(new_color, 0, self.width, 2, 3)

        # separator
        item = gtk.SeparatorMenuItem()
        item.show()
        self.attach(item, 0, self.width,  3, 4)

        # default colors
        self.set_default_colors(default_colors)

        # separator
        if self.posj != 0:
            self.posj = 0
            self.posi += 2
        else:
            self.posi += 1
        item = gtk.SeparatorMenuItem()
        item.show()
        self.attach(item, 0, self.width,  self.posi-1, self.posi)
        self.unrealize()
        self.realize()
        


    def set_default_colors(self, colors):
        self.default_colors = list(colors)
        for color in self.default_colors:
            self.append_color(map(int, color))

    def on_new_color(self, menu):
        """Callback for new color"""
        dialog = gtk.ColorSelectionDialog("Choose color")
        dialog.colorsel.set_has_opacity_control(False)
        response = dialog.run()

        if response == gtk.RESPONSE_OK:                    
            color = dialog.colorsel.get_current_color()
            self.append_color([color.red, color.green, color.blue])
            self.emit("set-color", (color.red, color.green, color.blue))

        dialog.destroy()

    def on_no_color(self, menu):
        """Callback for no color"""
        self.emit("set-color", None)

    def on_grab_color(self, menu):
        pass
        # TODO: complete

    def append_color(self, color):
        self.add_color(self.posi, self.posj,
                       color[0], color[1], color[2])
        self.posj += 1
        if self.posj >= self.width:
            self.posj = 0
            self.posi += 1

    def add_color(self, i, j, r, g, b):                
        self.unrealize()

        child = gtk.MenuItem("")
        child.remove(child.child)
        img = ColorTextImage(15, 15, False)                
        img.set_bg_color(r, g, b)
        child.add(img)
        child.child.show()
        child.show()
        child.connect("activate", lambda w: self.emit("set_color",
                                                      (r, g, b)))
        self.attach(child, j, j+1, i, i+1)

        self.realize()

gobject.type_register(ColorMenu)
gobject.signal_new("set-color", ColorMenu, gobject.SIGNAL_RUN_LAST, 
                   gobject.TYPE_NONE, (object,))


class ColorTool (gtk.MenuToolButton):
    """Abstract base class for a ColorTool"""

    def __init__(self, icon, default):
        gtk.MenuToolButton.__init__(self, self.icon, "")
        self.icon = icon
        self.connect("clicked", self.use_color)
        
        self.menu = ColorMenu()
        self.menu.connect("set-color", self.set_color)
        self.set_menu(self.menu)
        
        self.default = default
        self.color = None
        self.default_set = True

        # TODO: make my own menu drop with a smaller drop arrow
        #self.child.get_children()[1].set_image(
        #    get_resource_image("cut.png"))


    def set_color(self, menu, color):
        """Callback from menu"""
        raise Exception("unimplemented")


    def use_color(self, menu):
        self.emit("set-color", self.color)
        

    def set_default(self, color):
        """Set default color"""
        self.default = color
        if self.default_set:
            self.icon.set_fg_color(*self.default)


gobject.type_register(ColorTool)
gobject.signal_new("set-color", ColorTool, gobject.SIGNAL_RUN_LAST, 
                   gobject.TYPE_NONE, (object,))


class FgColorTool (ColorTool):
    """ToolItem for choosing the foreground color"""
    
    def __init__(self, width, height, default):
        self.icon = ColorTextImage(width, height, True, True)
        self.icon.set_fg_color(default[0], default[1], default[2])
        self.icon.set_bg_color(65535, 65535, 65535)
        ColorTool.__init__(self, self.icon, default)


    def set_color(self, menu, color):
        """Callback from menu"""
        if color is None:
            self.default_set = True
            self.icon.set_fg_color(*self.default)
        else:
            self.default_set = False
            self.icon.set_fg_color(color[0], color[1], color[2])

        self.color = color
        self.emit("set-color", color)

 

class BgColorTool (ColorTool):
    """ToolItem for choosing the backgroundground color"""
    
    def __init__(self, width, height, default):
        self.icon = ColorTextImage(width, height, False, True)
        self.icon.set_bg_color(default[0], default[1], default[2])
        ColorTool.__init__(self, self.icon, default)

    
    def set_color(self, menu, color):
        """Callback from menu"""
        if color is None:
            self.default_set = True
            self.icon.set_bg_color(*self.default)
        else:
            self.default_set = False
            self.icon.set_bg_color(color[0], color[1], color[2])

        self.color = color
        self.emit("set-color", color)
