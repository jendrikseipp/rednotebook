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
import re

import gi
from markdown_it import MarkdownIt


gi.require_version("Pango", "1.0")

from gi.repository import GObject, Pango  # noqa: E402

from rednotebook.util import t2t_to_markdown  # noqa: E402
from rednotebook.util.markup import REGEX_HTML_LINK  # noqa: E402


# Categories are short, single-line strings, so inline rendering is enough.
_PARSER = MarkdownIt("commonmark").enable("strikethrough")

# Map the (limited) set of HTML tags that markdown-it emits to the Pango tags
# the category tree understands.
_HTML_TO_PANGO = [
    ("<strong>", "<b>"),
    ("</strong>", "</b>"),
    ("<em>", "<i>"),
    ("</em>", "</i>"),
    ("<s>", "<s>"),
    ("</s>", "</s>"),
    ("<code>", "<tt>"),
    ("</code>", "</tt>"),
]


def convert_to_pango(txt, headers=None, options=None):
    """Convert (Markdown) category markup to Pango markup for display."""
    original_txt = txt

    txt = t2t_to_markdown.convert_to_markdown(txt)
    result = _PARSER.renderInline(txt)

    for html_tag, pango_tag in _HTML_TO_PANGO:
        result = result.replace(html_tag, pango_tag)

    # Pango has no anchor element, so reduce links to their text.
    result = re.sub(REGEX_HTML_LINK, r"\1", result)

    logging.log(5, f'Converted "{original_txt!r}" to Pango "{result!r}"')

    try:
        Pango.parse_markup(result, -1, "0")
    except GObject.GError:
        # There are unknown tags in the markup, return the original text.
        logging.debug(f"There are unknown tags in the markup: {result}")
        return original_txt
    return result


def convert_from_pango(pango_markup):
    """Convert Pango markup back to the Markdown stored in the journal."""
    original_txt = pango_markup
    replacements = {
        "<b>": "**",
        "</b>": "**",
        "<i>": "*",
        "</i>": "*",
        "<s>": "~~",
        "</s>": "~~",
        "<u>": "<u>",
        "</u>": "</u>",
        "<tt>": "`",
        "</tt>": "`",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
    }
    for orig, repl in replacements.items():
        pango_markup = pango_markup.replace(orig, repl)

    logging.log(5, f'Converted Pango "{original_txt!r}" to Markdown "{pango_markup!r}"')
    return pango_markup
