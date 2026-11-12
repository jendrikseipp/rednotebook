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
from urllib.parse import urlsplit
from urllib.request import url2pathname

from rednotebook.util import markdownmarkup, urls


# A trailing "<a ...>text</a>" link, used by pango_markup to strip links.
REGEX_HTML_LINK = r"<a.*?>(.*?)</a>"

# Optional image width suffix.
REGEX_IMAGE_WIDTH = re.compile(r"\?(\d+)$")


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


def _convert_uri(uri, data_dir, is_image=False):
    """Resolve a parsed local destination against the journal directory."""
    width = ""
    match = REGEX_IMAGE_WIDTH.search(uri) if is_image else None
    if match:
        width = match.group(0)
        uri = uri[: match.start()]
    # Old journals also use file://relative/path, so remove that prefix before
    # checking whether the path is absolute.
    local = uri[7:] if uri.lower().startswith("file://") else uri
    parts = urlsplit(local)
    if uri.startswith("#") or parts.scheme or parts.netloc or not parts.path:
        return uri + width
    path = url2pathname(parts.path)
    if not os.path.isabs(path):
        path = os.path.join(data_dir, path)
        if os.path.exists(path):
            uri = urls.get_local_url(path)
            if parts.query:
                uri += "?" + parts.query
            if parts.fragment:
                uri += "#" + parts.fragment
    return uri + width


def convert(txt, target, data_dir, options=None):
    """Convert Markdown journal text to ``target``."""
    data_dir = str(data_dir)
    options = options or {}

    try:
        return markdownmarkup.render(
            txt,
            target,
            options,
            resolve_link=lambda uri, is_image: _convert_uri(uri, data_dir, is_image),
        )
    except Exception:
        logging.exception("Markdown conversion failed")
        return (
            "<b>Error</b>: This day contains markup that RedNotebook could not "
            "convert. Please report this at "
            '<a href="https://github.com/jendrikseipp/rednotebook/issues/">'
            "the RedNotebook bugtracker</a> and append the day's text to the issue."
        )
