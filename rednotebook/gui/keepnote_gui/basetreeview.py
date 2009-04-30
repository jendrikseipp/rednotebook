


# pygtk imports
import pygtk
pygtk.require('2.0')
import gtk, gobject, pango
from gtk import gdk

# keepnote imports
from keepnote.notebook import NoteBookError, NoteBookTrash
from keepnote.gui.treemodel import \
     get_path_from_node
     


# treeview drag and drop config
DROP_TREE_MOVE = ("drop_node", gtk.TARGET_SAME_APP, 0)
#DROP_NO = ("drop_no", gtk.TARGET_SAME_WIDGET, 0)


# treeview reorder rules
REORDER_NONE = 0
REORDER_FOLDER = 1
REORDER_ALL = 2


def compute_new_path(model, target, drop_position):
    """Compute the new path of a tagret rowiter in a treemodel"""
    
    path = model.get_path(target)
    
    if drop_position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE or \
       drop_position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER:
        return path + (0,)
    elif drop_position == gtk.TREE_VIEW_DROP_BEFORE:
        return path
    elif drop_position == gtk.TREE_VIEW_DROP_AFTER:
        return path[:-1] + (path[-1] + 1,)
    else:
        raise Exception("unknown drop position %s" %
            str(drop_position))


class KeepNoteBaseTreeView (gtk.TreeView):
    """Base class for treeviews of a NoteBook notes"""

    def __init__(self):
        gtk.TreeView.__init__(self)
        
        self.model = None
        self.rich_model = None
        self._notebook = None
        self._master_node = None
        self.editing = False
        self.__sel_nodes = []
        self.__sel_nodes2 = []
        self.__suppress_sel = False
        self._node_col = None
        self._get_icon = None



        # selection
        self.get_selection().connect("changed", self.__on_select_changed)
        self.get_selection().connect("changed", self.on_select_changed)

        # row expand/collapse
        self.connect("row-expanded", self._on_row_expanded)
        self.connect("row-collapsed", self._on_row_collapsed)

        
        # drag and drop state
        self._is_dragging = False   # whether drag is in progress
        self._drag_count = 0
        self._dest_row = None       # current drag destition
        self._reorder = REORDER_ALL # enum determining the kind of reordering
                                    # that is possible via drag and drop
        # region, defined by number of vertical pixels from top and bottom of
        # the treeview widget, where drag scrolling will occur
        self._drag_scroll_region = 30


        # drop and drop events
        self.connect("drag-begin", self._on_drag_begin)
        self.connect("drag-end", self._on_drag_end)
        self.connect("drag-motion", self._on_drag_motion)
        self.connect("drag-drop", self._on_drag_drop)
        self.connect("drag-data-delete", self._on_drag_data_delete)
        self.connect("drag-data-get", self._on_drag_data_get)
        self.connect("drag-data-received", self._on_drag_data_received)

        # configure drag and drop events
        self.enable_model_drag_source(
           gtk.gdk.BUTTON1_MASK, [DROP_TREE_MOVE], gtk.gdk.ACTION_MOVE)
        self.drag_source_set(
            gtk.gdk.BUTTON1_MASK,
            [DROP_TREE_MOVE],
            gtk.gdk.ACTION_MOVE)
        self.enable_model_drag_dest(
            [DROP_TREE_MOVE], gtk.gdk.ACTION_MOVE)
        self.drag_dest_set(gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_MOTION,
            [DROP_TREE_MOVE],
            gtk.gdk.ACTION_MOVE)

    
    def set_master_node(self, node):
        self._master_node = node
        
        if self.rich_model:
            self.rich_model.set_master_node(node)


    def get_master_node(self):
        return self._master_node


    def set_notebook(self, notebook):

        self._notebook = notebook
    
        # NOTE: not used yet
        if self.model:
            if hasattr(self.model, "get_model"):
                self.model.get_model().set_notebook(notebook)
            else:
                self.model.set_notebook(notebook)
            

    def set_model(self, model):
        """Set the model for the view"""
        
        # TODO: could group signal IDs into lists, for each detach
        # if model already attached, disconnect all of its signals
        if self.model is not None:
            self.rich_model.disconnect(self.changed_start_id)
            self.rich_model.disconnect(self.changed_end_id)
            self.rich_model.disconnect(self.insert_id)
            self.rich_model.disconnect(self.delete_id)
            self.rich_model.disconnect(self.has_child_id)

            self._node_col = None
            self._get_icon = None

        # set new model
        self.model = model
        self.rich_model = None
        gtk.TreeView.set_model(self, self.model)


        # set new model
        if self.model is not None:
            # look to see if model has an inner model (happens when we have
            # sorting models)
            if hasattr(self.model, "get_model"):
                self.rich_model = self.model.get_model()
            else:
                self.rich_model = model

            # init signals for model
            self.rich_model.set_notebook(self._notebook)
            self.changed_start_id = self.rich_model.connect("node-changed-start",
                                                   self._on_node_changed_start)
            self.changed_end_id = self.rich_model.connect("node-changed-end",
                                                 self._on_node_changed_end)
            self._node_col = self.rich_model.get_node_column()
            self._get_icon = lambda row: \
                             self.model.get_value(row, self.rich_model.get_column_by_name("icon").pos)

                
            self.insert_id = self.model.connect("row-inserted",
                                                self.on_row_inserted)
            self.delete_id = self.model.connect("row-deleted",
                                                self.on_row_deleted)
            self.has_child_id = self.model.connect(
                "row-has-child-toggled",
                self.on_row_has_child_toggled)


    def popup_menu(self, x, y, button, time):
        """Display popup menu"""
        
        path = self.get_path_at_pos(int(x), int(y))
        if path is None:
            return False
        
        path = path[0]
        self.get_selection().select_path(path)
        self.menu.popup(None, None, None, button, time)
        self.menu.show()
        return True



    #=========================================
    # model change callbacks

    def _on_node_changed_start(self, model, nodes):
        # remember which nodes are selected
        self.__sel_nodes2 = list(self.__sel_nodes)

        # suppress selection changes while nodes are changing
        self.__suppress_sel = True


    def _on_node_changed_end(self, model, nodes):

        # maintain proper expansion
        for node in nodes:

            if node == self._master_node:
                for child in node.get_children():
                    if self.is_node_expanded(child):
                        path = get_path_from_node(self.model, child, self.rich_model.get_node_column())
                        self.expand_row(path, False)
            else:
                path = get_path_from_node(self.model, node,
                                          self.rich_model.get_node_column())
                if path is not None:
                    parent = node.get_parent()

                    # NOTE: parent may lose expand state if it has one child
                    # therefore, we should expand parent if it exists and is
                    # visible (i.e. len(path)>1) in treeview
                    if parent and self.is_node_expanded(parent) and \
                       len(path) > 1:
                        self.expand_row(path[:-1], False)

                    if self.is_node_expanded(node):
                        self.expand_row(path, False)
                
        
        # if nodes still exist, and expanded, try to reselect them
        if len(self.__sel_nodes2) > 0:
            # TODO: only reselects one node
            path2 = get_path_from_node(self.model, self.__sel_nodes2[0],
                                       self.rich_model.get_node_column())
            if path2 is not None and \
               (len(path2) <= 1 or self.row_expanded(path2[:-1])):
                # reselect and scroll to node    
                self.set_cursor(path2)
                gobject.idle_add(lambda: self.scroll_to_cell(path2))

        # resume emitting selection changes
        self.__suppress_sel = False


    def __on_select_changed(self, treeselect):
        """Keep track of which nodes are selected"""
        model, paths = treeselect.get_selected_rows()

        self.__sel_nodes = [self.model.get_value(self.model.get_iter(path),
                                                 self._node_col)
                            for path in paths]

        if self.__suppress_sel:
            self.get_selection().stop_emission("changed")
    

    def is_node_expanded(self, node):
        # query expansion from nodes
        return node.get_attr("expanded", False)

    def set_node_expanded(self, node, expand):
        # save expansion in node
        node.set_attr("expanded", expand)
        

    def _on_row_expanded(self, treeview, it, path):
        """Callback for row expand

           Performs smart expansion (remembers children expansion)"""

        # save expansion in node
        self.set_node_expanded(self.model.get_value(it, self._node_col), True)

        # recursively expand nodes that should be expanded
        def walk(it):
            child = self.model.iter_children(it)
            while child:
                node = self.model.get_value(child, self._node_col)
                if self.is_node_expanded(node):
                    path = self.model.get_path(child)
                    self.expand_row(path, False)
                    walk(child)
                child = self.model.iter_next(child)
        walk(it)
    
    def _on_row_collapsed(self, treeview, it, path):
        # save expansion in node
        self.set_node_expanded(self.model.get_value(it, self._node_col), False)


    def on_row_inserted(self, model, path, it):
        pass

    def on_row_deleted(self, model, path):
        pass

    def on_row_has_child_toggled(self, model, path, it):
        pass

    #===========================================
    # actions

    def expand_node(self, node):
        """Expand a node in TreeView"""
        path = get_path_from_node(self.model, node,
                                  self.rich_model.get_node_column())
        if path is not None:
            self.expand_to_path(path)


    #===========================================
    # selection

    def select_nodes(self, nodes):

        # NOTE: for now only select one node
        if len(nodes) > 0:
            node = nodes[0]
            path = get_path_from_node(self.model, node,
                                      self.rich_model.get_node_column())
            if path is not None:
                if len(path) > 1:
                    self.expand_to_path(path[:-1])
                self.set_cursor(path)
                gobject.idle_add(lambda: self.scroll_to_cell(path))
        else:
            # unselect all nodes
            self.get_selection().unselect_all()


    def on_select_changed(self, treeselect): 
        model, paths = treeselect.get_selected_rows()
        
        nodes = [self.model.get_value(self.model.get_iter(path), self._node_col)
                 for path in paths]
        self.emit("select-nodes", nodes)
        return True
    

    def get_selected_nodes(self):
        """Returns a list of currently selected nodes"""
        model, it = self.get_selection().get_selected()        
        if it is None:
            return []
        return [self.model.get_value(it, self._node_col)]



    #=====================================================
    # delete node
    
    def on_delete_node(self):
        # TODO: add folder name to message box
        # factor out confirm dialog?
        
        # get node to delete
        nodes = self.get_selected_nodes()
        if len(nodes) == 0:
            return
        node = nodes[0]
        
        if isinstance(node, NoteBookTrash):
            self.emit("error", "The Trash folder cannot be deleted.", None)
            return
        elif node.get_parent() == None:
            self.emit("error", "The top-level folder cannot be deleted.", None)
            return
        elif len(node.get_children()) > 0:
            message = "Do you want to delete this note and all of its children?"
        else:
            message = "Do you want to delete this note?"
        
        dialog = gtk.MessageDialog(self.get_toplevel(), 
            flags= gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            type=gtk.MESSAGE_QUESTION, 
            buttons=gtk.BUTTONS_YES_NO, 
            message_format=message)

        response = dialog.run()
        dialog.destroy()
        
        if response == gtk.RESPONSE_YES:
            self._delete_node(node)
            
    
    def _delete_node(self, node):
        parent = node.get_parent()
        children = parent.get_children()
        i = children.index(node)
        if i < len(children) - 1:
            self.select_nodes([children[i+1]])
        else:
            self.select_nodes([parent])
        
        if parent is not None:
            try:
                node.trash()
            except NoteBookError, e:
                self.emit("error", e.msg, e)
        else:
            # warn
            self.emit("error", "Cannot delete notebook's toplevel directory", None)
        


    #============================================
    # editing titles
    
    def on_editing_started(self, cellrenderer, editable, path):
        """Callback for start of title editing"""
        # remember editing state
        self.editing = True
        gobject.idle_add(lambda: self.scroll_to_cell(path))
    
    def on_editing_canceled(self, cellrenderer):
        """Callback for canceled of title editing"""
        # remember editing state
        self.editing = False

    def on_edit_title(self, cellrenderertext, path, new_text):
        """Callback for completion of title editing"""

        # remember editing state
        self.editing = False

        # get node being edited
        node = self.model.get_value(self.model.get_iter(path), self._node_col)
        if node is None:
            return
        
        # do not allow empty names
        if new_text.strip() == "":
            return

        # set new title and catch errors
        if new_text != node.get_title():
            try:
                node.rename(new_text)            
            except NoteBookError, e:
                self.emit("error", e.msg, e)

        # reselect node 
        # NOTE: I select the root inorder for set_cursor(path) to really take
        # effect (gtk seems to ignore a select call if it "thinks" the path
        # is selected)
        #if self.model.iter_n_children(None) > 0:
        #    self.set_cursor((0,))
        
        path = get_path_from_node(self.model, node,
                                  self.rich_model.get_node_column())
        if path is not None:
            self.set_cursor(path)
            gobject.idle_add(lambda: self.scroll_to_cell(path))

        self.emit("edit-title", node, new_text)
        
    

    
    #=============================================
    # drag and drop

    
    def set_reorder(self, order):
        self._reorder = order

    def get_reorderable(self):
        return self._reorder

    
    def get_drag_node(self):
        model, source = self.get_selection().get_selected()
        #source_path = model.get_path(source)
        return self.model.get_value(source, self._node_col)


    #  drag and drop callbacks

    def _on_drag_timer(self):

        # process scrolling
        self._process_drag_scroll()
        return self._is_dragging



    def _process_drag_scroll(self):

        # get header height
        header_height = [0]

        if self.get_headers_visible():
            self.forall(lambda w, d: header_height.__setitem__(
                0, w.allocation.height), None)

        # get mouse poistion in tree coordinates
        x, y = self.get_pointer()
        x, y = self.widget_to_tree_coords(x, y - header_height[0])

        # get visible rect in tree coordinates
        rect = self.get_visible_rect()

        def dist_to_scroll(dist):
            """Convert a distance outside the widget into a scroll step"""

            # TODO: put these scroll constants somewhere else
            small_scroll_dist = 30
            small_scroll = 30
            fast_scroll_coeff = small_scroll

            if dist < small_scroll_dist:
                # slow scrolling
                self._drag_count = 0
                return small_scroll
            else:
                # fast scrolling
                self._drag_count += 1
                return small_scroll + fast_scroll_coeff * self._drag_count**2

        # test for scroll boundary
        dist = rect.y - y
        if dist > 0:
            self.scroll_to_point(-1, rect.y - dist_to_scroll(dist))

        else:
            dist = y - rect.y - rect.height
            if dist > 0:            
                self.scroll_to_point(-1, rect.y + dist_to_scroll(dist))

        

    def _on_drag_begin(self, treeview, drag_context):
        """Callback for beginning of drag and drop"""
        self.stop_emission("drag-begin")

        # get the selection
        model, source = self.get_selection().get_selected()

        # setup the drag icon
        if self._get_icon:
            pixbuf = self._get_icon(source)
            pixbuf = pixbuf.scale_simple(40, 40, gtk.gdk.INTERP_BILINEAR)
            self.drag_source_set_icon_pixbuf(pixbuf)

        # clear the destination row
        self._dest_row = None

        self._is_dragging = True
        self._drag_count = 0
        gobject.timeout_add(200, self._on_drag_timer)

        
    def _on_drag_motion(self, treeview, drag_context, x, y, eventtime):
        """
        Callback for drag motion.
        Indicate which drops are allowed (cannot drop into descendant).
        Also record the destination for later use.
        """        

        # override gtk's default drag motion code
        self.stop_emission("drag-motion")

        # if reordering is disabled then terminate the drag
        if self._reorder == REORDER_NONE:
            return False
        
        # determine destination row   
        dest_row = treeview.get_dest_row_at_pos(x, y)
        
        if dest_row is not None:
            # get target info
            target_path, drop_position = dest_row
            target = self.model.get_iter(target_path)
            target_node = self.model.get_value(target, self._node_col)
        
            # process node drops
            if "drop_node" in drag_context.targets:
                # get source
                source_widget = drag_context.get_source_widget()
                source_node = source_widget.get_drag_node()
                #source_path = get_path_from_node(self.model, source_node)
            
                # determine if drag is allowed
                if self._drop_allowed(source_node, target_node, drop_position):
                    self.set_drag_dest_row(target_path, drop_position)
                    self._dest_row = target_path, drop_position

            # NOTE: other kinds of drops can be processed
            # for example added external files to notebook           




    def _on_drag_drop(self, widget, drag_context, x, y, timestamp):
        """
        Callback for drop event
        """        

        # override gtk's default drag drop code
        self.stop_emission("drag-drop")

        # if reordering is disabled, reject drop
        if self._reorder == REORDER_NONE:
            drag_context.finish(False, False, timestamp)
            return False

        # cause get data event to occur
        self.drag_get_data(drag_context, "drop_node")

        # accept drop
        return True


    def _on_drag_end(self, widget, drag_context):
        """Callback for end of dragging"""
        self._is_dragging = False


    def _on_drag_data_delete(self, widget, drag_context):
        """
        Callback for deleting data due to a 'move' event
        """

        # override gtk's delete event
        self.stop_emission("drag-data-delete")

        # do nothing else, deleting old copy is handled else where


    def _on_drag_data_get(self, widget, drag_context, selection_data,
                         info, timestamp):
        """
        Callback for when data is requested by drag_get_data
        """

        # override gtk's data get code
        self.stop_emission("drag-data-get")

        # set the source path into the selection
        model, source = self.get_selection().get_selected()
        source_path = model.get_path(source)
        selection_data.tree_set_row_drag_data(model, source_path)
    
    
    def _on_drag_data_received(self, treeview, drag_context, x, y,
                               selection_data, info, eventtime):

        """
        Callback for when data is received from source widget
        """

        # override gtk's data received code
        self.stop_emission("drag-data-received")

        
        # if no destination, give up.  Occurs when drop is not allowed
        if self._dest_row is None:
            drag_context.finish(False, False, eventtime)
            return

        
        if "drop_node" in drag_context.targets:
            # process node drops
            self._on_drag_node_received(treeview, drag_context, x, y,
                                        selection_data, info, eventtime)
        else:
            # unknown drop type, reject
            drag_context.finish(False, False, eventtime)


    def _on_drag_node_received(self, treeview, drag_context, x, y,
                               selection_data, info, eventtime):
        """
        Callback for node received from another widget
        """

        # get target
        target_path, drop_position  = self._dest_row
        target = self.model.get_iter(target_path)
        target_node = self.model.get_value(target, self._node_col)
        new_path = compute_new_path(self.model, target, drop_position)

        # get source
        source_widget = drag_context.get_source_widget()
        source_node = source_widget.get_drag_node()

        # determine if drop is allowed
        if not self._drop_allowed(source_node, target_node, drop_position):
            drag_context.finish(False, False, eventtime)
            return

        # determine new parent
        new_parent_path = new_path[:-1]
        if len(new_parent_path) == 0:
            new_parent = self._master_node
            assert self._master_node is not None
        else:
            new_parent_it = self.model.get_iter(new_parent_path)
            new_parent = self.model.get_value(new_parent_it, self._node_col)

        
        # perform move in notebook model
        try:
            source_node.move(new_parent, new_path[-1])
        except NoteBookError, e:
            drag_context.finish(False, False, eventtime)
            self.emit("error", e.msg, e)
            return

        # make sure to show new children
        if (drop_position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE or
            drop_position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER):
            new_parent_path = get_path_from_node(self.model, new_parent,
                                             self.rich_model.get_node_column())
            if new_parent_path is not None:
                self.expand_row(new_parent_path, False)

        # notify that drag was successful
        drag_context.finish(True, True, eventtime)
    
        
    def _drop_allowed(self, source_node, target_node, drop_position):
        """Determine if drop is allowed"""
        
        # source cannot be an ancestor of target
        ptr = target_node
        while ptr is not None:
            if ptr == source_node:
                return False
            ptr = ptr.get_parent()

        drop_into = (drop_position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE or 
                     drop_position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER)
        
        return (
            # (1) do not let nodes move out of notebook root
            not (target_node.get_parent() is None and not drop_into) and

            # (2) do not let nodes move into nodes that don't allow children
            not (not target_node.allows_children() and drop_into) and

            # (3) if reorder == FOLDER, ensure drop is either INTO a node
            #     or new_parent == old_parent
            not (self._reorder == REORDER_FOLDER and not drop_into and
                 target_node.get_parent() == source_node.get_parent()))
                #       or 
                #not (self._reorder == REORDER_FOLDER and 
                #    (drop_position not in (gtk.TREE_VIEW_DROP_INTO_OR_BEFORE,
                #                           gtk.TREE_VIEW_DROP_INTO_OR_AFTER))))



gobject.type_register(KeepNoteBaseTreeView)
gobject.signal_new("select-nodes", KeepNoteBaseTreeView,
                   gobject.SIGNAL_RUN_LAST, 
                   gobject.TYPE_NONE, (object,))
gobject.signal_new("edit-title", KeepNoteBaseTreeView,
                   gobject.SIGNAL_RUN_LAST, 
                   gobject.TYPE_NONE, (object, str))
gobject.signal_new("error", KeepNoteBaseTreeView, gobject.SIGNAL_RUN_LAST, 
    gobject.TYPE_NONE, (str, object,))
