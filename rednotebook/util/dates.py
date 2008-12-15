import datetime
import wx


oneDay = datetime.date(1,1,2) - datetime.date(1,1,1)
		
def getYearAndMonthFromDate(date):
	return date.strftime('%Y-%m')

def getDateFromDay(day):
	return datetime.date(day.month.yearNumber, day.month.monthNumber, day.dayNumber)

def getNumberOfDaysBetweenTwoDays(day1, day2):
	date1 = getDateFromDay(day1)
	date2 = getDateFromDay(day2)
	dateDiff = date1 - date2
	return dateDiff.days

def compareTwoDays(day1, day2):
	return getNumberOfDaysBetweenTwoDays(day1, day2)

def getWXDateTimeFromPyDate(date):
	wxDateTime = wx.DateTime()
	wxDateTime.SetYear(date.year)
	'Implementation buggy'
	wxDateTime.SetMonth(date.month - 1)
	wxDateTime.SetDay(date.day)
	return wxDateTime

def getPyDateFromWXDateTime(wxDateTime):
	'Implementation buggy'
	pyDate = datetime.date(wxDateTime.Year, wxDateTime.Month + 1, wxDateTime.Day)
	return pyDate




   
  