"""

    KeepNote
    Image Resize Dialog

"""

# python imports
import os

# pygtk imports
import pygtk
pygtk.require('2.0')
from gtk import gdk
import gtk.glade

# keepnote imports
import keepnote
from keepnote import get_resource

# TODO: separate out error callback



class ImageResizeDialog (object):
    """Image Resize dialog """
    
    def __init__(self, main_window, app_pref):
        self.main_window = main_window
        self.app_pref = app_pref
        self.dialog = None
        self.image = None
        self.aspect = True
        self.owidth, self.oheight = None, None
        self.init_width, self.init_height = None, None
        self.ignore_change = False
        self.snap_size = self.app_pref.image_size_snap_amount
        self.snap_enabled = self.app_pref.image_size_snap

        # widgets
        self.size_scale = None
        self.width_entry = None
        self.height_entry = None
        self.aspect_check = None
        self.snap_check = None
        self.snap_entry = None
        
    
    def on_resize(self, image):
        """Launch resize dialog"""
        if not image.is_valid():
            self.main_window.error("Cannot resize image that is not properly loaded")
            return
        
        self.xml = gtk.glade.XML(get_resource("rc", "keepnote.glade"))    
        self.dialog = self.xml.get_widget("image_resize_dialog")
        self.dialog.set_transient_for(self.main_window)
        self.dialog.connect("response", lambda d, r: self.on_response(r))       
        self.dialog.show()

        self.image = image
        self.aspect = True
        width, height = image.get_size(True)
        self.init_width, self.init_height = width, height
        self.owidth, self.oheight = image.get_original_size()

        # get widgets
        self.width_entry = self.xml.get_widget("width_entry")
        self.height_entry = self.xml.get_widget("height_entry")
        self.size_scale = self.xml.get_widget("size_scale")
        self.aspect_check = self.xml.get_widget("aspect_check")
        self.snap_check = self.xml.get_widget("img_snap_check")
        self.snap_entry = self.xml.get_widget("img_snap_amount_entry")

        # populate info
        self.width_entry.set_text(str(width))
        self.height_entry.set_text(str(height))
        self.size_scale.set_value(width)
        self.snap_check.set_active(self.snap_enabled)
        self.snap_entry.set_text(str(self.snap_size))
        
        # callback
        self.xml.signal_autoconnect({
            "on_width_entry_changed":
                lambda w: self.on_size_changed("width"),
            "on_height_entry_changed":
                lambda w: self.on_size_changed("height"),
            "on_aspect_check_toggled": 
                lambda w: self.on_aspect_toggled(),
            "on_size_scale_value_changed":
                self.on_scale_value_changed,
            "on_img_snap_check_toggled":
                self.on_snap_check_toggled,
            "on_img_snap_amount_entry_changed":
                self.on_snap_entry_changed,
            })


    def get_size(self):
        """Returns the current size setting of the dialog"""
        wstr = self.width_entry.get_text()
        hstr = self.height_entry.get_text()

        try:
            width, height = int(wstr), int(hstr)

            if width <= 0:
                width = None
            if height <= 0:
                height = None
            
        except ValueError:
            width, height = None, None
        return width, height
        

    def on_response(self, response):
        """Callback for a response button in dialog"""
        if response == gtk.RESPONSE_OK:
            width, height = self.get_size()

            self.app_pref.image_size_snap = self.snap_enabled
            self.app_pref.image_size_snap_amount = self.snap_size
            
            if width is not None:
                self.image.scale(width, height)
                self.dialog.destroy()
            else:
                self.main_window.error("Must specify positive integers for image size")
            
        elif response == gtk.RESPONSE_CANCEL:
            self.dialog.destroy()

        elif response == gtk.RESPONSE_APPLY:
            width, height = self.get_size()

            if width is not None:
                self.image.scale(width, height)

        elif response == gtk.RESPONSE_REJECT:
            # restore default image size
                        
            width, height = self.image.get_original_size()
            self.width_entry.set_text(str(width))
            self.height_entry.set_text(str(height))
            

    def on_size_changed(self, dim):
        """Callback when a size changes"""
        
        if self.aspect and not self.ignore_change:
            self.ignore_change = True
            width, height = self.get_size()
            
            if dim == "width" and width is not None:
                height = int(width / float(self.owidth) * self.oheight)
                self.size_scale.set_value(width)

                self.height_entry.set_text(str(height))

            elif dim == "height" and height is not None:
                width = int(height / float(self.oheight) * self.owidth)
                self.width_entry.set_text(str(width))
                
            self.ignore_change = False
        else:
            width, height = self.get_size()

        if width is not None and height is not None:
            self.init_width, self.init_height = width, height
            

    def on_aspect_toggled(self):
        """Callback when aspect checkbox is toggled"""
        self.aspect = self.aspect_check.get_active()
    

    def on_scale_value_changed(self, scale):
        """Callback for when scale value changes"""
        width = int(scale.get_value())

        if self.snap_enabled:
            snap = self.snap_size
            width = int((width + snap/2.0) // snap * snap)
        
        factor = width / float(self.init_width)
        height = int(factor * self.init_height)

        if not self.ignore_change:
            self.ignore_change = True
            self.width_entry.set_text(str(width))
            self.height_entry.set_text(str(height))
            self.ignore_change = False


    def on_snap_check_toggled(self, check):
        """Callback when snap checkbox is toggled"""
        self.snap_enabled = self.snap_check.get_active()
        self.snap_entry.set_sensitive(self.snap_enabled)
        


    def on_snap_entry_changed(self, entry):
        """Callback when snap text entry changes"""
        try:
            self.snap_size = int(self.snap_entry.get_text())
        except ValueError:
            pass
        
