


# pygtk imports
import pygtk
pygtk.require('2.0')
import gtk, gobject, pango
from gtk import gdk

# keepnote imports
from keepnote.gui import get_node_icon
from keepnote.notebook import NoteBookError, get_str_timestamp



def get_path_from_node(model, node, node_col):
    """Determine the path of a NoteBookNode 'node' in a gtk.TreeModel 'model'"""

    # NOTE: I must make no assumptions about the type of the model
    # I could change that if I make a wrapper around TreeSortModel
    
    if node is None:
        return ()

    # determine root set
    root_set = {}
    child = model.iter_children(None)
    i = 0
    while child is not None:
        root_set[model.get_value(child, node_col)] = i
        child = model.iter_next(child)
        i += 1

    # walk up parent path until root set
    node_path = []
    while node not in root_set:
        node_path.append(node)
        node = node.get_parent()
        if node is None:
            # node is not in the model (e.g. listview subset)
            return None

    # walk back down and record path
    path = [root_set[node]]
    it = model.get_iter(tuple(path))
    for node in reversed(node_path):
        child = model.iter_children(it)
        i = 0

        while child is not None:
            if model.get_value(child, node_col) == node:
                path.append(i)
                it = child
                break
            child = model.iter_next(child)
            i += 1
        else:
            raise Exception("bad model")

    return tuple(path)
        

class TreeModelColumn (object):

    def __init__(self, name, datatype, attr=None, get=lambda node: ""):
        self.pos = None
        self.name = name
        self.type = datatype
        self.attr = attr
        self.get_value = get





class KeepNoteTreeModel (gtk.GenericTreeModel):
    """
    TreeModel that wraps a subset of a NoteBook

    The subset is defined by the self._roots list.
    """

    def __init__(self, roots=[]):
        gtk.GenericTreeModel.__init__(self)
        self.set_property("leak-references", False)        
        
        self._notebook = None
        self._roots = []
        self._master_node = None
        self._date_formats = None
        self.set_root_nodes(roots)
        self._nested = True
        self._columns = []
        self._columns_lookup = {}

        # TODO: move to set_notebook
        # init default columns
        self.append_column(TreeModelColumn("icon", gdk.Pixbuf,
                            get=lambda node: get_node_icon(node, False)))
        self.append_column(
            TreeModelColumn("icon_open", gdk.Pixbuf,
                            get=lambda node: get_node_icon(node, True)))
        self.append_column(
            TreeModelColumn("title", str, get=lambda node: node.get_title()))
        self.append_column(
            TreeModelColumn("title_sort", str,
                            attr="title",
                            get=lambda node: node.get_title().lower()))
        self.append_column(
            TreeModelColumn("created_time", str,
                            get=lambda node: self.get_time_text(node,
                                                            "created_time")))
        self.append_column(
            TreeModelColumn("created_time_sort", int,
                            attr="created_time",
                            get=lambda node: node.get_attr("created_time", 0)))
        self.append_column(
            TreeModelColumn("modified_time", str,
                            get=lambda node: self.get_time_text(node,
                                                         "modified_time")))
        self.append_column(
            TreeModelColumn("modified_time_sort", int,
                            attr="modified_time",
                            get=lambda node: node.get_attr("modified_time", 0)))
        self.append_column(
            TreeModelColumn("order", int,
                            attr="order",
                            get=lambda node: node.get_order()))
        self.append_column(TreeModelColumn("node", object,
                                           get=lambda node: node))


        self._node_column = self.get_column_by_name("node")




    def append_column(self, column):
        column.pos = len(self._columns)
        self._columns.append(column)
        self._columns_lookup[column.name] = column


    def get_column(self, pos):
        return self._columns[pos]

    def get_columns(self):
        return self._columns

    def get_column_by_name(self, colname):
        return self._columns_lookup[colname]

    def get_node_column(self):
        return self._node_column.pos


    def get_time_text(self, node, attr_key):
        timestamp = node.get_attr(attr_key, None)
        if timestamp is None:
            return ""
        else:
            return get_str_timestamp(timestamp, formats=self._date_formats)


    if gtk.gtk_version < (2, 10):
        # NOTE: not available in pygtk 2.8?
        
        def create_tree_iter(self, node):
            return self.get_iter(self.on_get_path(node))

        def get_user_data(self, it):
            return self.on_get_iter(self.get_path(it))        

    def set_notebook(self, notebook):
        """
        Set the notebook for this model
        A notebook must be set before any nodes can be added to the model
        """
        
        # TODO: eventually initialize columns based on notebook
        
        # unhook listeners for old notebook. if it exists
        if self._notebook is not None:
            self._notebook.node_changed.remove(self._on_node_changed)
            
        self._notebook = notebook

        # attach new listeners for new notebook, if it exists
        if self._notebook:
            self._notebook.node_changed.add(self._on_node_changed)
        

    def set_master_node(self, node):
        self._master_node = node

    def get_master_node(self):
        return self._master_node

    def set_date_formats(self, formats):
        self._date_formats = formats

    def set_nested(self, nested):
        self._nested = nested
        self.set_root_nodes(self._roots)

    def get_nested(self):
        return self._nested


    def clear(self):
        """Clear all rows from model"""
        
        for i in xrange(len(self._roots)-1, -1, -1):
            self.row_deleted((i,))

        self._roots = []
        self._root_set = {}

    
    def set_root_nodes(self, roots=[]):
        
        # clear the model
        self.clear()

        for node in roots:
            self.append(node)

        # we must have a notebook, so that we can react to NoteBook changes
        if len(roots) > 0:
            assert self._notebook is not None


    def get_root_nodes(self):
        return self._roots
    

    def append(self, node):
        index = len(self._roots)
        self._root_set[node] = index
        self._roots.append(node)
        rowref = self.create_tree_iter(node)
        self.row_inserted((index,), rowref)
        self.row_has_child_toggled((index,), rowref)
        self.row_has_child_toggled((index,), rowref)


    def _on_node_changed(self, nodes, recurse):

        self.emit("node-changed-start", nodes)
        
        for node in nodes:
            if node == self._master_node:
                # reset roots
                self.set_root_nodes(self._master_node.get_children())
            else:
                try:
                    path = self.on_get_path(node)
                except:
                    # node is not part of model, ignore it
                    continue
                
                rowref = self.create_tree_iter(node)

                self.row_deleted(path)
                self.row_inserted(path, rowref)
                self.row_has_child_toggled(path, rowref)
                self.row_has_child_toggled(path, rowref)
                
        self.emit("node-changed-end", nodes)

    
    def on_get_flags(self):
        return gtk.TREE_MODEL_ITERS_PERSIST
    
    def on_get_n_columns(self):
        return len(self._columns)

    def on_get_column_type(self, index):
        return self._columns[index].type
    
    def on_get_iter(self, path):
        if path[0] >= len(self._roots):
            return None
        
        node = self._roots[path[0]]
                
        for i in path[1:]:
            if i >= len(node.get_children()):
                raise ValueError()
            node = node.get_children()[i]

        return node


    def on_get_path(self, rowref):
        if rowref is None:
            return ()
        
        path = []
        node = rowref
        while node not in self._root_set:
            path.append(node.get_order())
            node = node.get_parent()
            if node is None:
                raise Exception("treeiter is not part of model")
        path.append(self._root_set[node])
        
        return tuple(reversed(path))
    
    def on_get_value(self, rowref, column):
        return self.get_column(column).get_value(rowref)

    
    def on_iter_next(self, rowref):
        parent = rowref.get_parent()

        #if parent is None:
        if parent is None or rowref in self._root_set:
            n = self._root_set[rowref]
            if n >= len(self._roots) - 1:
                return None
            else:
                return self._roots[n+1]
        
        children = parent.get_children()
        order = rowref.get_order()
        assert 0 <= order < len(children)
        
        if order == len(children) - 1:
            return None
        else:
            return children[order+1]

    
    def on_iter_children(self, parent):
        if parent is None:
            if len(self._roots) > 0:
                return self._roots[0]
            else:
                return None        
        elif self._nested and len(parent.get_children()) > 0:
            return parent.get_children()[0]
        else:
            return None
    
    def on_iter_has_child(self, rowref):
        return self._nested and len(rowref.get_children()) > 0
    
    def on_iter_n_children(self, rowref):
        if rowref is None:
            return len(self._roots)
        if not self._nested:
            return 0

        return len(rowref.get_children())
    
    def on_iter_nth_child(self, parent, n):
        
        if parent is None:
            if n >= len(self._roots):
                return None
            else:
                return self._roots[n]
        elif not self._nested:
            return None
        else:
            children = parent.get_children()
            if n >= len(children):
                print "out of bounds", parent.get_title(), n
                return None
            else:
                return children[n]
    
    def on_iter_parent(self, child):
        if child in self._root_set:
            return None
        else:
            parent = child.get_parent()
            return parent

gobject.type_register(KeepNoteTreeModel)
gobject.signal_new("node-changed-start", KeepNoteTreeModel,
                   gobject.SIGNAL_RUN_LAST, 
                   gobject.TYPE_NONE, (object,))
gobject.signal_new("node-changed-end", KeepNoteTreeModel,
                   gobject.SIGNAL_RUN_LAST, 
                   gobject.TYPE_NONE, (object,))

