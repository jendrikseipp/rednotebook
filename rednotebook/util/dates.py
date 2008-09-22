import datetime


oneDay = datetime.date(1,1,2) - datetime.date(1,1,1)
        
def getYearAndMonthFromDate(date):
    return date.strftime('%Y-%m')