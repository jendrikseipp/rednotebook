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

"""Render Markdown to HTML, LaTeX and plain text.

This module wraps `markdown-it-py <https://github.com/executablebooks/
markdown-it-py>`_ and adds the RedNotebook specific constructs that have no
standard Markdown equivalent:

* ``#hashtags`` are coloured (and indexed in LaTeX),
* ``{text|color:value}`` colours arbitrary text,
* image links may carry a ``?width`` suffix, and
* ``$$...$$``, ``\\[...\\]`` and ``\\(...\\)`` math is rendered for
  MathJax/LaTeX. A single ``$`` is plain text, since it is mostly used for
  prices.
"""

import re
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
from markdown_it.common.normalize_url import validateLink
from markdown_it.common.utils import escapeHtml
from markdown_it.renderer import RendererHTML
from markdown_it.token import Token


CSS = """\
<style type="text/css">
    :root {
        color-scheme: light dark;
        --fgcolor: %(fgcolor)s;
        --bgcolor: %(bgcolor)s;
        --dark-link-color: rgb(0, 188, 212);
        --light-link-color: rgb(0, 0, 238);
    }
    a { color: var(--light-link-color); }
    body {
        font-family: %(font)s;
        background: var(--bgcolor);
        color: var(--fgcolor);
    }
    p {
        page-break-inside: avoid;
    }
    blockquote {
        margin: 1em 2em;
        border-left: 2px solid #999;
        font-style: oblique;
        padding-left: 1em;
    }
    table {
        border-collapse: collapse;
    }
    td, th {
        padding: 3px 7px 2px 7px;
    }
    th {
        text-align: left;
        padding-top: 5px;
        padding-bottom: 4px;
        background-color: #aaa;
        color: #ffffff;
    }
    img {
        max-width: 100%%;
    }
    @media (prefers-color-scheme: dark) {
        a { color: var(--dark-link-color); }
    }
</style>
"""

MATHJAX_FILE = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"
MATHJAX = f"""\
<!--MathJax included-->
<script type="text/javascript" src="{MATHJAX_FILE}"></script>
"""

# A #hashtag must contain at least one letter and must not be a hex colour or
# a C preprocessor directive. This mirrors rednotebook.data.HASHTAG.
HASHTAG_BODY = re.compile(
    r"(?![0-9a-fA-F]{6}\b|include\b|define\b|ifdef\b|ifndef\b|endif\b)(\w*[^\W\d_]+\w*)"
)
FULLWIDTH_HASHTAG = re.compile(r"(^|[^\w&#])(\uff03" + HASHTAG_BODY.pattern + ")")
# Inside table cells, the "|" has to be escaped.
COLOR = re.compile(r"\{([^{}|]+)\\?\|color:([^{}]+)\}")
IMAGE_WIDTH = re.compile(r"\?(\d+)$")
ENTRY_REFERENCE = re.compile(r"\[(?:(?P<name>[^\[\]\n]+?)\s+)?(?P<date>\d{4}-\d{2}-\d{2})\s*\]")


# --------------------------------------------------------------------------
# Inline plugins
# --------------------------------------------------------------------------


def _hashtag_rule(state, silent):
    pos = state.pos
    if state.src[pos] not in "#＃":
        return False
    if pos > 0:
        prev = state.src[pos - 1]
        if prev.isalnum() or prev == "_" or prev in "&#":
            return False
    match = HASHTAG_BODY.match(state.src, pos + 1)
    if not match:
        return False
    if not silent:
        token = state.push("hashtag", "", 0)
        token.content = state.src[pos : match.end()]
        token.meta = {"tag": match.group(1)}
    state.pos = match.end()
    return True


def _parse_children(state, text):
    children = []
    state.md.inline.parse(text, state.md, state.env, children)
    # Newer markdown-it versions only merge escaped characters into text
    # tokens at the top level.
    for child in children:
        if child.type == "text_special":
            child.type = "text"
    return children


def _color_rule(state, silent):
    if state.src[state.pos] != "{":
        return False
    match = COLOR.match(state.src, state.pos)
    if not match:
        return False
    if not silent:
        token = state.push("rn_color", "", 0)
        token.meta = {"text": match.group(1), "color": match.group(2)}
        token.children = _parse_children(state, match.group(1))
    state.pos = match.end()
    return True


def _fullwidth_hashtags(state):
    """Split text tokens at fullwidth hashtags, which the inline parser skips."""
    for block in state.tokens:
        if block.type != "inline" or "\uff03" not in block.content:
            continue
        children = []
        for token in block.children:
            if token.type != "text" or "\uff03" not in token.content:
                children.append(token)
                continue
            text = token.content
            pos = 0
            for match in FULLWIDTH_HASHTAG.finditer(text):
                start = match.start(2)
                if start > pos:
                    children.append(_text_token(text[pos:start]))
                hashtag = Token("hashtag", "", 0)
                hashtag.content = text[start : match.end()]
                hashtag.meta = {"tag": match.group(3)}
                children.append(hashtag)
                pos = match.end()
            if pos < len(text):
                children.append(_text_token(text[pos:]))
        block.children = children


def _text_token(content):
    token = Token("text", "", 0)
    token.content = content
    return token


def _entry_reference_rule(state, silent):
    # Markdown probes labels in silent mode to reject nested links. Let it
    # finish recognizing an outer link before considering date references.
    if silent:
        return False
    match = ENTRY_REFERENCE.match(state.src, state.pos, state.posMax)
    if not match:
        return False
    # A reference inside a Markdown link label must not create a nested link.
    if sum(token.nesting for token in state.tokens if token.tag == "a"):
        return False
    token = state.push("entry_reference", "", 0)
    token.content = match.group("name") or match.group("date")
    token.meta = {"date": match.group("date"), "named": bool(match.group("name"))}
    # Keep label formatting while preventing nested autolinks.
    token.children = [child for child in _parse_children(state, token.content) if child.tag != "a"]
    state.pos = match.end()
    return True


_MATH_DELIMITERS = {"$$": "$$", "\\(": "\\)", "\\[": "\\]"}


def _math_inline_rule(state, silent):
    opening = state.src[state.pos : state.pos + 2]
    closing = _MATH_DELIMITERS.get(opening)
    if closing is None:
        return False
    end = state.src.find(closing, state.pos + 2, state.posMax)
    if end <= state.pos + 2:
        return False
    if not silent:
        kind = "math_inline" if opening == "\\(" else "math_inline_double"
        token = state.push(kind, "math", 0)
        token.content = state.src[state.pos + 2 : end]
        token.markup = opening
    state.pos = end + 2
    return True


def _math_block_rule(state, start_line, end_line, silent):
    """Parse display math that starts a line and ends at the end of a line.

    Blank lines are only allowed if the delimiters are on lines of their own.
    """
    if state.sCount[start_line] - state.blkIndent >= 4:
        return False
    start = state.bMarks[start_line] + state.tShift[start_line]
    opening = state.src[start : start + 2]
    if opening not in ("$$", "\\["):
        return False
    closing = _MATH_DELIMITERS[opening]
    first_line = state.src[start : state.eMarks[start_line]].rstrip()
    allow_blank_lines = first_line == opening
    for line in range(start_line, end_line):
        line_start = state.bMarks[line] + state.tShift[line]
        text = state.src[line_start : state.eMarks[line]].rstrip()
        if not text:
            if allow_blank_lines:
                continue
            return False
        if line == start_line:
            text = text[2:]
        if not text.endswith(closing):
            continue
        if silent:
            return True
        content = state.getLines(start_line, line + 1, state.blkIndent, False).strip()
        token = state.push("math_block", "math", 0)
        token.block = True
        token.content = content[2:-2].strip("\n")
        token.markup = opening
        token.map = [start_line, line + 1]
        state.line = line + 1
        return True
    return False


def _rednotebook_plugin(md):
    md.inline.ruler.before("emphasis", "hashtag", _hashtag_rule)
    md.inline.ruler.before("emphasis", "rn_color", _color_rule)
    # Standard Markdown links take precedence over journal date references.
    md.inline.ruler.after("link", "entry_reference", _entry_reference_rule)
    md.inline.ruler.before("escape", "math", _math_inline_rule)
    md.block.ruler.before(
        "fence",
        "math",
        _math_block_rule,
        {"alt": ["paragraph", "reference", "blockquote", "list"]},
    )
    md.core.ruler.push("fullwidth_hashtags", _fullwidth_hashtags)


# --------------------------------------------------------------------------
# HTML renderer
# --------------------------------------------------------------------------


class HtmlRenderer(RendererHTML):
    def paragraph_open(self, tokens, idx, options, env):
        # Flow paragraphs from right to left or left to right depending on the
        # language of their text.
        tokens[idx].attrSet("dir", "auto")
        return self.renderToken(tokens, idx, options, env)

    def fence(self, tokens, idx, options, env):
        if tokens[idx].info.strip() == "rednotebook-raw":
            return tokens[idx].content
        return super().fence(tokens, idx, options, env)

    def entry_reference(self, tokens, idx, options, env):
        token = tokens[idx]
        label = self.renderInline(token.children, options, env)
        return f'<a href="#{token.meta["date"]}">{label}</a>'

    def hashtag(self, tokens, idx, options, env):
        return f'<span style="color:red">{escapeHtml(tokens[idx].content)}</span>'

    def rn_color(self, tokens, idx, options, env):
        token = tokens[idx]
        text = self.renderInline(token.children, options, env)
        return f'<span style="color:{escapeHtml(token.meta["color"])}">{text}</span>'

    def image(self, tokens, idx, options, env):
        token = tokens[idx]
        src = token.attrs.get("src", "")
        width = ""
        match = IMAGE_WIDTH.search(src)
        if match:
            width = f' width="{match.group(1)}"'
            src = src[: match.start()]
        alt = escapeHtml(_get_inline_text(token))
        title = token.attrs.get("title")
        title_attr = f' title="{escapeHtml(title)}"' if title is not None else ""
        return f'<img src="{escapeHtml(src)}"{width} alt="{alt}"{title_attr}>'

    def math_inline(self, tokens, idx, options, env):
        return f"\\({escapeHtml(tokens[idx].content)}\\)"

    def math_inline_double(self, tokens, idx, options, env):
        return f"$${escapeHtml(tokens[idx].content)}$$"

    def math_block(self, tokens, idx, options, env):
        return f"$$\n{escapeHtml(tokens[idx].content)}\n$$\n"

    def text_special(self, tokens, idx, options, env):
        return escapeHtml(tokens[idx].content)


# --------------------------------------------------------------------------
# Token-walking renderers for LaTeX and plain text
# --------------------------------------------------------------------------

_HEADING_TO_TEX = {
    "h1": "section",
    "h2": "subsection",
    "h3": "subsubsection",
    "h4": "paragraph",
    "h5": "subparagraph",
    "h6": "subparagraph",
}

_TEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_TEX_ESCAPE_RE = re.compile("|".join(re.escape(key) for key in _TEX_ESCAPES))


_HTML_TO_TEX = {
    "u": "uline",
    "b": "textbf",
    "strong": "textbf",
    "i": "textit",
    "em": "textit",
    "s": "sout",
    "del": "sout",
}
_TEX_HTML_TAG = re.compile(r"<(/?)(" + "|".join(_HTML_TO_TEX) + r")>")


def tex_escape(text):
    return _TEX_ESCAPE_RE.sub(lambda m: _TEX_ESCAPES[m.group()], text)


def _file_uri_path(uri):
    parts = urlsplit(uri)
    path = unquote(parts.path)
    if parts.netloc:
        path = f"//{parts.netloc}{path}"
    # A Windows drive letter is not preceded by a slash in a filesystem path.
    return path[1:] if re.match(r"^/[A-Za-z]:/", path) else path


def _tex_local_link_path(path):
    # Hyperref loads ltxcmds, whose character macros expand without adding
    # backslashes to the filename. Delay them until after hyperref splits off
    # URL fragments, otherwise a literal filename '#' becomes a fragment.
    characters = {
        "#": "hashchar",
        "%": "percentchar",
        "{": "leftbracechar",
        "}": "rightbracechar",
        "\\": "backslashchar",
    }
    return "".join(
        r"\unexpanded{\csname ltx@" + characters[char] + r"\endcsname}"
        if char in characters
        else char
        for char in path
    )


class _TokenRenderer:
    """Walk the markdown-it token stream and dispatch by token type."""

    def __init__(self, parser=None):
        self.parser = parser
        self._first_cell_in_row = True

    def render(self, tokens, options, env):
        out = []
        for token in tokens:
            if token.type == "inline":
                out.append(self.render(token.children or [], options, env))
            else:
                method = getattr(self, token.type, None)
                if method is not None:
                    out.append(method(token, env))
        return "".join(out)

    # Fallbacks for the markup we do not specially handle.
    def text(self, token, env):
        return token.content

    def text_special(self, token, env):
        return self.text(token, env)

    def softbreak(self, token, env):
        return "\n"

    def html_inline(self, token, env):
        return ""

    def html_block(self, token, env):
        return ""

    def entry_reference(self, token, env):
        label = self.render(token.children, self.parser.options, env)
        if token.meta["named"]:
            return f"{label} ({token.meta['date']})"
        return label


class LatexRenderer(_TokenRenderer):
    def __init__(self, parser=None):
        super().__init__(parser)
        self._open_tags = []

    def text(self, token, env):
        return tex_escape(token.content)

    def html_inline(self, token, env):
        # Keep basic formatting tags (the format menu inserts "<u>...</u>"),
        # drop everything else. Stray closing tags are ignored; stray
        # opening tags are closed in render() below.
        match = _TEX_HTML_TAG.fullmatch(token.content.lower())
        if not match:
            return ""
        closing, tag = match.groups()
        if not closing:
            self._open_tags.append(tag)
            return "\\" + _HTML_TO_TEX[tag] + "{"
        if tag not in self._open_tags:
            return ""
        # Close tags that were opened later, too, to keep braces balanced.
        index = len(self._open_tags) - 1 - self._open_tags[::-1].index(tag)
        closed = len(self._open_tags) - index
        del self._open_tags[index:]
        return "}" * closed

    def softbreak(self, token, env):
        return "\n"

    def hardbreak(self, token, env):
        return "\\\\\n"

    def paragraph_open(self, token, env):
        return ""

    def paragraph_close(self, token, env):
        # Tight list items wrap their text in hidden paragraphs.
        return "" if token.hidden else "\n\n"

    def heading_open(self, token, env):
        return "\\" + _HEADING_TO_TEX.get(token.tag, "section") + "{"

    def heading_close(self, token, env):
        return "}\n\n"

    def strong_open(self, token, env):
        return "\\textbf{"

    def strong_close(self, token, env):
        return "}"

    def em_open(self, token, env):
        return "\\textit{"

    def em_close(self, token, env):
        return "}"

    def s_open(self, token, env):
        return "\\sout{"

    def s_close(self, token, env):
        return "}"

    def code_inline(self, token, env):
        return "\\texttt{" + tex_escape(token.content) + "}"

    def fence(self, token, env):
        if token.info.strip() == "rednotebook-raw":
            return token.content
        return "\\begin{verbatim}\n" + token.content + "\\end{verbatim}\n\n"

    code_block = fence

    def link_open(self, token, env):
        href = token.attrs.get("href", "")
        if href.lower().startswith("file://"):
            href = "run:" + _tex_local_link_path(_file_uri_path(href))
        else:
            # Escape characters that break \href inside other commands.
            href = re.sub(r"([#%{}\\])", r"\\\1", href)
        return "\\href{" + href + "}{"

    def link_close(self, token, env):
        return "}"

    def image(self, token, env):
        src = token.attrs.get("src", "")
        match = IMAGE_WIDTH.search(src)
        options = ""
        if match:
            options = f"[width={match.group(1)}px]"
            src = src[: match.start()]
        src = _file_uri_path(src) if src.lower().startswith("file://") else unquote(src)
        if any(char in src for char in "#%{}"):
            src = r"\detokenize{" + re.sub(r"([#%{}])", r"\\\1", src) + "}"
        return f'\\includegraphics{options}{{"{src}"}}'

    def bullet_list_open(self, token, env):
        return "\\begin{itemize}\n"

    def bullet_list_close(self, token, env):
        return "\\end{itemize}\n"

    def ordered_list_open(self, token, env):
        return "\\begin{enumerate}\n"

    def ordered_list_close(self, token, env):
        return "\\end{enumerate}\n"

    def list_item_open(self, token, env):
        return "\\item "

    def list_item_close(self, token, env):
        return "\n"

    def hr(self, token, env):
        return "\\par\\noindent\\rule{\\linewidth}{0.4pt}\n\n"

    def blockquote_open(self, token, env):
        return "\\begin{quote}\n"

    def blockquote_close(self, token, env):
        return "\\end{quote}\n"

    def hashtag(self, token, env):
        display = tex_escape(token.content.lstrip("#＃"))
        index = tex_escape(token.meta["tag"])
        return f"\\textcolor{{red}}{{\\#{display}\\index{{{index}}}}}"

    def rn_color(self, token, env):
        text = self.render(token.children, self.parser.options, env)
        return f"\\textcolor{{{tex_escape(token.meta['color'])}}}{{{text}}}"

    def math_inline(self, token, env):
        return f"${token.content}$"

    def math_inline_double(self, token, env):
        return f"$${token.content}$$"

    def math_block(self, token, env):
        return f"$$\n{token.content}\n$$\n\n"

    # Tables. The column count is stored on the table_open token by
    # _annotate_table_columns() before rendering starts.
    def table_open(self, token, env):
        num_columns = max(token.meta.get("ncols", 1), 1)
        return "\\begin{tabular}{" + "l" * num_columns + "}\n"

    def table_close(self, token, env):
        return "\\end{tabular}\n\n"

    def thead_close(self, token, env):
        return "\\hline\n"

    def tr_open(self, token, env):
        self._first_cell_in_row = True
        return ""

    def tr_close(self, token, env):
        return " \\\\\n"

    def td_open(self, token, env):
        if self._first_cell_in_row:
            self._first_cell_in_row = False
            return ""
        return " & "

    th_open = td_open


class PlainRenderer(_TokenRenderer):
    """Render plain text, indenting nested blocks like txt2tags did.

    Block tokens are rendered as a tree of blocks, so that list items and
    quotes can indent all lines of their content. Inline tokens use the
    token-type dispatch of _TokenRenderer.
    """

    def __init__(self, parser=None):
        super().__init__(parser)
        self._links = []

    def render(self, tokens, options, env):
        if tokens and tokens[0].block:
            return "\n\n".join(self._blocks(tokens, env)) + "\n"
        return super().render(tokens, options, env)

    def _blocks(self, tokens, env):
        """Return the text of each block in a sequence of sibling block tokens."""
        return [
            text
            for token, children in _sibling_blocks(tokens)
            if (text := self._block(token, children, env)) is not None
        ]

    def _inline(self, tokens, env):
        return "".join(self.render(t.children or [], self.parser.options, env) for t in tokens)

    def _block(self, token, children, env):
        kind = token.type
        if kind in ("paragraph_open", "heading_open"):
            return self._inline(children, env)
        if kind in ("bullet_list_open", "ordered_list_open"):
            return self._list(token, children, env)
        if kind == "blockquote_open":
            text = "\n\n".join(self._blocks(children, env))
            return "\n".join("\t" + line if line else "" for line in text.split("\n"))
        if kind == "table_open":
            rows = [cells for _row, cells in _rows(children)]
            return "\n".join(" | ".join(self._inline([c], env) for c in row) for row in rows)
        if kind in ("fence", "code_block"):
            return token.content.rstrip("\n")
        if kind == "math_block":
            return token.content
        if kind == "hr":
            return "=" * 20
        return None

    def _list(self, token, children, env):
        number = int(token.attrGet("start") or 1)
        # Tight lists hide the paragraphs of their items.
        tight = all(t.hidden for t in children if t.type == "paragraph_open")
        items = []
        for _item, content in _sibling_blocks(children):
            if token.type == "ordered_list_open":
                marker = f"{number}. "
                number += 1
            else:
                marker = "- "
            text = ("\n" if tight else "\n\n").join(self._blocks(content, env))
            first, *rest = text.split("\n")
            indent = " " * len(marker)
            rest = [indent + line if line else "" for line in rest]
            items.append("\n".join([marker + first, *rest]))
        return ("\n" if tight else "\n\n").join(items)

    def link_open(self, token, env):
        self._links.append("" if token.info == "auto" else token.attrs.get("href", ""))
        return ""

    def link_close(self, token, env):
        href = self._links.pop()
        return f" ({href})" if href else ""

    def hardbreak(self, token, env):
        return "\n"

    def code_inline(self, token, env):
        return token.content

    def image(self, token, env):
        return f"[{token.attrs.get('src', '')}]"

    def hashtag(self, token, env):
        return token.content

    def rn_color(self, token, env):
        return self.render(token.children, self.parser.options, env)

    def math_inline(self, token, env):
        return token.content

    math_inline_double = math_inline


def _sibling_blocks(tokens):
    """Yield (opening token, tokens inside) for each top-level block in tokens.

    For blocks without closing token, e.g. fences, the content is empty.
    """
    pos = 0
    while pos < len(tokens):
        token = tokens[pos]
        end = pos
        if token.nesting == 1:
            closing = token.type[: -len("_open")] + "_close"
            end = next(
                i
                for i in range(pos + 1, len(tokens))
                if tokens[i].type == closing and tokens[i].level == token.level
            )
        yield token, tokens[pos + 1 : end]
        pos = end + 1


def _rows(table_tokens):
    """Yield (row token, inline tokens of the cells) for each table row."""
    row = None
    for token in table_tokens:
        if token.type == "tr_open":
            row, cells = token, []
        elif token.type == "inline" and row is not None:
            cells.append(token)
        elif token.type == "tr_close":
            yield row, cells


_RENDERERS = {"html": HtmlRenderer, "tex": LatexRenderer, "txt": PlainRenderer}


def get_parser(target):
    md = MarkdownIt("commonmark", {"html": True, "linkify": True, "breaks": False})
    # Journal attachments are local files. Retain the default checks for other
    # schemes, especially javascript:, vbscript:, and non-image data: URLs.
    md.validateLink = lambda url: url.lower().startswith("file://") or validateLink(url)
    md.enable(["table", "strikethrough", "linkify"])
    md.use(_rednotebook_plugin)
    md.renderer = _RENDERERS[target](md)
    return md


def _walk(tokens):
    for token in tokens:
        yield token
        if token.children:
            yield from _walk(token.children)


def _annotate_table_columns(tokens):
    """Store the number of columns on each table_open token.

    The LaTeX renderer needs the column count for ``\\begin{tabular}`` before
    it sees any cells, so count the cells of the first row in advance.
    """
    table = None
    ncols = 0
    for token in tokens:
        if token.type == "table_open":
            table = token
            ncols = 0
        elif table is not None:
            if token.type in ("th_open", "td_open"):
                ncols += 1
            elif token.type == "tr_close":
                table.meta["ncols"] = ncols
                table = None


def _remove_empty_table_headers(tokens):
    """Drop header rows without content, e.g. from converted txt2tags tables."""
    result = []
    pos = 0
    while pos < len(tokens):
        token = tokens[pos]
        if token.type == "thead_open":
            end = next(i for i in range(pos, len(tokens)) if tokens[i].type == "thead_close")
            header = tokens[pos : end + 1]
            if all(t.type != "inline" or not t.content.strip() for t in header):
                pos = end + 1
                continue
        result.append(token)
        pos += 1
    return result


def _get_inline_text(inline_token):
    return "".join(
        child.content
        for child in _walk(inline_token.children or [])
        if child.type in ("text", "text_special", "code_inline", "math_inline", "hashtag")
    )


def _slugify(title):
    slug = re.sub(r"[^\w\- ]", "", title.lower()).strip().replace(" ", "-")
    return slug or "section"


def _add_heading_anchors(tokens):
    """Give each heading an id attribute and return (level, title, id) tuples."""
    entries = []
    used_slugs = set()
    for pos, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        title = _get_inline_text(tokens[pos + 1])
        slug = base_slug = _slugify(title)
        counter = 1
        while slug in used_slugs:
            counter += 1
            slug = f"{base_slug}-{counter}"
        used_slugs.add(slug)
        token.attrs["id"] = slug
        entries.append((int(token.tag[1]), title, slug))
    return entries


def _render_toc(entries):
    """Render a nested list of links to the given headings."""
    if not entries:
        return ""
    min_level = min(level for level, _, _ in entries)
    parts = ['<nav class="toc">\n']
    current_level = min_level - 1
    for level, title, slug in entries:
        while current_level < level:
            parts.append("<ul>\n")
            current_level += 1
        while current_level > level:
            parts.append("</ul>\n")
            current_level -= 1
        parts.append(f'<li><a href="#{slug}">{escapeHtml(title)}</a></li>\n')
    while current_level >= min_level:
        parts.append("</ul>\n")
        current_level -= 1
    parts.append("</nav>\n")
    return "".join(parts)


# --------------------------------------------------------------------------
# Document templates
# --------------------------------------------------------------------------

LATEX_PREAMBLE = r"""\documentclass[a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage[normalem]{ulem}
\usepackage{hyperref}
\usepackage{makeidx}
\makeindex
\title{%(title)s}
\begin{document}
\maketitle
"""

LATEX_FOOTER = r"""
\printindex
\end{document}
"""


def _html_document(body, options, has_math):
    css = CSS % {
        "font": options.get("font", "sans-serif"),
        "bgcolor": options.get("bgcolor", "white"),
        "fgcolor": options.get("fgcolor", "black"),
    }
    mathjax = MATHJAX if has_math else ""
    title = escapeHtml(options.get("title", "RedNotebook"))
    return (
        "<!DOCTYPE html>\n<html>\n<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n"
        f"{css}{mathjax}"
        "</head>\n<body>\n"
        f"{body}"
        "</body>\n</html>\n"
    )


def _latex_document(body, options):
    title = options.get("title", "RedNotebook")
    return LATEX_PREAMBLE % {"title": title} + body + LATEX_FOOTER


def render(text, target, options=None, *, resolve_link=None):
    """Render Markdown, optionally resolving parsed link/image destinations."""
    options = options or {}
    md = get_parser(target)
    env = {}
    tokens = md.parse(text, env)

    if resolve_link is not None:
        for token in _walk(tokens):
            if token.type in ("link_open", "image"):
                is_image = token.type == "image"
                attribute = "src" if is_image else "href"
                token.attrs[attribute] = resolve_link(token.attrs[attribute], is_image)

    tokens = _remove_empty_table_headers(tokens)

    toc = ""
    if target == "html" and options.get("toc"):
        toc = _render_toc(_add_heading_anchors(tokens))
    elif target == "tex":
        _annotate_table_columns(tokens)

    body = md.renderer.render(tokens, md.options, env)

    if target == "html":
        has_math = options.get("add_mathjax")
        if has_math is None:
            has_math = any(token.type.startswith("math") for token in _walk(tokens))
        return _html_document(toc + body, options, has_math)
    if target == "tex":
        # Close any "<u>" etc. that was never closed to keep the braces balanced.
        body += "}" * len(md.renderer._open_tags)
        return _latex_document(body, options)
    # Keep leading tabs of quotes.
    return body.strip("\n") + "\n"
