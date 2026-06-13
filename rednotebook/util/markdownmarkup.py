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
* ``$...$`` / ``$$...$$`` math is rendered for MathJax/LaTeX.
"""

import re

from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml
from markdown_it.renderer import RendererHTML
from mdit_py_plugins.dollarmath import dollarmath_plugin


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
COLOR = re.compile(r"\{([^{}|]+)\|color:([^{}]+)\}")
IMAGE_WIDTH = re.compile(r"\?(\d+)$")


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


def _color_rule(state, silent):
    if state.src[state.pos] != "{":
        return False
    match = COLOR.match(state.src, state.pos)
    if not match:
        return False
    if not silent:
        token = state.push("rn_color", "", 0)
        token.meta = {"text": match.group(1), "color": match.group(2)}
    state.pos = match.end()
    return True


def _rednotebook_plugin(md):
    md.inline.ruler.before("emphasis", "hashtag", _hashtag_rule)
    md.inline.ruler.before("emphasis", "rn_color", _color_rule)


# --------------------------------------------------------------------------
# HTML renderer
# --------------------------------------------------------------------------


class HtmlRenderer(RendererHTML):
    def hashtag(self, tokens, idx, options, env):
        return f'<span style="color:red">{escapeHtml(tokens[idx].content)}</span>'

    def rn_color(self, tokens, idx, options, env):
        meta = tokens[idx].meta
        return f'<span style="color:{escapeHtml(meta["color"])}">{escapeHtml(meta["text"])}</span>'

    def image(self, tokens, idx, options, env):
        token = tokens[idx]
        src = token.attrs.get("src", "")
        width = ""
        match = IMAGE_WIDTH.search(src)
        if match:
            width = f' width="{match.group(1)}"'
            src = src[: match.start()]
        alt = escapeHtml(token.content)
        return f'<img src="{escapeHtml(src)}"{width} alt="{alt}">'

    def math_inline(self, tokens, idx, options, env):
        return f"\\({tokens[idx].content}\\)"

    def math_block(self, tokens, idx, options, env):
        return f"$$\n{tokens[idx].content}\n$$\n"


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


def tex_escape(text):
    return _TEX_ESCAPE_RE.sub(lambda m: _TEX_ESCAPES[m.group()], text)


class _TokenRenderer:
    """Walk the markdown-it token stream and dispatch by token type."""

    def __init__(self, parser=None):
        self.parser = parser

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

    def softbreak(self, token, env):
        return "\n"

    def html_inline(self, token, env):
        return ""

    def html_block(self, token, env):
        return ""


class LatexRenderer(_TokenRenderer):
    def text(self, token, env):
        return tex_escape(token.content)

    def softbreak(self, token, env):
        return "\n"

    def hardbreak(self, token, env):
        return "\\\\\n"

    def paragraph_open(self, token, env):
        return ""

    def paragraph_close(self, token, env):
        return "\n\n"

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
        return "\\begin{verbatim}\n" + token.content + "\\end{verbatim}\n\n"

    code_block = fence

    def link_open(self, token, env):
        return "\\href{" + token.attrs.get("href", "") + "}{"

    def link_close(self, token, env):
        return "}"

    def image(self, token, env):
        src = token.attrs.get("src", "")
        match = IMAGE_WIDTH.search(src)
        options = ""
        if match:
            options = f"[width={match.group(1)}px]"
            src = src[: match.start()]
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
        index = token.meta["tag"]
        return f"\\textcolor{{red}}{{\\#{display}\\index{{{index}}}}}"

    def rn_color(self, token, env):
        meta = token.meta
        return f"\\textcolor{{{tex_escape(meta['color'])}}}{{{tex_escape(meta['text'])}}}"

    def math_inline(self, token, env):
        return f"${token.content}$"

    def math_block(self, token, env):
        return f"$${token.content}$$\n"

    # Minimal table support: render cells separated by " & " and rows by "\\".
    def tr_close(self, token, env):
        return "\\\\\n"

    def td_close(self, token, env):
        return " & "

    th_close = td_close


class PlainRenderer(_TokenRenderer):
    def hardbreak(self, token, env):
        return "\n"

    def paragraph_close(self, token, env):
        return "\n\n"

    def heading_close(self, token, env):
        return "\n\n"

    def code_inline(self, token, env):
        return token.content

    def fence(self, token, env):
        return token.content + "\n"

    code_block = fence

    def image(self, token, env):
        return f"[{token.attrs.get('src', '')}]"

    def list_item_open(self, token, env):
        return "- "

    def list_item_close(self, token, env):
        return "\n"

    def hr(self, token, env):
        return "\n" + "=" * 20 + "\n\n"

    def hashtag(self, token, env):
        return token.content

    def rn_color(self, token, env):
        return token.meta["text"]

    def math_inline(self, token, env):
        return token.content

    def math_block(self, token, env):
        return token.content + "\n"


_RENDERERS = {"html": HtmlRenderer, "tex": LatexRenderer, "txt": PlainRenderer}


def _get_parser(target):
    md = MarkdownIt("commonmark", {"html": True, "linkify": True, "breaks": False})
    md.enable(["table", "strikethrough", "linkify"])
    md.use(dollarmath_plugin, double_inline=True)
    md.use(_rednotebook_plugin)
    md.renderer = _RENDERERS[target](md)
    return md


def _walk(tokens):
    for token in tokens:
        yield token
        if token.children:
            yield from _walk(token.children)


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
    return (
        "<!DOCTYPE html>\n<html>\n<head>\n"
        '<meta charset="utf-8">\n'
        f"{css}{mathjax}"
        "</head>\n<body>\n"
        f"{body}"
        "</body>\n</html>\n"
    )


def _latex_document(body, options):
    title = options.get("title", "RedNotebook")
    return LATEX_PREAMBLE % {"title": title} + body + LATEX_FOOTER


def render(text, target, options=None):
    """Render Markdown ``text`` to ``target`` (``html``, ``tex`` or ``txt``)."""
    options = options or {}
    md = _get_parser(target)
    env = {}
    tokens = md.parse(text, env)
    body = md.renderer.render(tokens, md.options, env)

    if target == "html":
        has_math = options.get("add_mathjax")
        if has_math is None:
            has_math = any(token.type.startswith("math") for token in _walk(tokens))
        return _html_document(body, options, has_math)
    if target == "tex":
        return _latex_document(body, options)
    return body.strip() + "\n"
