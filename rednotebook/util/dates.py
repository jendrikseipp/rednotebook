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


one_day = datetime.timedelta(days=1)


def get_year_and_month_from_date(date):
    year_and_month = date.strftime("%Y-%m")
    assert len(year_and_month) == 7
    return year_and_month


def get_date_from_date_string(date_string):
    date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
    return datetime.date(date.year, date.month, date.day)


# Number of days per month (except for February in leap years)
month_days = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def isleap(year):
    """Return True for leap years, False for non-leap years."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def get_number_of_days(year, month):
    """
    Return the number of days in a given month of a given year
    """
    days = month_days[month] + (month == 2 and isleap(year))
    return days


def format_date(format_string, date=None):
    if date is None:
        date = datetime.datetime.now()
    try:
        date_string = date.strftime(format_string)
    except ValueError:
        # This happens if the format string ends with "%"
        date_string = _("Incorrect date format")
    return date_string


def same_month(date1, date2):
    return (
        date1 is not None
        and date2 is not None
        and date1.month == date2.month
        and date1.year == date2.year
    )
