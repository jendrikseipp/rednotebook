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
# with this program.  If not, see <https://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------

import logging
import os
import re

from rednotebook.util import filesystem, markdownmarkup, t2t_to_markdown, urls


# A trailing "<a ...>text</a>" link, used by pango_markup to strip links.
REGEX_HTML_LINK = r"<a.*?>(.*?)</a>"

# Markdown image/link target: "![alt](url)" or "[text](url)".
REGEX_MD_LINK = re.compile(r"(!?\[[^\]]*\]\()([^)\s]+)(\))")
# Optional image width suffix.
REGEX_IMAGE_WIDTH = re.compile(r"\?(\d+)$")

# Entry references such as "[2019-08-01]" or "[my day 2019-08-01]".
REGEX_NAMED_REFERENCE = re.compile(r"\[(?P<name>.+?)\s+(?P<date>\d{4}-\d{2}-\d{2})\s*\]")
REGEX_DATE_REFERENCE = re.compile(r"\[(?P<date>\d{4}-\d{2}-\d{2})\]")

# Math delimiters that MathJax understands besides "$"/"$$".
REGEX_MATH_DISPLAY = re.compile(r"\\\[(.+?)\\\]", flags=re.DOTALL)
REGEX_MATH_INLINE = re.compile(r"\\\((.+?)\\\)", flags=re.DOTALL)


def convert_categories_to_markup(categories, with_category_title=True):
    # Only add the "Tags" title if the text is displayed.
    markup = "## {}\n".format(_("Tags")) if with_category_title else ""
    for category, entry_list in categories.items():
        markup += f"- {category}\n"
        for entry in entry_list:
            markup += f"  - {entry}\n"
    markup += "\n\n"
    return markup


def get_markup_for_day(day, target, with_text=True, with_tags=True, categories=None, date=None):
    """
    Used for exporting days
    """
    export_string = ""

    # Add date if it is not None and not the empty string
    if date:
        if target == "html":
            # The anchor is the target for entry references mentioning this date.
            export_string += f'<span id="{day.date:%Y-%m-%d}"></span>\n\n'

        export_string += f"# {date}\n\n"

    # Add text
    if with_text:
        export_string += day.text

    # Add Categories
    category_content_pairs = day.get_category_content_pairs()

    if with_tags and categories:
        categories = [word.lower() for word in categories]
        export_categories = {
            x: y for (x, y) in category_content_pairs.items() if x.lower() in categories
        }
    elif with_tags and categories is None:
        # No restrictions
        export_categories = category_content_pairs
    else:
        # "Export no categories" selected
        export_categories = []

    if export_categories:
        export_string += "\n\n\n" + convert_categories_to_markup(
            export_categories, with_category_title=with_text
        )
    elif with_text:
        export_string += "\n\n"

    # Only return the string, when there is text or there are categories
    # We don't want to list empty dates
    if export_categories or with_text:
        export_string += "\n\n\n"
        return export_string

    return ""


def _convert_uri(uri, data_dir):
    path = uri[len("file://") :] if uri.startswith("file://") else uri
    # Check if relative file exists and convert it if it does.
    if not any(
        uri.startswith(proto) for proto in filesystem.REMOTE_PROTOCOLS
    ) and not os.path.isabs(path):
        path = os.path.join(data_dir, path)
        assert os.path.isabs(path), path
        if os.path.exists(path):
            uri = urls.get_local_url(path)
    return uri


def _convert_paths(txt, data_dir):
    """Turn relative paths in Markdown links and images into absolute URLs."""
    data_dir = str(data_dir)

    def repl(match):
        prefix, url, suffix = match.groups()
        width = ""
        is_image = prefix.startswith("!")
        width_match = REGEX_IMAGE_WIDTH.search(url)
        if is_image and width_match:
            width = width_match.group(0)
            url = url[: width_match.start()]
        # Leave fragment-only references (entry references) untouched.
        if url.startswith("#"):
            return match.group(0)
        return prefix + _convert_uri(url, data_dir) + width + suffix

    return REGEX_MD_LINK.sub(repl, txt)


def _convert_entry_references(txt, target):
    """Turn date references into links (HTML) or plain text (other targets)."""
    if target == "html":
        txt = REGEX_NAMED_REFERENCE.sub(r"[\g<name>](#\g<date>)", txt)
        txt = REGEX_DATE_REFERENCE.sub(r"[\g<date>](#\g<date>)", txt)
    else:
        txt = REGEX_NAMED_REFERENCE.sub(r"\g<name> (\g<date>)", txt)
        txt = REGEX_DATE_REFERENCE.sub(r"\g<date>", txt)
    return txt


def _normalize_math(txt):
    """Rewrite "\\(...\\)" and "\\[...\\]" to the "$" delimiters MathJax uses."""
    txt = REGEX_MATH_DISPLAY.sub(r"$$\1$$", txt)
    txt = REGEX_MATH_INLINE.sub(r"$\1$", txt)
    return txt


def convert(txt, target, data_dir, options=None):
    """Convert journal text (Markdown, with txt2tags fallback) to ``target``."""
    data_dir = str(data_dir)
    options = options or {}

    # Translate any legacy txt2tags markup to Markdown first.
    txt = t2t_to_markdown.convert_to_markdown(txt)

    # Turn relative paths into absolute paths.
    txt = _convert_paths(txt, data_dir)

    # Handle RedNotebook-specific constructs.
    txt = _convert_entry_references(txt, target)
    txt = _normalize_math(txt)

    try:
        return markdownmarkup.render(txt, target, options)
    except Exception:
        logging.exception("Markdown conversion failed")
        return (
            "<b>Error</b>: This day contains markup that RedNotebook could not "
            "convert. Please report this at "
            '<a href="https://github.com/jendrikseipp/rednotebook/issues/">'
            "the RedNotebook bugtracker</a> and append the day's text to the issue."
        )
