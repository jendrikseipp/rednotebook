# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2009  Jendrik Seipp
# 
# RedNotebook is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# RedNotebook is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with RedNotebook; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# -----------------------------------------------------------------------

import datetime


oneDay = datetime.timedelta(days=1)

def get_date_string(date):
	return date.strftime("%A, %x")
		
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




   
  
