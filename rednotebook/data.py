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
import re


TEXT_RESULT_LENGTH = 42

ALPHA = r"[^\W\d_]"
ALPHA_NUMERIC = r"\w"
HEX = r"[0-9A-F]{6}"
HASHTAG_EXCLUDES = r"%(HEX)s|include" % locals()
HASHTAG_TEXT = r"%(ALPHA_NUMERIC)s*%(ALPHA)s+%(ALPHA_NUMERIC)s*" % locals()
HASHTAG_PATTERN = (
    r"(^|[^%(ALPHA_NUMERIC)s&#])(#|\uFF03)(?!%(HASHTAG_EXCLUDES)s)"
    "(%(HASHTAG_TEXT)s)" % locals()
)
HASHTAG = re.compile(HASHTAG_PATTERN, flags=re.I)


def escape_tag(tag):
    return tag.lower().replace(" ", "_")


def get_text_with_dots(text, start, end, found_text=None):
    """
    Find the outermost spaces and innermost newlines around
    (start, end) and add dots if needed.
    """
    bound1 = max(0, start - int(TEXT_RESULT_LENGTH // 2))
    bound2 = max(0, start)
    bound3 = min(end, len(text))
    bound4 = min(len(text), end + int(TEXT_RESULT_LENGTH // 2))

    start_values = [bound1]
    newline = text.rfind("\n", bound1, bound2)
    start_values.append(newline)
    if newline == -1:
        start_values.append(text.find(" ", bound1, bound2))
    start = max(start_values)

    end_values = [bound4]
    newline = text.find("\n", bound3, bound4)
    if newline != -1:
        end_values.append(newline)
    else:
        space = text.rfind(" ", bound3, bound4)
        if space != -1:
            end_values.append(space)
    end = min(end_values)

    assert bound1 <= start <= bound2
    assert bound3 <= end <= bound4, (bound3, end, bound4)

    res = ""
    if start > 0:
        res += "... "
    res += text[start:end]
    if end < len(text):
        res += " ..."

    res = res.replace("\n", " ")
    if found_text:
        # Make the searched_text bold
        res = res.replace(found_text, "STARTBOLD%sENDBOLD" % found_text)

    return res


class Day:
    def __init__(self, month, day_number, day_content=None):
        day_content = day_content or {"text": ""}
        assert "text" in day_content, day_content

        self.month = month
        self.date = datetime.date(month.year_number, month.month_number, day_number)

        # Turn all entries of old "Tags" categories into tags without entries.
        # Apparently, "Tags" may map to None, so explicitly convert to dict.
        old_tags = day_content.pop("Tags", None) or {}
        for old_tag in old_tags:
            day_content[old_tag] = None
            self.month.edited = True

        self._content = day_content

    def _get_content(self):
        return self._content

    def _set_content(self, content):
        old_text = self.text
        new_text = content["text"]
        content["text"] = old_text
        self._content = content
        self.text = new_text

    content = property(_get_content, _set_content)

    def _get_text(self):
        """Return the day's text as a unicode string."""
        return self.content["text"]

    def _set_text(self, text):
        assert "text" in self.content
        self.content["text"] = text

    text = property(_get_text, _set_text)

    @property
    def has_text(self):
        return bool(self.text.strip())

    @property
    def empty(self):
        return len(self.content) == 1 and "text" in self.content and not self.has_text

    @property
    def hashtags(self):
        # The same tag can occur multiple times.
        return [hashtag.lower() for _, _hash, hashtag in HASHTAG.findall(self.text)]

    @property
    def categories(self):
        return list(self.get_category_content_pairs().keys())

    def get_entries(self, category):
        return sorted((self.content.get(category) or {}).keys())

    def get_category_content_pairs(self):
        """
        Returns a dict of (category: content_in_category_as_list) pairs.
        """
        pairs = {}
        for category, content in self.content.items():
            if category == "text":
                pass
            elif content is None:
                pairs[category] = []
            else:
                pairs[category] = list(content.keys())
        # Include hashtags
        for tag in self.hashtags:
            pairs[tag] = []
        return pairs

    def get_words(self, with_special_chars=False):
        categories_text = " ".join(
            " ".join([category] + content)
            for category, content in self.get_category_content_pairs().items()
        )

        all_text = self.text + " " + categories_text
        words = all_text.split()

        if with_special_chars:
            return words

        # Strip all ASCII punctuation except for $, %, @ and '.
        words = [w.strip('.|-!"&/()=?*+~#_:;,<>^°`{}[]\\') for w in words]
        return [word for word in words if word]

    def get_number_of_words(self):
        return len(self.get_words(with_special_chars=True))

    def search(self, text, tags):
        """
        This method is only called for days that have all given tags.
        Search in date first, then in the text, then in the tags.
        Uses case-insensitive search.
        """
        results = []
        if not text:
            # Only add text result once for all tags.
            add_text_to_results = False
            for day_tag, entries in self.get_category_content_pairs().items():
                for tag in tags:
                    # We know that all tags are present, but we loop through
                    # day_tags nonetheless, to escape the day_tags.
                    if escape_tag(day_tag) != tag:
                        continue
                    if entries:
                        results.extend(entries)
                    else:
                        add_text_to_results = True
            if add_text_to_results:
                results.append(get_text_with_dots(self.text, 0, TEXT_RESULT_LENGTH))
        elif text in str(self):
            # Date contains searched text.
            results.append(get_text_with_dots(self.text, 0, TEXT_RESULT_LENGTH))
        else:
            text_result = self.search_in_text(text)
            if text_result:
                results.append(text_result)
            results.extend(self.search_in_categories(text))
        return str(self), results

    def search_in_text(self, search_text):
        occurence = self.text.upper().find(search_text.upper())

        # Check if search_text is in text
        if occurence < 0:
            return None

        found_text = self.text[occurence : occurence + len(search_text)]
        result_text = get_text_with_dots(
            self.text, occurence, occurence + len(search_text), found_text
        )
        return result_text

    def search_in_categories(self, text):
        results = []
        for category, content in self.get_category_content_pairs().items():
            if content:
                if text.upper() in category.upper():
                    results.extend(content)
                else:
                    results.extend(
                        entry for entry in content if text.upper() in entry.upper()
                    )
            elif text.upper() in category.upper():
                results.append(category)
        return results

    def __str__(self):
        return self.date.strftime("%Y-%m-%d")


class Month:
    def __init__(self, year_number, month_number, month_content=None, mtime=0):
        self.year_number = year_number
        self.month_number = month_number

        month_content = month_content or {}
        self.days = {}
        for day_number, day_content in month_content.items():
            self.days[day_number] = Day(self, day_number, day_content)

        self.edited = False
        self.mtime = mtime

    def get_day(self, day_number):
        if day_number not in self.days:
            self.days[day_number] = Day(self, day_number)
        return self.days[day_number]

    def __str__(self):
        lines = ["Month {} {}".format(self.year_number, self.month_number)]
        for day_number, day in self.days.items():
            lines.append("{}: {}".format(day_number, day.text))
        return "\n".join(lines)

    @property
    def empty(self):
        return all(day.empty for day in self.days.values())
