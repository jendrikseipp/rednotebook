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

from collections import Counter
import itertools
import logging
import re
import sys

import gtk
import gobject

from rednotebook.gui.browser import HtmlView
from rednotebook.util import unicode


CLOUD_WORDS = 50

CLOUD_CSS = """\
<style type="text/css">
    body {
        font-family: Ubuntu, sans-serif;
        text-align: center;
    }
    a:link { color:black; text-decoration:none; }
    a:visited { color:black; text-decoration:none; }
    a:focus { color:black; text-decoration:none; }
    a:hover { color:black; text-decoration:none; }
    a:active { color:black; text-decoration:none; }
</style>
"""


def get_regex(word):
    try:
        return re.compile(word + '$', re.I)
    except Exception:
        logging.warning('"%s" is not a valid regular expression' % word)
        return re.compile('^$')


def get_cloud_html(word_count_dict, categories_counter, ignores, includes):
    # filter short words
    words = [(word, freq) for (word, freq) in word_count_dict.items()
             if (len(word) > 4 or
             any(pattern.match(word) for pattern in includes)) and not
             # filter words in ignore_list
             any(pattern.match(word) for pattern in ignores)]

    def frequency((word, freq)):
        return freq

    # only take the longest words. If there are less words than n,
    # len(words) words are returned
    words.sort(key=frequency)
    cloud_words = words[-CLOUD_WORDS:] + categories_counter.items()

    if not cloud_words:
        return [], ''

    counts = [freq for (word, freq) in cloud_words]
    min_count = min(counts)
    delta_count = max(counts) - min_count
    if delta_count == 0:
        delta_count = 1

    min_font_size = 10
    max_font_size = 50

    font_delta = max_font_size - min_font_size

    # sort words with unicode sort function
    cloud_words.sort(key=lambda (word, count): unicode.coll(word.lstrip(u'#')))

    html_elements = []

    for index, (word, count) in enumerate(cloud_words):
        font_factor = (count - min_count) / delta_count
        font_size = int(min_font_size + font_factor * font_delta)

        if word in categories_counter:
            word = '<u><b>%s</b></u>' % word

        # Add some whitespace to separate words
        html_elements.append('<a href="search/%s">'
                             '<span style="font-size:%spx">%s</span></a>&#160;'
                             % (index, font_size, word))

    html_body = ''.join(['<body>', '\n'.join(html_elements), '\n</body>\n'])
    html_doc = ''.join(['<html><head>', CLOUD_CSS, '</head>', html_body, '</html>'])

    return (cloud_words, html_doc)


class Cloud(HtmlView):
    def __init__(self, journal):
        HtmlView.__init__(self)

        self.journal = journal

        self.update_lists()

        self.webview.connect("hovering-over-link", self.on_hovering_over_link)
        self.webview.connect('populate-popup', self.on_populate_popup)

        self.last_hovered_word = None

    def update_lists(self):
        config = self.journal.config

        default_ignore_list = _('filter, these, comma, separated, words')
        self.ignore_list = config.read_list('cloudIgnoreList', default_ignore_list)
        self.ignore_list = [word.lower() for word in self.ignore_list]
        logging.info('Cloud ignore list: %s' % self.ignore_list)

        default_include_list = _('mtv, spam, work, job, play')
        self.include_list = config.read_list('cloudIncludeList', default_include_list)
        self.include_list = [word.lower() for word in self.include_list]
        logging.info('Cloud include list: %s' % self.include_list)

        self.update_regexes()

    def update_regexes(self):
        logging.debug('Start compiling regexes')
        self.regexes_ignore = [get_regex(word) for word in self.ignore_list]
        self.regexes_include = [get_regex(word) for word in self.include_list]
        logging.debug('Finished')

    def update(self, force_update=False):
        """Public method that calls the private "_update"."""
        if self.journal.frame is None:
            return

        # Do not update the cloud with words as it requires a lot of searching
        if not force_update:
            return

        gobject.idle_add(self._update)

    def get_categories_counter(self):
        return Counter(itertools.chain.from_iterable(
                ['#' + cat.lower() for cat in day.categories] for day in self.journal.days))

    def _update(self):
        logging.debug('Update the cloud')
        self.journal.save_old_day()

        word_count_dict = self.journal.get_word_count_dict()
        self.cloud_words, html = get_cloud_html(word_count_dict,
            self.get_categories_counter(), self.regexes_ignore, self.regexes_include)

        self.load_html(html)
        self.last_hovered_word = None

        logging.debug('Cloud updated')

    def on_navigate(self, webview, frame, request):
        """
        Called when user clicks on a cloud word
        """
        if self.loading_html:
            # Keep processing
            return False

        uri = request.get_uri()
        logging.info('Clicked URI "%s"' % uri)

        self.journal.save_old_day()

        # uri has the form "something/somewhere/search/search_index"
        if 'search' in uri:
            # search_index is the part after last slash
            search_index = int(uri.split('/')[-1])
            search_text, count = self.cloud_words[search_index]

            self.journal.frame.search_box.set_active_text(search_text)

            # returning True here stops loading the document
            return True

    def on_button_press(self, webview, event):
        """
        Here we want the context menus
        """
        # keep processing
        return False

    def on_hovering_over_link(self, webview, title, uri):
        """
        We want to save the last hovered link to be able to add it
        to the context menu when the user right-clicks the next time
        """
        if uri:
            search_index = int(uri.split('/')[-1])
            search_text, count = self.cloud_words[search_index]
            self.last_hovered_word = search_text

    def on_populate_popup(self, webview, menu):
        """Called when the cloud's popup menu is created."""
        # remove normal menu items
        children = menu.get_children()
        for child in children:
            menu.remove(child)

        if self.last_hovered_word:
            label = _('Hide "%s" from clouds') % self.last_hovered_word
            ignore_menu_item = gtk.MenuItem(label)
            ignore_menu_item.show()
            menu.prepend(ignore_menu_item)
            ignore_menu_item.connect('activate', self.on_ignore_menu_activate, self.last_hovered_word)

    def on_ignore_menu_activate(self, menu_item, selected_word):
        logging.info('"%s" will be hidden from clouds' % selected_word)
        self.ignore_list.append(selected_word)
        self.journal.config.write_list('cloudIgnoreList', self.ignore_list)
        self.regexes_ignore.append(get_regex(selected_word))
        self.update(force_update=True)
