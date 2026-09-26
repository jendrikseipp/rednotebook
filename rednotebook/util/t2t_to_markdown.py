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

from markdown_it import MarkdownIt
from markdown_it.helpers import parseLinkDestination, parseLinkTitle

from rednotebook.util.markdownlinks import escape_destination, escape_label


IMG_EXT = r"png|jpe?g|gif|eps|bmp|svg"

# Inline conversions applied to a single line of text (outside code fences).
# Order matters: links/images are handled before the emphasis markers so that
# their contents are not mangled.

# [alt ""/path/to/pic"".png?50] and [""/path/to/pic"".png?50]
REGEX_IMAGE = re.compile(rf'\[(?:(.*?) )?""(\S.*?\S|\S)""\.({IMG_EXT})(\?\d+)?\]', flags=re.I)
REGEX_SIMPLE_IMAGE = re.compile(rf"\[([^\[\]\s]+\.(?:{IMG_EXT})(?:\?\d+)?)\](?![\[(:])", re.I)
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
REGEX_CODE = re.compile(r"(?<!`)(`+)(?!`)([\s\S]*?)(?<!`)\1(?!`)")
REGEX_MATH = re.compile(
    r"\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]|\$\$[\s\S]*?\$\$|(?<!\\)\$(?!\s|\$)[^\n$]+?\$"
)
REGEX_URL = re.compile(r"(?:[a-zA-Z][a-zA-Z0-9+.-]*://|www[23]?\.)[^\s<>]+")

# Headings: "== Title ==" optionally followed by an "[anchor]".
REGEX_HEADING = re.compile(r"^(={1,5}|\+{1,5})\s+(.*?)\s+\1\s*(?:\[[^\]]*\])?\s*$")
# Horizontal rule: 20 or more -, = or _ on their own line.
REGEX_HRULE = re.compile(r"^\s*[-=_]{20,}\s*$")
# Numbered list item.
REGEX_NUMBERED = re.compile(r"^(\s*)\+(?:\s+(.*)|$)")
# Trailing txt2tags line break.
REGEX_LINEBREAK = re.compile(r"\\\\[ \t]*$")

REGEX_LIST = re.compile(r"^( *)([-+])(?: +(.*)|$)")


def _convert_inline(line):
    line = REGEX_ITALIC.sub(r"*\1*", line)
    line = REGEX_UNDERLINE.sub(r"<u>\1</u>", line)
    line = REGEX_STRIKE.sub(r"~~\1~~", line)
    line = REGEX_LINEBREAK.sub("  ", line)
    return line


def _image_repl(match, restore):
    alt = match.group(1) or ""
    width = match.group(4) or ""
    destination = escape_destination(restore(f"{match.group(2)}.{match.group(3)}{width}"))
    return f"![{escape_label(alt)}]({destination})"


def _convert_block(line, heading_numbers):
    """Convert line-level constructs that have no Markdown counterpart."""
    if REGEX_HRULE.match(line):
        return "---"

    heading = REGEX_HEADING.match(line)
    if heading:
        level = len(heading.group(1))
        title = _convert_inline(heading.group(2))
        if heading.group(1).startswith("+"):
            heading_numbers[level - 1] += 1
            heading_numbers[level:] = [0] * (len(heading_numbers) - level)
            title = ".".join(map(str, heading_numbers[:level])) + ". " + title
        return "#" * level + " " + title

    numbered = REGEX_NUMBERED.match(line)
    if numbered:
        return f"{numbered.group(1)}1. {_convert_inline(numbered.group(2) or '')}"

    return None


def _literal_text(text):
    # Entities prevent Markdown and linkification while preserving visible text.
    return re.sub(r"[^\w\s]|_", lambda char: f"&#{ord(char.group())};", text)


def _protect_quote_blocks(text, protect):
    if not re.search(r"(?m)^(?:\"{3}|'{3})[ \t]*$", text):
        return text
    code_lines = set()
    for token in MarkdownIt("commonmark").parse(text):
        if token.type in ("fence", "code_block"):
            code_lines.update(range(*token.map))
    lines = text.split("\n")
    result = []
    pos = 0
    in_comment = False
    while pos < len(lines):
        marker = lines[pos].strip()
        if pos not in code_lines and marker == "%%%":
            in_comment = not in_comment
        if not in_comment and pos not in code_lines and marker in ('"""', "'''"):
            end = pos + 1
            while end < len(lines) and lines[end].strip() != marker:
                end += 1
            content = "\n".join(lines[pos + 1 : end])
            if marker == '"""':
                replacement = _literal_text(content)
            else:
                longest = max((len(run) for run in re.findall(r"`+", content)), default=0)
                fence = "`" * max(3, longest + 1)
                replacement = f"{fence}rednotebook-raw\n{content}\n{fence}"
            result.append(protect("\n\n" + replacement + "\n\n"))
            pos = end + 1
        else:
            result.append(lines[pos])
            pos += 1
    return "\n".join(result)


def _protect_literals(text, protect, restore, inline):
    if not inline:
        text = _protect_quote_blocks(text, protect)
    # Source maps also cover fences inside blockquotes/lists and arbitrary
    # fence lengths. Keep the original lines, including their indentation.
    lines = text.split("\n")
    tokens = [] if inline else MarkdownIt("commonmark").parse(text)
    for token in tokens:
        if token.type in ("fence", "code_block", "html_block"):
            for pos in range(*token.map):
                line = lines[pos]
                if not line.strip():
                    continue
                prefix = re.match(r" *(?:[-+*] +)?" if pos == token.map[0] else r" *", line).group()
                lines[pos] = prefix + protect(line[len(prefix) :])
    text = "\n".join(lines)

    def code(match):
        marker, content = match.groups()
        # Old inline code uses two backticks. They can be shortened only if
        # the content does not itself contain backticks.
        if marker == "``" and "`" not in content and content.strip() == content:
            return protect(f"`{content}`")
        return protect(match.group())

    text = REGEX_CODE.sub(code, text)
    text = REGEX_MATH.sub(lambda match: protect(match.group()), text)
    text = re.sub(r"<[^>\n]+>", lambda match: protect(match.group()), text)
    text = re.sub(r"(?m)^ {0,3}\[[^\]\n]+\]:[^\n]+", lambda match: protect(match.group()), text)

    # Let the Markdown parser locate balanced and angle-bracket destinations.
    # Replacing only the destination keeps formatting in the label available.
    destinations = []
    for match in re.finditer(r"\]\(\s*", text):
        destination = parseLinkDestination(text, match.end(), len(text))
        if destination.ok:
            end = destination.pos
            title_start = end
            while title_start < len(text) and text[title_start].isspace():
                title_start += 1
            if title_start > end:
                title = parseLinkTitle(text, title_start, len(text))
                if title.ok:
                    end = title.pos
            destinations.append((match.end(), end))
    for start, end in reversed(destinations):
        text = text[:start] + protect(text[start:end]) + text[end:]

    text = REGEX_IMAGE.sub(lambda match: protect(_image_repl(match, restore)), text)
    text = REGEX_SIMPLE_IMAGE.sub(
        lambda match: protect(f"![]({escape_destination(restore(match.group(1)))})"), text
    )

    def link(label, destination):
        destination = restore(destination)
        if destination.startswith(("www.", "www2.", "www3.")):
            destination = "http://" + destination
        elif destination.startswith("ftp."):
            destination = "ftp://" + destination
        return protect(f"[{escape_label(label)}]({escape_destination(destination)})")

    text = REGEX_QUOTED_LINK.sub(lambda m: link(m.group(1), m.group(2)), text)
    text = REGEX_NAMED_LINK.sub(lambda m: link(m.group(1), m.group(2) + m.group(3)), text)
    # txt2tags unparsed spans display their contents without formatting.
    text = re.sub(
        r'""(.+?)""',
        lambda m: protect(_literal_text(restore(m.group(1)))),
        text,
    )
    text = REGEX_URL.sub(lambda match: protect(match.group()), text)
    # Preserve Markdown escapes, except the legacy end-of-line break marker.
    return re.sub(r"\\(?:[^\w\s\\]|_)", lambda match: protect(match.group()), text)


def _convert_tables(lines):
    result = []
    pos = 0
    while pos < len(lines):
        if not lines[pos].lstrip().startswith("|"):
            result.append(lines[pos])
            pos += 1
            continue
        end = pos + 1
        while end < len(lines) and lines[end].lstrip().startswith("|"):
            end += 1
        rows = lines[pos:end]
        # A separator row identifies an existing Markdown table.
        if len(rows) > 1 and re.fullmatch(r"[\s|:-]+", rows[1]) and "-" in rows[1]:
            result.extend(rows)
        else:
            cells = []
            for row in rows:
                row = row.strip()
                row = row[2:] if row.startswith("||") else row[1:]
                # Remove only the outer delimiter. Extra pipes reserve columns
                # for legacy spans, keeping following cells in their column.
                if row.endswith("|"):
                    row = row[:-1]
                cells.append(row.split("|"))
            columns = max(map(len, cells))
            for row in cells:
                row.extend([""] * (columns - len(row)))
            if result and result[-1].strip():
                result.append("")
            if rows[0].lstrip().startswith("||"):
                header = cells.pop(0)
            else:
                header = [""] * columns
            result.append("| " + " | ".join(cell.strip() for cell in header) + " |")
            result.append("| " + " | ".join(["---"] * columns) + " |")
            for row in cells:
                result.append("| " + " | ".join(cell.strip() for cell in row) + " |")
        pos = end
    return result


def convert_to_markdown(text, *, inline=False):
    """Convert legacy markup, optionally treating the input as an inline label."""
    # Mask literal regions before applying any legacy substitutions. Choose a
    # sentinel absent from the input, so restoring cannot alter journal text.
    sentinel = "\ue000"
    while sentinel in text:
        sentinel += "\ue000"
    protected = {}

    def protect(value):
        key = f"{sentinel}{len(protected)}{sentinel}"
        protected[key] = value
        return key

    def restore(value):
        # Later masks can contain earlier ones, such as code in a link label.
        for key, original in reversed(protected.items()):
            value = value.replace(key, original)
        return value

    text = _protect_literals(text, protect, restore, inline)
    if inline:
        return restore(_convert_inline(text))
    lines = []
    in_comment = False
    for line in text.split("\n"):
        if line.strip() == "%%%":
            in_comment = not in_comment
        elif not in_comment and not line.startswith("%"):
            lines.append(line)

    result = []
    heading_numbers = [0] * 5
    list_indents = []
    blank_lines = 0
    for line in _convert_tables(lines):
        heading = REGEX_HEADING.match(line)
        item = None if heading else REGEX_LIST.match(line)
        indent = len(line) - len(line.lstrip(" "))
        if item or line.strip():
            while list_indents and list_indents[-1][0] >= indent:
                list_indents.pop()
            extra_indent = sum(extra for _, extra in list_indents)
            line = " " * extra_indent + line
            if item:
                list_indents.append((indent, int(item.group(2) == "+")))
            blank_lines = 0
        else:
            blank_lines += 1
            if blank_lines >= 2:
                list_indents.clear()

        block = _convert_block(line, heading_numbers)
        if block is not None:
            # A "---" directly below a line of text would turn that line into
            # a setext heading, so make sure a blank line separates them.
            if block == "---" and result and result[-1].strip():
                result.append("")
            result.append(block)
        else:
            result.append(_convert_inline(line))
    return restore("\n".join(result))
