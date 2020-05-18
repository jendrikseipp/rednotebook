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

import logging
import os
import re
import sys

from gi.repository import GObject, Pango

from rednotebook.data import HASHTAG
from rednotebook.external import txt2tags
from rednotebook.util import filesystem, urls


# Linebreaks are only allowed at line ends
REGEX_LINEBREAK = r"\\\\[\s]*$"
REGEX_HTML_LINK = r"<a.*?>(.*?)</a>"

# pic [""/home/user/Desktop/RedNotebook pic"".png]
PIC_NAME = r"\S.*?\S|\S"
PIC_EXT = r"(?:png|jpe?g|gif|eps|bmp|svg)"
REGEX_PIC = re.compile(
    r'(\["")({})("")(\.{})(\?\d+)?(\])'.format(PIC_NAME, PIC_EXT), flags=re.I
)

# named local link [my file.txt ""file:///home/user/my file.txt""]
# named link in web [heise ""http://heise.de""]
REGEX_NAMED_LINK = re.compile(r'(\[)(.*?)(\s"")(\S.*?\S)(""\])', flags=re.I)

ESCAPE_COLOR = r"XBEGINCOLORX\1XSEPARATORX\2XENDCOLORX"
COLOR_ESCAPED = r"XBEGINCOLORX(.*?)XSEPARATORX(.*?)XENDCOLORX"

CHARSET_UTF8 = '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'

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
    @media (prefers-color-scheme: dark) {
        a { color: var(--dark-link-color); }
    }
    <!-- Don't split last line between pages.
         This fix is only supported by Opera -->
    p {
        page-break-inside: avoid;
    }
    blockquote {
        margin: 1em 2em;
        border-left: 2px solid #999;
        font-style: oblique;
        padding-left: 1em;
    }
    blockquote:first-letter {
        margin: .2em .1em .1em 0;
        font-size: 160%%;
        font-weight: bold;
    }
    blockquote:first-line {
        font-weight: bold;
    }
    table {
        border-collapse: collapse;
    }
    td, th {
        <!--border: 1px solid #888;--> <!--Allow tables without borders-->
        padding: 3px 7px 2px 7px;
    }
    th {
        text-align: left;
        padding-top: 5px;
        padding-bottom: 4px;
        background-color: #aaa;
        color: #ffffff;
    }
    hr.heavy {
        height: 2px;
        background-color: black;
    }
</style>
"""

# MathJax
FORMULAS_SUPPORTED = True
MATHJAX_FILE = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js"

# Explicitly setting inlineMath: [ ['\\(','\\)'] ] doesn't work.
# Using defaults:
#       displayMath: [ ['$$','$$'], ['\[','\]'] ]
#       inlineMath:  [['\(','\)']]
MATHJAX_DELIMITERS = ["$$", "\\(", "\\)", r"\\[", "\\]"]
MATHJAX = """\
<script type="text/x-mathjax-config">
  MathJax.Hub.Config({{
    messageStyle: "none",
    config: ["MMLorHTML.js"],
    jax: ["input/TeX","input/MathML","output/HTML-CSS","output/NativeMML"],
    tex2jax: {{}},
    extensions: ["tex2jax.js","mml2jax.js","MathMenu.js","MathZoom.js"],
    TeX: {{
      extensions: ["AMSmath.js","AMSsymbols.js","noErrors.js","noUndefined.js"]
    }}
  }});
</script>
<script type="text/javascript" src="{MATHJAX_FILE}"></script>
""".format(
    **locals()
)


def convert_categories_to_markup(categories, with_category_title=True):
    # Only add Category title if the text is displayed
    if with_category_title:
        markup = "== %s ==\n" % _("Tags")
    else:
        markup = ""

    for category, entry_list in categories.items():
        markup += "- " + category + "\n"
        for entry in entry_list:
            markup += "  - " + entry + "\n"
    markup += "\n\n"
    return markup


def get_markup_for_day(
    day, target, with_text=True, with_tags=True, categories=None, date=None
):
    """
    Used for exporting days
    """
    export_string = ""

    # Add date if it is not None and not the empty string
    if date:
        if target in ["xhtml", "html"]:
            # Following anchor will be used as a target for every entry reference mentioning
            # this entry's date.
            export_string += "''<span id=\"{:%Y-%m-%d}\"></span>''\n".format(day.date)

        export_string += "= {} =\n\n".format(date)

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


def _get_config(target, options):
    # Set the configuration on the 'config' dict.
    config = txt2tags.ConfigMaster()._get_defaults()

    config["outfile"] = txt2tags.MODULEOUT  # results as list
    config["target"] = target

    # The Pre (and Post) processing config is a list of lists:
    # [ [this, that], [foo, bar], [patt, replace] ]
    config["postproc"] = []
    config["preproc"] = []
    config["style"] = []

    # Allow line breaks, r'\\\\' are 2 \ for regexes
    config["preproc"].append([REGEX_LINEBREAK, "LINEBREAK"])

    # Highlight hashtags.
    if target == "tex":
        config["preproc"].append(
            [HASHTAG.pattern, r"\1{\2\3BEGININDEX\3ENDINDEX|color:red}"]
        )
    else:
        config["preproc"].append([HASHTAG.pattern, r"\1{\2\3|color:red}"])

    # Escape color markup.
    config["preproc"].append([r"\{(.*?)\|color:(.+?)\}", ESCAPE_COLOR])

    if target in ["xhtml", "html"]:
        config["encoding"] = "UTF-8"  # document encoding
        config["toc"] = 0
        config["css-sugar"] = 1

        # Fix encoding for export opened in firefox
        config["postproc"].append([r"<head>", "<head>" + CHARSET_UTF8])

        # Line breaks
        config["postproc"].append([r"LINEBREAK", "<br />"])

        # Apply image resizing
        config["postproc"].append([r"src=\"WIDTH(\d+)-", r'width="\1" src="'])

        # {{red text|color:red}} -> <span style="color:red">red text</span>
        config["postproc"].append([COLOR_ESCAPED, r'<span style="color:\2">\1</span>'])

        # Custom css
        font = options.pop("font", "sans-serif")
        css = CSS % {
            "font": font,
            "bgcolor": options.get("bgcolor", "white"),
            "fgcolor": options.get("fgcolor", "black"),
        }
        config["postproc"].append([r"</head>", css + "</head>"])

        # MathJax
        if options.pop("add_mathjax"):
            config["postproc"].append([r"</body>", MATHJAX + "</body>"])

    elif target == "tex":
        config["encoding"] = "utf8"
        config["preproc"].append(["€", "Euro"])

        # Latex only allows whitespace and underscores in filenames if
        # the filename is surrounded by "...". This is in turn only possible
        # if the extension is omitted.
        config["preproc"].append([r'\[""', r'["""'])
        config["preproc"].append([r'""\.', r'""".'])

        scheme = "file:///" if sys.platform == "win32" else "file://"

        # For images we have to omit the file:// prefix
        config["postproc"].append(
            [r'includegraphics\{(.*)"%s' % scheme, r'includegraphics{"\1']
        )

        # Special handling for LOCAL file links (Omit scheme, add run:)
        # \htmladdnormallink{file.txt}{file:///home/user/file.txt}
        # -->
        # \htmladdnormallink{file.txt}{run:/home/user/file.txt}
        config["postproc"].append(
            [
                r"htmladdnormallink\{(.*)\}\{%s(.*)\}" % scheme,
                r"htmladdnormallink{\1}{run:\2}",
            ]
        )

        # Line breaks
        config["postproc"].append([r"LINEBREAK", r"\\\\"])

        # Apply image resizing
        config["postproc"].append(
            [r'includegraphics\{("?)WIDTH(\d+)-', r"includegraphics[width=\2px]{\1"]
        )

        # We want the plain latex formulas unescaped.
        # Allowed formulas: $$...$$, \[...\], \(...\)
        config["preproc"].append(
            [r"\\\[\s*(.+?)\s*\\\]", r"BEGINEQUATION''\1''ENDEQUATION"]
        )
        config["preproc"].append(
            [r"\$\$\s*(.+?)\s*\$\$", r"BEGINEQUATION''\1''ENDEQUATION"]
        )
        config["postproc"].append([r"BEGINEQUATION(.+)ENDEQUATION", r"$$\1$$"])

        config["preproc"].append([r"\\\(\s*(.+?)\s*\\\)", r"BEGINMATH''\1''ENDMATH"])
        config["postproc"].append([r"BEGINMATH(.+)ENDMATH", r"$\1$"])

        # Fix utf8 quotations - „, “ and ” cause problems compiling the latex document.
        config["postproc"].extend([["„", '"'], ["”", '"'], ["“", '"']])

        # Enable index.
        config["style"].append("makeidx")
        config["postproc"].append([r"BEGININDEX(.+?)ENDINDEX", r"\\index{\1}"])
        config["postproc"].append(["begin{document}", "makeindex\n\\\\begin{document}"])
        config["postproc"].append(["end{document}", "printindex\n\n\\\\end{document}"])

        config["postproc"].append([COLOR_ESCAPED, r"\\textcolor{\2}{\1}"])

    elif target == "txt":
        # Line breaks
        config["postproc"].append([r"LINEBREAK", "\n"])

        # Apply image resizing ([WIDTH400-file:///pathtoimage.jpg])
        config["postproc"].append([r"\[WIDTH(\d+)-(.+)\]", r"[\2?\1]"])

    # Entry references
    if target in ["xhtml", "html"]:
        # txt2tags will generate links to the named entry references because they share common bracket
        # notation used by the URIs. We just need to add our internal schema to make it a proper URI.
        config["preproc"].append(
            [
                r"\[(?P<name>.+)\s+(?P<date>\d{4}-\d{2}-\d{2})\s*\]",
                r"[\g<name> #\g<date>]",
            ]
        )

        # Convert bracketed dates into named references where the date itself is being used as a name.
        # For example:
        # "Today is [2019-10-20]" will be converted into "Today is [2019-10-20 #2019-10-20]"
        config["preproc"].append(
            [r"\[(?P<date>\d{4}-\d{2}-\d{2})\]", r"[\g<date> #\g<date>]"]
        )
    else:
        # Links to entry references are not supported for targets other than (X)HTML
        config["preproc"].append(
            [r"\[(?P<name>.+)\s+(?P<date>\d{4}-\d{2}-\d{2})\]", r"\g<name> (\g<date>)"]
        )

    # Allow resizing images by changing
    # [filename.png?width] to [WIDTHwidth-filename.png]
    img_ext = r"png|jpe?g|gif|eps|bmp|svg"
    img_name = r"\S.*\S|\S"

    # Apply this prepoc only after the latex image quotes have been added
    config["preproc"].append(
        [r"\[({}\.({}))\?(\d+)\]".format(img_name, img_ext), r"[WIDTH\3-\1]"]
    )

    # Disable colors for all other targets.
    config["postproc"].append([COLOR_ESCAPED, r"\1"])

    config.update(options)

    return config


def _convert_paths(txt, data_dir):
    def _convert_uri(uri):
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

    def _convert_pic_path(match):
        uri = _convert_uri(match.group(2) + match.group(4))
        # Reassemble picture markup.
        name, ext = os.path.splitext(uri)
        parts = [match.group(1), name, match.group(3), ext]
        if match.group(5) is not None:
            parts.append(match.group(5))
        parts.append(match.group(6))
        return "".join(parts)

    def _convert_file_path(match):
        uri = _convert_uri(match.group(4))
        # Reassemble link markup
        parts = [match.group(i) for i in range(1, 6)]
        parts[3] = uri
        return "".join(parts)

    txt = REGEX_PIC.sub(_convert_pic_path, txt)
    txt = REGEX_NAMED_LINK.sub(_convert_file_path, txt)
    return txt


def convert(txt, target, data_dir, headers=None, options=None):
    """
    Code partly taken from txt2tags tarball
    """
    options = options or {}

    # Only add MathJax code if there is a formula.
    options["add_mathjax"] = (
        FORMULAS_SUPPORTED
        and "html" in target
        and any(x in txt for x in MATHJAX_DELIMITERS)
    )
    logging.debug("Add mathjax code: %s" % options["add_mathjax"])

    # Turn relative paths into absolute paths.
    txt = _convert_paths(txt, data_dir)

    # The body text must be a list.
    txt = txt.split("\n")

    # Set the three header fields
    if headers is None:
        if target == "tex":
            # LaTeX requires a title if \maketitle is used
            headers = ["RedNotebook", "", ""]
        else:
            headers = ["", "", ""]

    config = _get_config(target, options)

    # Let's do the conversion
    try:
        headers = txt2tags.doHeader(headers, config)
        body, toc = txt2tags.convert(txt, config)
        footer = txt2tags.doFooter(config)
        toc = txt2tags.toc_tagger(toc, config)
        toc = txt2tags.toc_formatter(toc, config)
        full_doc = headers + toc + body + footer
        finished = txt2tags.finish_him(full_doc, config)
        result = "\n".join(finished)
    # Txt2tags error, show the messsage to the user
    except txt2tags.error as msg:
        logging.error(msg)
        result = msg
    # Unknown error, show the traceback to the user
    except Exception:
        result = (
            "<b>Error</b>: This day contains invalid "
            '<a href="http://txt2tags.org/markup.html">txt2tags markup</a>. '
            "You can help us fix this by submitting a bugreport in the "
            '<a href="https://code.google.com/p/txt2tags/issues/list">'
            "txt2tags bugtracker</a>. Please append the day's text to the issue."
        )
        logging.error("Invalid markup:\n%s" % txt2tags.getUnknownErrorMessage())
    return result


def convert_to_pango(txt, headers=None, options=None):
    """
    Code partly taken from txt2tags tarball
    """
    original_txt = txt

    # Here is the marked body text, it must be a list.
    txt = txt.split("\n")

    # Set the three header fields
    if headers is None:
        headers = ["", "", ""]

    config = txt2tags.ConfigMaster()._get_defaults()

    config["outfile"] = txt2tags.MODULEOUT  # results as list
    config["target"] = "xhtml"

    config["preproc"] = []
    # We need to escape the ampersand here, otherwise "&amp;" would become
    # "&amp;amp;"
    config["preproc"].append([r"&amp;", "&"])

    # Allow line breaks
    config["postproc"] = []
    config["postproc"].append([REGEX_LINEBREAK, "\n"])

    if options is not None:
        config.update(options)

    # Let's do the conversion
    try:
        body, toc = txt2tags.convert(txt, config)
        full_doc = body
        finished = txt2tags.finish_him(full_doc, config)
        result = "".join(finished)

    # Txt2tags error, show the messsage to the user
    except txt2tags.error as msg:
        logging.error(msg)
        result = msg

    # Unknown error, show the traceback to the user
    except Exception:
        result = txt2tags.getUnknownErrorMessage()
        logging.error(result)

    # remove unwanted paragraphs
    result = result.replace("<p>", "").replace("</p>", "")

    logging.log(
        5,
        'Converted "%s" text to "%s" txt2tags markup'
        % (repr(original_txt), repr(result)),
    )

    # Remove unknown tags (<a>)
    def replace_links(match):
        """Return the link name."""
        return match.group(1)

    result = re.sub(REGEX_HTML_LINK, replace_links, result)

    try:
        Pango.parse_markup(result, -1, "0")
        # result is valid pango markup, return the markup.
        return result
    except GObject.GError:
        # There are unknown tags in the markup, return the original text
        logging.debug("There are unknown tags in the markup: %s" % result)
        return original_txt


def convert_from_pango(pango_markup):
    original_txt = pango_markup
    replacements = {
        "<b>": "**",
        "</b>": "**",
        "<i>": "//",
        "</i>": "//",
        "<s>": "--",
        "</s>": "--",
        "<u>": "__",
        "</u>": "__",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "\n": r"\\",
    }
    for orig, repl in replacements.items():
        pango_markup = pango_markup.replace(orig, repl)

    logging.log(
        5,
        'Converted "%s" pango to "%s" txt2tags'
        % (repr(original_txt), repr(pango_markup)),
    )
    return pango_markup
