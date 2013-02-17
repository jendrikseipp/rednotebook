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

from __future__ import division


class Statistics(object):
    def __init__(self, journal):
        self.journal = journal

    def get_number_of_words(self):
        number_of_words = 0
        for day in self.days:
            number_of_words += day.get_number_of_words()
        return number_of_words

    def get_number_of_distinct_words(self):
        return len(self.journal.get_word_count_dict())

    def get_number_of_chars(self):
        number_of_chars = 0
        for day in self.days:
            number_of_chars += len(day.text)
        return number_of_chars

    def get_number_of_usage_days(self):
        '''Returns the timespan between the first and last entry'''
        sorted_days = self.days
        if len(sorted_days) <= 1:
            return len(sorted_days)
        first_day = sorted_days[0]
        last_day = sorted_days[-1]
        timespan = last_day.date - first_day.date
        return abs(timespan.days) + 1

    def get_number_of_entries(self):
        return len(self.days)

    def get_edit_percentage(self):
        total = self.get_number_of_usage_days()
        edited = self.get_number_of_entries()
        if total == 0:
            return 0
        percent = round(100 * edited / total, 2)
        return '%s%%' % percent

    def get_average_number_of_words(self):
        if self.get_number_of_entries() == 0:
            return 0
        return round(self.get_number_of_words() / self.get_number_of_entries(), 2)

    @property
    def overall_pairs(self):
        return [
            [_('Words'), self.get_number_of_words()],
            [_('Distinct Words'), self.get_number_of_distinct_words()],
            [_('Edited Days'), self.get_number_of_entries()],
            [_('Letters'), self.get_number_of_chars()],
            [_('Days between first and last Entry'), self.get_number_of_usage_days()],
            [_('Average number of Words'), self.get_average_number_of_words()],
            [_('Percentage of edited Days'), self.get_edit_percentage()],
        ]

    @property
    def day_pairs(self):
        day = self.journal.day
        return [
            [_('Words'), day.get_number_of_words()],
            [_('Lines'), len(day.text.splitlines())],
            [_('Letters'), len(day.text)],
        ]

    def show_dialog(self, dialog):
        self.journal.save_old_day()
        self.days = self.journal.days

        day_store = dialog.day_list.get_model()
        day_store.clear()
        for pair in self.day_pairs:
            day_store.append(pair)

        overall_store = dialog.overall_list.get_model()
        overall_store.clear()
        for pair in self.overall_pairs:
            overall_store.append(pair)

        dialog.show_all()
        dialog.run()
        dialog.hide()
