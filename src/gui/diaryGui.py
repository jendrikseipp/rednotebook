import os
import wx
import sys
import datetime
from wx.lib.customtreectrl import CustomTreeCtrl
import wx.lib.mixins.listctrl as listmix
#import redNotebook

from util import filesystem

class DiaryCalendar(wx.calendar.CalendarCtrl):
    def __init__(self, parent, id=-1, date=wx.DefaultDateTime, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.calendar.CAL_SHOW_HOLIDAYS|wx.WANTS_CHARS):  
        wx.calendar.CalendarCtrl.__init__(self, parent, id, date, pos, size, style)
        
    def setDayEdited(self, dayNumber, edited):
        if edited:
            self.SetAttr(dayNumber, wx.calendar.CalendarDateAttr('RED', 'WHITE'))
        else:
            self.SetAttr(dayNumber, wx.calendar.CalendarDateAttr('BLACK', 'WHITE'))
            
    def setMonth(self, month):
        for dayNumber in range(1, 31 + 1):
            self.setDayEdited(dayNumber, False)
        for dayNumber, day in month.days.iteritems():
            self.setDayEdited(dayNumber, not day.empty)
            
class ComboBoxDialog(wx.Dialog):
    def __init__(self, parent=None, id=wx.ID_ANY, title='', list=None):
        wx.Dialog.__init__(self, parent, id, title)
        
        if list == None:
            list = []
        
        self.comboBox = wx.ComboBox(self, -1, choices=list, style=wx.CB_DROPDOWN|wx.CB_SORT)

        self.__do_layout()


    def __do_layout(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.comboBox, 0, wx.ALIGN_CENTER|wx.TOP, 25)
        vbox.Add((20,20))
        sizer =  self.CreateButtonSizer(wx.CANCEL|wx.OK)
        vbox.Add(sizer, 0, wx.ALIGN_CENTER)
        self.SetSizer(vbox)
        vbox.Fit(self)
        self.Layout()
        
    def GetValue(self):
        return self.comboBox.GetValue()
        
class SearchPanel(wx.Panel):
    def __init__(self, parent, mainFrame):
        self.mainFrame = mainFrame
        self.redNotebook = mainFrame.redNotebook
        #self.resultPanel = self.redNotebook.frame.resultPanel
        
        wx.Panel.__init__(self, parent, -1, style=0)

        self.search = wx.SearchCtrl(self, size=(200,-1), style=wx.TE_PROCESS_ENTER)
        self.search.ShowSearchButton(True)
        self.search.ShowCancelButton(True)
        self.search.SetMenu(self.MakeMenu())
        
        #self.resultBox = 

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((15,15))
        sizer.Add(self.search, 0, wx.ALL, 15)

##         self.tc = wx.TextCtrl(self)  # just for testing that heights match...
##         sizer.Add(self.tc, 0, wx.TOP, 15)

        self.SetSizer(sizer)


        # Set event bindings
        #self.Bind(wx.EVT_CHECKBOX, self.OnToggleSearchButton, searchBtnOpt)
        #self.Bind(wx.EVT_CHECKBOX, self.OnToggleCancelButton, cancelBtnOpt)
        #self.Bind(wx.EVT_CHECKBOX, self.OnToggleSearchMenu,   menuBtnOpt)

        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearchButton, self.search)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel, self.search)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch, self.search)
        ##self.Bind(wx.EVT_TEXT, self.OnDoSearch, self.search)        


    def OnSearchButton(self, evt):
        print 'Searching'
        #self.redNotebook.search(self.search.GetValue())
            
    def OnCancel(self, evt):
        self.log.write("OnCancel")

    def OnDoSearch(self, evt):
        print 'DoSearching'
        results = self.redNotebook.search(self.search.GetValue())
        self.mainFrame.resultPanel.clearList()
        print results
        for result in results:
            self.mainFrame.resultPanel.addResult(result[0], result[1])        

    def MakeMenu(self):
        menu = wx.Menu()
        item = menu.Append(-1, "Recent Searches")
        item.Enable(False)
        for txt in [ "You can maintain",
                     "a list of old",
                     "search strings here",
                     "and bind EVT_MENU to",
                     "catch their selections" ]:
            menu.Append(-1, txt)
        return menu
    


        



#---------------------------------------------------------------------------

class ResultListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


class ResultPanel(wx.Panel, listmix.ColumnSorterMixin):
    def __init__(self, parent, mainFrame):
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)

        self.mainFrame = mainFrame
        tID = wx.NewId()
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        if wx.Platform == "__WXMAC__" and \
               hasattr(wx.GetApp().GetTopWindow(), "LoadDemo"):
            self.useNative = wx.CheckBox(self, -1, "Use native listctrl")
            self.useNative.SetValue( 
                not wx.SystemOptions.GetOptionInt("mac.listctrl.always_use_generic") )
            self.Bind(wx.EVT_CHECKBOX, self.OnUseNative, self.useNative)
            sizer.Add(self.useNative, 0, wx.ALL | wx.ALIGN_RIGHT, 4)
            
        self.il = wx.ImageList(16, 16)

        #self.idx1 = self.il.Add(images.Smiles.GetBitmap())
        #self.sm_up = self.il.Add(images.SmallUpArrow.GetBitmap())
        #self.sm_dn = self.il.Add(images.SmallDnArrow.GetBitmap())
        self.idx1 = self.il.Add(getBitmap("redNotebook-16.png"))
        self.sm_up = self.il.Add(getBitmap("arrowUp.png"))
        self.sm_dn = self.il.Add(getBitmap("arrowDown.png"))

        self.list = ResultListCtrl(self, tID,
                                 style=wx.LC_REPORT 
                                 #| wx.BORDER_SUNKEN
                                 | wx.BORDER_NONE
                                 | wx.LC_EDIT_LABELS
                                 | wx.LC_SORT_ASCENDING
                                 #| wx.LC_NO_HEADER
                                 #| wx.LC_VRULES
                                 #| wx.LC_HRULES
                                 #| wx.LC_SINGLE_SEL
                                 )
        
        self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        sizer.Add(self.list, 1, wx.EXPAND)

        self.PopulateList()

        # Now that the list exists we can init the other base class,
        # see wx/lib/mixins/listctrl.py
        self.itemDataMap = {}
        listmix.ColumnSorterMixin.__init__(self, 2)
        #self.SortListItems(0, True)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, self.list)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated, self.list)
        self.Bind(wx.EVT_LIST_DELETE_ITEM, self.OnItemDelete, self.list)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list)
        self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnColRightClick, self.list)
        #self.Bind(wx.EVT_LIST_COL_BEGIN_DRAG, self.OnColBeginDrag, self.list)
        #self.Bind(wx.EVT_LIST_COL_DRAGGING, self.OnColDragging, self.list)
        #self.Bind(wx.EVT_LIST_COL_END_DRAG, self.OnColEndDrag, self.list)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginEdit, self.list)

        #self.list.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.list.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)

        # for wxMSW
        self.list.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)

        # for wxGTK
        self.list.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)
        
    def addResult(self, day, text):
        dayNumberString = str(day.dayNumber)
        if len(dayNumberString) < 2:
            dayNumberString = '0' + dayNumberString
            
        dateString = str(day.month.yearNumber) + '-' + str(day.month.monthNumber) + '-' + dayNumberString
        dateNumber = long(str(day.month.yearNumber) + str(day.month.monthNumber) + dayNumberString)
        
        #For itemDataMap
        self.itemDataMap[dateNumber] = (dateString, text)
        
        #index = self.list.InsertImageStringItem(sys.maxint, dayString, self.idx1)
        index = self.list.InsertStringItem(sys.maxint, dateString)
        self.list.SetStringItem(index, 1, text)
        self.list.SetItemData(index, dateNumber)
        
    def clearList(self):
        self.list.DeleteAllItems()
        self.itemDataMap = {}


    def OnUseNative(self, event):
        wx.SystemOptions.SetOptionInt("mac.listctrl.always_use_generic", not event.IsChecked())
        wx.GetApp().GetTopWindow().LoadDemo("ListCtrl")

    def PopulateList(self):
        if 0:
            # for normal, simple columns, you can add them like this:
            self.list.InsertColumn(0, "Day")
            self.list.InsertColumn(1, "Text") #, wx.LIST_FORMAT_RIGHT)
        else:
            # but since we want images on the column header we have to do it the hard way:
            info = wx.ListItem()
            info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
            info.m_image = -1
            info.m_format = 0
            info.m_text = "Day"
            self.list.InsertColumnInfo(0, info)

            info.m_format = 0 #wx.LIST_FORMAT_RIGHT
            info.m_text = "Text"
            self.list.InsertColumnInfo(1, info)

        self.list.SetColumnWidth(0, 100) #wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)

        # show how to select an item
        #self.list.SetItemState(5, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

        # show how to change the colour of a couple items
        item = self.list.GetItem(1)
        item.SetTextColour(wx.BLUE)
        self.list.SetItem(item)
        item = self.list.GetItem(4)
        item.SetTextColour(wx.RED)
        self.list.SetItem(item)

        self.currentItem = 0


    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.list

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)


    def OnRightDown(self, event):
        x = event.GetX()
        y = event.GetY()
        self.log.WriteText("x, y = %s\n" % str((x, y)))
        item, flags = self.list.HitTest((x, y))

        if item != wx.NOT_FOUND and flags & wx.LIST_HITTEST_ONITEM:
            self.list.Select(item)

        event.Skip()


    def getColumnText(self, index, col):
        item = self.list.GetItem(index, col)
        return item.GetText()


    def OnItemSelected(self, event):
        ##print event.GetItem().GetTextColour()
        self.currentItem = event.m_itemIndex
        #self.log.WriteText("OnItemSelected: %s, %s, %s, %s\n" %
         #                  (self.currentItem,
          #                  self.list.GetItemText(self.currentItem),
           #                 self.getColumnText(self.currentItem, 1),
           #                 self.getColumnText(self.currentItem, 2)))

        #if self.currentItem == 10:
            #self.log.WriteText("OnItemSelected: Veto'd selection\n")
            #event.Veto()  # doesn't work
            # this does
            #self.list.SetItemState(10, 0, wx.LIST_STATE_SELECTED)
        itemDataString = str(self.list.GetItemData(self.currentItem))#.GetData)
        #print itemDataString
        year = itemDataString[:4]
        #print year
        month = itemDataString[4:6]
        #print month
        day = itemDataString[6:]
        #print day
        
        self.mainFrame.redNotebook.changeDate(datetime.date(int(year), int(month), int(day)))
        
        event.Skip()


    def OnItemDeselected(self, evt):
        item = evt.GetItem()
        #self.log.WriteText("OnItemDeselected: %d" % evt.m_itemIndex)

        # Show how to reselect something we don't want deselected
        #if evt.m_itemIndex == 11:
            #wx.CallAfter(self.list.SetItemState, 11, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)


    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex
        #self.log.WriteText("OnItemActivated: %s\nTopItem: %s" %
                           #(self.list.GetItemText(self.currentItem), self.list.GetTopItem()))

    def OnBeginEdit(self, event):
        #self.log.WriteText("OnBeginEdit")
        event.Allow()

    def OnItemDelete(self, event):
        pass
        #self.log.WriteText("OnItemDelete\n")

    def OnColClick(self, event):
        #self.log.WriteText("OnColClick: %d\n" % event.GetColumn())
        event.Skip()

    def OnColRightClick(self, event):
        item = self.list.GetColumn(event.GetColumn())
        #self.log.WriteText("OnColRightClick: %d %s\n" %
        #                   (event.GetColumn(), (item.GetText(), item.GetAlign(),
        #                                        item.GetWidth(), item.GetImage())))

    #def OnColBeginDrag(self, event):
        #self.log.WriteText("OnColBeginDrag\n")
        ## Show how to not allow a column to be resized
        #if event.GetColumn() == 0:
        #    event.Veto()


    #def OnColDragging(self, event):
        #self.log.WriteText("OnColDragging\n")

    #def OnColEndDrag(self, event):
        #self.log.WriteText("OnColEndDrag\n")

    #def OnDoubleClick(self, event):
    #    self.log.WriteText("OnDoubleClick item %s\n" % self.list.GetItemText(self.currentItem))
    #    event.Skip()

    def OnRightClick(self, event):
        #self.log.WriteText("OnRightClick %s\n" % self.list.GetItemText(self.currentItem))

        # only do this part the first time so the events are only bound once
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID4 = wx.NewId()
            self.popupID5 = wx.NewId()
            self.popupID6 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.OnPopupOne, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnPopupTwo, id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.OnPopupThree, id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.OnPopupFour, id=self.popupID4)
            self.Bind(wx.EVT_MENU, self.OnPopupFive, id=self.popupID5)
            self.Bind(wx.EVT_MENU, self.OnPopupSix, id=self.popupID6)

        # make a menu
        menu = wx.Menu()
        # add some items
        menu.Append(self.popupID1, "FindItem tests")
        menu.Append(self.popupID2, "Iterate Selected")
        menu.Append(self.popupID3, "ClearAll and repopulate")
        menu.Append(self.popupID4, "DeleteAllItems")
        menu.Append(self.popupID5, "GetItem")
        menu.Append(self.popupID6, "Edit")

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()


    def OnPopupOne(self, event):
        self.log.WriteText("Popup one\n")
        print "FindItem:", self.list.FindItem(-1, "Roxette")
        print "FindItemData:", self.list.FindItemData(-1, 11)

    def OnPopupTwo(self, event):
        self.log.WriteText("Selected items:\n")
        index = self.list.GetFirstSelected()

        while index != -1:
            self.log.WriteText("      %s: %s\n" % (self.list.GetItemText(index), self.getColumnText(index, 1)))
            index = self.list.GetNextSelected(index)

    def OnPopupThree(self, event):
        self.log.WriteText("Popup three\n")
        self.list.ClearAll()
        wx.CallAfter(self.PopulateList)

    def OnPopupFour(self, event):
        self.list.DeleteAllItems()

    def OnPopupFive(self, event):
        item = self.list.GetItem(self.currentItem)
        print item.m_text, item.m_itemId, self.list.GetItemData(self.currentItem)

    def OnPopupSix(self, event):
        self.list.EditLabel(self.currentItem)
        
        
            
def getBitmap(file):
    return wx.Bitmap(os.path.join(filesystem.imageDir, file), wx.BITMAP_TYPE_ANY)
        
    
        
        