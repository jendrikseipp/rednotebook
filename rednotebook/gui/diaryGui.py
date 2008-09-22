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

        self.search = wx.SearchCtrl(self, size=(220,-1), style=wx.TE_PROCESS_ENTER)
        self.search.ShowSearchButton(True)
        self.search.ShowCancelButton(True)
        
        self.recentSearches = []
        self.searchHistoryCapacity = 10

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((15,15))
        sizer.Add(self.search, 0, wx.ALL, 10)

##         self.tc = wx.TextCtrl(self)  # just for testing that heights match...
##         sizer.Add(self.tc, 0, wx.TOP, 15)

        self.SetSizer(sizer)


        # Set event bindings
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearchButton, self.search)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel, self.search)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoEnterSearch, self.search)
        #Live Search
        self.Bind(wx.EVT_TEXT, self.OnDoLiveSearch, self.search)     
        
    


    def OnSearchButton(self, evt):
        self.updateMenu()
        #self.redNotebook.search(self.search.GetValue())
            
    def OnCancel(self, evt):
        self.addCurrentSearchTermToHistory()
        self.search.SetValue('')
        
    def OnDoLiveSearch(self, event):
        #print 'Live Search'
        self.mainFrame.resultPanel.clearList()
        searchTerm = self.search.GetValue()
        if len(searchTerm.strip()) > 0:
            results = self.redNotebook.search(self.search.GetValue())
            for result in results:
                self.mainFrame.resultPanel.addResult(result[0], result[1])

    def OnDoEnterSearch(self, event):
        self.addCurrentSearchTermToHistory()
        self.OnDoLiveSearch(event)
            
    def addCurrentSearchTermToHistory(self):
        searchTerm = self.search.GetValue()
        if len(searchTerm.strip()) > 0:
            if self.recentSearches.count(searchTerm) == 0:
                self.recentSearches.insert(0, searchTerm)
                if len(self.recentSearches) > self.searchHistoryCapacity:
                    self.recentSearches.pop()
    
    def updateMenu(self):
        self.search.SetMenu(self.MakeMenu())     

    def MakeMenu(self):
        menu = wx.Menu()
        item = menu.Append(-1, "Recent Searches")
        item.Enable(False)
        #for category in self.redNotebook.nodeNames:
        for category in self.recentSearches:
            menu.Append(-1, category)
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
                                 | wx.LC_SINGLE_SEL
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

        self.list.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        
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

        self.list.SetColumnWidth(0, 90) #wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)


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
        item, flags = self.list.HitTest((x, y))

        if item != wx.NOT_FOUND and flags & wx.LIST_HITTEST_ONITEM:
            self.list.Select(item)

        event.Skip()


    def OnItemSelected(self, event):
        self.currentItem = event.m_itemIndex
        itemDataString = str(self.list.GetItemData(self.currentItem))
        year = itemDataString[:4]
        month = itemDataString[4:6]
        day = itemDataString[6:]
        
        self.mainFrame.redNotebook.changeDate(datetime.date(int(year), int(month), int(day)))
        
        event.Skip()
        
        
            
def getBitmap(file):
    return wx.Bitmap(os.path.join(filesystem.imageDir, file), wx.BITMAP_TYPE_ANY)

def getIcon(file):
    icon = wx.EmptyIcon()
    icon.CopyFromBitmap(getBitmap(file))
    return icon
        
    
        
        