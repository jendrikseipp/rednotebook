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

"""Translate legacy txt2tags markup to its Markdown equivalent.

RedNotebook used txt2tags markup for many years. To keep old journals
readable after the switch to Markdown, every entry is run through this
converter before it reaches the Markdown parser. Constructs that Markdown
shares with txt2tags (``**bold**``, ``- lists``, fenced ```` ``` ```` code
blocks, ...) are left untouched, so text that is already Markdown passes
through essentially unchanged.
"""

import re


IMG_EXT = r"png|jpe?g|gif|eps|bmp|svg"

# Inline conversions applied to a single line of text (outside code fences).
# Order matters: links/images are handled before the emphasis markers so that
# their contents are not mangled.

# [alt ""/path/to/pic"".png?50] and [""/path/to/pic"".png?50]
REGEX_IMAGE = re.compile(rf'\[(?:(.*?) )?""(\S.*?\S|\S)""\.({IMG_EXT})(\?\d+)?\]', flags=re.I)
# [text ""url""]
REGEX_QUOTED_LINK = re.compile(r'\[(.*?)\s""(\S.*?\S)""\]')
# [text http://url] (only genuine URLs, to avoid swallowing entry references)
REGEX_NAMED_LINK = re.compile(
    r"\[([^\]]+?)\s+((?:https?|ftp|news|telnet|gopher|wais)://|www[23]?\.|ftp\.)([^\]]+)\]"
)

# Emphasis. Boundaries follow txt2tags: markers hug non-space characters.
REGEX_ITALIC = re.compile(r"(?<![:/])//(?![/\s])(.+?)(?<![\s/])//(?![:/])")
REGEX_UNDERLINE = re.compile(r"__(?!\s)(.+?)(?<!\s)__")
REGEX_STRIKE = re.compile(r"(?<!-)--(?!\s|-)(.+?)(?<![\s-])--(?!-)")
REGEX_MONOSPACE = re.compile(r"``(?!\s)(.+?)(?<!\s)``")

# Headings: "== Title ==" optionally followed by an "[anchor]".
REGEX_HEADING = re.compile(r"^(=+)\s+(.*?)\s+=+\s*(?:\[[^\]]*\])?\s*$")
# Horizontal rule: 20 or more -, = or _ on their own line.
REGEX_HRULE = re.compile(r"^\s*[-=_]{20,}\s*$")
# Numbered list item.
REGEX_NUMBERED = re.compile(r"^(\s*)\+\s+(.*)$")
# Trailing txt2tags line break.
REGEX_LINEBREAK = re.compile(r"\\\\[ \t]*$")

FENCE = re.compile(r"^\s*```")


def _convert_inline(line):
    line = REGEX_IMAGE.sub(_image_repl, line)
    line = REGEX_QUOTED_LINK.sub(r"[\1](\2)", line)
    line = REGEX_NAMED_LINK.sub(r"[\1](\2\3)", line)
    line = REGEX_MONOSPACE.sub(r"`\1`", line)
    line = REGEX_ITALIC.sub(r"*\1*", line)
    line = REGEX_UNDERLINE.sub(r"<u>\1</u>", line)
    line = REGEX_STRIKE.sub(r"~~\1~~", line)
    line = REGEX_LINEBREAK.sub("  ", line)
    return line


def _image_repl(match):
    alt = match.group(1) or ""
    width = match.group(4) or ""
    return f"![{alt}]({match.group(2)}.{match.group(3)}{width})"


def _convert_block(line):
    """Convert line-level constructs that have no Markdown counterpart."""
    if REGEX_HRULE.match(line):
        return "---"

    heading = REGEX_HEADING.match(line)
    if heading:
        level = len(heading.group(1))
        return "#" * level + " " + heading.group(2)

    numbered = REGEX_NUMBERED.match(line)
    if numbered:
        return f"{numbered.group(1)}1. {numbered.group(2)}"

    return None


def convert_to_markdown(text):
    lines = text.split("\n")
    result = []
    in_fence = False
    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
            result.append(line)
            continue
        if in_fence:
            result.append(line)
            continue

        block = _convert_block(line)
        if block is not None:
            result.append(block)
        else:
            result.append(_convert_inline(line))
    return "\n".join(result)
