import datetime


oneDay = datetime.date(1,1,2) - datetime.date(1,1,1)
		
def getYearAndMonthFromDate(date):
	yearAndMonth = date.strftime('%Y-%m')
	assert len(yearAndMonth) == 7
	return yearAndMonth

def getDateFromDay(day):
	return datetime.date(day.month.yearNumber, day.month.monthNumber, day.dayNumber)

def get_date_from_date_string(dateString):
	dateArray = dateString.split('-')
	year, month, day = map(int, dateArray)
	return datetime.date(year, month, day)

def getNumberOfDaysBetweenTwoDays(day1, day2):
	date1 = getDateFromDay(day1)
	date2 = getDateFromDay(day2)
	dateDiff = date1 - date2
	return dateDiff.days

def compareTwoDays(day1, day2):
	return getNumberOfDaysBetweenTwoDays(day1, day2)




   
  
