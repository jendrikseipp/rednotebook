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

"""Convert txt2tags markup to Markdown.

RedNotebook used txt2tags markup until it switched to Markdown. Journals and
templates written with txt2tags are converted once (see
rednotebook/util/migration.py). The conversion mirrors how txt2tags rendered
the text: txt2tags constructs are translated to Markdown and characters that
Markdown would interpret, but txt2tags displayed literally, are escaped.

The regular expressions below are taken from the txt2tags version that
RedNotebook bundled (txt2tags is Copyright (C) 2001-2010 Aurelio Jargas),
so that the converter recognizes exactly the same constructs.
"""

import logging
import re
import unicodedata
from collections import Counter

from rednotebook.data import HASHTAG
from rednotebook.util.markdownlinks import escape_destination


# --------------------------------------------------------------------------
# txt2tags syntax
# --------------------------------------------------------------------------

_URL_CHARS = r"A-Za-z0-9%._/~:,=$@&+-"
_URL_ANCHOR = r"A-Za-z0-9%._-"
_URL_FORM = r"A-Za-z0-9/%&=+:;.,$@*_-"
_URL_LOGIN = r"A-Za-z0-9_.-"
_PROTOCOL = r"(?:https?|ftp|news|telnet|gopher|wais)://"
_GUESS = r"(?:www[23]?|ftp)\."
_URL = (
    rf"\b(?:{_PROTOCOL}(?:[{_URL_LOGIN}]+(?::[^ @]*)?@)?|{_GUESS})"
    rf"[{_URL_CHARS}]+\b/*(?:\?[{_URL_FORM}]+)?(?:#[{_URL_ANCHOR}]*)?"
)
_EMAIL = rf"\b[{_URL_LOGIN}]+@(?:[A-Za-z0-9_-]+\.)+[A-Za-z]{{2,4}}\b(?:\?[{_URL_FORM}]+)?"
_LOCAL = rf"[{_URL_CHARS}]+|[{_URL_CHARS}]*(?:#[{_URL_ANCHOR}]*)"
_IMG_EXT = r"png|jpe?g|gif|eps|bmp|svg"
# RedNotebook allows an image width suffix: [picture.png?300].
_IMAGE = rf"\[([\w_,.+%$#@!?+~/-]+\.(?:{_IMG_EXT}))(?:\?(\d+))?\]"
_IMAGE_LABEL = rf"\[[\w_,.+%$#@!?+~/-]+\.(?:{_IMG_EXT})(?:\?\d+)?\]"

LINK = re.compile(rf"{_URL}|{_EMAIL}", re.I)
LINKMARK = re.compile(
    rf"\[(?P<label>{_IMAGE_LABEL}|[^\]]+) (?P<link>{_URL}|{_EMAIL}|{_LOCAL})\]", re.I
)
EMAIL = re.compile(_EMAIL, re.I)
URL = re.compile(_URL, re.I)
IMAGE = re.compile(_IMAGE, re.I)

BOLD = re.compile(r"\*\*([^\s](?:|.*?[^\s])\**)\*\*")
ITALIC = re.compile(r"//([^\s](?:|.*?[^\s])/*)//")
UNDERLINE = re.compile(r"__([^\s](?:|.*?[^\s])_*)__")
STRIKE = re.compile(r"--([^\s](?:|.*?[^\s])-*)--")
TAGGED = re.compile(r"''([^\s](?:|.*?[^\s])'*)''")
RAW = re.compile(r'""([^\s](?:|.*?[^\s])"*)""')
MONO = re.compile(r"``([^\s](?:|.*?[^\s])`*)``")

BLOCK_VERB = re.compile(r"^```\s*$")
BLOCK_RAW = re.compile(r'^"""\s*$')
BLOCK_TAGGED = re.compile(r"^'''\s*$")
BLOCK_COMMENT = re.compile(r"^%%%\s*$")
# Blocks whose content txt2tags doesn't parse, with their closing lines.
BLOCK_ENDS = {"comment": BLOCK_COMMENT, "tagged": BLOCK_TAGGED, "raw": BLOCK_RAW}
BLOCK_ENDS["verb"] = BLOCK_VERB
LINE_VERB = re.compile(r"^``` (?=.)")
LINE_RAW = re.compile(r'^""" (?=.)')
LINE_TAGGED = re.compile(r"^''' (?=.)")
QUOTE = re.compile(r"^\t+")
LIST_ITEM = re.compile(r"^( *)([-+]) (?=[^ ])|^( *)(:) (.*)$")
LIST_CLOSE = re.compile(r"^( *)([-+:])\s*$")
BAR = re.compile(r"^(\s*)([_=-]{20,})\s*$")
TABLE = re.compile(r"^ *\|([|_/])? ")
BLANK = re.compile(r"^\s*$")
TITLE = re.compile(r"^ *(?P<id>={1,5}|\+{1,5})(?P<txt>[^=+](?:|.*[^=+]))(?P=id)(?:\[[\w-]*\])?\s*$")
# Titles must not contain their own marker at the edges, e.g. "== a =" is text.
TITLE_EDGES = {"=": re.compile(r"^[^=](?:|.*[^=])$"), "+": re.compile(r"^[^+](?:|.*[^+])$")}

# RedNotebook extensions of txt2tags.
LINEBREAK = re.compile(r"\\\\\s*$")
COLOR = re.compile(r"\{([^{}|]+)\|color:([^{}]+)\}")
NAMED_ENTRY_REFERENCE = re.compile(
    r"\[(?P<name>[^\[\]\n]*[^\s\[\]])\s+(?P<date>\d{4}-\d{2}-\d{2})\s*\]"
)
ENTRY_REFERENCE = re.compile(r"\[(?P<date>\d{4}-\d{2}-\d{2})\]")
# Entry references as recognized by the Markdown renderer.
MARKDOWN_ENTRY_REFERENCE = re.compile(
    r"\[(?:(?P<name>[^\[\]\n]+?)\s+)?(?P<date>\d{4}-\d{2}-\d{2})\s*\]"
)
# Math is rendered by MathJax (HTML) and passed through to LaTeX.
MATH = re.compile(r"\\\(.+?\\\)|\\\[.+?\\\]|\$\$.+?\$\$")

LIST_MARKERS = {"-": "list", "+": "numlist", ":": "deflist"}
MARKDOWN_LIST_MARKERS = {"list": "-", "numlist": "1.", "deflist": "-"}

# --------------------------------------------------------------------------
# Markdown escaping
# --------------------------------------------------------------------------

ASCII_PUNCTUATION = set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
ENTITY = re.compile(r"&(?:#[0-9]{1,7}|#[xX][0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});")
HTML_START = re.compile(r"<[A-Za-z/!?]")

# Line starts that Markdown interprets as block structure.
BLOCK_STARTS = [
    re.compile(r"#{1,6}(?:[ \t]|$)"),
    re.compile(r">"),
    re.compile(r"[-+*](?:[ \t]|$)"),
    re.compile(r"\d{1,9}(?=[.)](?:[ \t]|$))"),
    re.compile(r"([-*_])(?:[ \t]*\1){2,}[ \t]*$"),
    re.compile(r"=+[ \t]*$"),
    re.compile(r"-+[ \t]*$"),
    re.compile(r"`{3,}|~{3,}"),
    re.compile(r"\[[^\]]*\]:"),
    re.compile(r"\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-*:?[ \t]*)+$"),
    # Display math whose closing delimiter isn't in the same paragraph.
    re.compile(r"\$\$[ \t]*$"),
]


def _is_whitespace(char):
    return char is None or char.isspace()


def _is_punctuation(char, symbols):
    if char in ASCII_PUNCTUATION:
        return True
    category = unicodedata.category(char)
    return category.startswith("P") or (symbols and category.startswith("S"))


def _flanking(prev, next_, symbols):
    """Return whether a delimiter run is left- and right-flanking."""
    prev_punct = prev is not None and _is_punctuation(prev, symbols)
    next_punct = next_ is not None and _is_punctuation(next_, symbols)
    left = not _is_whitespace(next_) and (not next_punct or _is_whitespace(prev) or prev_punct)
    right = not _is_whitespace(prev) and (not prev_punct or _is_whitespace(next_) or next_punct)
    return left, right, prev_punct, next_punct


def _can_open_or_close(char, prev, next_):
    """Return (can_open, can_close) for a run of char, erring on the side of True.

    Markdown parsers differ in whether Unicode symbols count as punctuation,
    so a run counts as a potential delimiter if either definition says so.
    """
    can_open = can_close = False
    for symbols in (False, True):
        left, right, prev_punct, next_punct = _flanking(prev, next_, symbols)
        if char == "_":
            can_open |= left and (not right or prev_punct)
            can_close |= right and (not left or next_punct)
        else:
            can_open |= left
            can_close |= right
    return can_open, can_close


def _escape_literal(text, prev, next_, *, table_cell=False, maximal=False, label=False):
    """Escape text that txt2tags displayed literally.

    prev and next_ are the characters directly before and after the text in
    the final Markdown (None at the line boundaries).
    """
    out = []
    pos = 0
    while pos < len(text):
        char = text[pos]
        following = text[pos + 1] if pos + 1 < len(text) else next_
        before = out[-1][-1] if out else prev
        if char == "\\":
            # Markdown only treats backslashes before punctuation specially.
            if following is None or following in ASCII_PUNCTUATION or maximal:
                out.append("\\\\")
            else:
                out.append(char)
        elif char in "*_~":
            end = pos
            while end < len(text) and text[end] == char:
                end += 1
            run = text[pos:end]
            after = text[end] if end < len(text) else next_
            if maximal or before == char or after == char:
                escape = True
            elif char == "~" and len(run) < 2:
                escape = False
            else:
                escape = any(_can_open_or_close(char, before, after))
            out.append("".join("\\" + c for c in run) if escape else run)
            pos = end
            continue
        elif char == "`":
            out.append("\\`")
        elif char == "<":
            out.append("\\<" if maximal or HTML_START.match(text, pos) else char)
        elif char == "&":
            out.append("\\&" if maximal or ENTITY.match(text, pos) else char)
        elif char in "([" and pos == 0 and prev == "]":
            # Keep "[2019-02-14](...)" an entry reference, not a Markdown link.
            out.append(f"&#{ord(char)};")
        elif char == "[":
            # Keep bracketed dates literal if txt2tags didn't link them. A
            # backslash escape would turn "\[" into a math delimiter.
            escape = maximal or label or MARKDOWN_ENTRY_REFERENCE.match(text, pos)
            out.append("&#91;" if escape else char)
        elif char == "]":
            # "](" and "][" would turn preceding brackets into a link.
            escape = maximal or label or following in ("(", "[")
            out.append("\\]" if escape else char)
        elif char == "|" and table_cell:
            out.append("\\|")
        elif maximal and char in ASCII_PUNCTUATION and char not in "#{}()":
            out.append("\\" + char)
        else:
            out.append(char)
        pos += 1
    return "".join(out)


def _escape_block_start(line, literal_prefix_length):
    """Escape a line start that Markdown would parse as block structure."""
    if not literal_prefix_length:
        return line
    for pattern in BLOCK_STARTS:
        match = pattern.match(line)
        if not match:
            continue
        # Escape the last digit's punctuation for ordered list markers,
        # otherwise the first character.
        pos = match.end() if pattern.pattern.startswith(r"\d") else 0
        if pos >= literal_prefix_length:
            return line
        if line[pos] == "[":
            # "\[" would start display math.
            return line[:pos] + "&#91;" + line[pos + 1 :]
        return line[:pos] + "\\" + line[pos:]
    return line


# --------------------------------------------------------------------------
# Inline conversion
# --------------------------------------------------------------------------


class _Piece:
    """A part of a converted line whose Markdown is known."""

    def __init__(self, kind, markdown="", **data):
        self.kind = kind
        self.markdown = markdown
        self.__dict__.update(data)


class _Line:
    """Mask the constructs of a single txt2tags line, like txt2tags does.

    Masked constructs are replaced by placeholders consisting of private-use
    characters. Raw text uses letters instead, because txt2tags allows it
    inside link and image targets.
    """

    def __init__(self, text, symbols):
        self.pieces = []
        self.open, self.close = symbols
        self.raw_prefix = "RnRaw"
        while self.raw_prefix in text:
            self.raw_prefix += "Q"
        self.raw_texts = []
        self.raw_pattern = re.compile(re.escape(self.raw_prefix) + r"(\d+)Z")
        self.placeholder = re.compile(re.escape(self.open) + r"(\d+)" + re.escape(self.close))

    def add(self, piece):
        self.pieces.append(piece)
        return f"{self.open}{len(self.pieces) - 1}{self.close}"

    def add_raw(self, text):
        self.raw_texts.append(text)
        return f"{self.raw_prefix}{len(self.raw_texts) - 1}Z"

    def restore_raw(self, text):
        return self.raw_pattern.sub(lambda match: self.raw_texts[int(match.group(1))], text)

    def unmask(self, text):
        """Return the original text for masked text, e.g. to show it verbatim."""
        text = self.placeholder.sub(lambda m: self.pieces[int(m.group(1))].original, text)
        return self.raw_pattern.sub(lambda m: f'""{self.raw_texts[int(m.group(1))]}""', text)


def _link_target_is_explicit(url, line):
    """Return whether a local txt2tags link target is really meant as a link.

    txt2tags turns any "[words word]" into a link to the file "word", which
    hid the last word of bracketed remarks like "[not sure]". Only keep
    targets that look like paths or file names.
    """
    return bool(
        line.raw_pattern.fullmatch(url)
        or "/" in url
        or re.search(r"\.[A-Za-z][A-Za-z0-9]{0,4}$", url)
    )


def _mask_math(text, line):
    def math(match):
        original = line.unmask(match.group())
        return line.add(_Piece("math", original, original=original))

    return MATH.sub(math, text)


def _mask(text, line, *, title=False, math=True):
    """Replace all constructs of a line that are not subject to formatting.

    Table rows mask math per cell (math=False), since txt2tags split cells
    before it would have seen any math.
    """

    # Entry references. txt2tags treats them as links with literal labels.
    def entry_reference(match):
        name = match.groupdict().get("name")
        piece = _Piece("entry", name=name, date=match.group("date"), original=match.group())
        return line.add(piece)

    text = NAMED_ENTRY_REFERENCE.sub(entry_reference, text)
    text = ENTRY_REFERENCE.sub(entry_reference, text)

    # RedNotebook colored hashtags before txt2tags saw the line, so their
    # text isn't formatted. Hashtags in URLs are part of the link.
    urls = [match.span() for match in LINK.finditer(text)]

    def hashtag(match):
        start = match.start(2)
        if any(url_start <= start < url_end for url_start, url_end in urls):
            return match.group()
        tag = match.group(2) + match.group(3)
        return match.group(1) + line.add(_Piece("hashtag", tag, original=tag))

    text = HASHTAG.sub(hashtag, text)

    # Colored text keeps its formatting, so only mask the markers.
    def color(match):
        closing = f"|color:{match.group(2)}}}"
        opening = line.add(_Piece("color", "{", original="{"))
        return opening + match.group(1) + line.add(_Piece("color", closing, original=closing))

    text = COLOR.sub(color, text)

    if title:
        return _mask_math(text, line)

    # The first of tagged, raw or monospace text wins, as in txt2tags.
    while True:
        matches = [
            match for match in (TAGGED.search(text), RAW.search(text), MONO.search(text)) if match
        ]
        if not matches:
            break
        match = min(matches, key=lambda m: m.start())
        content = line.unmask(match.group(1))
        original = line.unmask(match.group())
        if match.re is TAGGED:
            replacement = line.add(_Piece("tagged", content=content, original=original))
        elif match.re is RAW:
            replacement = line.add_raw(content)
        else:
            replacement = line.add(_Piece("code", content=content, original=original))
        text = text[: match.start()] + replacement + text[match.end() :]

    if math:
        text = _mask_math(text, line)

    # Links and e-mail addresses, again in order of appearance.
    skip = 0
    while True:
        plain = LINK.search(text)
        named = LINKMARK.search(text, skip)
        if not plain and not named:
            break
        match = named if named and (not plain or named.start() < plain.start()) else plain
        if match is plain:
            label, url, local = "", match.group(), False
        else:
            label, url = match.group("label").rstrip(), match.group("link")
            local = not (URL.fullmatch(url) or EMAIL.fullmatch(url))
            if local and not _link_target_is_explicit(url, line):
                skip = match.start() + 1
                continue
        original = line.unmask(match.group())
        replacement = line.add(_Piece("link", label=label, url=url, original=original))
        text = text[: match.start()] + replacement + text[match.end() :]
        if match is named:
            skip = match.start()
    return text


def _add_delimiters(line, kind, text):
    pair = len(line.pieces)
    opening = line.add(_Piece("delim", format=kind, side="open", pair=pair, original=""))
    closing = line.add(_Piece("delim", format=kind, side="close", pair=pair, original=""))
    return opening + text + closing


def _apply_formatting(text, line, original):
    """Replace txt2tags emphasis and images by placeholders."""
    formats = [("strong", BOLD), ("em", ITALIC), ("u", UNDERLINE), ("s", STRIKE)]
    for kind, pattern in formats:
        # txt2tags doesn't parse a horizontal bar as strikethrough.
        if kind == "s" and BAR.search(original):
            continue

        text = pattern.sub(
            lambda match, kind=kind: _add_delimiters(line, kind, match.group(1)), text
        )

    def image(match):
        piece = _Piece("image", path=match.group(1), width=match.group(2), original="")
        return line.add(piece)

    return IMAGE.sub(image, text)


_DELIMITERS = {"strong": "**", "em": "*", "s": "~~"}
# Schemes that Markdown's linkify recognizes without angle brackets.
_LINKIFY_SCHEMES = ("http://", "https://", "ftp://")


class _Renderer:
    """Render masked text and its pieces to Markdown."""

    def __init__(self, line, *, table_cell=False, parent=None):
        self.line = line
        self.table_cell = table_cell
        self.html_pairs = parent.html_pairs if parent else set()
        self.maximal = parent.maximal if parent else False
        self.autolinks = parent.autolinks if parent else False
        # Pieces rendered by this renderer and nested renderers.
        self.used = parent.used if parent else []
        self.literal_prefix = 0

    def _nested(self, text, *, label=False):
        renderer = _Renderer(self.line, table_cell=self.table_cell, parent=self)
        return renderer.render(text, label=label)

    def _split(self, text):
        items = []
        pos = 0
        for match in self.line.placeholder.finditer(text):
            if match.start() > pos:
                items.append(text[pos : match.start()])
            items.append(self.line.pieces[int(match.group(1))])
            pos = match.end()
        if pos < len(text):
            items.append(text[pos:])
        return items

    def _render_piece(self, piece, next_text):
        self.used.append(piece)
        kind = piece.kind
        if kind == "delim":
            if piece.format == "u" or piece.pair in self.html_pairs:
                return f"<{piece.format}>" if piece.side == "open" else f"</{piece.format}>"
            return _DELIMITERS[piece.format]
        if kind == "code":
            return _code_span(self.line.restore_raw(piece.content), self.table_cell)
        if kind == "tagged":
            return self._render_tagged(self.line.restore_raw(piece.content))
        if kind == "entry":
            if not piece.name:
                return f"[{piece.date}]"
            return f"[{self._nested(piece.name, label=True)} {piece.date}]"
        if kind == "link":
            return self._render_link(piece, next_text)
        if kind == "image":
            return self._render_image(piece.path, piece.width)
        if kind in ("color", "math") and self.table_cell:
            return piece.markdown.replace("|", "\\|")
        return piece.markdown

    def _render_tagged(self, content):
        # Tagged text is raw HTML. Keep its tags, but not Markdown syntax.
        parts = re.split(r"(<[^<>]*>|&[#\w]+;)", content)
        return "".join(
            part
            if index % 2
            else _escape_literal(part, None, None, table_cell=self.table_cell, maximal=True)
            for index, part in enumerate(parts)
        )

    def _render_image(self, path, width):
        path = self.line.restore_raw(path)
        suffix = f"?{width}" if width else ""
        return f"![]({escape_destination(path + suffix)})"

    def _render_link(self, piece, next_text):
        url = self.line.restore_raw(piece.url)
        is_email = bool(EMAIL.fullmatch(url))
        href = url
        if is_email:
            href = "mailto:" + url
        elif re.match(_GUESS, url, re.I):
            href = ("http://" if url[0] in "Ww" else "ftp://") + url
        if not piece.label:
            return self._render_bare_link(url, href, is_email, next_text)
        image = IMAGE.fullmatch(piece.label)
        if image:
            self.used.append(_Piece("image", original=""))
            label = self._render_image(image.group(1), image.group(2))
        else:
            label = self._nested(piece.label, label=True)
        return f"[{label}]({escape_destination(href)})"

    def _render_bare_link(self, url, href, is_email, next_text):
        # Linkify must end the link where txt2tags did.
        clean_end = (
            not next_text
            or next_text[0].isspace()
            or (next_text[0] in ".,;:!?\"'" and (len(next_text) < 2 or next_text[1].isspace()))
            or (next_text[0] == ")" and "(" not in url)
        )
        # "&copy" followed by ";" would become an entity.
        clean_end = clean_end and not (re.search(r"&\w+$", url) and next_text.startswith(";"))
        # Characters that Markdown might parse inside a bare URL.
        special = re.search(
            r"[*`\\\[\]<>]|~~|\$\$|&\w+;|(?<![A-Za-z0-9])[_#]|_(?![A-Za-z0-9])", url
        )
        bare_ok = not self.autolinks and clean_end and not special
        if re.search(r"[\s<>]", url):
            # Quoted txt2tags targets may contain spaces.
            label = _escape_literal(url, None, None, table_cell=self.table_cell, label=True)
            return f"[{label}]({escape_destination(href)})"
        if is_email:
            return url if bare_ok else f"<{url}>"
        if href != url:
            # Linkify guesses "http://" for "www." addresses, but not "ftp://".
            if bare_ok and href.startswith("http://"):
                return url
            label = _escape_literal(url, None, None, table_cell=self.table_cell, label=True)
            return f"[{label}]({escape_destination(href)})"
        if bare_ok and url.lower().startswith(_LINKIFY_SCHEMES):
            return url
        return f"<{url}>"

    def render(self, text, *, label=False):
        """Return the Markdown for masked text."""
        items = self._split(text)
        rendered = [None] * len(items)
        # Render pieces right to left, because bare links need the following text.
        next_text = ""
        for index in range(len(items) - 1, -1, -1):
            item = items[index]
            if isinstance(item, _Piece):
                rendered[index] = self._render_piece(item, next_text)
                next_text = (rendered[index] + next_text)[:2]
            else:
                next_text = (self.line.restore_raw(item) + next_text)[:2]
        out = []
        prev = None
        for index, item in enumerate(items):
            if isinstance(item, _Piece):
                markdown = rendered[index]
            else:
                following = next(
                    (rendered[i][0] for i in range(index + 1, len(items)) if rendered[i]),
                    None,
                )
                markdown = _escape_literal(
                    self.line.restore_raw(item),
                    prev,
                    following,
                    table_cell=self.table_cell,
                    maximal=self.maximal,
                    label=label,
                )
                if index == 0:
                    self.literal_prefix = len(markdown)
            if markdown:
                prev = markdown[-1]
            out.append(markdown)
        self.items = items
        self.rendered = out
        return "".join(out)


def _code_span(content, table_cell):
    if table_cell:
        content = content.replace("|", "\\|")
    longest = max((len(run) for run in re.findall(r"`+", content)), default=0)
    fence = "`" * (longest + 1)
    # Markdown strips one space from both ends, so add them if needed.
    if (
        content.startswith("`")
        or content.endswith("`")
        or (content.startswith(" ") and content.endswith(" ") and content.strip())
    ):
        content = f" {content} "
    return f"{fence}{content}{fence}"


def _delimiter_runs(renderer):
    """Yield (pieces, prev char, next char) for adjacent Markdown delimiters."""
    runs = []
    current = None
    position = 0
    for item, markdown in zip(renderer.items, renderer.rendered):
        start = position
        position += len(markdown)
        is_delimiter = (
            isinstance(item, _Piece) and item.kind == "delim" and markdown in _DELIMITERS.values()
        )
        if is_delimiter and current and current["end"] == start and current["char"] == markdown[0]:
            current["pieces"].append(item)
            current["end"] = position
        elif is_delimiter:
            current = {"pieces": [item], "start": start, "end": position, "char": markdown[0]}
            runs.append(current)
        elif markdown:
            current = None
    text = "".join(renderer.rendered)
    for run in runs:
        prev = text[run["start"] - 1] if run["start"] else None
        next_ = text[run["end"]] if run["end"] < len(text) else None
        yield run["pieces"], prev, next_


def _choose_delimiters(renderer, text):
    """Fall back to HTML tags for emphasis that Markdown wouldn't recognize."""
    for _ in range(len(renderer.line.pieces) + 1):
        del renderer.used[:]
        markdown = renderer.render(text)
        bad = []
        for pieces, prev, next_ in _delimiter_runs(renderer):
            sides = {piece.side for piece in pieces}
            flanks = [_flanking(prev, next_, symbols) for symbols in (False, True)]
            if sides == {"open", "close"}:
                bad += [piece for piece in pieces if piece.side == "open"]
            elif sides == {"open"} and not all(left for left, _, _, _ in flanks):
                bad += pieces
            elif sides == {"close"} and not all(right for _, right, _, _ in flanks):
                bad += pieces
        if not bad:
            break
        renderer.html_pairs.update(piece.pair for piece in bad)
    return markdown


_VALIDATOR = None
_COUNTED_TAGS = re.compile(r"<(/?)(strong|em|s|u)>")


def _count_tokens(markdown):
    global _VALIDATOR
    if _VALIDATOR is None:
        from rednotebook.util import markdownmarkup

        _VALIDATOR = markdownmarkup.get_parser("html")
    counts = Counter()

    def walk(tokens):
        for token in tokens:
            kind = {"link_open": "link", "math_inline_double": "math_inline"}.get(
                token.type, token.type
            )
            if kind == "html_inline":
                tag = _COUNTED_TAGS.fullmatch(token.content)
                kind = f"{tag.group(2)}_open" if tag and not tag.group(1) else None
            if kind:
                counts[kind] += 1
            if token.children:
                walk(token.children)

    walk(_VALIDATOR.parseInline(markdown))
    return counts


# Token types that each kind of piece produces.
_PIECE_TOKENS = {
    "code": "code_inline",
    "entry": "entry_reference",
    "image": "image",
    "link": "link",
    "math": "math_inline",
}


def _expected_counts(pieces):
    counts = Counter()
    for piece in pieces:
        if piece.kind == "delim" and piece.side == "open":
            counts[f"{piece.format}_open"] += 1
        elif piece.kind in _PIECE_TOKENS:
            counts[_PIECE_TOKENS[piece.kind]] += 1
        elif piece.kind == "tagged":
            for tag in _COUNTED_TAGS.finditer(piece.content):
                if not tag.group(1):
                    counts[f"{tag.group(2)}_open"] += 1
    return counts


_CHECKED = (
    "strong_open",
    "em_open",
    "s_open",
    "u_open",
    "code_inline",
    "image",
    "entry_reference",
    "math_inline",
)


def _is_consistent(pieces, markdown):
    expected = _expected_counts(pieces)
    actual = _count_tokens(markdown)
    # Linkify may add links for plain domain names, which is fine.
    if actual["link"] < expected["link"]:
        return False
    return all(actual[kind] == expected[kind] for kind in _CHECKED)


def _render_line(text, line, original, *, table_cell=False, formatting=True):
    """Return the Markdown for masked text and the length of its literal prefix."""
    if formatting:
        text = _apply_formatting(text, line, original)
    renderer = _Renderer(line, table_cell=table_cell)
    markdown = _choose_delimiters(renderer, text)
    if renderer.used or markdown != line.restore_raw(text):
        if not _is_consistent(renderer.used, markdown):
            renderer.html_pairs.update(p.pair for p in renderer.used if p.kind == "delim")
            renderer.maximal = renderer.autolinks = True
            del renderer.used[:]
            markdown = renderer.render(text)
            if not _is_consistent(renderer.used, markdown):
                logging.warning(f"Markdown conversion may be inexact for {original!r}")
    return markdown, renderer.literal_prefix


def _symbols(text):
    for base in range(0xE000, 0xF800, 0x10):
        opening, closing = chr(base), chr(base + 1)
        if opening not in text and closing not in text:
            return opening, closing
    raise ValueError("text uses all private-use characters")


def convert_inline(text):
    """Convert a single line of txt2tags markup, e.g. a tag name."""
    line = _Line(text, _symbols(text))
    text = LINEBREAK.sub("", text).strip()
    return _render_line(_mask(text, line), line, text)[0]


def _convert_text_line(text):
    """Convert a line of paragraph text and escape Markdown block syntax."""
    hard_break = bool(LINEBREAK.search(text))
    text = LINEBREAK.sub("", text).strip()
    line = _Line(text, _symbols(text))
    markdown, prefix = _render_line(_mask(text, line), line, text)
    markdown = _fix_entry_reference_start(_escape_block_start(markdown, prefix))
    markdown = _preserve_hashtags(text, markdown)
    return markdown + ("  " if hard_break and markdown else "")


def _fix_entry_reference_start(markdown):
    # "[2019-02-14]: done" would be a Markdown link reference definition.
    match = MARKDOWN_ENTRY_REFERENCE.match(markdown)
    if match and markdown[match.end() : match.end() + 1] == ":":
        return markdown[: match.end()] + "&#58;" + markdown[match.end() + 1 :]
    return markdown


def _hashtags(text):
    return [match.group(3).lower() for match in HASHTAG.finditer(text)]


def _preserve_hashtags(original, markdown):
    """Make sure the Markdown has the same hashtags as the txt2tags text.

    RedNotebook indexes hashtags with a regular expression on the text, so
    converted markup next to a "#" must not create or remove tags.
    """
    wanted = Counter(_hashtags(original))
    for _ in range(len(markdown) + 1):
        found = list(HASHTAG.finditer(markdown))
        have = Counter(match.group(3).lower() for match in found)
        if have == wanted:
            return markdown
        extra = have - wanted
        for match in reversed(found):
            tag = match.group(3).lower()
            if extra[tag]:
                extra[tag] -= 1
                start = match.start(2)
                markdown = markdown[:start] + "&#35;" + markdown[start + 1 :]
                break
        else:
            missing = wanted - have
            starts = {match.start(2) for match in found}
            for pos, char in enumerate(markdown):
                rest = markdown[pos + 1 :].lower()
                if char in "#\uff03" and pos not in starts and pos > 0:
                    if any(rest.startswith(tag) for tag in missing):
                        markdown = markdown[:pos] + "<!---->" + markdown[pos:]
                        break
            else:
                break
    logging.warning(f"Could not preserve the hashtags of {original!r}")
    return markdown


def _convert_literal_line(text):
    """Convert a line of txt2tags raw text, which is shown unformatted."""
    markdown = _escape_literal(text.strip(), None, None)
    markdown = _fix_entry_reference_start(_escape_block_start(markdown, len(markdown)))
    return _preserve_hashtags(text, markdown)


def _convert_title(text):
    line = _Line(text, _symbols(text))
    markdown = _render_line(_mask(text, line, title=True), line, text, formatting=False)[0]
    # A trailing "#" sequence would be removed as closing sequence.
    markdown = re.sub(r"(\s)(#+)$", lambda m: m.group(1) + "\\" + m.group(2), markdown)
    return _preserve_hashtags(text, markdown)


# --------------------------------------------------------------------------
# Block conversion
# --------------------------------------------------------------------------


def _is_paragraph_line(line):
    """Return whether txt2tags would add the line to the current paragraph."""
    if not line.strip() or line.startswith(("%", "\t")):
        return False
    patterns = [BLOCK_VERB, BLOCK_RAW, BLOCK_TAGGED, BLOCK_COMMENT, LINE_VERB, LINE_RAW]
    patterns += [LINE_TAGGED, LIST_ITEM, LIST_CLOSE, BAR, TABLE, TITLE]
    return not any(pattern.search(line) for pattern in patterns)


class _List:
    def __init__(self, kind, indent, column):
        self.kind = kind
        self.indent = indent
        self.column = column
        self.content = column + len(MARKDOWN_LIST_MARKERS[kind]) + 1


class _Converter:
    """Convert txt2tags text line by line, following txt2tags' block logic."""

    def __init__(self):
        self.out = []
        self.lists = []
        self.quote = 0
        self.para = False
        self.table = None
        self.last_blank = False
        self.comments = []
        self.title_numbers = [0] * 6
        # A blank line inside a list separates paragraphs of the item.
        self.item_break = False
        # Text after a closed sublist starts a new paragraph of the parent item.
        self.after_sublist = False
        # Marker column of the most recently closed list.
        self.closed_list_column = None
        self.block = None
        self.block_lines = []

    # -- output helpers -------------------------------------------------

    def emit(self, line):
        self.out.append(line)
        if line.strip():
            self.closed_list_column = None

    def blank(self):
        if self.out and self.out[-1] != "":
            self.out.append("")

    def container_indent(self):
        return " " * self.lists[-1].content if self.lists else ""

    def quote_prefix(self, depth=None):
        return "> " * (self.quote if depth is None else depth)

    def start_top_level_block(self):
        self.flush_comments()
        self.blank()

    def flush_comments(self):
        if not self.comments:
            return
        indent = self.container_indent()
        if self.item_break or not self.lists:
            self.blank()
        comments = [comment.replace("-->", "-- >") for comment in self.comments]
        if len(comments) == 1 and "\n" not in comments[0]:
            self.emit(f"{indent}<!-- {comments[0].strip()} -->")
        else:
            self.emit(f"{indent}<!--")
            for comment in "\n".join(comments).split("\n"):
                self.emit(f"{indent}{comment}".rstrip())
            self.emit(f"{indent}-->")
        self.comments = []

    # -- closing blocks -------------------------------------------------

    def close_para(self):
        self.para = False

    def close_table(self):
        if self.table is None:
            return
        rows, self.table = self.table, None
        self.start_top_level_block()
        columns = max(sum(cell["span"] for cell in row["cells"]) for row in rows)
        header = rows.pop(0) if rows[0]["title"] else None

        def markdown_row(row):
            cells = []
            for cell in row["cells"]:
                cells.append(cell["markdown"])
                cells.extend([""] * (cell["span"] - 1))
            cells.extend([""] * (columns - len(cells)))
            return "| " + " | ".join(cells) + " |"

        alignments = []
        for cell in (header or rows[0])["cells"]:
            alignments.extend([cell["align"]] + ["left"] * (cell["span"] - 1))
        alignments.extend(["left"] * (columns - len(alignments)))
        delimiters = {"left": "---", "center": ":---:", "right": "---:"}
        self.emit(markdown_row(header) if header else "|" + "  |" * columns)
        self.emit("| " + " | ".join(delimiters[align] for align in alignments) + " |")
        for row in rows:
            self.emit(markdown_row(row))
        self.blank()

    def close_quotes(self):
        if self.quote:
            self.quote = 0
            self.flush_comments()

    def close_list(self):
        closed = self.lists.pop()
        self.item_break = False
        self.after_sublist = bool(self.lists)
        self.closed_list_column = closed.column

    def close_lists(self):
        while self.lists:
            self.close_list()
        self.after_sublist = False

    def close_all(self):
        self.close_para()
        self.close_table()
        self.close_quotes()
        self.close_lists()

    # -- blocks ---------------------------------------------------------

    def open_list(self, kind, indent):
        if self.lists:
            column = self.lists[-1].content
        else:
            self.close_para()
            self.start_top_level_block()
            column = 0
        if self.closed_list_column == column:
            # Separate the lists, otherwise Markdown would join them.
            self.emit(" " * column + "<!-- -->")
        self.lists.append(_List(kind, indent, column))

    def list_item(self, indent, marker, content):
        self.flush_comments()
        kind = LIST_MARKERS[marker]
        current_indent = self.lists[-1].indent if self.lists else 0
        if self.lists and kind != self.lists[-1].kind and indent == current_indent:
            self.close_list()
            current_indent = self.lists[-1].indent if self.lists else 0
        if not self.lists or indent > current_indent:
            self.open_list(kind, indent)
        while self.lists and indent < self.lists[-1].indent:
            self.close_list()
        if not self.lists:
            self.open_list(kind, indent)
        if self.item_break:
            self.blank()
        self.item_break = False
        self.after_sublist = False
        current = self.lists[-1]
        marker = MARKDOWN_LIST_MARKERS[current.kind]
        self.emit(
            f"{' ' * current.column}{marker} {content}"
            if content
            else f"{' ' * current.column}{marker}"
        )

    def text(self, markdown):
        """Add a line of text to the current paragraph, list item or quote."""
        if not markdown:
            return
        if self.lists:
            if self.item_break or self.after_sublist:
                self.flush_comments()
                self.blank()
                self.item_break = self.after_sublist = False
            self.emit(self.container_indent() + markdown)
        elif self.quote:
            self.emit(self.quote_prefix() + markdown)
        else:
            if not self.para:
                self.start_top_level_block()
                self.para = True
            self.emit(markdown)

    def fence(self, lines, info=""):
        longest = max(
            (len(m.group(1)) for line in lines if (m := re.match(r"\s*(`+)", line))),
            default=0,
        )
        fence = "`" * max(3, longest + 1)
        if self.lists:
            if self.item_break or self.after_sublist:
                self.blank()
                self.item_break = self.after_sublist = False
            prefix = self.container_indent()
        elif self.quote:
            prefix = self.quote_prefix()
        else:
            self.close_para()
            self.start_top_level_block()
            prefix = ""
        self.emit(prefix + fence + info)
        for line in lines:
            self.emit((prefix + line) if line.strip() else prefix.rstrip())
        self.emit(prefix + fence)
        if not self.lists and not self.quote:
            self.blank()

    def raw_lines(self, lines):
        self.close_table()
        top_level = not (self.lists or self.quote or self.para)
        for line in lines:
            if line.strip():
                self.text(_convert_literal_line(line))
        if top_level:
            # Raw text isn't part of a paragraph in txt2tags.
            self.close_para()

    def verbatim(self, lines):
        self.close_para()
        self.close_table()
        self.close_quotes()
        self.flush_comments()
        self.fence(lines)

    def tagged(self, lines):
        self.close_table()
        self.flush_comments()
        self.fence(lines, "rednotebook-raw")

    def title(self, match):
        self.close_all()
        self.start_top_level_block()
        marker = match.group("id")
        level = len(marker)
        text = match.group("txt").strip()
        if marker.startswith("+"):
            self.title_numbers[level] += 1
            self.title_numbers[level + 1 :] = [0] * (len(self.title_numbers) - level - 1)
            numbers = ".".join(str(n) for n in self.title_numbers[1 : level + 1])
            text = f"{numbers}. {text}"
        self.emit("#" * level + " " + _convert_title(text))
        self.blank()

    def bar(self, in_quote):
        if in_quote:
            self.emit(self.quote_prefix().rstrip())
            self.emit(self.quote_prefix() + "---")
            return
        self.close_all()
        self.start_top_level_block()
        self.emit("---")
        self.blank()

    def quote_line(self, depth, content):
        if not self.quote:
            self.close_para()
            self.close_table()
            self.close_lists()
            self.start_top_level_block()
        elif depth < self.quote:
            # Leave the nested quote before continuing the outer one.
            self.emit(self.quote_prefix(depth).rstrip())
        self.quote = depth
        if content is None:
            return
        self.emit(self.quote_prefix() + content)

    def table_row(self, masked, masking, original):
        if self.table is None:
            self.close_para()
            self.close_quotes()
            self.close_lists()
            self.table = []
        row = masked.lstrip()
        title = row[1:2] == "|"
        if re.search(r" (\|+) *$", row):
            row += " "
        else:
            row += " | "
        row = TABLE.sub("", row, count=1)
        row = re.sub(r" (\|+)\| ", "\a\\1 | ", row)
        cells = []
        for cell in row.split(" | ")[:-1]:
            span_match = re.search(r"\a(\|+)$", cell)
            span = len(span_match.group(1)) + 1 if span_match else 1
            cell = re.sub(r"\a\|+$", "", cell)
            align = "left"
            if cell.strip():
                if cell[0] == " " and cell[-1] == " ":
                    align = "center"
                elif cell[0] == " ":
                    align = "right"
            content = _mask_math(cell.strip(), masking)
            if title and self.table and content:
                # Only the first row can be a Markdown header, so emphasize others.
                content = _add_delimiters(masking, "strong", content)
            markdown = _render_line(content, masking, original, table_cell=True)[0]
            markdown = _preserve_hashtags(masking.unmask(cell), markdown)
            cells.append({"markdown": markdown, "span": span, "align": align})
        self.table.append({"cells": cells, "title": title})

    # -- main loop ------------------------------------------------------

    def run(self, text):
        lines = text.replace("\r\n", "\n").split("\n")
        index = 0
        while index < len(lines):
            line = lines[index].rstrip("\r")
            index += 1
            index = self.line(line, lines, index)
        self.finish()
        while self.out and not self.out[-1].strip():
            self.out.pop()
        while self.out and not self.out[0].strip():
            self.out.pop(0)
        return "\n".join(self.out)

    def end_block(self):
        block, content = self.block, self.block_lines
        self.block, self.block_lines = None, []
        if block == "comment":
            self.comments.append("\n".join(content))
        elif block == "tagged":
            self.tagged(content)
        elif block == "raw":
            self.raw_lines(content)
        elif block == "verb":
            self.verbatim(content)

    def finish(self):
        # txt2tags closes all blocks at the end of the text.
        self.end_block()
        self.close_all()
        self.flush_comments()

    def line(self, line, lines, index):
        if self.block:
            if BLOCK_ENDS[self.block].search(line):
                self.end_block()
            else:
                self.block_lines.append(line)
            return index

        for name, opening, one_line in [
            ("comment", BLOCK_COMMENT, None),
            ("tagged", BLOCK_TAGGED, LINE_TAGGED),
            ("raw", BLOCK_RAW, LINE_RAW),
            ("verb", BLOCK_VERB, LINE_VERB),
        ]:
            if opening.search(line):
                if name == "verb":
                    self.last_blank = False
                self.block = name
                self.block_lines = []
                return index
            if one_line and one_line.search(line):
                content = [one_line.sub("", line)]
                if name == "tagged":
                    self.tagged(content)
                elif name == "raw":
                    self.raw_lines(content)
                else:
                    self.last_blank = False
                    self.verbatim(content)
                return index

        if BLANK.search(line):
            self.flush_comments()
            if self.para:
                self.close_para()
                self.last_blank = True
                return index
            if self.table is not None:
                self.close_table()
                self.last_blank = True
                return index
            self.close_quotes()
            if self.last_blank:
                self.close_lists()
                return index
            if self.lists:
                self.item_break = True
            self.last_blank = True
            return index

        if line.startswith("%"):
            # Comments (and txt2tags settings) stay hidden in HTML comments.
            self.comments.append(line[1:])
            return index

        self.last_blank = False
        is_quote = bool(QUOTE.search(line))
        if self.quote and not is_quote:
            self.close_quotes()
        if self.table is not None and not TABLE.search(line):
            self.close_table()

        if BAR.search(line):
            if not (self.quote or is_quote):
                self.bar(in_quote=False)
                return index

        title = TITLE.search(line)
        if title and not self.lists and TITLE_EDGES[title.group("id")[0]].match(title.group("txt")):
            self.title(title)
            return index

        if is_quote:
            depth = len(QUOTE.search(line).group())
            content = line[depth:]
            if BAR.search(content):
                self.quote_line(depth, None)
                self.bar(in_quote=True)
                return index
            math_lines, index = self.math_block(content, lines, index)
            if math_lines:
                self.quote_line(depth, math_lines[0])
                for math_line in math_lines[1:]:
                    self.emit(self.quote_prefix() + math_line)
                return index
            self.quote_line(depth, _convert_text_line(content))
            return index

        if self.lists:
            close = LIST_CLOSE.match(line)
            if close:
                current = self.lists[-1]
                if (
                    len(close.group(1)) == current.indent
                    and LIST_MARKERS[close.group(2)] == current.kind
                ):
                    self.close_list()
                    return index

        text = LINEBREAK.sub("", line)
        masking = _Line(text, _symbols(text))
        masked = _mask(text, masking, math=False)
        if TABLE.search(masked):
            self.table_row(masked, masking, line)
            return index
        masked = _mask_math(masked, masking)
        item = LIST_ITEM.match(masked)
        if item:
            if item.group(2):
                indent, marker, content = len(item.group(1)), item.group(2), masked[item.end() :]
            else:
                indent, marker, content = len(item.group(3)), ":", item.group(5)
            markdown = self.item_content(content, masking, line)
            self.list_item(indent, marker, markdown)
            return index

        math_lines, index = self.math_block(line, lines, index)
        if math_lines:
            for math_line in math_lines:
                self.text(math_line)
            return index
        self.text(_convert_text_line(line))
        return index

    def item_content(self, content, line, original):
        hard_break = bool(LINEBREAK.search(original))
        markdown, prefix = _render_line(content.strip(), line, original)
        markdown = _fix_entry_reference_start(_escape_block_start(markdown, prefix))
        markdown = _preserve_hashtags(original, markdown)
        return markdown + ("  " if hard_break and markdown else "")

    def math_block(self, line, lines, index):
        """Return display math that spans several lines, which MathJax rendered."""
        stripped = line.strip()
        for opening, closing in (("$$", "$$"), ("\\[", "\\]")):
            if not stripped.startswith(opening) or closing in stripped[len(opening) :]:
                continue
            end = index
            while end < len(lines) and _is_paragraph_line(lines[end]):
                if lines[end].rstrip().endswith(closing):
                    group = [stripped] + [lines[i].strip() for i in range(index, end + 1)]
                    return group, end + 1
                end += 1
        return None, index


def convert_to_markdown(text, *, inline=False):
    """Convert txt2tags markup to Markdown that renders the same way.

    With inline=True, text is treated as a single line, e.g. a tag name.
    """
    if inline:
        return convert_inline(text)
    return _Converter().run(text)
