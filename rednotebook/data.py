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

import datetime


TEXT_RESULT_LENGTH = 42


def get_text_with_dots(text, start, end, found_text=None):
    '''
    Find the outermost spaces and add dots if needed
    '''
    bound1 = max(0, start - int(TEXT_RESULT_LENGTH//2))
    bound2 = start
    bound3 = end
    bound4 = min(len(text), end + int(TEXT_RESULT_LENGTH//2))

    if bound1 == 0:
        start = 0
    else:
        start = max(bound1, text.find(' ', bound1, bound2))

    if bound4 == len(text):
        end = len(text)
    else:
        end = text.rfind(' ', bound3, bound4)
        if end == -1:
            end = bound4

    res = ''
    if start > 0:
        res += '... '
    res += text[start:end]
    if end < len(text):
        res += ' ...'

    res = res.replace('\n', ' ')
    if found_text:
        # Make the searched_text bold
        res = res.replace(found_text, 'STARTBOLD%sENDBOLD' % found_text)

    return res


class Day(object):
    def __init__(self, month, day_number, day_content = None):
        if day_content is None:
            day_content = {'text': u''}

        self.date = datetime.date(month.year_number, month.month_number, day_number)

        self.month = month
        self.day_number = day_number

        # Turn all entries of old "Tags" categories into tags without entries.
        old_tags = day_content.pop('Tags', {})
        for old_tag in old_tags.keys():
            day_content[old_tag] = None
            self.month.edited = True

        self.content = day_content

        # Remember the last edit and preview position
        self.last_edit_pos = None
        self.last_preview_pos = None

    # Text
    def _get_text(self):
        '''Return the day's text as unicode.'''
        if 'text' in self.content:
            return self.content['text'].decode('utf-8')
        else:
           return ''

    def _set_text(self, text):
        self.content['text'] = text
    text = property(_get_text, _set_text)

    @property
    def has_text(self):
        return len(self.text.strip()) > 0


    @property
    def empty(self):
        if len(self.content) == 0:
            return True
        return self.content.keys() == ['text'] and not self.has_text


    def add_category_entry(self, category, entry):
        if category in self.content:
            self.content[category][entry] = None
        else:
            self.content[category] = {entry: None}


    def merge(self, same_day):
        assert self.date == same_day.date

        # Merge texts
        text1 = self.text.strip()
        text2 = same_day.text.strip()
        if text2 in text1:
            # self.text contains the other text
            pass
        elif text1 in text2:
            # The other text contains contains self.text
            self.text = same_day.text
        else:
            self.text += '\n\n' + same_day.text

        # Merge categories
        for category, entries in same_day.get_category_content_pairs().items():
            for entry in entries:
                self.add_category_entry(category, entry)


    @property
    def categories(self):
        return self.get_category_content_pairs().keys()


    def get_entries(self, category):
        entries = self.content.get(category) or {}
        return sorted(entries.keys())


    def get_category_content_pairs(self):
        '''
        Returns a dict of (category: content_in_category_as_list) pairs.
        '''
        pairs = {}
        for category, content in self.content.iteritems():
            if category == 'text':
                continue
            if content is None:
                pairs[category] = []
            else:
                pairs[category] = content.keys()
        return pairs


    def get_words(self, with_special_chars=False):
        all_text = self.text
        for category, content in self.get_category_content_pairs().items():
            all_text += ' ' + ' '.join([category] + content)

        words = all_text.split()
        if with_special_chars:
            return words

        words = [w.strip(u'.|-!"/()=?*+~#_:;,<>^°´`{}[]\\') for w in words]
        return [word for word in words if word]


    def get_number_of_words(self):
        return len(self.get_words(with_special_chars=True))


    def search(self, text, tags):
        if not text:
            results = []
            for day_tag, entries in self.get_category_content_pairs():
                for tag in tags:
                    if day_tag.replace(' ', '').lower() != tag:
                        continue
                    if entries:
                        results.extend(entries)
                    else:
                        results.append(get_text_with_dots(self.text, 0,
                                       TEXT_RESULT_LENGTH))
            return str(self), results

        results = []
        # Search in date
        if text in str(self):
            results.append(get_text_with_dots(self.text, 0, TEXT_RESULT_LENGTH))
            return results
        text_result = self.search_in_text(text)
        if text_result:
            results.append(text_result)
        results.extend(self.search_in_categories(text))
        return str(self), results


    def search_in_text(self, search_text):
        '''
        Try searching in date first, then in the text, then in the annotations
        Uses case-insensitive search
        '''
        occurence = self.text.upper().find(search_text.upper())

        # Check if search_text is in text
        if occurence < 0:
            return None

        found_text = self.text[occurence:occurence + len(search_text)]
        result_text = get_text_with_dots(self.text, occurence,
                                    occurence + len(search_text), found_text)
        return result_text


    def search_in_categories(self, text):
        results = []
        for category, content in self.get_category_content_pairs().items():
            if content:
                if text.upper() in category.upper():
                    results.extend(content)
                else:
                    results.extend(entry for entry in content
                                   if text.upper() in entry.upper())
            elif text.upper() in category.upper():
                results.append(category)
        return results


    def __str__(self):
        return self.date.strftime('%Y-%m-%d')


    def __cmp__(self, other):
        return cmp(self.date, other.date)



class Month(object):
    def __init__(self, year_number, month_number, month_content = None):
        if month_content == None:
            month_content = {}

        self.edited = False

        self.year_number = year_number
        self.month_number = month_number
        self.days = {}
        for day_number, day_content in month_content.iteritems():
            self.days[day_number] = Day(self, day_number, day_content)

    def get_day(self, day_number):
        if day_number in self.days:
            return self.days[day_number]
        else:
            new_day = Day(self, day_number)
            self.days[day_number] = new_day
            return new_day

    def __str__(self):
        res = 'Month %s %s\n' % (self.year_number, self.month_number)
        for day_number, day in self.days.iteritems():
            res += '%s: %s\n' % (day_number, day.text)
        return res

    @property
    def empty(self):
        for day in self.days.values():
            if not day.empty:
                return False
        return True

    def same_month(date1, date2):
        if date1 == None or date2 == None:
            return False
        return date1.month == date2.month and date1.year == date2.year
    same_month = staticmethod(same_month)

    def __cmp__(self, other):
        return cmp((self.year_number, self.month_number),
                    (other.year_number, other.month_number))
