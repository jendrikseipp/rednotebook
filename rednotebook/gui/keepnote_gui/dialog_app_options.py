"""

    KeepNote
    Application Options Dialog

"""

# python imports
import os, sys

# pygtk imports
import pygtk
pygtk.require('2.0')
import gtk.glade

# keepnote imports
import keepnote
from keepnote import get_resource
from keepnote.gui.font_selector import FontSelector
from keepnote.gui import richtext


class ApplicationOptionsDialog (object):
    """Application options"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.app = main_window.app
        self.entries = {}
        
    
    def on_app_options(self):
        """Display application options"""
        
        self.xml = gtk.glade.XML(get_resource("rc", "keepnote.glade"),
                                 "app_config_dialog")
        self.dialog = self.xml.get_widget("app_config_dialog")
        self.dialog.set_transient_for(self.main_window)
        self.tabs = self.xml.get_widget("app_config_tabs")
        self.setup_overview_tree()

        

        # populate default notebook
        self.xml.get_widget("default_notebook_entry").\
            set_text(self.app.pref.default_notebook)

        # populate autosave
        self.xml.get_widget("autosave_check").set_active(
            self.app.pref.autosave)
        self.xml.get_widget("autosave_entry").set_text(
            str(int(self.app.pref.autosave_time / 1000)))

        self.xml.get_widget("autosave_entry").set_sensitive(
            self.app.pref.autosave)
        self.xml.get_widget("autosave_label").set_sensitive(
            self.app.pref.autosave)
        

        # populate default font
        #self.xml.get_widget("default_font_button").\
        #    set_font_name(self.app.pref.default_font)

        # use systray icon
        self.xml.get_widget("systray_check").set_active(self.app.pref.use_systray)
        self.xml.get_widget("skip_taskbar_check").set_active(self.app.pref.skip_taskbar)
        self.xml.get_widget("skip_taskbar_check").set_sensitive(self.app.pref.use_systray)

        # look and feel
        self.treeview_lines_check = self.xml.get_widget("treeview_lines_check")
        self.treeview_lines_check.set_active(self.app.pref.treeview_lines)
        self.listview_rules_check = self.xml.get_widget("listview_rules_check")
        self.listview_rules_check.set_active(self.app.pref.listview_rules)
        self.use_stock_icons_check = \
            self.xml.get_widget("use_stock_icons_check")
        self.use_stock_icons_check.set_active(self.app.pref.use_stock_icons)


        # populate dates
        for name in ["same_day", "same_month", "same_year", "diff_year"]:
            self.xml.get_widget("date_%s_entry" % name).\
                set_text(self.app.pref.timestamp_formats[name])


        # populate external apps
        self.entries = {}
        apps_widget = self.xml.get_widget("external_apps_frame")
        table = gtk.Table(len(self.app.pref.external_apps), 3)
        apps_widget.add_with_viewport(table)
        apps_widget.get_child().set_property("shadow-type", gtk.SHADOW_NONE)
        
        for i, app in enumerate(self.app.pref.external_apps):
            key = app.key
            app_title = app.title
            prog = app.prog
            
            # program label
            label = gtk.Label(app_title +":")
            label.set_justify(gtk.JUSTIFY_RIGHT)
            label.set_alignment(1.0, 0.5)
            label.show()
            table.attach(label, 0, 1, i, i+1,
                         xoptions=gtk.FILL, yoptions=0,
                         xpadding=2, ypadding=2)

            # program entry
            entry = gtk.Entry()
            entry.set_text(prog)
            entry.show()
            self.entries[key] = entry
            table.attach(entry, 1, 2, i, i+1,
                         xoptions=gtk.FILL | gtk.EXPAND, yoptions=0,
                         xpadding=2, ypadding=2)

            # browse button
            def button_clicked(key, title, prog):
                return lambda w: \
                    self.on_browse(key,
                                   "Choose %s" % title,
                                   prog)
            button = gtk.Button("Browse...")
            button.set_image(
                gtk.image_new_from_stock(gtk.STOCK_OPEN,
                                         gtk.ICON_SIZE_SMALL_TOOLBAR))
            button.show()
            button.connect("clicked", button_clicked(key, app_title, prog))
            table.attach(button, 2, 3, i, i+1,
                         xoptions=0, yoptions=0,
                         xpadding=2, ypadding=2)

        table.show()


        # add notebook font widget
        notebook_font_spot = self.xml.get_widget("notebook_font_spot")
        self.notebook_font_family = FontSelector()
        notebook_font_spot.add(self.notebook_font_family)
        self.notebook_font_family.show()        

        # populate notebook font
        self.notebook_font_size = self.xml.get_widget("notebook_font_size")
        self.notebook_font_size.set_value(10)

        if self.main_window.notebook is not None:
            font = self.main_window.notebook.pref.default_font
            family, mods, size = richtext.parse_font(font)
            self.notebook_font_family.set_family(family)
            self.notebook_font_size.set_value(size)

        self.xml.signal_autoconnect(self)
        self.xml.signal_autoconnect({
            "on_cancel_button_clicked": 
                lambda w: self.dialog.destroy(),
                
            "on_default_notebook_button_clicked": 
                lambda w: self.on_browse(
                    "default_notebook", 
                    "Choose Default Notebook",
                    self.app.pref.default_notebook),
            })

        self.dialog.show()


    def setup_overview_tree(self):

        # setup treeview
        self.overview = self.xml.get_widget("app_config_treeview")
        overview_store = gtk.TreeStore(str)
        self.overview.set_model(overview_store)
        self.overview.connect("cursor-changed", self.on_overview_select)
        #self.set_headers_visible(False)

        # create the treeview column
        column = gtk.TreeViewColumn()
        self.overview.append_column(column)
        cell_text = gtk.CellRendererText()
        column.pack_start(cell_text, True)
        column.add_attribute(cell_text, 'text', 0)

        # populate treestore
        app = overview_store.append(None, [keepnote.PROGRAM_NAME])
        overview_store.append(app, ["Look and Feel"])
        overview_store.append(app, ["Helper Applications"])
        overview_store.append(app, ["Data and Time"])        
        note = overview_store.append(None, ["This Notebook"])

        self.overview.expand_all()

        self.tree2tab = {
            (0,): 0,
            (0, 0,): 4,            
            (0, 1,): 1,
            (0, 2,): 2,
            (1,): 3
            }
        

    def on_overview_select(self, overview):
        """Callback for changing topic in overview"""
        
        row, col = overview.get_cursor()
        if row is not None:
            self.tabs.set_current_page(self.tree2tab[row])


    def on_autosave_check_toggled(self, widget):
        """The autosave option controls sensitivity of autosave time"""
        self.xml.get_widget("autosave_entry").set_sensitive(
            widget.get_active())
        self.xml.get_widget("autosave_label").set_sensitive(
            widget.get_active())


    def on_systray_check_toggled(self, widget):
        """Systray option controls sensitivity of skip taskbar"""
        self.xml.get_widget("skip_taskbar_check").set_sensitive(
            widget.get_active())
        
    
    def on_browse(self, name, title, filename):
        """Callback for selecting file browser"""
        
        dialog = gtk.FileChooserDialog(title, self.dialog, 
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=("Cancel", gtk.RESPONSE_CANCEL,
                     "Open", gtk.RESPONSE_OK))
        dialog.set_transient_for(self.dialog)
        dialog.set_modal(True)
                
        # set the filename if it is fully specified
        if os.path.isabs(filename):            
            dialog.set_filename(filename)
        
        response = dialog.run()
        
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()

            if name == "default_notebook":
                self.xml.get_widget("default_notebook_entry").\
                    set_text(filename)
            else:
                self.entries[name].set_text(filename)
            
        dialog.destroy()


    def on_set_default_notebook_button_clicked(self, widget):

        if self.main_window.notebook:
            self.xml.get_widget("default_notebook_entry").set_text(
                self.main_window.notebook.get_path())
            
        
    
    def on_ok_button_clicked(self, widget):
        # TODO: add arguments
    
        self.app.pref.default_notebook = \
            self.xml.get_widget("default_notebook_entry").get_text()

        # save autosave
        self.app.pref.autosave = \
            self.xml.get_widget("autosave_check").get_active()
        try:
            self.app.pref.autosave_time = \
                int(self.xml.get_widget("autosave_entry").get_text()) * 1000
        except:
            pass

        # use systray icon
        self.app.pref.use_systray = self.xml.get_widget("systray_check").get_active()
        self.app.pref.skip_taskbar = self.xml.get_widget("skip_taskbar_check").get_active()

        # look and feel
        self.app.pref.treeview_lines = self.treeview_lines_check.get_active()
        self.app.pref.listview_rules = self.listview_rules_check.get_active()
        self.app.pref.use_stock_icons = self.use_stock_icons_check.get_active()
        
        
        # save date formatting
        for name in ["same_day", "same_month", "same_year", "diff_year"]:
            self.app.pref.timestamp_formats[name] = \
                self.xml.get_widget("date_%s_entry" % name).get_text()
        

        # save external app options
        for key, entry in self.entries.iteritems():
            self.app.pref._external_apps_lookup[key].prog = \
                self.entries[key].get_text()

        # save notebook font        
        if self.main_window.notebook is not None:
            pref = self.main_window.notebook.pref
            pref.default_font = "%s %d" % (
                self.notebook_font_family.get_family(),
                self.notebook_font_size.get_value())

            self.main_window.notebook.write_preferences()
            self.main_window.notebook.notify_change(False)
            
        
        self.app.pref.write()
        self.app.pref.changed.notify()

        
        self.dialog.destroy()
        self.dialog = None
    
    
