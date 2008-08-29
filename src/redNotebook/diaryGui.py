import wx
from wx.lib.customtreectrl import CustomTreeCtrl
import redNotebook

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
        
    
        
        