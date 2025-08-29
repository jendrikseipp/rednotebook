# -----------------------------------------------------------------------
# Copyright (c) 2008-2024 Jendrik Seipp
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

import locale
import logging
import re
from collections import defaultdict

from gi.repository import GLib, Gtk

from rednotebook import data
from rednotebook.gui import browser
from rednotebook.util import utils


CLOUD_WORDS = 30

CLOUD_CSS = """\
<style type="text/css">
    :root {
        color-scheme: light dark;
        --fgcolor: %(fgcolor)s;
        --bgcolor: %(bgcolor)s;
    }
    body {
        font-family: %(font)s;
        text-align: center;
        background: var(--bgcolor);
        color: var(--fgcolor);
    }
    a { color: var(--fgcolor); text-decoration: none; }
    h1 { border-bottom: 1px solid grey; margin: 0; margin-bottom: 8px;
         padding: 0; font-size: 15px; line-height: 1; text-align: left;
         font-weight: normal; }
</style>
"""


def get_regex(word):
    try:
        return re.compile(f"{word}$", re.IGNORECASE)
    except Exception:
        logging.warning(f'"{word}" is not a valid regular expression')
        return re.compile("^$")


class Cloud(browser.HtmlView):
    def __init__(self, journal):
        super().__init__()
        self.journal = journal
        self.update_lists()

        self.connect("context-menu", self._on_context_menu)
        self.connect("decide-policy", self.on_decide_policy)

    def update_lists(self):
        config = self.journal.config

        default_ignore_list = _("filter, these, comma, separated, words, and, #tags")
        self.ignore_list = config.read_list("cloudIgnoreList", default_ignore_list)
        self.ignore_list = [word.lower() for word in self.ignore_list]
        logging.info(f"Cloud ignore list: {self.ignore_list}")

        default_include_list = _("mtv, spam, work, job, play")
        self.include_list = config.read_list("cloudIncludeList", default_include_list)
        self.include_list = [word.lower() for word in self.include_list]
        logging.info(f"Cloud include list: {self.include_list}")

        # Ignore files and web links in words cloud
        self.special_ignore_words_tuple = ("file://.*", "https?://.*")
        logging.info(f"Cloud special ignore regexes: {self.special_ignore_words_tuple}")

        self.update_regexes()

    def update_regexes(self):
        logging.debug("Start compiling regexes: ignore, include and special")
        self.regexes_ignore = [get_regex(word) for word in self.ignore_list]
        self.regexes_include = [get_regex(word) for word in self.include_list]
        self.regexes_special_ignore_words = [
            re.compile(regex) for regex in self.special_ignore_words_tuple
        ]
        logging.debug("Finished compiling")

    def update(self, force_update=False):
        """Public method that calls the private "_update"."""
        if self.journal.frame is None:
            return

        # Do not update the cloud with words as it requires a lot of searching
        if not force_update:
            return

        GLib.idle_add(self._update)

    def get_categories_counter(self):
        counter = defaultdict(int)
        for day in self.journal.days:
            for cat in day.categories:
                counter[f"#{data.escape_tag(cat)}"] += 1
        return counter

    def _update(self):
        logging.debug("Update the cloud")
        self.journal.save_old_day()

        # TODO: Avoid using an instance variable here.
        self.link_index = 0

        tags_count_dict = list(self.get_categories_counter().items())
        self.tags = self._get_tags_for_cloud(tags_count_dict, self.regexes_ignore)

        word_count_dict = self.journal.get_word_count_dict()
        self.words = self._get_words_for_cloud(
            word_count_dict,
            self.regexes_ignore + self.regexes_special_ignore_words,
            self.regexes_include,
            {tag for tag, _freq in self.tags},
        )

        self.link_dict = self.tags + self.words
        html = self.get_clouds(self.words, self.tags)
        self.load_html(html)
        logging.debug("Cloud updated")

    def _get_cloud_body(self, cloud_words):
        if not cloud_words:
            return ""
        counts = [freq for (word, freq) in cloud_words]
        min_count = min(counts)
        delta_count = max(counts) - min_count
        if delta_count == 0:
            delta_count = 1

        min_font_size = 10
        max_font_size = 40
        font_delta = max_font_size - min_font_size
        html_elements = []
        for word, count in cloud_words:
            font_factor = (count - min_count) / delta_count
            font_size = int(min_font_size + font_factor * font_delta)

            # Add some whitespace to separate words
            html_elements.append(
                f'<a href="/#search-{self.link_index}"><span '
                f'style="font-size:{font_size}px">{word}</span></a>&#160;'
            )
            self.link_index += 1
        return "\n".join(html_elements)

    @staticmethod
    def select_most_frequent_words(words_and_frequencies, nwords):
        """
        Return the 'nwords' most frequent words and their frequencies
        in 'words_and_frequences' sorted by the locale.
        """
        most_frequent_words = []
        if nwords > 0:
            words_and_frequencies.sort(key=lambda word_freq: word_freq[1], reverse=True)
            most_frequent_words = words_and_frequencies[:nwords]
            most_frequent_words.sort(key=lambda word_freq: locale.strxfrm(word_freq[0]))
        return most_frequent_words

    def _get_tags_for_cloud(self, tag_count_dict, ignores):
        tags_and_frequencies = [
            (tag, freq)
            for (tag, freq) in tag_count_dict
            if not any(pattern.match(tag) for pattern in ignores)
        ]

        tag_display_limit = self.journal.config.read("cloudMaxTags")
        return self.select_most_frequent_words(tags_and_frequencies, tag_display_limit)

    def _get_words_for_cloud(self, word_count_dict, ignores, includes, tags):
        words_and_frequencies = [
            (word, freq)
            for (word, freq) in word_count_dict.items()
            if (len(word) > 4 or any(pattern.match(word) for pattern in includes))
            and all(not pattern.match(word) for pattern in ignores)
            and f"#{word}" not in tags
        ]
        return self.select_most_frequent_words(words_and_frequencies, CLOUD_WORDS)

    def get_clouds(self, word_counter, tag_counter):
        tag_cloud = self._get_cloud_body(tag_counter)
        word_cloud = self._get_cloud_body(word_counter)
        font = self.journal.config.read("previewFont")
        heading = "<h1>&#160;%s</h1>"
        bgcolor, fgcolor = utils.get_gtk_colors(self.journal.frame.day_text_field.day_text_view)
        parts = [
            "<html><head>",
            CLOUD_CSS % {"font": font, "bgcolor": bgcolor, "fgcolor": fgcolor},
            "</head>",
            "<body>",
        ]
        if tag_cloud:
            parts.extend([heading % _("Tags"), tag_cloud, "\n", "<br />\n" * 3])
        if word_cloud:
            parts.extend([heading % _("Words"), word_cloud])
        parts.append("</body></html>")
        return "\n".join(parts)

    def _get_search_text(self, uri):
        if "/#search-" in uri:
            search_index = int(uri.split("-")[-1])
            search_text, count = self.link_dict[search_index]
            return search_text
        else:
            return None

    def on_decide_policy(self, webview, decision, decision_type):
        """
        Called (among others) when user clicks on a cloud word.
        """
        if decision_type == browser.WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            uri = decision.get_navigation_action().get_request().get_uri()

            search_text = self._get_search_text(uri)
            if search_text is not None:
                logging.info(f'Clicked cloud URI "{uri}"')
                self.journal.save_old_day()
                self.journal.frame.search_box.set_active_text(search_text)
                self.journal.frame.search_box.search(search_text)
                # returning True here stops loading the document
                return True

    def _on_context_menu(self, _view, menu, _event, hit_test_result):
        """Called when the cloud's popup menu is created."""
        menu.remove_all()

        tag = hit_test_result.get_link_label()

        if tag is not None:
            action = Gtk.Action.new("hide", _('Hide "%s" from clouds') % tag, None, None)
            action.connect("activate", self.on_ignore_menu_activate, tag)
            ignore_menu_item = browser.WebKit2.ContextMenuItem.new(action)
            menu.append(ignore_menu_item)

    def on_ignore_menu_activate(self, menu_item, word):
        word = re.escape(word)
        logging.info(f'"{word}" will be hidden from clouds')
        self.ignore_list.append(word)
        self.journal.config.write_list("cloudIgnoreList", self.ignore_list)
        self.regexes_ignore.append(get_regex(word))
        self.update(force_update=True)
