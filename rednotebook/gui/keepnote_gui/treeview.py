"""

    KeepNote
    
    TreeView 

"""


# pygtk imports
import pygtk
pygtk.require('2.0')
import gtk, gobject, pango
from gtk import gdk

# keepnote imports
from keepnote.gui import treemodel
from keepnote.gui import basetreeview
from keepnote.notebook import NoteBookTrash, \
              NoteBookError




class KeepNoteTreeView (basetreeview.KeepNoteBaseTreeView):
    """
    TreeView widget for the KeepNote NoteBook
    """
    
    def __init__(self):
        basetreeview.KeepNoteBaseTreeView.__init__(self)

        self._notebook = None

        self.set_model(treemodel.KeepNoteTreeModel())
                
        # treeview signals
        self.connect("key-release-event", self.on_key_released)
        self.connect("button-press-event", self.on_button_press)
        
        
        # selection config
        #self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
        self.set_headers_visible(False)

        # make treeview searchable
        self.set_search_column(self.model.get_column_by_name("title").pos)
        #self.set_fixed_height_mode(True)       

        # tree style
        try:
            # available only on gtk > 2.8
            self.set_property("enable-tree-lines", True)
        except TypeError, e:
            pass


        # create the treeview column
        self.column = gtk.TreeViewColumn()
        self.column.set_clickable(False)
        self.append_column(self.column)

        # create a cell renderers
        self.cell_icon = gtk.CellRendererPixbuf()
        self.cell_text = gtk.CellRendererText()
        self.cell_text.connect("editing-started", self.on_editing_started)
        self.cell_text.connect("editing-canceled", self.on_editing_canceled)
        self.cell_text.connect("edited", self.on_edit_title)
        self.cell_text.set_property("editable", True)        

        # add the cells to column
        self.column.pack_start(self.cell_icon, False)
        self.column.pack_start(self.cell_text, True)

        # map cells to columns in treestore
        self.column.add_attribute(self.cell_icon, 'pixbuf',
                                  self.model.get_column_by_name("icon").pos)
        self.column.add_attribute(self.cell_icon, 'pixbuf-expander-open',
                                  self.model.get_column_by_name("icon_open").pos)
        self.column.add_attribute(self.cell_text, 'text',
                                  self.model.get_column_by_name("title").pos)

        self.menu = gtk.Menu()
        self.menu.attach_to_widget(self, lambda w,m:None)

        self.set_sensitive(False)


        
    
    #=============================================
    # gui callbacks
    
        
    def on_key_released(self, widget, event):
        """Process delete key"""
        
        if event.keyval == gdk.keyval_from_name("Delete") and \
           not self.editing:
            self.on_delete_node()
            self.stop_emission("key-release-event")

    def on_button_press(self, widget, event):
        """Process context popup menu"""
        
        if event.button == 3:            
            # popup menu
            self.popup_menu(event.x, event.y, event.button, event.time)
            

    
    #==============================================
    # actions
    
    def set_notebook(self, notebook):
        basetreeview.KeepNoteBaseTreeView.set_notebook(self, notebook)
        
        
        if self._notebook is None:
            self.model.set_root_nodes([])
            self.set_sensitive(False)
        
        else:
            self.set_sensitive(True)
            
            root = self._notebook.get_root_node()
            model = self.model
            
            self.set_model(None)
            model.set_root_nodes([root])
            self.set_model(model)
            
            if root.get_attr("expanded", True):
                self.expand_to_path((0,))

    
    def edit_node(self, node):
        path = treemodel.get_path_from_node(self.model, node,
                                            self.rich_model.get_node_column())
        self.set_cursor_on_cell(path, self.column, self.cell_text, 
                                         True)
        gobject.idle_add(lambda: self.scroll_to_cell(path))


