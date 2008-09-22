import wx
import string
import webbrowser


import wx.lib.customtreectrl as CT

import diaryGui

#---------------------------------------------------------------------------


class TreeItem(object):
    def __init__(self, name, id):
        self.name = name
        self.id = id
        

#---------------------------------------------------------------------------
# CustomTreeCtrl Demo Implementation
#---------------------------------------------------------------------------
class ContentTree(CT.CustomTreeCtrl):

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.SUNKEN_BORDER | CT.TR_HAS_BUTTONS | CT.TR_HAS_VARIABLE_ROW_HEIGHT | wx.WANTS_CHARS):

        CT.CustomTreeCtrl.__init__(self, parent, id, pos, size, style)

        self.item = None
        
        self.categories = []
        
        
        self.count = 0

        # NOTE:  For some reason tree items have to have a data object in
        #        order to be sorted.  Since our compare just uses the labels
        #        we don't need any real data, so we'll just use None below for
        #        the item data.

        self.root = self.AddRoot("Content")

        if not(self.GetTreeStyle() & CT.TR_HIDE_ROOT):
            self.SetPyData(self.root, None)
            self.SetItemImage(self.root, 24, CT.TreeItemIcon_Normal)
            self.SetItemImage(self.root, 13, CT.TreeItemIcon_Expanded)

        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        #self.Bind(wx.EVT_IDLE, self.OnIdle)

        self.eventdict = {'EVT_TREE_BEGIN_DRAG': self.OnBeginDrag, 'EVT_TREE_BEGIN_LABEL_EDIT': self.OnBeginEdit,
                          'EVT_TREE_BEGIN_RDRAG': self.OnBeginRDrag, 'EVT_TREE_DELETE_ITEM': self.OnDeleteItem,
                          'EVT_TREE_END_DRAG': self.OnEndDrag, 'EVT_TREE_END_LABEL_EDIT': self.OnEndEdit,
                          'EVT_TREE_ITEM_GETTOOLTIP': self.OnToolTip,
                          'EVT_TREE_ITEM_MENU': self.OnItemMenu, 'EVT_TREE_ITEM_RIGHT_CLICK': self.OnRightDown,
                          "EVT_TREE_ITEM_HYPERLINK": self.OnHyperLink}

        mainframe = wx.GetTopLevelParent(self)
        
        if not hasattr(mainframe, "leftpanel"):
            self.Bind(CT.EVT_TREE_ITEM_EXPANDED, self.OnItemExpanded)
            self.Bind(CT.EVT_TREE_ITEM_COLLAPSED, self.OnItemCollapsed)
            self.Bind(CT.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
            self.Bind(CT.EVT_TREE_SEL_CHANGING, self.OnSelChanging)
            self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
            self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        else:
            for combos in mainframe.treeevents:
                self.BindEvents(combos)

        if hasattr(mainframe, "leftpanel"):
            self.ChangeStyle(mainframe.treestyles)

        if not(self.GetTreeStyle() & CT.TR_HIDE_ROOT):
            self.SelectItem(self.root)
            self.Expand(self.root)
    
    #def _getAvailabe
    #def _setAvailableCategories(self, list):
        #self.definedCategories = list
    #availableCategories = property(_setAvailableCategories)
            
    def addCategory(self, name):
        self.addItem(self.root, name)
        
    def addItem(self, parent, text):
        child = self.AppendItem(parent, text)
        self.SetPyData(child, None)
        return child

    def clear(self):
        self.DeleteChildren(self.root)
        self.current = None
        self.item = None
        
    def getElementContent(self, element):
        if not element.HasChildren():
            return None
        else:
            content = {}
            for child in element.GetChildren():
                content[child.GetText()] = self.getElementContent(child)
            
            return content      
        
    def getDayContent(self):
        if self.root.HasChildren():
            return self.getElementContent(self.root)
        else:
            return {}
        
    def addElement(self, parent, elementContent):
        for key, value in elementContent.iteritems():
            newChild = self.addItem(parent, key)
            if not value == None:
                #print 'set', key
                self.addElement(newChild, value)
            
        
    def addDayContent(self, day):
        for key, value in day.content.iteritems():
            if not key == 'text':
                self.addElement(self.root, {key: value})
                

    def BindEvents(self, choice, recreate=False):

        value = choice.GetValue()
        text = choice.GetLabel()
        
        evt = "CT." + text
        binder = self.eventdict[text]

        if value == 1:
            if evt == "CT.EVT_TREE_BEGIN_RDRAG":
                self.Bind(wx.EVT_RIGHT_DOWN, None)
                self.Bind(wx.EVT_RIGHT_UP, None)
            self.Bind(eval(evt), binder)
        else:
            self.Bind(eval(evt), None)
            if evt == "CT.EVT_TREE_BEGIN_RDRAG":
                self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
                self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
            

    def OnCompareItems(self, item1, item2):
        
        t1 = self.GetItemText(item1)
        t2 = self.GetItemText(item2)
        
        #self.log.write('compare: ' + t1 + ' <> ' + t2 + "\n")

        if t1 < t2:
            return -1
        if t1 == t2:
            return 0

        return 1

    def OnRightDown(self, event):
        
        pt = event.GetPosition()
        item, flags = self.HitTest(pt)

        if item:
            self.item = item
            #self.log.write("OnRightClick: %s, %s, %s" % (self.GetItemText(item), type(item), item.__class__) + "\n")
            self.SelectItem(item)
        else:
            self.item = None

    def showCreateItemContextMenu(self):
        
        menu = wx.Menu()

        menuItemCreate = menu.Append(wx.ID_ANY, "Add New Category")

        self.Bind(wx.EVT_MENU, self.OnItemCreate, menuItemCreate)
        
        self.PopupMenu(menu)
        menu.Destroy()
        
    def itemIsCategory(self, item):
        itemText = self.GetItemText(item)
        #return self.categories.count(itemText) > 0
        return self.GetItemParent(item) == self.root
        

    def OnRightUp(self, event):

        item = self.item
        
        if not item:
            self.showCreateItemContextMenu()
            event.Skip()
            return

        if not self.IsItemEnabled(item):
            event.Skip()
            return

        # Generic Item's Info
        children = self.GetChildrenCount(item)
        itemtype = self.GetItemType(item)
        text = self.GetItemText(item)
        pydata = self.GetPyData(item)
        
        self.current = item
        self.itemdict = {"children": children, "text": text, "pydata": pydata}
        
        menu = wx.Menu()

        #if ishtml:
        #    strs = "Set Item As Non-Hyperlink"
        #else:
        #    strs = "Set Item As Hyperlink"
        #item5 = menu.Append(wx.ID_ANY, strs)

        item10 = menu.Append(wx.ID_ANY, "Delete Item")
        if item == self.GetRootItem():
            item10.Enable(False)
        #item11 = menu.Append(wx.ID_ANY, "Prepend An Item")
        
        if self.itemIsCategory(item):
            item12 = menu.Append(wx.ID_ANY, "Add Entry")
            self.Bind(wx.EVT_MENU, self.OnItemAppend, item12)

        #self.Bind(wx.EVT_MENU, self.OnItemHyperText, item5)
        self.Bind(wx.EVT_MENU, self.OnItemDelete, item10)
        #self.Bind(wx.EVT_MENU, self.OnItemPrepend, item11)
        
        
        self.PopupMenu(menu)
        menu.Destroy()
        

    def OnItemHyperText(self, event):

        self.SetItemHyperText(self.current, not self.itemdict["ishtml"])
                
        

    def OnItemDelete(self, event):

        strs = "Are You Sure You Want To Delete Item " + self.GetItemText(self.current) + "?"
        dlg = wx.MessageDialog(None, strs, 'Deleting Item', wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)

        if dlg.ShowModal() in [wx.ID_NO, wx.ID_CANCEL]:
            dlg.Destroy()
            return

        dlg.Destroy()

        self.DeleteChildren(self.current)
        self.Delete(self.current)
        self.current = None
        


    def OnItemPrepend(self, event):

        dlg = wx.TextEntryDialog(self, "Please Enter The New Item Name", 'Item Naming', 'Python')

        if dlg.ShowModal() == wx.ID_OK:
            newname = dlg.GetValue()
            newitem = self.PrependItem(self.current, newname)
            self.EnsureVisible(newitem)

        dlg.Destroy()
        
        
    def OnItemCreate(self, event):

        #dlg = wx.TextEntryDialog(self, "Please Enter The New Item Name", 'Item Naming', 'Ideas')
        
        dlg = diaryGui.ComboBoxDialog(title='Add Category', list=self.categories)

        if dlg.ShowModal() == wx.ID_OK:
            newname = dlg.GetValue()
            newitem = self.AppendItem(self.root, newname)
            self.EnsureVisible(newitem)

        dlg.Destroy()


    def OnItemAppend(self, event):

        dlg = wx.TextEntryDialog(self, "Please Enter The New Entry's Text", 'New Entry', 'Entry Text')

       
        
        if dlg.ShowModal() == wx.ID_OK:
            newname = dlg.GetValue()
            newitem = self.AppendItem(self.current, newname)
            self.EnsureVisible(newitem)

        dlg.Destroy()
        

    def OnBeginEdit(self, event):
        
        #self.log.write("OnBeginEdit" + "\n")
        # show how to prevent edit...
        item = event.GetItem()
        if item and self.GetItemText(item) == "The Root Item":
            wx.Bell()
            #self.log.write("You can't edit this one..." + "\n")

            # Lets just see what's visible of its children
            cookie = 0
            root = event.GetItem()
            (child, cookie) = self.GetFirstChild(root)

            while child:
                #self.log.write("Child [%s] visible = %d" % (self.GetItemText(child), self.IsVisible(child)) + "\n")
                (child, cookie) = self.GetNextChild(root, cookie)

            event.Veto()


    def OnEndEdit(self, event):
        
        #self.log.write("OnEndEdit: %s %s" %(event.IsEditCancelled(), event.GetLabel()))
        # show how to reject edit, we'll not allow any digits
        for x in event.GetLabel():
            if x in string.digits:
                #self.log.write(", You can't enter digits..." + "\n")
                event.Veto()
                return
            
        #self.log.write("\n")


    def OnLeftDClick(self, event):
        
        pt = event.GetPosition()
        item, flags = self.HitTest(pt)
        if item and (flags & CT.TREE_HITTEST_ONITEMLABEL):
            if self.GetTreeStyle() & CT.TR_EDIT_LABELS:
                #self.log.write("OnLeftDClick: %s (manually starting label edit)"% self.GetItemText(item) + "\n")
                self.EditLabel(item)
            #else:
                #self.log.write("OnLeftDClick: Cannot Start Manual Editing, Missing Style TR_EDIT_LABELS\n")

        event.Skip()                
        

    def OnItemExpanded(self, event):
        
        item = event.GetItem()
        #if item:
            #self.log.write("OnItemExpanded: %s" % self.GetItemText(item) + "\n")


    def OnItemExpanding(self, event):
        
        item = event.GetItem()
        #if item:
            #self.log.write("OnItemExpanding: %s" % self.GetItemText(item) + "\n")
            
        event.Skip()

        
    def OnItemCollapsed(self, event):

        item = event.GetItem()
        #if item:
            #self.log.write("OnItemCollapsed: %s" % self.GetItemText(item) + "\n")
            

    def OnItemCollapsing(self, event):

        item = event.GetItem()
        #if item:
            #self.log.write("OnItemCollapsing: %s" % self.GetItemText(item) + "\n")
    
        event.Skip()

        
    def OnSelChanged(self, event):

        self.item = event.GetItem()
        #if self.item:
            #self.log.write("OnSelChanged: %s" % self.GetItemText(self.item))
            #if wx.Platform == '__WXMSW__':
                #self.log.write(", BoundingRect: %s" % self.GetBoundingRect(self.item, True) + "\n")
            #else:
                #self.log.write("\n")
                
        event.Skip()


    def OnSelChanging(self, event):

        item = event.GetItem()
        olditem = event.GetOldItem()
        
        if item:
            if not olditem:
                olditemtext = "None"
            else:
                olditemtext = self.GetItemText(olditem)
            #self.log.write("OnSelChanging: From %s" % olditemtext + " To %s" % self.GetItemText(item) + "\n")
                
        event.Skip()


    def OnBeginDrag(self, event):

        self.item = event.GetItem()
        if self.item:
            #self.log.write("Beginning Drag..." + "\n")

            event.Allow()


    def OnBeginRDrag(self, event):

        self.item = event.GetItem()
        if self.item:
            #self.log.write("Beginning Right Drag..." + "\n")

            event.Allow()
        

    def OnEndDrag(self, event):

        self.item = event.GetItem()
        #if self.item:
            #self.log.write("Ending Drag!" + "\n")

        event.Skip()            


    def OnDeleteItem(self, event):

        item = event.GetItem()

        if not item:
            return

        #self.log.write("Deleting Item: %s" % self.GetItemText(item) + "\n")
        event.Skip()
        

    def OnToolTip(self, event):

        item = event.GetItem()
        if item:
            event.SetToolTip(wx.ToolTip(self.GetItemText(item)))


    def OnItemMenu(self, event):

        item = event.GetItem()
        #if item:
            #self.log.write("OnItemMenu: %s" % self.GetItemText(item) + "\n")
    
        event.Skip()
        
        
    def OnActivate(self, event):
        
        #if self.item:
            #self.log.write("OnActivate: %s" % self.GetItemText(self.item) + "\n")

        event.Skip()

        
    def OnHyperLink(self, event):
        print 'Go to link'
        item = event.GetItem()
        webbrowser.open(item.GetText())