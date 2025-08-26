#!/usr/bin/env python
# txt2tags - generic text conversion tool
# https://txt2tags.org/
# https://github.com/jendrikseipp/txt2tags
#
# Copyright 2001-2010 Aurelio Jargas
# Copyright 2010-2019 Jendrik Seipp
#
# License: GPL2+ (http://www.gnu.org/licenses/gpl-2.0.txt)
#
########################################################################
#
# The code that [1] parses the marked text is separated from the
# code that [2] insert the target tags.
#
#   [1] made by: def convert()
#   [2] made by: class BlockMaster
#
# The structures of the marked text are identified and its contents are
# extracted into a data holder (Python lists and dictionaries).
#
# When parsing the source file, the blocks (para, lists, quote, table)
# are opened with BlockMaster, right when found. Then its contents,
# which spans on several lines, are feeded into a special holder on the
# BlockMaster instance. Just when the block is closed, the target tags
# are inserted for the full block as a whole, in one pass. This way, we
# have a better control on blocks. Much better than the previous line by
# line approach.
#
# In other words, whenever inside a block, the parser *holds* the tag
# insertion process, waiting until the full block is read. That was
# needed primary to close paragraphs for the XHTML target, but
# proved to be a very good adding, improving many other processing.
#
# -------------------------------------------------------------------
#
# These important classes are all documented:
# CommandLine, SourceDocument, ConfigMaster, ConfigLines.
#
# There is a RAW Config format and all kind of configuration is first
# converted to this format. Then a generic method parses it.
#
# These functions get information about the input file(s) and take
# care of the init processing:
# process_source_file() and convert_file()
#
########################################################################

# XXX Smart Image Align don't work if the image is a link
# Can't fix that because the image is expanded together with the
# link, at the linkbank filling moment. Only the image is passed
# to parse_images(), not the full line, so it is always 'middle'.

# XXX Paragraph separation not valid inside Quote
# Quote will not have <p></p> inside, instead will close and open
# again the <blockquote>. This really sux in CSS, when defining a
# different background color. Still don't know how to fix it.

# XXX TODO (maybe)
# New mark which expands to an anchor full title.
# It is necessary to parse the full document in this order:
#  DONE  1st scan: HEAD: get all settings, including %!includeconf
#  DONE  2nd scan: BODY: expand includes & apply %!preproc
#        3rd scan: BODY: read titles and compose TOC info
#        4th scan: BODY: full parsing, expanding [#anchor] 1st
# Steps 2 and 3 can be made together, with no tag adding.
# Two complete body scans will be *slow*, don't know if it worths.
# One solution may be add the titles as postproc rules


import collections
import getopt
import os
import re
import sys

##############################################################################

# Program information
my_url = "https://txt2tags.org"
my_name = "txt2tags"
my_email = "jendrikseipp@gmail.com"
__version__ = "3.9"

# FLAGS   : the conversion related flags  , may be used in %!options
# OPTIONS : the conversion related options, may be used in %!options
# ACTIONS : the other behavior modifiers, valid on command line only
# NO_TARGET: actions that don't require a target specification
# NO_MULTI_INPUT: actions that don't accept more than one input file
# CONFIG_KEYWORDS: the valid %!key:val keywords
#
# FLAGS and OPTIONS are configs that affect the converted document.
# They usually have also a --no-<option> to turn them OFF.
#
# ACTIONS are needed because when handling multiple input files, strange
# behavior may occur. There is no --no-<action>.
# Options --version and --help inside %!options are odd.

FLAGS = {"headers": 1, "enum-title": 0, "toc": 0, "rc": 1, "quiet": 0, "slides": 0}
OPTIONS = {
    "target": "",
    "style": "",
    "infile": "",
    "outfile": "",
    "config-file": "",
    "lang": "",
}
ACTIONS = {"help": 0, "version": 0, "verbose": 0, "debug": 0, "targets": 0}
NO_TARGET = ["help", "version", "targets"]
CONFIG_KEYWORDS = ["target", "style", "options", "preproc", "postproc"]

TARGET_NAMES = {
    "html": "HTML page",
    "sgml": "SGML document",
    "dbk": "DocBook document",
    "tex": "LaTeX document",
    "lout": "Lout document",
    "man": "UNIX Manual page",
    "mgp": "MagicPoint presentation",
    "wiki": "Wikipedia page",
    "gwiki": "Google Wiki page",
    "doku": "DokuWiki page",
    "pmw": "PmWiki page",
    "moin": "MoinMoin page",
    "txt": "Plain Text",
    "adoc": "AsciiDoc document",
    "creole": "Creole 1.0 document",
    "md": "Markdown document",
    "ctx": "ConTeXt document",
}

TARGETS = sorted(TARGET_NAMES)

DEBUG = 0  # do not edit here, please use --debug
VERBOSE = 0  # do not edit here, please use -v, -vv or -vvv
QUIET = 0  # do not edit here, please use --quiet

ENCODING = "utf-8"
DFT_TEXT_WIDTH = 72

RC_RAW = []
CMDLINE_RAW = []
CONF = {}
BLOCK = None
TITLE = None
regex = {}
TAGS = {}
rules = {}

TARGET = ""

STDIN = STDOUT = "-"
MODULEIN = MODULEOUT = "-module-"
ESCCHAR = "\x00"
SEPARATOR = "\x01"
LISTNAMES = {"-": "list", "+": "numlist", ":": "deflist"}

VERSIONSTR = "{} version {} <{}>".format(my_name, __version__, my_url)

USAGE = "\n".join(
    [
        "",
        "Usage: %s [OPTIONS] infile.t2t" % my_name,
        "",
        "      --targets       list available targets and exit",
        "  -t, --target=TYPE   set target document type. currently supported:",
        "                      %s" % ", ".join(TARGETS),
        "  -i, --infile=FILE   set FILE as the input file name ('-' for STDIN)",
        "  -o, --outfile=FILE  set FILE as the output file name ('-' for STDOUT)",
        "      --toc           add a table of contents to the output",
        "  -n, --enum-title    enumerate all titles as 1, 1.1, 1.1.1, etc.",
        "      --style=FILE    use FILE as the document style (e.g., a CSS file)",
        "  -H, --no-headers    omit header and footer from output",
        "  -C, --config-file=F read configuration from file F",
        "  -q, --quiet         suppress all output (except errors)",
        "  -v, --verbose       print informative messages during conversion",
        "  -h, --help          print this help text and exit",
        "  -V, --version       print program version and exit",
        "",
        "Turn off options:",
        "     --no-enum-title, --headers, --no-quiet,",
        "     --no-rc, --no-style, --no-toc",
        "",
        "Example:",
        "     {} -t html --toc {}".format(my_name, "file.t2t"),
        "",
        "By default, converted output is saved to 'infile.<target>'.",
        "Use --outfile to force an output file name.",
        "If  input file is '-', read from STDIN.",
        "If output file is '-', dump output to STDOUT.",
        "",
        my_url,
        "",
    ]
)


##############################################################################


# Here is all the target's templates
# You may edit them to fit your needs
#  - the %(HEADERn)s strings represent the Header lines
#  - the %(STYLE)s string is changed by --style contents
#  - the %(ENCODING)s string is changed to "utf-8"
#  - if any of the above is empty, the full line is removed
#  - use %% to represent a literal %
#
HEADER_TEMPLATE = {
    "txt": """\
%(HEADER1)s
%(HEADER2)s
%(HEADER3)s
""",
    "sgml": """\
<!doctype linuxdoc system>
<article>
<title>%(HEADER1)s
<author>%(HEADER2)s
<date>%(HEADER3)s
""",
    "html": """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="%(ENCODING)s">
<title>%(HEADER1)s</title>
<meta name="generator" content="https://txt2tags.org">
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="stylesheet" href="%(STYLE)s">
<style>
blockquote{margin: 1em 2em; border-left: 2px solid #999;
  font-style: oblique; padding-left: 1em;}
blockquote:first-letter{margin: .2em .1em .1em 0; font-size: 160%%; font-weight: bold;}
blockquote:first-line{font-weight: bold;}
body{font-family: sans-serif;}
hr{background-color:#000;border:0;color:#000;}
hr.heavy{height:2px;}
hr.light{height:1px;}
img{border:0;display:block;}
img.right{margin:0 0 0 auto;}
img.center{border:0;margin:0 auto;}
table{border-collapse: collapse;}
table th,table td{padding: 3px 7px 2px 7px;}
table th{background-color: lightgrey;}
table.center{margin-left:auto; margin-right:auto;}
.center{text-align:center;}
.right{text-align:right;}
.left{text-align:left;}
.tableborder,.tableborder td,.tableborder th{border:1px solid #000;}
.underline{text-decoration:underline;}
</style>
</head>
<body>
<header>
<hgroup>
<h1>%(HEADER1)s</h1>
<h2>%(HEADER2)s</h2>
<h3>%(HEADER3)s</h3>
</hgroup>
</header>

""",
    "dbk": """\
<?xml version="1.0"
      encoding="%(ENCODING)s"
?>
<!DOCTYPE article PUBLIC "-//OASIS//DTD DocBook XML V4.5//EN"\
 "docbook/dtd/xml/4.5/docbookx.dtd">
<article lang="en">
  <articleinfo>
    <title>%(HEADER1)s</title>
    <authorgroup>
      <author><othername>%(HEADER2)s</othername></author>
    </authorgroup>
    <date>%(HEADER3)s</date>
  </articleinfo>
""",
    "man": """\
.TH "%(HEADER1)s" 1 "%(HEADER3)s" "%(HEADER2)s"
""",
    "mgp": """\
#!/usr/X11R6/bin/mgp -t 90
%%deffont "normal"    xfont  "utopia-medium-r", charset "iso8859-1"
%%deffont "normal-i"  xfont  "utopia-medium-i", charset "iso8859-1"
%%deffont "normal-b"  xfont  "utopia-bold-r"  , charset "iso8859-1"
%%deffont "normal-bi" xfont  "utopia-bold-i"  , charset "iso8859-1"
%%deffont "mono"      xfont "courier-medium-r", charset "iso8859-1"
%%default 1 size 5
%%default 2 size 8, fore "yellow", font "normal-b", center
%%default 3 size 5, fore "white",  font "normal", left, prefix "  "
%%tab 1 size 4, vgap 30, prefix "     ", icon arc "red" 40, leftfill
%%tab 2 prefix "            ", icon arc "orange" 40, leftfill
%%tab 3 prefix "                   ", icon arc "brown" 40, leftfill
%%tab 4 prefix "                          ", icon arc "darkmagenta" 40, leftfill
%%tab 5 prefix "                                ", icon arc "magenta" 40, leftfill
%%%%------------------------- end of headers -----------------------------
%%page





%%size 10, center, fore "yellow"
%(HEADER1)s

%%font "normal-i", size 6, fore "white", center
%(HEADER2)s

%%font "mono", size 7, center
%(HEADER3)s
""",
    "moin": """\
'''%(HEADER1)s'''

''%(HEADER2)s''

%(HEADER3)s
""",
    "gwiki": """\
*%(HEADER1)s*

%(HEADER2)s

_%(HEADER3)s_
""",
    "adoc": """\
= %(HEADER1)s
%(HEADER2)s
%(HEADER3)s
""",
    "doku": """\
===== %(HEADER1)s =====

**//%(HEADER2)s//**

//%(HEADER3)s//
""",
    "pmw": """\
(:Title %(HEADER1)s:)

(:Description %(HEADER2)s:)

(:Summary %(HEADER3)s:)
""",
    "wiki": """\
'''%(HEADER1)s'''

%(HEADER2)s

''%(HEADER3)s''
""",
    "tex": r"""\documentclass{article}
\usepackage{booktabs} %% needed for tables
\usepackage{graphicx}
\usepackage{paralist} %% needed for compact lists
\usepackage[normalem]{ulem} %% needed by strike
\usepackage[urlcolor=blue,colorlinks=true]{hyperref}
\usepackage[%(ENCODING)s]{inputenc}  %% char encoding
\usepackage{%(STYLE)s}  %% user defined

\title{%(HEADER1)s}
\author{%(HEADER2)s}
\begin{document}
\date{%(HEADER3)s}
\maketitle
\clearpage
""",
    "lout": """\
@SysInclude { doc }
@Document
  @InitialFont { Times Base 12p }  # Times, Courier, Helvetica, ...
  @PageOrientation { Portrait }    # Portrait, Landscape
  @ColumnNumber { 1 }              # Number of columns (2, 3, ...)
  @PageHeaders { Simple }          # None, Simple, Titles, NoTitles
  @InitialLanguage { English }     # German, French, Portuguese, ...
  @OptimizePages { Yes }           # Yes/No smart page break feature
//
@Text @Begin
@Display @Heading { %(HEADER1)s }
@Display @I { %(HEADER2)s }
@Display { %(HEADER3)s }
#@NP                               # Break page after Headers
""",
    "creole": """\
%(HEADER1)s
%(HEADER2)s
%(HEADER3)s
""",
    "md": """\
%(HEADER1)s
%(HEADER2)s
%(HEADER3)s
""",
    "ctx": r"""\mainlanguage[en]
\definecolor[linkcolor][h=0007F0]
\setupcolors[state=start]
\setupinteraction[state=start,
    title={%(HEADER1)s},
    author={%(HEADER2)s},
    contrastcolor=linkcolor,
    color=linkcolor,
    ]
\placebookmarks[section,subsection,subsubsection]
\definehead[myheaderone][title]
\setuphead
  [myheaderone]
  [textstyle=cap,
   align=middle,
   after=\nowhitespace
  ]
\definehead[myheadertwo][subject]
\setuphead
  [myheadertwo]
  [ before=\nowhitespace,
   align=middle,
   after=\nowhitespace
  ]
\definehead[myheaderthree][subsubject]
\setuphead
  [myheaderthree]
  [before=\nowhitespace,
   align=middle,
  ]
\definedescription
   [compdesc]
   [alternative=serried,
    headstyle=bold,
    width=broad,
    ]
\setupTABLE[frame=off]
\setupexternalfigures[maxwidth=0.7\textwidth]
\setupheadertexts[]
\setupfootertexts[pagenumber]
\setupwhitespace[medium]
\setupheads[number=no]
\usemodule[%(STYLE)s]
\starttext

\myheaderone{%(HEADER1)s}
\myheadertwo{%(HEADER2)s}
\myheaderthree{%(HEADER3)s}

""",
    # @SysInclude { tbl }                   # Tables support
    # setup: @MakeContents { Yes }          # show TOC
    # setup: @SectionGap                    # break page at each section
}
assert set(HEADER_TEMPLATE) == set(TARGETS)


##############################################################################


def getTags(config):
    "Returns all the known tags for the specified target"

    keys = """
    title1              numtitle1
    title2              numtitle2
    title3              numtitle3
    title4              numtitle4
    title5              numtitle5
    title1Open          title1Close
    title2Open          title2Close
    title3Open          title3Close
    title4Open          title4Close
    title5Open          title5Close
    blockTitle1Open     blockTitle1Close
    blockTitle2Open     blockTitle2Close
    blockTitle3Open     blockTitle3Close

    paragraphOpen       paragraphClose
    blockVerbOpen       blockVerbClose  blockVerbLine
    blockQuoteOpen      blockQuoteClose blockQuoteLine
    blockCommentOpen    blockCommentClose

    fontMonoOpen        fontMonoClose
    fontBoldOpen        fontBoldClose
    fontItalicOpen      fontItalicClose
    fontUnderlineOpen   fontUnderlineClose
    fontStrikeOpen      fontStrikeClose

    listOpen            listClose
    listOpenCompact     listCloseCompact
    listItemOpen        listItemClose     listItemLine
    numlistOpen         numlistClose
    numlistOpenCompact  numlistCloseCompact
    numlistItemOpen     numlistItemClose  numlistItemLine
    deflistOpen         deflistClose
    deflistOpenCompact  deflistCloseCompact
    deflistItem1Open    deflistItem1Close
    deflistItem2Open    deflistItem2Close deflistItem2LinePrefix

    bar1                bar2
    url                 urlMark
    email               emailMark
    img                 imgAlignLeft  imgAlignRight  imgAlignCenter
                       _imgAlignLeft _imgAlignRight _imgAlignCenter

    tableOpen           tableClose
    _tableBorder        _tableAlignLeft      _tableAlignCenter
    tableRowOpen        tableRowClose        tableRowSep
    tableTitleRowOpen   tableTitleRowClose
    tableCellOpen       tableCellClose       tableCellSep
    tableTitleCellOpen  tableTitleCellClose  tableTitleCellSep
    _tableColAlignLeft  _tableColAlignRight  _tableColAlignCenter
    _tableCellAlignLeft _tableCellAlignRight _tableCellAlignCenter
    _tableCellColSpan   tableColAlignSep
    _tableCellMulticolOpen
    _tableCellMulticolClose

    bodyOpen            bodyClose
    cssOpen             cssClose
    tocOpen             tocClose             TOC
    anchor
    comment
    pageBreak
    EOD
    """.split()

    # TIP: \a represents the current text inside the mark
    # TIP: ~A~, ~B~ and ~C~ are expanded to other tags parts
    alltags = {
        "txt": {
            "title1": "  \a",
            "title2": "\t\a",
            "title3": "\t\t\a",
            "title4": "\t\t\t\a",
            "title5": "\t\t\t\t\a",
            "blockQuoteLine": "\t",
            "listItemOpen": "- ",
            "numlistItemOpen": "\a. ",
            "bar1": "\a",
            "url": "\a",
            "urlMark": "\a (\a)",
            "email": "\a",
            "emailMark": "\a (\a)",
            "img": "[\a]",
        },
        "html": {
            "anchor": ' id="\a"',
            "bar1": '<hr class="light">',
            "bar2": '<hr class="heavy">',
            "blockQuoteClose": "</blockquote>",
            "blockQuoteOpen": "<blockquote>",
            "blockVerbClose": "</pre>",
            "blockVerbOpen": "<pre>",
            "bodyClose": "</div>",
            "bodyOpen": '<div class="body">',
            "comment": "<!-- \a -->",
            "cssClose": "</style>",
            "cssOpen": "<style>",
            "deflistClose": "</dl>",
            "deflistItem1Close": "</dt>",
            "deflistItem1Open": "<dt>",
            "deflistItem2Close": "</dd>",
            "deflistItem2Open": "<dd>",
            "deflistOpen": "<dl>",
            "email": '<a href="mailto:\a">\a</a>',
            "emailMark": '<a href="mailto:\a">\a</a>',
            "EOD": "</body></html>",
            "fontBoldClose": "</strong>",
            "fontBoldOpen": "<strong>",
            "fontItalicClose": "</em>",
            "fontItalicOpen": "<em>",
            "fontMonoClose": "</code>",
            "fontMonoOpen": "<code>",
            "fontStrikeClose": "</del>",
            "fontStrikeOpen": "<del>",
            "fontUnderlineClose": "</span>",
            "fontUnderlineOpen": '<span class="underline">',
            "_imgAlignCenter": ' class="center"',
            "_imgAlignLeft": ' class="left"',
            "_imgAlignRight": ' class="right"',
            "img": '<img~a~ src="\a" alt="">',
            "listClose": "</ul>",
            "listItemClose": "</li>",
            "listItemOpen": "<li>",
            "listOpen": "<ul>",
            "numlistClose": "</ol>",
            "numlistItemClose": "</li>",
            "numlistItemOpen": "<li>",
            "numlistOpen": "<ol>",
            "paragraphClose": "</p>",
            "paragraphOpen": "<p>",
            "_tableAlignCenter": ' style="margin-left: auto; margin-right: auto;"',
            "_tableBorder": ' class="tableborder"',
            "_tableCellAlignCenter": ' class="center"',
            "_tableCellAlignRight": ' class="right"',
            "tableCellClose": "</td>",
            "_tableCellColSpan": ' colspan="\a"',
            "tableCellOpen": "<td~a~~s~>",
            "tableClose": "</table>",
            "tableOpen": "<table~a~~b~>",
            "tableRowClose": "</tr>",
            "tableRowOpen": "<tr>",
            "tableTitleCellClose": "</th>",
            "tableTitleCellOpen": "<th~s~>",
            "title1Close": "</section>",
            "title1Open": "<section~A~>\n<h1>\a</h1>",
            "title2Close": "</section>",
            "title2Open": "<section~A~>\n<h2>\a</h2>",
            "title3Close": "</section>",
            "title3Open": "<section~A~>\n<h3>\a</h3>",
            "title4Close": "</section>",
            "title4Open": "<section~A~>\n<h4>\a</h4>",
            "title5Close": "</section>",
            "title5Open": "<section~A~>\n<h5>\a</h5>",
            "tocClose": "</nav>",
            "tocOpen": "<nav>",
            "url": '<a href="\a">\a</a>',
            "urlMark": '<a href="\a">\a</a>',
        },
        "sgml": {
            "paragraphOpen": "<p>",
            "title1": "<sect>\a~A~<p>",
            "title2": "<sect1>\a~A~<p>",
            "title3": "<sect2>\a~A~<p>",
            "title4": "<sect3>\a~A~<p>",
            "title5": "<sect4>\a~A~<p>",
            "anchor": '<label id="\a">',
            "blockVerbOpen": "<tscreen><verb>",
            "blockVerbClose": "</verb></tscreen>",
            "blockQuoteOpen": "<quote>",
            "blockQuoteClose": "</quote>",
            "fontMonoOpen": "<tt>",
            "fontMonoClose": "</tt>",
            "fontBoldOpen": "<bf>",
            "fontBoldClose": "</bf>",
            "fontItalicOpen": "<em>",
            "fontItalicClose": "</em>",
            "fontUnderlineOpen": "<bf><em>",
            "fontUnderlineClose": "</em></bf>",
            "listOpen": "<itemize>",
            "listClose": "</itemize>",
            "listItemOpen": "<item>",
            "numlistOpen": "<enum>",
            "numlistClose": "</enum>",
            "numlistItemOpen": "<item>",
            "deflistOpen": "<descrip>",
            "deflistClose": "</descrip>",
            "deflistItem1Open": "<tag>",
            "deflistItem1Close": "</tag>",
            "bar1": "<!-- \a -->",
            "url": '<htmlurl url="\a" name="\a">',
            "urlMark": '<htmlurl url="\a" name="\a">',
            "email": '<htmlurl url="mailto:\a" name="\a">',
            "emailMark": '<htmlurl url="mailto:\a" name="\a">',
            "img": '<figure><ph vspace=""><img src="\a"></figure>',
            "tableOpen": '<table><tabular ca="~C~">',
            "tableClose": "</tabular></table>",
            "tableRowSep": "<rowsep>",
            "tableCellSep": "<colsep>",
            "_tableColAlignLeft": "l",
            "_tableColAlignRight": "r",
            "_tableColAlignCenter": "c",
            "comment": "<!-- \a -->",
            "TOC": "<toc>",
            "EOD": "</article>",
        },
        "dbk": {
            "paragraphOpen": "<para>",
            "paragraphClose": "</para>",
            "title1Open": "~A~<sect1><title>\a</title>",
            "title1Close": "</sect1>",
            "title2Open": "~A~  <sect2><title>\a</title>",
            "title2Close": "  </sect2>",
            "title3Open": "~A~    <sect3><title>\a</title>",
            "title3Close": "    </sect3>",
            "title4Open": "~A~      <sect4><title>\a</title>",
            "title4Close": "      </sect4>",
            "title5Open": "~A~        <sect5><title>\a</title>",
            "title5Close": "        </sect5>",
            "anchor": '<anchor id="\a"/>\n',
            "blockVerbOpen": "<programlisting>",
            "blockVerbClose": "</programlisting>",
            "blockQuoteOpen": "<blockquote><para>",
            "blockQuoteClose": "</para></blockquote>",
            "fontMonoOpen": "<code>",
            "fontMonoClose": "</code>",
            "fontBoldOpen": '<emphasis role="bold">',
            "fontBoldClose": "</emphasis>",
            "fontItalicOpen": "<emphasis>",
            "fontItalicClose": "</emphasis>",
            "fontUnderlineOpen": '<emphasis role="underline">',
            "fontUnderlineClose": "</emphasis>",
            "fontStrikeOpen": None,  # Maybe <emphasis role="strikethrough">
            "fontStrikeClose": None,  # Maybe </emphasis>
            "listOpen": "<itemizedlist>",
            "listClose": "</itemizedlist>",
            "listItemOpen": "<listitem><para>",
            "listItemClose": "</para></listitem>",
            "numlistOpen": '<orderedlist numeration="arabic">',
            "numlistClose": "</orderedlist>",
            "numlistItemOpen": "<listitem><para>",
            "numlistItemClose": "</para></listitem>",
            "deflistOpen": "<variablelist>",
            "deflistClose": "</variablelist>",
            "deflistItem1Open": "<varlistentry><term>",
            "deflistItem1Close": "</term>",
            "deflistItem2Open": "<listitem><para>",
            "deflistItem2Close": "</para></listitem></varlistentry>",
            "bar1": None,
            "bar2": None,
            "url": '<ulink url="\a">\a</ulink>',
            "urlMark": '<ulink url="\a">\a</ulink>',
            "email": "<email>\a</email>",
            "emailMark": "<email>\a</email>",
            "img": (
                '<mediaobject><imageobject><imagedata fileref="\a"/>'
                "</imageobject></mediaobject>"
            ),
            # Tables not supported, need to know number of columns.
            # 'tableOpen'            : '<informaltable><tgroup cols=""><tbody>',
            # 'tableClose'           : '</tbody></tgroup></informaltable>' ,
            # 'tableRowOpen'         : '<row>'                             ,
            # 'tableRowClose'        : '</row>'                            ,
            # 'tableCellOpen'        : '<entry>'                           ,
            # 'tableCellClose'       : '</entry>'                          ,
            # 'tableTitleRowOpen'    : '<thead>'                           ,
            # 'tableTitleRowClose'   : '</thead>'                          ,
            # '_tableBorder'         : ' frame="all"'                      ,
            # '_tableAlignCenter'    : ' align="center"'                   ,
            # '_tableCellAlignRight' : ' align="right"'                    ,
            # '_tableCellAlignCenter': ' align="center"'                   ,
            # '_tableCellColSpan'    : ' COLSPAN="\a"'                     ,
            "TOC": "<index/>",
            "comment": "<!-- \a -->",
            "EOD": "</article>",
        },
        "tex": {
            "title1": "~A~\\section*{\a}",
            "title2": "~A~\\subsection*{\a}",
            "title3": "~A~\\subsubsection*{\a}",
            # title 4/5: DIRTY: para+BF+\\+\n
            "title4": "~A~\\paragraph{}\\textbf{\a}\\\\\n",
            "title5": "~A~\\paragraph{}\\textbf{\a}\\\\\n",
            "numtitle1": "\n~A~\\section{\a}",
            "numtitle2": "~A~\\subsection{\a}",
            "numtitle3": "~A~\\subsubsection{\a}",
            "anchor": "\\hypertarget{\a}{}\n",
            "blockVerbOpen": "\\begin{verbatim}",
            "blockVerbClose": "\\end{verbatim}",
            "blockQuoteOpen": "\\begin{quotation}",
            "blockQuoteClose": "\\end{quotation}",
            "fontMonoOpen": "\\texttt{",
            "fontMonoClose": "}",
            "fontBoldOpen": "\\textbf{",
            "fontBoldClose": "}",
            "fontItalicOpen": "\\textit{",
            "fontItalicClose": "}",
            "fontUnderlineOpen": "\\underline{",
            "fontUnderlineClose": "}",
            "fontStrikeOpen": "\\sout{",
            "fontStrikeClose": "}",
            "listOpen": "\\begin{itemize}",
            "listClose": "\\end{itemize}",
            "listOpenCompact": "\\begin{compactitem}",
            "listCloseCompact": "\\end{compactitem}",
            "listItemOpen": "\\item ",
            "numlistOpen": "\\begin{enumerate}",
            "numlistClose": "\\end{enumerate}",
            "numlistOpenCompact": "\\begin{compactenum}",
            "numlistCloseCompact": "\\end{compactenum}",
            "numlistItemOpen": "\\item ",
            "deflistOpen": "\\begin{description}",
            "deflistClose": "\\end{description}",
            "deflistOpenCompact": "\\begin{compactdesc}",
            "deflistCloseCompact": "\\end{compactdesc}",
            "deflistItem1Open": "\\item[",
            "deflistItem1Close": "]",
            "bar1": "\\hrulefill{}",
            "bar2": "\\rule{\\linewidth}{1mm}",
            "url": "\\htmladdnormallink{\a}{\a}",
            "urlMark": "\\htmladdnormallink{\a}{\a}",
            "email": "\\htmladdnormallink{\a}{mailto:\a}",
            "emailMark": "\\htmladdnormallink{\a}{mailto:\a}",
            "img": "\\includegraphics{\a}",
            "tableOpen": "\\begin{tabular}{@{}~C~@{}}",
            "tableClose": "\\end{tabular}",
            "tableRowOpen": None,
            "tableRowClose": " \\\\",
            "tableTitleRowClose": " \\\\\n\\midrule",
            "tableCellSep": " & ",
            "_tableColAlignLeft": "l",
            "_tableColAlignRight": "r",
            "_tableColAlignCenter": "c",
            "_tableCellAlignLeft": "l",
            "_tableCellAlignRight": "r",
            "_tableCellAlignCenter": "c",
            "_tableCellColSpan": "\a",
            "_tableCellMulticolOpen": "\\multicolumn{\a}{~C~}{",
            "_tableCellMulticolClose": "}",
            "tableColAlignSep": None,
            "comment": "% \a",
            "TOC": "\\tableofcontents",
            "pageBreak": "\\clearpage",
            "EOD": "\\end{document}",
        },
        "lout": {
            "paragraphOpen": "@LP",
            "blockTitle1Open": "@BeginSections",
            "blockTitle1Close": "@EndSections",
            "blockTitle2Open": " @BeginSubSections",
            "blockTitle2Close": " @EndSubSections",
            "blockTitle3Open": "  @BeginSubSubSections",
            "blockTitle3Close": "  @EndSubSubSections",
            "title1Open": "~A~@Section @Title { \a } @Begin",
            "title1Close": "@End @Section",
            "title2Open": "~A~ @SubSection @Title { \a } @Begin",
            "title2Close": " @End @SubSection",
            "title3Open": "~A~  @SubSubSection @Title { \a } @Begin",
            "title3Close": "  @End @SubSubSection",
            "title4Open": "~A~@LP @LeftDisplay @B { \a }",
            "title5Open": "~A~@LP @LeftDisplay @B { \a }",
            "anchor": "@Tag { \a }\n",
            "blockVerbOpen": "@LP @ID @F @RawVerbatim @Begin",
            "blockVerbClose": "@End @RawVerbatim",
            "blockQuoteOpen": "@QD {",
            "blockQuoteClose": "}",
            # enclosed inside {} to deal with joined**words**
            "fontMonoOpen": "{@F {",
            "fontMonoClose": "}}",
            "fontBoldOpen": "{@B {",
            "fontBoldClose": "}}",
            "fontItalicOpen": "{@II {",
            "fontItalicClose": "}}",
            "fontUnderlineOpen": "{@Underline{",
            "fontUnderlineClose": "}}",
            # the full form is more readable, but could be BL EL LI NL TL DTI
            "listOpen": "@BulletList",
            "listClose": "@EndList",
            "listItemOpen": "@ListItem{",
            "listItemClose": "}",
            "numlistOpen": "@NumberedList",
            "numlistClose": "@EndList",
            "numlistItemOpen": "@ListItem{",
            "numlistItemClose": "}",
            "deflistOpen": "@TaggedList",
            "deflistClose": "@EndList",
            "deflistItem1Open": "@DropTagItem {",
            "deflistItem1Close": "}",
            "deflistItem2Open": "{",
            "deflistItem2Close": "}",
            "bar1": "@DP @FullWidthRule",
            "url": "{blue @Colour { \a }}",
            "urlMark": "\a ({blue @Colour { \a }})",
            "email": "{blue @Colour { \a }}",
            "emailMark": "\a ({blue @Colour{ \a }})",
            "img": "~A~@IncludeGraphic { \a }",  # eps only!
            "_imgAlignLeft": "@LeftDisplay ",
            "_imgAlignRight": "@RightDisplay ",
            "_imgAlignCenter": "@CentredDisplay ",
            # lout tables are *way* too complicated, no support for now
            # 'tableOpen'            : '~A~@Tbl~B~\naformat{ @Cell A | @Cell B } {',
            # 'tableClose'           : '}'     ,
            # 'tableRowOpen'         : '@Rowa\n'       ,
            # 'tableTitleRowOpen'    : '@HeaderRowa'       ,
            # 'tableCenterAlign'     : '@CentredDisplay '         ,
            # 'tableCellOpen'        : '\a {'                     ,  # A, B, ...
            # 'tableCellClose'       : '}'                        ,
            # '_tableBorder'         : '\nrule {yes}'             ,
            "comment": "# \a",
            # @MakeContents must be on the config file
            "TOC": "@DP @ContentsGoesHere @DP",
            "pageBreak": "@NP",
            "EOD": "@End @Text",
        },
        # https://moinmo.in/HelpOnMoinWikiSyntax
        "moin": {
            "title1": "= \a =",
            "title2": "== \a ==",
            "title3": "=== \a ===",
            "title4": "==== \a ====",
            "title5": "===== \a =====",
            "blockVerbOpen": "{{{",
            "blockVerbClose": "}}}",
            "blockQuoteLine": "  ",
            "fontMonoOpen": "{{{",
            "fontMonoClose": "}}}",
            "fontBoldOpen": "'''",
            "fontBoldClose": "'''",
            "fontItalicOpen": "''",
            "fontItalicClose": "''",
            "fontUnderlineOpen": "__",
            "fontUnderlineClose": "__",
            "fontStrikeOpen": "--(",
            "fontStrikeClose": ")--",
            "listItemOpen": " * ",
            "numlistItemOpen": " \a. ",
            "deflistItem1Open": " ",
            "deflistItem1Close": "::",
            "deflistItem2LinePrefix": " :: ",
            "bar1": "----",
            "bar2": "--------",
            "url": "[[\a]]",
            "urlMark": "[[\a|\a]]",
            "email": "\a",
            "emailMark": "[[mailto:\a|\a]]",
            "img": "[\a]",
            "tableRowOpen": "||",
            "tableCellOpen": "~A~",
            "tableCellClose": "||",
            "tableTitleCellClose": "||",
            "_tableCellAlignRight": "<)>",
            "_tableCellAlignCenter": "<:>",
            "comment": "/* \a */",
            "TOC": "[[TableOfContents]]",
        },
        # http://code.google.com/p/support/wiki/WikiSyntax
        "gwiki": {
            "title1": "= \a =",
            "title2": "== \a ==",
            "title3": "=== \a ===",
            "title4": "==== \a ====",
            "title5": "===== \a =====",
            "blockVerbOpen": "{{{",
            "blockVerbClose": "}}}",
            "blockQuoteLine": "  ",
            "fontMonoOpen": "{{{",
            "fontMonoClose": "}}}",
            "fontBoldOpen": "*",
            "fontBoldClose": "*",
            "fontItalicOpen": "_",  # underline == italic
            "fontItalicClose": "_",
            "fontStrikeOpen": "~~",
            "fontStrikeClose": "~~",
            "listItemOpen": " * ",
            "numlistItemOpen": " # ",
            "url": "\a",
            "urlMark": "[\a \a]",
            "email": "mailto:\a",
            "emailMark": "[mailto:\a \a]",
            "img": "[\a]",
            "tableRowOpen": "|| ",
            "tableRowClose": " ||",
            "tableCellSep": " || ",
        },
        # http://powerman.name/doc/asciidoc
        "adoc": {
            "title1": "== \a",
            "title2": "=== \a",
            "title3": "==== \a",
            "title4": "===== \a",
            "title5": "===== \a",
            "blockVerbOpen": "----",
            "blockVerbClose": "----",
            "fontMonoOpen": "+",
            "fontMonoClose": "+",
            "fontBoldOpen": "*",
            "fontBoldClose": "*",
            "fontItalicOpen": "_",
            "fontItalicClose": "_",
            "listItemOpen": "- ",
            "listItemLine": "\t",
            "numlistItemOpen": ". ",
            "url": "\a",
            "urlMark": "\a[\a]",
            "email": "mailto:\a",
            "emailMark": "mailto:\a[\a]",
            "img": "image::\a[]",
        },
        # http://wiki.splitbrain.org/wiki:syntax
        # Hint: <br> is \\ $
        # Hint: You can add footnotes ((This is a footnote))
        "doku": {
            "title1": "===== \a =====",
            "title2": "==== \a ====",
            "title3": "=== \a ===",
            "title4": "== \a ==",
            "title5": "= \a =",
            # DokuWiki uses '  ' identation to mark verb blocks (see indentverbblock)
            "blockQuoteLine": ">",
            "fontMonoOpen": "''",
            "fontMonoClose": "''",
            "fontBoldOpen": "**",
            "fontBoldClose": "**",
            "fontItalicOpen": "//",
            "fontItalicClose": "//",
            "fontUnderlineOpen": "__",
            "fontUnderlineClose": "__",
            "fontStrikeOpen": "<del>",
            "fontStrikeClose": "</del>",
            "listItemOpen": "  * ",
            "numlistItemOpen": "  - ",
            "bar1": "----",
            "url": "[[\a]]",
            "urlMark": "[[\a|\a]]",
            "email": "[[\a]]",
            "emailMark": "[[\a|\a]]",
            "img": "{{\a}}",
            "imgAlignLeft": "{{\a }}",
            "imgAlignRight": "{{ \a}}",
            "imgAlignCenter": "{{ \a }}",
            "tableTitleRowOpen": "^ ",
            "tableTitleRowClose": " ^",
            "tableTitleCellSep": " ^ ",
            "tableRowOpen": "| ",
            "tableRowClose": " |",
            "tableCellSep": " | ",
            # DokuWiki has no attributes. The content must be aligned!
            # '_tableCellAlignRight' : '<)>'           , # ??
            # '_tableCellAlignCenter': '<:>'           , # ??
            # DokuWiki colspan is the same as txt2tags' with multiple |||
            # 'comment'             : '## \a'         , # ??
            # TOC is automatic
        },
        # http://www.pmwiki.org/wiki/PmWiki/TextFormattingRules
        "pmw": {
            "title1": "~A~! \a ",
            "title2": "~A~!! \a ",
            "title3": "~A~!!! \a ",
            "title4": "~A~!!!! \a ",
            "title5": "~A~!!!!! \a ",
            "blockQuoteOpen": "->",
            "blockQuoteClose": "\n",
            # In-text font
            "fontMonoOpen": "@@",
            "fontMonoClose": "@@",
            "fontBoldOpen": "'''",
            "fontBoldClose": "'''",
            "fontItalicOpen": "''",
            "fontItalicClose": "''",
            "fontUnderlineOpen": "{+",
            "fontUnderlineClose": "+}",
            "fontStrikeOpen": "{-",
            "fontStrikeClose": "-}",
            # Lists
            "listItemLine": "*",
            "numlistItemLine": "#",
            "deflistItem1Open": ": ",
            "deflistItem1Close": ":",
            # Verbatim block
            "blockVerbOpen": "[@",
            "blockVerbClose": "@]",
            "bar1": "----",
            # URL, email and anchor
            "url": "\a",
            "urlMark": "[[\a -> \a]]",
            "email": "\a",
            "emailMark": "[[\a -> mailto:\a]]",
            "anchor": "[[#\a]]\n",
            # Image markup
            "img": "\a",
            # Table attributes
            "tableTitleRowOpen": "||! ",
            "tableTitleRowClose": "||",
            "tableTitleCellSep": " ||!",
            "tableRowOpen": "||",
            "tableRowClose": "||",
            "tableCellSep": " ||",
        },
        # http://en.wikipedia.org/wiki/Help:Editing
        "wiki": {
            "title1": "== \a ==",
            "title2": "=== \a ===",
            "title3": "==== \a ====",
            "title4": "===== \a =====",
            "title5": "====== \a ======",
            "blockVerbOpen": "<pre>",
            "blockVerbClose": "</pre>",
            "blockQuoteOpen": "<blockquote>",
            "blockQuoteClose": "</blockquote>",
            "fontMonoOpen": "<tt>",
            "fontMonoClose": "</tt>",
            "fontBoldOpen": "'''",
            "fontBoldClose": "'''",
            "fontItalicOpen": "''",
            "fontItalicClose": "''",
            "fontUnderlineOpen": "<u>",
            "fontUnderlineClose": "</u>",
            "fontStrikeOpen": "<s>",
            "fontStrikeClose": "</s>",
            # XXX Mixed lists not working: *#* list inside numlist inside list
            "listItemLine": "*",
            "numlistItemLine": "#",
            "deflistItem1Open": "; ",
            "deflistItem2LinePrefix": ": ",
            "bar1": "----",
            "url": "[\a]",
            "urlMark": "[\a \a]",
            "email": "mailto:\a",
            "emailMark": "[mailto:\a \a]",
            # [[Image:foo.png|right|Optional alt/caption text]]
            # (right, left, center, none)
            "img": "[[Image:\a~A~]]",
            "_imgAlignLeft": "|left",
            "_imgAlignCenter": "|center",
            "_imgAlignRight": "|right",
            # {| border="1" cellspacing="0" cellpadding="4" align="center"
            "tableOpen": '{|~A~~B~ cellpadding="4"',
            "tableClose": "|}",
            "tableRowOpen": "|-\n| ",
            "tableTitleRowOpen": "|-\n! ",
            "tableCellSep": " || ",
            "tableTitleCellSep": " !! ",
            "_tableBorder": ' border="1"',
            "_tableAlignCenter": ' align="center"',
            "comment": "<!-- \a -->",
            "TOC": "__TOC__",
        },
        # http://www.inference.phy.cam.ac.uk/mackay/mgp/SYNTAX
        # http://en.wikipedia.org/wiki/MagicPoint
        "mgp": {
            "paragraphOpen": '%font "normal", size 5',
            "title1": "%page\n\n\a\n",
            "title2": "%page\n\n\a\n",
            "title3": "%page\n\n\a\n",
            "title4": "%page\n\n\a\n",
            "title5": "%page\n\n\a\n",
            "blockVerbOpen": '%font "mono"',
            "blockVerbClose": '%font "normal"',
            "blockQuoteOpen": '%prefix "       "',
            "blockQuoteClose": '%prefix "  "',
            "fontMonoOpen": '\n%cont, font "mono"\n',
            "fontMonoClose": '\n%cont, font "normal"\n',
            "fontBoldOpen": '\n%cont, font "normal-b"\n',
            "fontBoldClose": '\n%cont, font "normal"\n',
            "fontItalicOpen": '\n%cont, font "normal-i"\n',
            "fontItalicClose": '\n%cont, font "normal"\n',
            "fontUnderlineOpen": '\n%cont, fore "cyan"\n',
            "fontUnderlineClose": '\n%cont, fore "white"\n',
            "listItemLine": "\t",
            "numlistItemLine": "\t",
            "numlistItemOpen": "\a. ",
            "deflistItem1Open": '\t\n%cont, font "normal-b"\n',
            "deflistItem1Close": '\n%cont, font "normal"\n',
            "bar1": '%bar "white" 5',
            "bar2": "%pause",
            "url": '\n%cont, fore "cyan"\n\a' + '\n%cont, fore "white"\n',
            "urlMark": '\a \n%cont, fore "cyan"\n\a' + '\n%cont, fore "white"\n',
            "email": '\n%cont, fore "cyan"\n\a' + '\n%cont, fore "white"\n',
            "emailMark": '\a \n%cont, fore "cyan"\n\a' + '\n%cont, fore "white"\n',
            "img": '~A~\n%newimage "\a"\n%left\n',
            "_imgAlignLeft": "\n%left",
            "_imgAlignRight": "\n%right",
            "_imgAlignCenter": "\n%center",
            "comment": "%% \a",
            "pageBreak": "%page\n\n\n",
            "EOD": "%%EOD",
        },
        # man groff_man ; man 7 groff
        "man": {
            "paragraphOpen": ".P",
            "title1": ".SH \a",
            "title2": ".SS \a",
            "title3": ".SS \a",
            "title4": ".SS \a",
            "title5": ".SS \a",
            "blockVerbOpen": ".nf",
            "blockVerbClose": ".fi\n",
            "blockQuoteOpen": ".RS",
            "blockQuoteClose": ".RE",
            "fontBoldOpen": "\\fB",
            "fontBoldClose": "\\fR",
            "fontItalicOpen": "\\fI",
            "fontItalicClose": "\\fR",
            "listOpen": ".RS",
            "listItemOpen": ".IP \\(bu 3\n",
            "listClose": ".RE\n.IP",
            "numlistOpen": ".RS",
            "numlistItemOpen": ".IP \a. 3\n",
            "numlistClose": ".RE\n.IP",
            "deflistItem1Open": ".TP\n",
            "bar1": "\n\n",
            "url": "\a",
            "urlMark": "\a (\a)",
            "email": "\a",
            "emailMark": "\a (\a)",
            "img": "\a",
            "tableOpen": ".TS\n~A~~B~tab(^); ~C~.",
            "tableClose": ".TE",
            "tableRowOpen": " ",
            "tableCellSep": "^",
            "_tableAlignCenter": "center, ",
            "_tableBorder": "allbox, ",
            "_tableColAlignLeft": "l",
            "_tableColAlignRight": "r",
            "_tableColAlignCenter": "c",
            "comment": '.\\" \a',
        },
        # http://www.wikicreole.org/wiki/AllMarkup
        "creole": {
            "title1": "= \a =",
            "title2": "== \a ==",
            "title3": "=== \a ===",
            "title4": "==== \a ====",
            "title5": "===== \a =====",
            "blockVerbOpen": "{{{",
            "blockVerbClose": "}}}",
            "blockQuoteLine": "  ",
            "fontMonoOpen": None,  # planned for 2.0,
            "fontMonoClose": None,  # meanwhile we disable it
            "fontBoldOpen": "**",
            "fontBoldClose": "**",
            "fontItalicOpen": "//",
            "fontItalicClose": "//",
            "fontUnderlineOpen": "//",  # no underline in 1.0, planned for 2.0,
            "fontUnderlineClose": "//",  # meanwhile we use italic (emphasized)
            "fontStrikeOpen": None,  # planned for 2.0,
            "fontStrikeClose": None,  # meanwhile we disable it
            "listItemLine": "*",
            "numlistItemLine": "#",
            "deflistItem2LinePrefix": ":",
            "bar1": "----",
            "url": "[[\a]]",
            "urlMark": "[[\a|\a]]",
            "img": "{{\a}}",
            "tableTitleRowOpen": "|= ",
            "tableTitleRowClose": "|",
            "tableTitleCellSep": " |= ",
            "tableRowOpen": "| ",
            "tableRowClose": " |",
            "tableCellSep": " | ",
            # TODO: placeholder (mark for unknown syntax)
            # if possible: http://www.wikicreole.org/wiki/Placeholder
        },
        # regular markdown: http://daringfireball.net/projects/markdown/syntax
        # markdown extra:   http://michelf.com/projects/php-markdown/extra/
        "md": {
            "title1": "# \a ",
            "title2": "## \a ",
            "title3": "### \a ",
            "title4": "#### \a ",
            "title5": "##### \a ",
            "blockVerbLine": "    ",
            "blockQuoteLine": "> ",
            "fontMonoOpen": "`",
            "fontMonoClose": "`",
            "fontBoldOpen": "**",
            "fontBoldClose": "**",
            "fontItalicOpen": "*",
            "fontItalicClose": "*",
            "fontUnderlineOpen": None,
            "fontUnderlineClose": None,
            "fontStrikeOpen": "~~",
            "fontStrikeClose": "~~",
            # Lists
            "listOpenCompact": None,
            "listItemLine": None,
            "listItemOpen": "*",
            "numlistItemLine": None,
            "numlistItemOpen": "1.",
            "deflistItem1Open": ": ",
            "deflistItem1Close": None,
            "deflistItem2Open": None,
            "deflistItem2Close": None,
            # Verbatim block
            "blockVerbOpen": None,
            "blockVerbClose": None,
            "bar1": "---",
            "bar2": "---",
            # URL, email and anchor
            "url": "\a",
            "urlMark": "[\a](\a)",
            "email": "<\a>",
            "emailMark": "[\a](mailto:\a)",
            "anchor": None,
            # Image markup
            "img": "![](\a)",
            "imgAlignLeft": None,
            "imgAlignRight": None,
            "imgAlignCenter": None,
            # Table attributes
            "tableTitleRowOpen": "| ",
            "tableTitleRowClose": None,
            "tableTitleCellSep": " |",
            "tableRowOpen": "|",
            "tableRowClose": "|",
            "tableCellSep": " |",
        },
        "ctx": {
            "anchor": "\a",
            "bar1": "\\hairline",
            "bar2": "\\blackrule",
            "blockQuoteClose": "\\stopblockquote",
            "blockQuoteOpen": "\\startblockquote",
            "blockVerbClose": "\\stoptyping",
            "blockVerbOpen": "\\starttyping",
            "bodyClose": None,
            "bodyOpen": None,
            "comment": "% \a",
            "deflistClose": None,
            "deflistItem1Close": "}",
            "deflistItem1Open": "\\compdesc{",
            "deflistItem2Close": None,
            "deflistItem2Open": None,
            "deflistOpen": None,
            "email": "\\goto{\a}[url(mailto:\a)]",
            "emailMark": "\\goto{\a}[url(mailto:\a)]",
            "EOD": "\\stoptext",
            "fontBoldClose": "}",
            "fontBoldOpen": "{\\bf ",
            "fontItalicClose": "}",
            "fontItalicOpen": "{\\em ",
            "fontMonoClose": "}",
            "fontMonoOpen": "{\\tt ",
            "fontStrikeClose": "}",
            "fontStrikeOpen": "\\overstrike{",
            "fontUnderlineClose": "}",
            "fontUnderlineOpen": "\\overstrike{",
            "_imgAlignCenter": "middle",
            "_imgAlignLeft": "flushleft",
            "_imgAlignRight": "flushright",
            "img": "\\startalignment[~A~]\\dontleavehmode{"
            "\\externalfigure[\a]}\\stopalignment",
            "listClose": "\\stopitemize",
            "listCloseCompact": "\\stopitemize",
            "listItemClose": None,
            "listItemLine": None,
            "listItemOpen": "\\item ",
            "listOpen": "\\startitemize",
            "listOpenCompact": "\\startitemize[joinedup,nowhite]",
            "numlistClose": "\\stopitemize",
            "numlistCloseCompact": "\\stopitemize",
            "numlistItemClose": None,
            "numlistItemLine": None,
            "numlistItemOpen": "\\item ",
            "numlistOpen": "\\startitemize[n]",
            "numlistOpenCompact": "\\startitemize[n,joinedup,nowhite]",
            "pageBreak": "\\pagebreak",
            "paragraphClose": None,
            "paragraphOpen": None,
            "_tableAlignCenter": "middle",
            "_tableBorder": "frame=on",
            "_tableCellAlignCenter": "align=middle",
            "_tableCellAlignRight": "align=left",
            "tableCellClose": "\\eTD",
            "_tableCellColSpan": ",nc=\a",
            "tableCellOpen": "\\bTD[~A~~s~]",
            "tableClose": "\\eTABLE}\\stopalignment",
            "tableOpen": "\\blank[medium]\\startalignment[~A~]{\\bTABLE[~B~]",
            "tableRowClose": "\\eTR",
            "tableRowOpen": "\\bTR",
            "tableTitleCellClose": "\\eTH",
            "tableTitleCellOpen": "\\bTH",
            "title1Close": "\\stopsection\n",
            "title1Open": "\\startsection[title=\a, reference=~A~]",
            "title2Close": "\\stopsubsection\n",
            "title2Open": "\\startsubsection[title=\a, reference=~A~]",
            "title3Close": "\\stopsubsubsection\n",
            "title3Open": "\\startsubsubsection[title=\a, reference=~A~]",
            "title4Close": None,
            "title4Open": None,
            "title5Close": None,
            "title5Open": None,
            "tocClose": None,
            "tocOpen": None,
            "TOC": "\\subsubject{Contents}  \\placecontent",
            "url": "\\goto{\a}[url(\a)]",
            "urlMark": "\\goto{\a}[url(\a)]",
        },
    }
    assert set(alltags) == set(TARGETS)

    for target, tags in alltags.items():
        for key, value in tags.items():
            if key not in keys:
                raise AssertionError("{} target has invalid key {}".format(target, key))
            if value is not None and not value:
                raise AssertionError("{} target drops {}".format(target, key))

    # Compose the target tags dictionary.
    tags = collections.defaultdict(str)
    for key, value in alltags[config["target"]].items():
        if value:  # Skip unsupported markup.
            tags[key] = maskEscapeChar(value)

    # Map strong line to pagebreak
    if rules["mapbar2pagebreak"] and tags["pageBreak"]:
        tags["bar2"] = tags["pageBreak"]

    # Map strong line to separator if not defined
    if not tags["bar2"] and tags["bar1"]:
        tags["bar2"] = tags["bar1"]

    return tags


##############################################################################


def getRules(config):
    """Return all the target-specific syntax rules."""
    allrules = [
        # target rules (ON/OFF)
        "linkable",  # target supports external links
        "tableable",  # target supports tables
        "imglinkable",  # target supports images as links
        "imgalignable",  # target supports image alignment
        "imgasdefterm",  # target supports image as definition term
        "autonumberlist",  # target supports numbered lists natively
        "autonumbertitle",  # target supports numbered titles natively
        "stylable",  # target supports external style files
        "parainsidelist",  # lists items supports paragraph
        "compactlist",  # separate enclosing tags for compact lists
        "spacedlistitem",  # lists support blank lines between items
        "listnotnested",  # lists cannot be nested
        "quotenotnested",  # quotes cannot be nested
        "verbblocknotescaped",  # don't escape specials in verb block
        "verbblockfinalescape",  # do final escapes in verb block
        "escapeurl",  # escape special in link URL
        "labelbeforelink",  # label comes before the link on the tag
        "onelinepara",  # dump paragraph as a single long line
        "tabletitlerowinbold",  # manually bold any cell on table titles
        "tablecellstrip",  # strip extra spaces from each table cell
        "tablecellspannable",  # the table cells can have span attribute
        "tablecellmulticol",  # separate open+close tags for multicol cells
        "barinsidequote",  # bars are allowed inside quote blocks
        "finalescapetitle",  # perform final escapes on title lines
        "autotocnewpagebefore",  # break page before automatic TOC
        "autotocnewpageafter",  # break page after automatic TOC
        "autotocwithbars",  # automatic TOC surrounded by bars
        "mapbar2pagebreak",  # map the strong bar to a page break
        "titleblocks",  # titles must be on open/close section blocks
        # Target code beautify (ON/OFF)
        "indentverbblock",  # add leading spaces to verb block lines
        "breaktablecell",  # break lines after any table cell
        "breaktablelineopen",  # break line after opening table line
        "notbreaklistopen",  # don't break line after opening a new list
        "keepquoteindent",  # don't remove the leading TABs on quotes
        "keeplistindent",  # don't remove the leading spaces on lists
        "blankendautotoc",  # append a blank line at the auto TOC end
        "tagnotindentable",  # tags must be placed at the line beginning
        "spacedlistitemopen",  # append a space after the list item open tag
        "spacednumlistitemopen",  # append a space after the numlist item open tag
        "deflisttextstrip",  # strip the contents of the deflist text
        "blanksaroundpara",  # put a blank line before and after paragraphs
        "blanksaroundverb",  # put a blank line before and after verb blocks
        "blanksaroundquote",  # put a blank line before and after quotes
        "blanksaroundlist",  # put a blank line before and after lists
        "blanksaroundnumlist",  # put a blank line before and after numlists
        "blanksarounddeflist",  # put a blank line before and after deflists
        "blanksaroundtable",  # put a blank line before and after tables
        "blanksaroundbar",  # put a blank line before and after bars
        "blanksaroundtitle",  # put a blank line before and after titles
        "blanksaroundnumtitle",  # put a blank line before and after numtitles
        # Value settings
        "listmaxdepth",  # maximum depth for lists
        "quotemaxdepth",  # maximum depth for quotes
        "tablecellaligntype",  # type of table cell align: cell, column
    ]

    rules_bank = {
        "txt": {
            "indentverbblock": 1,
            "spacedlistitem": 1,
            "parainsidelist": 1,
            "keeplistindent": 1,
            "barinsidequote": 1,
            "autotocwithbars": 1,
            "blanksaroundpara": 1,
            "blanksaroundverb": 1,
            "blanksaroundquote": 1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            "blanksaroundbar": 1,
            "blanksaroundtitle": 1,
            "blanksaroundnumtitle": 1,
        },
        "html": {
            "indentverbblock": 0,
            "linkable": 1,
            "stylable": 1,
            "escapeurl": 1,
            "imglinkable": 1,
            "imgalignable": 1,
            "imgasdefterm": 1,
            "autonumberlist": 1,
            "spacedlistitem": 1,
            "parainsidelist": 1,
            "tableable": 1,
            "tablecellstrip": 1,
            "breaktablecell": 1,
            "breaktablelineopen": 1,
            "keeplistindent": 1,
            "keepquoteindent": 1,
            "barinsidequote": 1,
            "autotocwithbars": 0,
            "tablecellspannable": 1,
            "tablecellaligntype": "cell",
            # 'blanksaroundpara':1,
            "blanksaroundverb": 1,
            # 'blanksaroundquote':1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            "blanksaroundbar": 1,
            "blanksaroundtitle": 1,
            "blanksaroundnumtitle": 1,
            "titleblocks": 1,
        },
        "sgml": {
            "linkable": 1,
            "escapeurl": 1,
            "autonumberlist": 1,
            "spacedlistitem": 1,
            "tableable": 1,
            "tablecellstrip": 1,
            "blankendautotoc": 1,
            "quotenotnested": 1,
            "keeplistindent": 1,
            "keepquoteindent": 1,
            "barinsidequote": 1,
            "finalescapetitle": 1,
            "tablecellaligntype": "column",
            "blanksaroundpara": 1,
            "blanksaroundverb": 1,
            "blanksaroundquote": 1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            "blanksaroundbar": 1,
            "blanksaroundtitle": 1,
            "blanksaroundnumtitle": 1,
        },
        "dbk": {
            "linkable": 1,
            "tableable": 0,  # activate when table tags are ready
            "imglinkable": 1,
            "imgalignable": 1,
            "imgasdefterm": 1,
            "autonumberlist": 1,
            "autonumbertitle": 1,
            "parainsidelist": 1,
            "spacedlistitem": 1,
            "titleblocks": 1,
        },
        "mgp": {
            "tagnotindentable": 1,
            "spacedlistitem": 1,
            "imgalignable": 1,
            "autotocnewpagebefore": 1,
            "blanksaroundpara": 1,
            "blanksaroundverb": 1,
            # 'blanksaroundquote':1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            "blanksaroundbar": 1,
            # 'blanksaroundtitle':1,
            # 'blanksaroundnumtitle':1,
        },
        "tex": {
            "stylable": 1,
            "escapeurl": 1,
            "autonumberlist": 1,
            "autonumbertitle": 1,
            "spacedlistitem": 1,
            "compactlist": 1,
            "parainsidelist": 1,
            "tableable": 1,
            "tablecellstrip": 1,
            "tabletitlerowinbold": 0,
            "verbblocknotescaped": 1,
            "keeplistindent": 1,
            "listmaxdepth": 4,  # deflist is 6
            "quotemaxdepth": 6,
            "barinsidequote": 1,
            "finalescapetitle": 1,
            "autotocnewpageafter": 1,
            "mapbar2pagebreak": 1,
            "tablecellaligntype": "column",
            "tablecellmulticol": 1,
            "blanksaroundpara": 1,
            "blanksaroundverb": 1,
            # 'blanksaroundquote':1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            "blanksaroundbar": 1,
            "blanksaroundtitle": 1,
            "blanksaroundnumtitle": 1,
        },
        "lout": {
            "keepquoteindent": 1,
            "deflisttextstrip": 1,
            "escapeurl": 1,
            "verbblocknotescaped": 1,
            "imgalignable": 1,
            "mapbar2pagebreak": 1,
            "titleblocks": 1,
            "autonumberlist": 1,
            "parainsidelist": 1,
            "blanksaroundpara": 1,
            "blanksaroundverb": 1,
            # 'blanksaroundquote':1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            "blanksaroundbar": 1,
            "blanksaroundtitle": 1,
            "blanksaroundnumtitle": 1,
        },
        "moin": {
            "spacedlistitem": 1,
            "linkable": 1,
            "keeplistindent": 1,
            "tableable": 1,
            "barinsidequote": 1,
            "tabletitlerowinbold": 1,
            "tablecellstrip": 1,
            "autotocwithbars": 1,
            "tablecellaligntype": "cell",
            "deflisttextstrip": 1,
            "blanksaroundpara": 1,
            "blanksaroundverb": 1,
            # 'blanksaroundquote':1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            # 'blanksaroundbar':1,
            "blanksaroundtitle": 1,
            "blanksaroundnumtitle": 1,
        },
        "gwiki": {
            "spacedlistitem": 1,
            "linkable": 1,
            "keeplistindent": 1,
            "tableable": 1,
            "tabletitlerowinbold": 1,
            "tablecellstrip": 1,
            "autonumberlist": 1,
            "blanksaroundpara": 1,
            "blanksaroundverb": 1,
            # 'blanksaroundquote':1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            # 'blanksaroundbar':1,
            "blanksaroundtitle": 1,
            "blanksaroundnumtitle": 1,
        },
        "adoc": {
            "spacedlistitem": 1,
            "linkable": 1,
            "keeplistindent": 1,
            "autonumberlist": 1,
            "autonumbertitle": 1,
            "listnotnested": 1,
            "blanksaroundpara": 1,
            "blanksaroundverb": 1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            "blanksaroundtitle": 1,
            "blanksaroundnumtitle": 1,
        },
        "doku": {
            "indentverbblock": 1,  # DokuWiki uses '  ' to mark verb blocks
            "spacedlistitem": 1,
            "linkable": 1,
            "keeplistindent": 1,
            "tableable": 1,
            "barinsidequote": 1,
            "tablecellstrip": 1,
            "autotocwithbars": 1,
            "autonumberlist": 1,
            "imgalignable": 1,
            "tablecellaligntype": "cell",
            "blanksaroundpara": 1,
            "blanksaroundverb": 1,
            # 'blanksaroundquote':1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            "blanksaroundbar": 1,
            "blanksaroundtitle": 1,
            "blanksaroundnumtitle": 1,
        },
        "pmw": {
            "indentverbblock": 1,
            "spacedlistitem": 1,
            "linkable": 1,
            "labelbeforelink": 1,
            # 'keeplistindent':1,
            "tableable": 1,
            "barinsidequote": 1,
            "tablecellstrip": 1,
            "autotocwithbars": 1,
            "autonumberlist": 1,
            "spacedlistitemopen": 1,
            "spacednumlistitemopen": 1,
            "imgalignable": 1,
            "tabletitlerowinbold": 1,
            "tablecellaligntype": "cell",
            "blanksaroundpara": 1,
            "blanksaroundverb": 1,
            "blanksaroundquote": 1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            "blanksaroundbar": 1,
            "blanksaroundtitle": 1,
            "blanksaroundnumtitle": 1,
        },
        "wiki": {
            "linkable": 1,
            "tableable": 1,
            "tablecellstrip": 1,
            "autotocwithbars": 1,
            "spacedlistitemopen": 1,
            "spacednumlistitemopen": 1,
            "deflisttextstrip": 1,
            "autonumberlist": 1,
            "imgalignable": 1,
            "blanksaroundpara": 1,
            "blanksaroundverb": 1,
            # 'blanksaroundquote':1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            "blanksaroundbar": 1,
            "blanksaroundtitle": 1,
            "blanksaroundnumtitle": 1,
        },
        "man": {
            "spacedlistitem": 1,
            "tagnotindentable": 1,
            "tableable": 1,
            "tablecellaligntype": "column",
            "tabletitlerowinbold": 1,
            "tablecellstrip": 1,
            "barinsidequote": 1,
            "parainsidelist": 0,
            "blanksaroundpara": 0,
            "blanksaroundverb": 1,
            # 'blanksaroundquote':1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            # 'blanksaroundbar':1,
            "blanksaroundtitle": 0,
            "blanksaroundnumtitle": 1,
        },
        "creole": {
            "linkable": 1,
            "tableable": 1,
            "imglinkable": 1,
            "tablecellstrip": 1,
            "autotocwithbars": 1,
            "spacedlistitemopen": 1,
            "spacednumlistitemopen": 1,
            "deflisttextstrip": 1,
            "verbblocknotescaped": 1,
            "blanksaroundpara": 1,
            "blanksaroundverb": 1,
            "blanksaroundquote": 1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            "blanksaroundbar": 1,
            "blanksaroundtitle": 1,
        },
        "md": {
            "keeplistindent": 1,
            "linkable": 1,
            "labelbeforelink": 1,
            "tableable": 1,
            "imglinkable": 1,
            "tablecellstrip": 1,
            "autonumberlist": 1,
            "spacedlistitemopen": 1,
            "spacednumlistitemopen": 1,
            "deflisttextstrip": 1,
            "blanksaroundpara": 1,
            "blanksaroundlist": 1,
            "blanksaroundnumlist": 1,
            # "blanksarounddeflist": 1,
            "blanksaroundtable": 1,
            "blanksaroundbar": 1,
            "blanksaroundtitle": 1,
        },
        "ctx": {
            "autonumberlist": 1,  # target supports numbered lists natively
            "autonumbertitle": 0,  # target supports numbered titles natively
            "autotocnewpageafter": 0,  # break page after automatic TOC
            "autotocnewpagebefore": 0,  # break page before automatic TOC
            "autotocwithbars": 0,  # automatic TOC surrounded by bars
            "barinsidequote": 0,  # bars are allowed inside quote blocks
            "compactlist": 1,  # separate enclosing tags for compact lists
            "escapeurl": 1,  # escape special in link URL
            "finalescapetitle": 1,  # perform final escapes on title lines
            "imgalignable": 1,  # target supports image alignment
            "imglinkable": 1,  # target supports images as links
            "labelbeforelink": 1,  # label comes before the link on the tag
            "linkable": 1,  # target supports external links
            "listnotnested": 0,  # lists cannot be nested
            "mapbar2pagebreak": 1,  # map the strong bar to a page break
            "onelinepara": 0,  # dump paragraph as a single long line
            "parainsidelist": 1,  # lists items supports paragraph
            "quotenotnested": 0,  # quotes cannot be nested
            "spacedlistitem": 1,  # lists support blank lines between items
            "stylable": 1,  # target supports external style files
            "tableable": 1,  # target supports tables
            "tablecellmulticol": 0,  # separate open+close tags for multicol cells
            "tablecellspannable": 1,  # the table cells can have span attribute
            "tablecellstrip": 1,  # strip extra spaces from each table cell
            "tabletitlerowinbold": 1,  # manually bold any cell on table titles
            "titleblocks": 1,  # titles must be on open/close section blocks
            "verbblockfinalescape": 0,  # do final escapes in verb block
            "verbblocknotescaped": 1,  # don't escape specials in verb block
            "blankendautotoc": 1,  # append a blank line at the auto TOC end
            "blanksaroundbar": 1,  # put a blank line before and after bars
            "blanksarounddeflist": 1,  # put a blank line before and after deflists
            "blanksaroundlist": 1,  # put a blank line before and after lists
            "blanksaroundnumlist": 1,  # put a blank line before and after numlists
            "blanksaroundnumtitle": 0,  # put a blank line before and after numtitles
            "blanksaroundpara": 1,  # put a blank line before and after paragraphs
            "blanksaroundquote": 1,  # put a blank line before and after quotes
            "blanksaroundtable": 1,  # put a blank line before and after tables
            "blanksaroundtitle": 0,  # put a blank line before and after titles
            "blanksaroundverb": 1,  # put a blank line before and after verb blocks
            "breaktablecell": 0,  # break lines after any table cell
            "breaktablelineopen": 0,  # break line after opening table line
            "indentverbblock": 0,  # add leading spaces to verb block lines
            "keeplistindent": 1,  # don't remove the leading spaces on lists
            "keepquoteindent": 0,  # don't remove the leading TABs on quotes
            "notbreaklistopen": 0,  # don't break line after opening a new list
            "tagnotindentable": 0,  # tags must be placed at the line beginning
            "tablecellaligntype": "cell",  # type of table cell align: cell, column
        },
    }
    assert set(rules_bank) == set(TARGETS)

    for target, rules in rules_bank.items():
        for rule in rules:
            if rule not in allrules:
                raise AssertionError(
                    "{} target has invalid rule {}".format(target, rule)
                )

    ret = collections.defaultdict(int)
    ret.update(rules_bank[config["target"]])
    return ret


##############################################################################


def getRegexes():
    "Returns all the regexes used to find the t2t marks"

    bank = {
        "blockVerbOpen": re.compile(r"^```\s*$"),
        "blockVerbClose": re.compile(r"^```\s*$"),
        "blockRawOpen": re.compile(r'^"""\s*$'),
        "blockRawClose": re.compile(r'^"""\s*$'),
        "blockTaggedOpen": re.compile(r"^'''\s*$"),
        "blockTaggedClose": re.compile(r"^'''\s*$"),
        "blockCommentOpen": re.compile(r"^%%%\s*$"),
        "blockCommentClose": re.compile(r"^%%%\s*$"),
        "quote": re.compile(r"^\t+"),
        "1lineVerb": re.compile(r"^``` (?=.)"),
        "1lineRaw": re.compile(r'^""" (?=.)'),
        "1lineTagged": re.compile(r"^''' (?=.)"),
        # mono, raw, bold, italic, underline:
        # - marks must be glued with the contents, no boundary spaces
        # - they are greedy, so in ****bold****, turns to <b>**bold**</b>
        "fontMono": re.compile(r"``([^\s](|.*?[^\s])`*)``"),
        "raw": re.compile(r'""([^\s](|.*?[^\s])"*)""'),
        "tagged": re.compile(r"''([^\s](|.*?[^\s])'*)''"),
        "fontBold": re.compile(r"\*\*([^\s](|.*?[^\s])\**)\*\*"),
        "fontItalic": re.compile(r"//([^\s](|.*?[^\s])/*)//"),
        "fontUnderline": re.compile(r"__([^\s](|.*?[^\s])_*)__"),
        "fontStrike": re.compile(r"--([^\s](|.*?[^\s])-*)--"),
        "list": re.compile(r"^( *)(-) (?=[^ ])"),
        "numlist": re.compile(r"^( *)(\+) (?=[^ ])"),
        "deflist": re.compile(r"^( *)(:) (.*)$"),
        "listclose": re.compile(r"^( *)([-+:])\s*$"),
        "bar": re.compile(r"^(\s*)([_=-]{20,})\s*$"),
        "table": re.compile(r"^ *\|([|_/])? "),
        "blankline": re.compile(r"^\s*$"),
        "comment": re.compile(r"^%"),
        # Auxiliary tag regexes
        "_imgAlign": re.compile(r"~A~", re.I),
        "_tableAlign": re.compile(r"~A~", re.I),
        "_anchor": re.compile(r"~A~", re.I),
        "_tableBorder": re.compile(r"~B~", re.I),
        "_tableColAlign": re.compile(r"~C~", re.I),
        "_tableCellColSpan": re.compile(r"~S~", re.I),
        "_tableCellAlign": re.compile(r"~A~", re.I),
    }

    # Special char to place data on TAGs contents  (\a == bell)
    bank["x"] = re.compile("\a")

    # Almost complicated title regexes ;)
    titskel = r"^ *(?P<id>%s)(?P<txt>%s)\1(\[(?P<label>[\w-]*)\])?\s*$"
    bank["title"] = re.compile(titskel % ("[=]{1,5}", "[^=](|.*[^=])"))
    bank["numtitle"] = re.compile(titskel % ("[+]{1,5}", "[^+](|.*[^+])"))

    # Complicated regexes begin here ;)
    #
    # Textual descriptions on --help's style: [...] is optional, | is OR

    # First, some auxiliary variables
    #

    # [image.EXT]
    patt_img = r"\[([\w_,.+%$#@!?+~/-]+\.(png|jpe?g|gif|eps|bmp|svg))\]"

    # Link things
    # http://www.gbiv.com/protocols/uri/rfc/rfc3986.html
    # pchar: A-Za-z._~- / %FF / !$&'()*+,;= / :@
    # Recomended order: scheme://user:pass@domain/path?query=foo#anchor
    # Also works      : scheme://user:pass@domain/path#anchor?query=foo
    # TODO form: !'():
    urlskel = {
        "proto": r"(https?|ftp|news|telnet|gopher|wais)://",
        "guess": r"(www[23]?|ftp)\.",  # w/out proto, try to guess
        "login": r"A-Za-z0-9_.-",  # for ftp://login@domain.com
        "pass": r"[^ @]*",  # for ftp://login:pass@dom.com
        "chars": r"A-Za-z0-9%._/~:,=$@&+-",  # %20(space), :80(port), D&D
        "anchor": r"A-Za-z0-9%._-",  # %nn(encoded)
        "form": r"A-Za-z0-9/%&=+:;.,$@*_-",  # .,@*_-(as is)
        "punct": r".,;:!?",
    }

    # username [ :password ] @
    patt_url_login = r"([{}]+(:{})?@)?".format(urlskel["login"], urlskel["pass"])

    # [ http:// ] [ username:password@ ] domain.com [ / ]
    #     [ #anchor | ?form=data ]
    retxt_url = r"\b({}{}|{})[{}]+\b/*(\?[{}]+)?(#[{}]*)?".format(
        urlskel["proto"],
        patt_url_login,
        urlskel["guess"],
        urlskel["chars"],
        urlskel["form"],
        urlskel["anchor"],
    )

    # filename | [ filename ] #anchor
    retxt_url_local = r"[{}]+|[{}]*(#[{}]*)".format(
        urlskel["chars"], urlskel["chars"], urlskel["anchor"]
    )

    # user@domain [ ?form=data ]
    patt_email = r"\b[{}]+@([A-Za-z0-9_-]+\.)+[A-Za-z]{{2,4}}\b(\?[{}]+)?".format(
        urlskel["login"], urlskel["form"]
    )

    # Saving for future use
    bank["_urlskel"] = urlskel

    # And now the real regexes

    bank["email"] = re.compile(patt_email, re.I)

    # email | url
    bank["link"] = re.compile(r"{}|{}".format(retxt_url, patt_email), re.I)

    # \[ label | imagetag    url | email | filename \]
    bank["linkmark"] = re.compile(
        r"\[(?P<label>%s|[^]]+) (?P<link>%s|%s|%s)\]"
        % (patt_img, retxt_url, patt_email, retxt_url_local),
        re.I,
    )

    # Image
    bank["img"] = re.compile(patt_img, re.I)

    # Special things
    bank["special"] = re.compile(r"^%!\s*")
    return bank


# END OF regex nightmares


class error(Exception):
    pass


def Quit(msg=""):
    if msg:
        print(msg)
    sys.exit(0)


def Error(msg):
    sys.exit("Error: {}".format(msg))


def getTraceback():
    try:
        from traceback import format_exception

        etype, value, tb = sys.exc_info()
        return "".join(format_exception(etype, value, tb))
    except Exception:
        pass


def getUnknownErrorMessage():
    msg = "{}\n{} ({}):\n\n{}".format(
        "Sorry! Txt2tags aborted by an unknown error.",
        "Please send the following Error Traceback to the author",
        my_email,
        getTraceback(),
    )
    return msg


def Message(msg, level):
    if level <= VERBOSE and not QUIET:
        prefix = "-" * 5
        print("{} {}".format(prefix * level, msg))


def Debug(msg, id_=0, linenr=None):
    """Show debug messages, categorized."""
    if QUIET or not DEBUG:
        return
    ids = ["INI", "CFG", "SRC", "BLK", "HLD", "GUI", "OUT", "DET"]
    if linenr is not None:
        msg = "LINE %04d: %s" % (linenr, msg)
    print("++ {}: {}".format(ids[id_], msg))


def Readfile(file_path):
    if file_path == "-":
        try:
            contents = sys.stdin.read()
        except KeyboardInterrupt:
            Error("You must feed me with data on STDIN!")
    else:
        try:
            with open(file_path, encoding=ENCODING) as f:
                contents = f.read()
        except OSError as exception:
            Error("Cannot read file: {}\n{}".format(file_path, exception))
    lines = contents.splitlines()
    Message("File read (%d lines): %s" % (len(lines), file_path), 2)
    return lines


def Savefile(file_path, lines):
    contents = "\n".join(lines) + "\n"
    try:
        with open(file_path, "w", encoding=ENCODING) as f:
            try:
                f.write(contents)
            except TypeError:
                f.write(contents.decode(ENCODING))
    except OSError as exception:
        Error("Cannot open file for writing: {}\n{}".format(file_path, exception))


def dotted_spaces(txt=""):
    return txt.replace(" ", ".")


# TIP: win env vars http://www.winnetmag.com/Article/ArticleID/23873/23873.html
def get_rc_path():
    "Return the full path for the users' RC file"
    # Try to get the path from an env var. if yes, we're done
    user_defined = os.environ.get("T2TCONFIG")
    if user_defined:
        return user_defined
    # Env var not found, so perform automatic path composing
    # Set default filename according system platform
    rc_names = {"default": ".txt2tagsrc", "win": "_t2trc"}
    rc_file = rc_names.get(sys.platform[:3]) or rc_names["default"]
    # The file must be on the user directory, but where is this dir?
    rc_dir_search = ["HOME", "HOMEPATH"]
    for var in rc_dir_search:
        rc_dir = os.environ.get(var)
        if rc_dir:
            break
    # rc dir found, now we must join dir+file to compose the full path
    if rc_dir:
        # Compose path and return it if the file exists
        rc_path = os.path.join(rc_dir, rc_file)
        # On windows, prefix with the drive (%homedrive%: 2k/XP/NT)
        if sys.platform.startswith("win"):
            rc_drive = os.environ.get("HOMEDRIVE")
            rc_path = os.path.join(rc_drive, rc_path)
        return rc_path
    # Sorry, not found
    return ""


##############################################################################


class CommandLine:
    """
    Command Line class - Masters command line

    This class checks and extract data from the provided command line.
    The --long options and flags are taken from the global OPTIONS,
    FLAGS and ACTIONS dictionaries. The short options are registered
    here, and also their equivalence to the long ones.

    _compose_short_opts() -> str
    _compose_long_opts() -> list
            Compose the valid short and long options list, on the
            'getopt' format.

    parse() -> (opts, args)
            Call getopt to check and parse the command line.
            It expects to receive the command line as a list, and
            without the program name (sys.argv[1:]).

    get_raw_config() -> [RAW config]
            Scans command line and convert the data to the RAW config
            format. See ConfigMaster class to the RAW format description.
            Optional 'ignore' and 'filter_' arguments are used to filter
            in or out specified keys.

    The get_raw_config() calls parse(), so the typical use of this
    class is:

        raw = CommandLine().get_raw_config(sys.argv[1:])
    """

    def __init__(self):
        self.all_options = list(OPTIONS.keys())
        self.all_flags = list(FLAGS.keys())
        self.all_actions = list(ACTIONS.keys())

        # short:long options equivalence
        self.short_long = {
            "C": "config-file",
            "h": "help",
            "H": "no-headers",
            "i": "infile",
            "n": "enum-title",
            "o": "outfile",
            "q": "quiet",
            "t": "target",
            "v": "verbose",
            "V": "version",
        }

        # Compose valid short and long options data for getopt
        self.short_opts = self._compose_short_opts()
        self.long_opts = self._compose_long_opts()

    def _compose_short_opts(self):
        "Returns a string like 'hVt:o' with all short options/flags"
        ret = []
        for opt in self.short_long.keys():
            long_ = self.short_long[opt]
            if long_ in self.all_options:  # is flag or option?
                opt = opt + ":"  # option: have param
            ret.append(opt)
        # Debug('Valid SHORT options: %s'%ret)
        return "".join(ret)

    def _compose_long_opts(self):
        "Returns a list with all the valid long options/flags"
        ret = [x + "=" for x in self.all_options]  # add =
        ret.extend(self.all_flags)  # flag ON
        ret.extend(self.all_actions)  # actions
        ret.extend(["no-" + x for x in self.all_flags])  # add no-*
        ret.extend(["no-style"])  # turn OFF
        ret.extend(["no-outfile", "no-infile"])  # turn OFF
        ret.extend(["no-targets"])  # turn OFF
        # Debug('Valid LONG options: %s'%ret)
        return ret

    def _tokenize(self, cmd_string=""):
        "Convert a command line string to a list"
        # TODO protect quotes contents -- Don't use it, pass cmdline as list
        return cmd_string.split()

    def parse(self, cmdline):
        "Check/Parse a command line list     TIP: no program name!"
        # Get the valid options
        short, long_ = self.short_opts, self.long_opts
        # Parse it!
        try:
            opts, args = getopt.getopt(cmdline, short, long_)
        except getopt.error as errmsg:
            Error("%s (try --help)" % errmsg)
        return (opts, args)

    def get_raw_config(self, cmdline=None, ignore=None, filter_=None, relative=False):
        "Returns the options/arguments found as RAW config"

        if not cmdline:
            return []
        ignore = ignore or []
        filter_ = filter_ or []

        ret = []

        # We need lists, not strings (such as from %!options)
        if not isinstance(cmdline, list):
            cmdline = self._tokenize(cmdline)

        # Extract name/value pair of all configs, check for invalid names
        options, arguments = self.parse(cmdline[:])

        # Some cleanup on the raw config
        for name, value in options:

            # Remove leading - and --
            name = re.sub("^--?", "", name)

            # Translate short option to long
            if len(name) == 1:
                name = self.short_long[name]

            # Outfile exception: path relative to PWD
            if name == "outfile" and relative and value not in [STDOUT, MODULEOUT]:
                value = os.path.abspath(value)

            # -C, --config-file inclusion, path relative to PWD
            if name == "config-file":
                ret.extend(ConfigLines().include_config_file(value))
                continue

            # Save this config
            ret.append(["all", name, value])

        # All configuration was read and saved

        # Get infile, if any
        while arguments:
            infile = arguments.pop(0)
            ret.append(["all", "infile", infile])

        # Apply 'ignore' and 'filter_' rules (filter_ is stronger)
        if ignore or filter_:
            filtered = []
            for target, name, value in ret:
                if (filter_ and name in filter_) or (ignore and name not in ignore):
                    filtered.append([target, name, value])
            ret = filtered[:]

        return ret


##############################################################################


class SourceDocument:
    """
    SourceDocument class - scan document structure, extract data

    It knows about full files. It reads a file and identify all
    the areas beginning (Head,Conf,Body). With this info it can
    extract each area contents.
    Note: the original line break is removed.

    DATA:
      self.arearef - Save Head, Conf, Body init line number
      self.areas   - Store the area names which are not empty
      self.buffer  - The full file contents (with NO \\r, \\n)

    METHODS:
      get()   - Access the contents of an Area. Example:
                config = SourceDocument(file).get('conf')

      split() - Get all the document Areas at once. Example:
                head, conf, body = SourceDocument(file).split()

    RULES:
        * The document parts are sequential: Head, Conf and Body.
        * One ends when the next begins.
        * The Conf Area is optional, so a document can have just
          Head and Body Areas.

        These are the Areas limits:
          - Head Area: the first three lines
          - Body Area: from the first valid text line to the end
          - Conf Area: the comments between Head and Body Areas

        Exception: If the first line is blank, this means no
        header info, so the Head Area is just the first line.
    """

    def __init__(self, filename="", contents=None):
        self.areas = ["head", "conf", "body"]
        self.arearef = []
        self.areas_fancy = ""
        self.filename = filename
        self.buffer = []
        if filename:
            self.scan_file(filename)
        elif contents:
            self.scan(contents)

    def split(self):
        "Returns all document parts, splitted into lists."
        return self.get("head"), self.get("conf"), self.get("body")

    def get(self, areaname):
        "Returns head|conf|body contents from self.buffer"
        # Sanity
        if areaname not in self.areas:
            return []
        if not self.buffer:
            return []
        # Go get it
        bufini = 1
        bufend = len(self.buffer)
        if areaname == "head":
            ini = bufini
            end = self.arearef[1] or self.arearef[2] or bufend
        elif areaname == "conf":
            ini = self.arearef[1]
            end = self.arearef[2] or bufend
        elif areaname == "body":
            ini = self.arearef[2]
            end = bufend
        else:
            Error("Unknown Area name '%s'" % areaname)
        lines = self.buffer[ini:end]
        # Make sure head will always have 3 lines
        while areaname == "head" and len(lines) < 3:
            lines.append("")
        return lines

    def scan_file(self, filename):
        Debug("source file: %s" % filename)
        Message("Loading source document", 1)
        buf = Readfile(filename)
        self.scan(buf)

    def scan(self, lines):
        "Run through source file and identify head/conf/body areas"
        buf = lines
        if len(buf) == 0:
            Error("The input file is empty: %s" % self.filename)
        cfg_parser = ConfigLines().parse_line
        buf.insert(0, "")  # text start at pos 1
        ref = [1, 4, 0]
        if not buf[1].strip():  # no header
            ref[0] = 0
            ref[1] = 2
        rgx = getRegexes()
        on_comment_block = 0
        for i in range(ref[1], len(buf)):  # find body init:
            # Handle comment blocks inside config area
            if not on_comment_block and rgx["blockCommentOpen"].search(buf[i]):
                on_comment_block = 1
                continue
            if on_comment_block and rgx["blockCommentOpen"].search(buf[i]):
                on_comment_block = 0
                continue
            if on_comment_block:
                continue

            if buf[i].strip() and (
                buf[i][0] != "%" or cfg_parser(buf[i], "include")[1]
            ):
                ref[2] = i
                break
        if ref[1] == ref[2]:
            ref[1] = 0  # no conf area
        for i in 0, 1, 2:  # del !existent
            if ref[i] >= len(buf):
                ref[i] = 0  # title-only
            if not ref[i]:
                self.areas[i] = ""
        Debug("Head,Conf,Body start line: %s" % ref)
        self.arearef = ref  # save results
        self.buffer = buf
        # Fancyness sample: head conf body (1 4 8)
        self.areas_fancy = "{} ({})".format(
            " ".join(self.areas), " ".join(str(x or "") for x in ref)
        )
        Message("Areas found: %s" % self.areas_fancy, 2)

    def get_raw_config(self):
        "Handy method to get the CONF area RAW config (if any)"
        if not self.areas.count("conf"):
            return []
        Message("Scanning source document CONF area", 1)
        raw = ConfigLines(
            file_=self.filename, lines=self.get("conf"), first_line=self.arearef[1]
        ).get_raw_config()
        Debug("document raw config: %s" % raw, 1)
        return raw


##############################################################################


class ConfigMaster:
    """
    ConfigMaster class - the configuration wizard

    This class is the configuration master. It knows how to handle
    the RAW and PARSED config format. It also performs the sanity
    checking for a given configuration.

    DATA:
      self.raw         - Stores the config on the RAW format
      self.parsed      - Stores the config on the PARSED format
      self.defaults    - Stores the default values for all keys
      self.off         - Stores the OFF values for all keys
      self.multi       - List of keys which can have multiple values
      self.incremental - List of keys which are incremental

    RAW FORMAT:
      The RAW format is a list of lists, being each mother list item
      a full configuration entry. Any entry is a 3 item list, on
      the following format: [ TARGET, KEY, VALUE ]
      Being a list, the order is preserved, so it's easy to use
      different kinds of configs, as CONF area and command line,
      respecting the precedence.
      The special target 'all' is used when no specific target was
      defined on the original config.

    PARSED FORMAT:
      The PARSED format is a dictionary, with all the 'key : value'
      found by reading the RAW config. The self.target contents
      matters, so this dictionary only contains the target's
      config. The configs of other targets are ignored.

    The CommandLine and ConfigLines classes have the get_raw_config()
    method which convert the configuration found to the RAW format.
    Just feed it to parse() and get a brand-new ready-to-use config
    dictionary. Example:

        >>> raw = CommandLine().get_raw_config(['-n', '-H'])
        >>> print raw
        [['all', 'enum-title', ''], ['all', 'no-headers', '']]
        >>> parsed = ConfigMaster(raw).parse()
        >>> print parsed
        {'enum-title': 1, 'headers': 0}
    """

    def __init__(self, raw=None, target=""):
        self.raw = raw or []
        self.target = target
        self.parsed = {}
        self.dft_options = OPTIONS.copy()
        self.dft_flags = FLAGS.copy()
        self.dft_actions = ACTIONS.copy()
        self.defaults = self._get_defaults()
        self.off = self._get_off()
        self.incremental = ["verbose"]
        self.multi = ["infile", "preproc", "postproc", "options", "style"]

    def _get_defaults(self):
        "Get the default values for all config/options/flags"
        empty = {}
        for kw in CONFIG_KEYWORDS:
            empty[kw] = ""
        empty.update(self.dft_options)
        empty.update(self.dft_flags)
        empty.update(self.dft_actions)
        empty["sourcefile"] = ""  # internal use only
        return empty

    def _get_off(self):
        "Turns OFF all the config/options/flags"
        off = {}
        for key in self.defaults.keys():
            kind = type(self.defaults[key])
            if kind == int:
                off[key] = 0
            elif kind == str:
                off[key] = ""
            elif kind == list:
                off[key] = []
            else:
                Error("ConfigMaster: %s: Unknown type" % key)
        return off

    def _check_target(self):
        "Checks if the target is already defined. If not, do it"
        if not self.target:
            self.target = self.find_value("target")

    def get_target_raw(self):
        "Returns the raw config for self.target or 'all'"
        ret = []
        self._check_target()
        for entry in self.raw:
            if entry[0] == self.target or entry[0] == "all":
                ret.append(entry)
        return ret

    def add(self, key, val):
        "Adds the key:value pair to the config dictionary (if needed)"
        # %!options
        if key == "options":
            ignoreme = list(self.dft_actions.keys()) + ["target"]
            ignoreme.remove("targets")
            raw_opts = CommandLine().get_raw_config(val, ignore=ignoreme)
            for _target, key, val in raw_opts:
                self.add(key, val)
            return
        # The no- prefix turns OFF this key
        if key.startswith("no-"):
            key = key[3:]  # remove prefix
            val = self.off.get(key)  # turn key OFF
        # Is this key valid?
        if key not in self.defaults.keys():
            Debug("Bogus Config {}:{}".format(key, val), 1)
            return
        # Is this value the default one?
        if val == self.defaults.get(key):
            # If default value, remove previous key:val
            if key in self.parsed:
                del self.parsed[key]
            # Nothing more to do
            return
        # Flags ON comes empty. we'll add the 1 value now
        if val == "" and (
            key in self.dft_flags.keys() or key in self.dft_actions.keys()
        ):
            val = 1
        # Multi value or single?
        if key in self.multi:
            # First one? start new list
            if key not in self.parsed:
                self.parsed[key] = []
            self.parsed[key].append(val)
        # Incremental value? so let's add it
        elif key in self.incremental:
            self.parsed[key] = (self.parsed.get(key) or 0) + val
        else:
            self.parsed[key] = val
        fancykey = dotted_spaces("%12s" % key)
        Message("Added config {} : {}".format(fancykey, val), 3)

    def get_outfile_name(self, config):
        "Dirname is the same for {in,out}file"
        infile, outfile = config["sourcefile"], config["outfile"]
        if (
            outfile
            and outfile not in (STDOUT, MODULEOUT)
            and not os.path.isabs(outfile)
        ):
            outfile = os.path.join(os.path.dirname(infile), outfile)
        if infile == STDIN and not outfile:
            outfile = STDOUT
        if infile == MODULEIN and not outfile:
            outfile = MODULEOUT
        if not outfile and (infile and config.get("target")):
            basename = re.sub(r"\.(txt|t2t)$", "", infile)
            outfile = "{}.{}".format(basename, config["target"])
        Debug(" infile: '%s'" % infile, 1)
        Debug("outfile: '%s'" % outfile, 1)
        return outfile

    def sanity(self, config):
        "Basic config sanity checking"
        if not config:
            return {}
        target = config.get("target")
        # Some actions don't require target specification
        if not target:
            for action in NO_TARGET:
                if config.get(action):
                    target = "txt"
                    break

        # We *need* a target
        if not target:
            Error(
                "No target specified (try --help)."
                + "\n\n"
                + "Please select a target using the -t option or the %!target command."
                + "\n"
                + "Example:"
                + " {} -t html {}".format(my_name, "file.t2t")
                + "\n\n"
                + "Run 'txt2tags --targets' to see all available targets."
            )
        # And of course, an infile also
        if "infile" not in config:
            Error("Missing input file (try --help)")
        # Is the target valid?
        if not TARGETS.count(target):
            Error(
                "Invalid target '%s'" % target
                + "\n\n"
                + "Run 'txt2tags --targets' to see all the available targets."
            )
        # Ensure all keys are present
        empty = self.defaults.copy()
        empty.update(config)
        config = empty.copy()
        # Restore target
        config["target"] = target
        # Set output file name
        config["outfile"] = self.get_outfile_name(config)
        # Checking suicide
        if os.path.abspath(config["sourcefile"]) == os.path.abspath(
            config["outfile"]
        ) and config["outfile"] not in [STDOUT, MODULEOUT]:
            Error("Input and Output files are the same: %s" % config["outfile"])
        return config

    def parse(self):
        "Returns the parsed config for the current target"
        raw = self.get_target_raw()
        for _target, key, value in raw:
            self.add(key, value)
        Message("Added the following keys: %s" % ", ".join(sorted(self.parsed)), 2)
        return self.parsed.copy()

    def find_value(self, key="", target=""):
        "Scans ALL raw config to find the desired key"
        ret = []
        # Scan and save all values found
        for targ, k, val in self.raw:
            if k == key and (targ == target or targ == "all"):
                ret.append(val)
        if not ret:
            return ""
        # If not multi value, return only the last found
        if key in self.multi:
            return ret
        else:
            return ret[-1]


########################################################################


class ConfigLines:
    """
    ConfigLines class - the config file data extractor

    This class reads and parse the config lines on the %!key:val
    format, converting it to RAW config. It deals with user
    config file (RC file), source document CONF area and
    %!includeconf directives.

    Call it passing a file name or feed the desired config lines.
    Then just call the get_raw_config() method and wait to
    receive the full config data on the RAW format. This method
    also follows the possible %!includeconf directives found on
    the config lines. Example:

            raw = ConfigLines(file=".txt2tagsrc").get_raw_config()

    The parse_line() method is also useful to be used alone,
    to identify and tokenize a single config line. For example,
    to get the %!include command components, on the source
    document BODY:

            target, key, value = ConfigLines().parse_line(body_line)
    """

    def __init__(self, file_="", lines=None, first_line=1):
        self.file = file_ or "NOFILE"
        self.lines = lines or []
        self.first_line = first_line

    def load_lines(self):
        "Make sure we've loaded the file contents into buffer"
        if not self.lines and not self.file:
            Error("ConfigLines: No file or lines provided")
        if not self.lines:
            self.lines = self.read_config_file(self.file)

    def read_config_file(self, filename=""):
        "Read a Config File contents, aborting on invalid line"
        if not filename:
            return []
        errormsg = "Invalid CONFIG line on %s" + "\n%03d:%s"
        lines = Readfile(filename)
        # Sanity: try to find invalid config lines
        for i in range(len(lines)):
            line = lines[i].rstrip()
            if not line:
                continue  # empty
            if line[0] != "%":
                Error(errormsg % (filename, i + 1, line))
        return lines

    def include_config_file(self, file_=""):
        "Perform the %!includeconf action, returning RAW config"
        if not file_:
            return []
        # Current dir relative to the current file (self.file)
        current_dir = os.path.dirname(self.file)
        file_ = os.path.join(current_dir, file_)
        # Read and parse included config file contents
        lines = self.read_config_file(file_)
        return ConfigLines(file_=file_, lines=lines).get_raw_config()

    def get_raw_config(self):
        "Scan buffer and extract all config as RAW (including includes)"
        ret = []
        self.load_lines()
        first = self.first_line
        for i in range(len(self.lines)):
            line = self.lines[i]
            Message("Processing line %03d: %s" % (first + i, line), 2)
            target, key, val = self.parse_line(line)
            if not key:
                continue  # no config on this line
            if key == "includeconf":
                err = "A file cannot include itself (loop!)"
                if val == self.file:
                    Error("{}: %!includeconf: {}".format(err, self.file))
                more_raw = self.include_config_file(val)
                ret.extend(more_raw)
                Message("Finished Config file inclusion: %s" % val, 2)
            else:
                ret.append([target, key, val])
                Message("Added %s" % key, 3)
        return ret

    def parse_line(self, line="", keyname="", target=""):
        "Detects %!key:val config lines and extract data from it"
        empty = ["", "", ""]
        if not line:
            return empty
        no_target = ["target", "includeconf"]
        re_name = keyname or "[a-z]+"
        re_target = target or "[a-z]*"
        # XXX TODO <value>\S.+?  requires TWO chars, breaks %!include:a
        cfgregex = re.compile(
            r"""
                ^%%!\s*               # leading id with opt spaces
                (?P<name>%s)\s*       # config name
                (\((?P<target>%s)\))? # optional target spec inside ()
                \s*:\s*               # key:value delimiter with opt spaces
                (?P<value>\S.+?)      # config value
                \s*$                  # rstrip() spaces and hit EOL
                """
            % (re_name, re_target),
            re.I + re.VERBOSE,
        )
        prepostregex = re.compile(
            r"""
                                      # ---[ PATTERN ]---
                ^( "([^"]*)"          # "double quoted" or
                | '([^']*)'           # 'single quoted' or
                | ([^\s]+)            # single_word
                )
                \s+                   # separated by spaces

                                      # ---[ REPLACE ]---
                ( "([^"]*)"           # "double quoted" or
                | '([^']*)'           # 'single quoted' or
                | (.*)                # anything
                )
                \s*$
                """,
            re.VERBOSE,
        )

        # Give me a match or get out
        match = cfgregex.match(line)
        if not match:
            return empty

        # Save information about this config
        name = (match.group("name") or "").lower()
        target = (match.group("target") or "all").lower()
        value = match.group("value")

        # %!keyword(target) not allowed for these
        if name in no_target and match.group("target"):
            Error("You can't use (target) with %s" % ("%!" + name) + "\n%s" % line)

        # Force no_target keywords to be valid for all targets
        if name in no_target:
            target = "all"

        # Special config with two quoted values (%!preproc: "foo" 'bar')
        if name == "preproc" or name == "postproc":
            valmatch = prepostregex.search(value)
            if not valmatch:
                return empty
            getval = valmatch.group
            patt = getval(2) or getval(3) or getval(4) or ""
            repl = getval(6) or getval(7) or getval(8) or ""
            value = (patt, repl)
        return [target, name, value]


##############################################################################


class MaskMaster:
    "(Un)Protect important structures from escaping and formatting"

    def __init__(self):
        self.linkmask = "vvvLINKvvv"
        self.monomask = "vvvMONOvvv"
        self.rawmask = "vvvRAWvvv"
        self.taggedmask = "vvvTAGGEDvvv"
        self.reset()

    def reset(self):
        self.linkbank = []
        self.monobank = []
        self.rawbank = []
        self.taggedbank = []

    def mask(self, line=""):
        # The verbatim, raw and tagged inline marks are mutually exclusive.
        # This means that one can't appear inside the other.
        # If found, the inner marks must be ignored.
        # Example: ``foo ""bar"" ''baz''``
        # In HTML: <code>foo ""bar"" ''baz''</code>
        #
        # The trick here is to protect the mark who appears first on the line.
        # The three regexes are tried and the one with the lowest index wins.
        # If none is found (else), we get out of the loop.
        #
        while True:
            try:
                t = regex["tagged"].search(line).start()
            except Exception:
                t = -1

            try:
                r = regex["raw"].search(line).start()
            except Exception:
                r = -1

            try:
                v = regex["fontMono"].search(line).start()
            except Exception:
                v = -1

            # Protect tagged text
            if t >= 0 and (r == -1 or t < r) and (v == -1 or t < v):
                txt = regex["tagged"].search(line).group(1)
                if TARGET == "tex":
                    txt = txt.replace("_", "vvvUnderscoreInTaggedTextvvv")
                self.taggedbank.append(txt)
                line = regex["tagged"].sub(self.taggedmask, line, 1)

            # Protect raw text
            elif r >= 0 and (t == -1 or r < t) and (v == -1 or r < v):
                txt = regex["raw"].search(line).group(1)
                txt = doEscape(TARGET, txt)
                if TARGET == "tex":
                    txt = txt.replace("_", "vvvUnderscoreInRawTextvvv")
                self.rawbank.append(txt)
                line = regex["raw"].sub(self.rawmask, line, 1)

            # Protect verbatim text
            elif v >= 0 and (t == -1 or v < t) and (r == -1 or v < r):
                txt = regex["fontMono"].search(line).group(1)
                txt = doEscape(TARGET, txt)
                self.monobank.append(txt)
                line = regex["fontMono"].sub(self.monomask, line, 1)
            else:
                break

        # Protect URLs and emails
        while regex["linkmark"].search(line) or regex["link"].search(line):

            # Try to match plain or named links
            match_link = regex["link"].search(line)
            match_named = regex["linkmark"].search(line)

            # Define the current match
            if match_link and match_named:
                # Both types found, which is the first?
                m = match_link
                if match_named.start() < match_link.start():
                    m = match_named
            else:
                # Just one type found, we're fine
                m = match_link or match_named

            # Extract link data and apply mask
            if m == match_link:  # plain link
                link = m.group()
                label = ""
                link_re = regex["link"]
            else:  # named link
                link = m.group("link")
                label = m.group("label").rstrip()
                link_re = regex["linkmark"]
            line = link_re.sub(self.linkmask, line, 1)

            # Save link data to the link bank
            self.linkbank.append((label, link))
        return line

    def undo(self, line):
        # url & email
        for label, url in self.linkbank:
            link = get_tagged_link(label, url)
            line = line.replace(self.linkmask, link, 1)

        # Expand verb
        for mono in self.monobank:
            open_, close = TAGS["fontMonoOpen"], TAGS["fontMonoClose"]
            line = line.replace(self.monomask, open_ + mono + close, 1)

        # Expand raw
        for raw in self.rawbank:
            line = line.replace(self.rawmask, raw, 1)

        # Expand tagged
        for tagged in self.taggedbank:
            line = line.replace(self.taggedmask, tagged, 1)

        return line


##############################################################################


class TitleMaster:
    "Title things"

    def __init__(self):
        self.count = ["", 0, 0, 0, 0, 0]
        self.toc = []
        self.level = 0
        self.kind = ""
        self.txt = ""
        self.label = ""
        self.tag = ""
        self.tag_hold = []
        self.last_level = 0
        self.count_id = ""
        self.anchor_count = 0
        self.anchor_prefix = "toc"

    def _open_close_blocks(self):
        "Open new title blocks, closing the previous (if any)"
        if not rules["titleblocks"]:
            return
        tag = ""
        last = self.last_level
        curr = self.level

        # Same level, just close the previous
        if curr == last:
            tag = TAGS.get("title%dClose" % last)
            if tag:
                self.tag_hold.append(tag)

        # Section -> subsection, more depth
        while curr > last:
            last += 1

            # Open the new block of subsections
            tag = TAGS.get("blockTitle%dOpen" % last)
            if tag:
                self.tag_hold.append(tag)

            # Jump from title1 to title3 or more
            # Fill the gap with an empty section
            if curr - last > 0:
                tag = TAGS.get("title%dOpen" % last)
                tag = regex["x"].sub("", tag)  # del \a
                if tag:
                    self.tag_hold.append(tag)

        # Section <- subsection, less depth
        while curr < last:
            # Close the current opened subsection
            tag = TAGS.get("title%dClose" % last)
            if tag:
                self.tag_hold.append(tag)

            # Close the current opened block of subsections
            tag = TAGS.get("blockTitle%dClose" % last)
            if tag:
                self.tag_hold.append(tag)

            last -= 1

            # Close the previous section of the same level
            # The subsections were under it
            if curr == last:
                tag = TAGS.get("title%dClose" % last)
                if tag:
                    self.tag_hold.append(tag)

    def add(self, line):
        "Parses a new title line."
        if not line:
            return
        self._set_prop(line)
        self._open_close_blocks()
        self._set_count_id()
        self._set_label()
        self._save_toc_info()

    def close_all(self):
        "Closes all opened title blocks"
        ret = []
        ret.extend(self.tag_hold)
        while self.level:
            tag = TAGS.get("title%dClose" % self.level)
            if tag:
                ret.append(tag)
            tag = TAGS.get("blockTitle%dClose" % self.level)
            if tag:
                ret.append(tag)
            self.level -= 1
        return ret

    def _save_toc_info(self):
        "Save TOC info, used by self.dump_marked_toc()"
        self.toc.append((self.level, self.count_id, self.txt, self.label))

    def _set_prop(self, line=""):
        "Extract info from original line and set data holders."
        # Detect title type (numbered or not)
        id_ = line.lstrip()[0]
        if id_ == "=":
            kind = "title"
        elif id_ == "+":
            kind = "numtitle"
        else:
            Error("Unknown Title ID '%s'" % id_)
        # Extract line info
        match = regex[kind].search(line)
        level = len(match.group("id"))
        txt = match.group("txt").strip()
        label = match.group("label")
        # Parse info & save
        if CONF["enum-title"]:
            kind = "numtitle"  # force
        if rules["titleblocks"]:
            self.tag = TAGS.get("%s%dOpen" % (kind, level)) or TAGS.get(
                "title%dOpen" % level
            )
        else:
            self.tag = TAGS.get(kind + repr(level)) or TAGS.get("title" + repr(level))
        self.last_level = self.level
        self.kind = kind
        self.level = level
        self.txt = txt
        self.label = label

    def _set_count_id(self):
        "Compose and save the title count identifier (if needed)."
        count_id = ""
        if self.kind == "numtitle" and not rules["autonumbertitle"]:
            # Manually increase title count
            self.count[self.level] += 1
            # Reset sublevels count (if any)
            max_levels = len(self.count)
            if self.level < max_levels - 1:
                for i in range(self.level + 1, max_levels):
                    self.count[i] = 0
            # Compose count id from hierarchy
            for i in range(self.level):
                count_id = "%s%d." % (count_id, self.count[i + 1])
        self.count_id = count_id

    def _set_label(self):
        "Compose and save title label, used by anchors."
        # Remove invalid chars from label set by user
        self.label = re.sub("[^A-Za-z0-9_-]", "", self.label or "")

    def _get_tagged_anchor(self):
        "Return anchor if user defined a label, or TOC is on."
        ret = ""
        label = self.label
        if CONF["toc"]:
            self.anchor_count += 1
            # Autonumber label (if needed)
            label = label or "{}{}".format(self.anchor_prefix, self.anchor_count)
        if label and TAGS["anchor"]:
            ret = regex["x"].sub(label, TAGS["anchor"])
        return ret

    def _get_full_title_text(self):
        "Returns the full title contents, already escaped."
        ret = self.txt
        # Insert count_id (if any) before text
        if self.count_id:
            ret = "{} {}".format(self.count_id, ret)
        # Escape specials
        ret = doEscape(TARGET, ret)
        # Same targets needs final escapes on title lines
        # It's here because there is a 'continue' after title
        if rules["finalescapetitle"]:
            ret = doFinalEscape(TARGET, ret)
        return ret

    def get(self):
        "Returns the tagged title as a list."
        ret = []

        # Maybe some anchoring before?
        anchor = self._get_tagged_anchor()
        self.tag = regex["_anchor"].sub(anchor, self.tag)

        # Compose & escape title text (TOC uses unescaped)
        full_title = self._get_full_title_text()

        # Close previous section area
        ret.extend(self.tag_hold)
        self.tag_hold = []

        tagged = regex["x"].sub(full_title, self.tag)

        # Adds "underline" on TXT target
        if TARGET == "txt":
            if BLOCK.count > 1:
                ret.append("")  # blank line before
            ret.append(tagged)
            # Get the right letter count for UTF
            if isinstance(full_title, bytes):
                full_title = full_title.decode(ENCODING)
            ret.append(regex["x"].sub("=" * len(full_title), self.tag))
        else:
            ret.append(tagged)
        return ret

    def dump_marked_toc(self):
        "Dumps all toc itens as a valid t2t-marked list"
        ret = []
        toc_count = 1
        for level, count_id, txt, label in self.toc:
            indent = "  " * level
            id_txt = ("{} {}".format(count_id, txt)).lstrip()
            label = label or self.anchor_prefix + repr(toc_count)
            toc_count += 1

            # TOC will have crosslinks to anchors
            if TAGS["anchor"]:
                if CONF["enum-title"] and level == 1:
                    # 1. [Foo #anchor] is more readable than [1. Foo #anchor] in level 1.
                    # This is an idea stolen from Windows .CHM help files.
                    tocitem = '{}+ [""{}"" #{}]'.format(indent, txt, label)
                else:
                    tocitem = '{}- [""{}"" #{}]'.format(indent, id_txt, label)

            # TOC will be plain text (no links)
            else:
                if TARGET in ["txt", "man"]:
                    # For these, the list is not necessary, just dump the text
                    tocitem = '{}""{}""'.format(indent, id_txt)
                else:
                    tocitem = '{}- ""{}""'.format(indent, id_txt)
            ret.append(tocitem)
        return ret


##############################################################################

# TODO check all this table mess
# It uses parse_row properties for table lines
# BLOCK.table() replaces the cells by the parsed content
class TableMaster:
    def __init__(self, line=""):
        self.rows = []
        self.border = False
        self.align = "Left"
        self.cellalign = []
        self.colalign = []
        self.cellspan = []
        if line:
            prop = self.parse_row(line)
            self.border = prop["border"]
            self.align = prop["align"]
            self.cellalign = prop["cellalign"]
            self.cellspan = prop["cellspan"]
            self.colalign = self._get_col_align()

    def _get_col_align(self):
        colalign = []
        for cell in range(len(self.cellalign)):
            align = self.cellalign[cell]
            span = self.cellspan[cell]
            colalign.extend([align] * span)
        return colalign

    def _get_open_tag(self):
        topen = TAGS["tableOpen"]
        tborder = TAGS["_tableBorder"]
        talign = TAGS["_tableAlign" + self.align]
        calignsep = TAGS["tableColAlignSep"]
        calign = ""

        # The first line defines if table has border or not
        if not self.border:
            tborder = ""
        # Set the columns alignment
        if rules["tablecellaligntype"] == "column":
            calign = [TAGS["_tableColAlign%s" % x] for x in self.colalign]
            calign = calignsep.join(calign)
        # Align full table, set border and Column align (if any)
        topen = regex["_tableAlign"].sub(talign, topen)
        topen = regex["_tableBorder"].sub(tborder, topen)
        topen = regex["_tableColAlign"].sub(calign, topen)
        # Tex table spec, border or not: {|l|c|r|} , {lcr}
        if calignsep and not self.border:
            # Remove cell align separator
            topen = topen.replace(calignsep, "")
        return topen

    def _get_cell_align(self, cells):
        ret = []
        for cell in cells:
            align = "Left"
            if cell.strip():
                if cell[0] == " " and cell[-1] == " ":
                    align = "Center"
                elif cell[0] == " ":
                    align = "Right"
            ret.append(align)
        return ret

    def _get_cell_span(self, cells):
        ret = []
        for cell in cells:
            span = 1
            m = re.search(r"\a(\|+)$", cell)
            if m:
                span = len(m.group(1)) + 1
            ret.append(span)
        return ret

    def _tag_cells(self, rowdata):
        row = []
        cells = rowdata["cells"]
        open_ = TAGS["tableCellOpen"]
        close = TAGS["tableCellClose"]
        sep = TAGS["tableCellSep"]
        calign = [TAGS["_tableCellAlign" + x] for x in rowdata["cellalign"]]
        calignsep = TAGS["tableColAlignSep"]

        # Populate the span and multicol open tags
        cspan = []
        multicol = []
        colindex = 0
        for cellindex in range(0, len(rowdata["cellspan"])):
            span = rowdata["cellspan"][cellindex]

            if span > 1:
                cspan.append(regex["x"].sub(str(span), TAGS["_tableCellColSpan"]))

                mcopen = regex["x"].sub(str(span), TAGS["_tableCellMulticolOpen"])
                multicol.append(mcopen)
            else:
                cspan.append("")
                multicol.append("")

            if not self.border:
                multicol[-1] = multicol[-1].replace(calignsep, "")

            colindex += span

        # Maybe is it a title row?
        if rowdata["title"]:
            open_ = TAGS["tableTitleCellOpen"] or open_
            close = TAGS["tableTitleCellClose"] or close
            sep = TAGS["tableTitleCellSep"] or sep

        # Should we break the line on *each* table cell?
        if rules["breaktablecell"]:
            close = close + "\n"

        # Cells pre processing
        if rules["tablecellstrip"]:
            cells = [x.strip() for x in cells]
        if rowdata["title"] and rules["tabletitlerowinbold"]:
            cells = [enclose_me("fontBold", x) for x in cells]

        # Add cell BEGIN/END tags
        for cell in cells:
            copen = open_
            cclose = close
            # Make sure we will pop from some filled lists
            # Fixes empty line bug '| |'
            this_align = this_span = this_mcopen = ""
            if calign:
                this_align = calign.pop(0)
            if cspan:
                this_span = cspan.pop(0)
            if multicol:
                this_mcopen = multicol.pop(0)

            # Insert cell align into open tag (if cell is alignable)
            if rules["tablecellaligntype"] == "cell":
                copen = regex["_tableCellAlign"].sub(this_align, copen)

            # Insert cell span into open tag (if cell is spannable)
            if rules["tablecellspannable"]:
                copen = regex["_tableCellColSpan"].sub(this_span, copen)

            # Use multicol tags instead (if multicol supported, and if
            # cell has a span or is aligned differently to column)
            if rules["tablecellmulticol"]:
                if this_mcopen:
                    copen = regex["_tableColAlign"].sub(this_align, this_mcopen)
                    cclose = TAGS["_tableCellMulticolClose"]

            row.append(copen + cell + cclose)

        # Maybe there are cell separators?
        return sep.join(row)

    def add_row(self, cells):
        self.rows.append(cells)

    def parse_row(self, line):
        # Default table properties
        ret = {
            "border": False,
            "title": False,
            "align": "Left",
            "cells": [],
            "cellalign": [],
            "cellspan": [],
        }
        # Detect table align (and remove spaces mark)
        if line[0] == " ":
            ret["align"] = "Center"
        line = line.lstrip()
        # Detect title mark
        if line[1] == "|":
            ret["title"] = True
        # Detect border mark and normalize the EOL
        m = re.search(r" (\|+) *$", line)
        if m:
            line += " "
            ret["border"] = True
        else:
            line += " | "
        # Delete table mark
        line = regex["table"].sub("", line)
        # Detect colspan  | foo | bar baz |||
        line = re.sub(r" (\|+)\| ", "\a\\1 | ", line)
        # Split cells (the last is fake)
        ret["cells"] = line.split(" | ")[:-1]
        # Find cells span
        ret["cellspan"] = self._get_cell_span(ret["cells"])
        # Remove span ID
        ret["cells"] = [re.sub(r"\a\|+$", "", x) for x in ret["cells"]]
        # Find cells align
        ret["cellalign"] = self._get_cell_align(ret["cells"])
        # Hooray!
        Debug("Table Prop: %s" % ret, 7)
        return ret

    def dump(self):
        open_ = self._get_open_tag()
        rows = self.rows
        close = TAGS["tableClose"]

        rowopen = TAGS["tableRowOpen"]
        rowclose = TAGS["tableRowClose"]
        rowsep = TAGS["tableRowSep"]
        titrowopen = TAGS["tableTitleRowOpen"] or rowopen
        titrowclose = TAGS["tableTitleRowClose"] or rowclose

        if rules["breaktablelineopen"]:
            rowopen = rowopen + "\n"
            titrowopen = titrowopen + "\n"

        # Tex gotchas
        if TARGET == "tex":
            if not self.border:
                rowopen = titrowopen = ""
            else:
                close = rowopen + close

        # Now we tag all the table cells on each row
        tagged_cells = [self._tag_cells(cell) for cell in rows]

        # Add row separator tags between lines
        tagged_rows = []
        if rowsep:
            tagged_rows = [cell + rowsep for cell in tagged_cells]
            # Remove last rowsep, because the table is over
            tagged_rows[-1] = tagged_rows[-1].replace(rowsep, "")
        # Add row BEGIN/END tags for each line
        else:
            for rowdata in rows:
                if rowdata["title"]:
                    o, c = titrowopen, titrowclose
                else:
                    o, c = rowopen, rowclose
                row = tagged_cells.pop(0)
                tagged_rows.append(o + row + c)
                if rowdata["title"] and TARGET == "md":
                    titrowcloserow = "|"
                    for _cell in rowdata["cells"]:
                        titrowcloserow += "---|"
                    tagged_rows.append(titrowcloserow)

        # Join the pieces together
        fulltable = []
        if open_:
            fulltable.append(open_)
        fulltable.extend(tagged_rows)
        if close:
            fulltable.append(close)

        return fulltable


##############################################################################


class BlockMaster:
    "TIP: use blockin/out to add/del holders"

    def __init__(self):
        self.BLK = []
        self.HLD = []
        self.PRP = []
        self.depth = 0
        self.count = 0
        self.last = ""
        self.tableparser = None
        self.contains = {
            "para": ["comment", "raw", "tagged"],
            "verb": [],
            "table": ["comment"],
            "raw": [],
            "tagged": [],
            "comment": [],
            "quote": ["quote", "comment", "raw", "tagged"],
            "list": [
                "list",
                "numlist",
                "deflist",
                "para",
                "verb",
                "comment",
                "raw",
                "tagged",
            ],
            "numlist": [
                "list",
                "numlist",
                "deflist",
                "para",
                "verb",
                "comment",
                "raw",
                "tagged",
            ],
            "deflist": [
                "list",
                "numlist",
                "deflist",
                "para",
                "verb",
                "comment",
                "raw",
                "tagged",
            ],
            "bar": [],
            "title": [],
            "numtitle": [],
        }
        self.allblocks = list(self.contains.keys())

        # If one is found inside another, ignore the marks
        self.exclusive = ["comment", "verb", "raw", "tagged"]

        # May we include bars inside quotes?
        if rules["barinsidequote"]:
            self.contains["quote"].append("bar")

    def block(self):
        if not self.BLK:
            return ""
        return self.BLK[-1]

    def isblock(self, name=""):
        return self.block() == name

    def prop(self, key):
        if not self.PRP:
            return ""
        return self.PRP[-1].get(key) or ""

    def propset(self, key, val):
        self.PRP[-1][key] = val
        # Debug('BLOCK prop ++: %s->%s'%(key,repr(val)), 1)
        # Debug('BLOCK props: %s'%(repr(self.PRP)), 1)

    def hold(self):
        if not self.HLD:
            return []
        return self.HLD[-1]

    def holdadd(self, line):
        if self.block().endswith("list"):
            line = [line]
        self.HLD[-1].append(line)
        Debug("HOLD add: %s" % repr(line), 4)
        Debug("FULL HOLD: %s" % self.HLD, 4)

    def holdaddsub(self, line):
        self.HLD[-1][-1].append(line)
        Debug("HOLD addsub: %s" % repr(line), 4)
        Debug("FULL HOLD: %s" % self.HLD, 4)

    def holdextend(self, lines):
        if self.block().endswith("list"):
            lines = [lines]
        self.HLD[-1].extend(lines)
        Debug("HOLD extend: %s" % repr(lines), 4)
        Debug("FULL HOLD: %s" % self.HLD, 4)

    def blockin(self, block):
        ret = []
        if block not in self.allblocks:
            Error("Invalid block '%s'" % block)

        # First, let's close other possible open blocks
        while self.block() and block not in self.contains[self.block()]:
            ret.extend(self.blockout())

        # Now we can gladly add this new one
        self.BLK.append(block)
        self.HLD.append([])
        self.PRP.append({})
        self.count += 1
        if block == "table":
            self.tableparser = TableMaster()
        # Deeper and deeper
        self.depth = len(self.BLK)
        Debug("block ++ ({}): {}".format(block, self.BLK), 3)
        return ret

    def blockout(self):
        if not self.BLK:
            raise AssertionError("No block to pop")
        blockname = self.BLK.pop()
        result = getattr(self, blockname)()
        parsed = self.HLD.pop()
        self.PRP.pop()
        self.depth = len(self.BLK)
        if blockname == "table":
            del self.tableparser

        # Inserting a nested block into mother
        if self.block():
            if blockname != "comment":  # ignore comment blocks
                if self.block().endswith("list"):
                    self.HLD[-1][-1].append(result)
                else:
                    self.HLD[-1].append(result)
            # Reset now. Mother block will have it all
            result = []

        Debug("block -- ({}): {}".format(blockname, self.BLK), 3)
        Debug("RELEASED ({}): {}".format(blockname, parsed), 3)

        # Save this top level block name (produced output)
        # The next block will use it
        if result:
            self.last = blockname
            Debug("BLOCK: %s" % result, 6)

        return result

    def _last_escapes(self, line):
        return doFinalEscape(TARGET, line)

    def _get_escaped_hold(self):
        ret = []
        for line in self.hold():
            if isinstance(line, list):
                ret.extend(line)
            else:
                ret.append(self._last_escapes(line))
        return ret

    def _remove_twoblanks(self, lastitem):
        if len(lastitem) > 1 and lastitem[-2:] == ["", ""]:
            return lastitem[:-2]
        return lastitem

    def _should_add_blank_line(self, where, blockname):
        "Validates the blanksaround* rules"

        # Nestable blocks: only mother blocks (level 1) are spaced
        if blockname.endswith("list") and self.depth > 1:
            return False

        # The blank line after the block is always added
        if where == "after" and rules["blanksaround" + blockname]:
            return True

        # The blank line before the block is only added if
        # the previous block haven't added a blank line
        # (to avoid consecutive blanks)
        elif (
            where == "before"
            and rules["blanksaround" + blockname]
            and not rules.get("blanksaround" + self.last)
        ):
            return True

        # Nested quotes are handled here,
        # because the mother quote isn't closed yet
        elif (
            where == "before"
            and blockname == "quote"
            and rules["blanksaround" + blockname]
            and self.depth > 1
        ):
            return True

        return False

    def comment(self):
        return ""

    def raw(self):
        lines = self.hold()
        return [doEscape(TARGET, x) for x in lines]

    def tagged(self):
        return self.hold()

    def para(self):
        result = []
        open_ = TAGS["paragraphOpen"]
        close = TAGS["paragraphClose"]
        lines = self._get_escaped_hold()

        # Blank line before?
        if self._should_add_blank_line("before", "para"):
            result.append("")

        # Open tag
        if open_:
            result.append(open_)

        # Pagemaker likes a paragraph as a single long line
        if rules["onelinepara"]:
            result.append(" ".join(lines))
        # Others are normal :)
        else:
            result.extend(lines)

        # Close tag
        if close:
            result.append(close)

        # Blank line after?
        if self._should_add_blank_line("after", "para"):
            result.append("")

        return result

    def verb(self):
        "Verbatim lines are not masked, so there's no need to unmask"
        result = []
        open_ = TAGS["blockVerbOpen"]
        close = TAGS["blockVerbClose"]

        # Blank line before?
        if self._should_add_blank_line("before", "verb"):
            result.append("")

        # Open tag
        if open_:
            result.append(open_)

        # Get contents
        for line in self.hold():
            if not rules["verbblocknotescaped"]:
                line = doEscape(TARGET, line)
            if TAGS["blockVerbLine"]:
                line = TAGS["blockVerbLine"] + line
            if rules["indentverbblock"]:
                line = "  " + line
            if rules["verbblockfinalescape"]:
                line = doFinalEscape(TARGET, line)
            result.append(line)

        # Close tag
        if close:
            result.append(close)

        # Blank line after?
        if self._should_add_blank_line("after", "verb"):
            result.append("")

        return result

    def numtitle(self):
        return self.title("numtitle")

    def title(self, name="title"):
        result = []

        # Blank line before?
        if self._should_add_blank_line("before", name):
            result.append("")

        # Get contents
        result.extend(TITLE.get())

        # Blank line after?
        if self._should_add_blank_line("after", name):
            result.append("")

        return result

    def table(self):
        result = []

        # Blank line before?
        if self._should_add_blank_line("before", "table"):
            result.append("")

        # Rewrite all table cells by the unmasked and escaped data
        lines = self._get_escaped_hold()
        for i in range(len(lines)):
            cells = lines[i].split(SEPARATOR)
            self.tableparser.rows[i]["cells"] = cells
        result.extend(self.tableparser.dump())

        # Blank line after?
        if self._should_add_blank_line("after", "table"):
            result.append("")

        return result

    def quote(self):
        result = []
        open_ = TAGS["blockQuoteOpen"]  # block based
        close = TAGS["blockQuoteClose"]
        qline = TAGS["blockQuoteLine"]  # line based
        indent = tagindent = "\t" * self.depth

        # Apply rules
        if rules["tagnotindentable"]:
            tagindent = ""
        if not rules["keepquoteindent"]:
            indent = ""

        # Blank line before?
        if self._should_add_blank_line("before", "quote"):
            result.append("")

        # Open tag
        if open_:
            result.append(tagindent + open_)

        # Get contents
        for item in self.hold():
            if isinstance(item, list):
                result.extend(item)  # subquotes
            else:
                item = regex["quote"].sub("", item)  # del TABs
                item = self._last_escapes(item)
                item = qline * self.depth + item
                result.append(indent + item)  # quote line

        # Close tag
        if close:
            result.append(tagindent + close)

        # Blank line after?
        if self._should_add_blank_line("after", "quote"):
            result.append("")

        return result

    def bar(self):
        result = []
        bar_tag = ""

        # Blank line before?
        if self._should_add_blank_line("before", "bar"):
            result.append("")

        # Get the original bar chars
        bar_chars = self.hold()[0].strip()

        # Set bar type
        if bar_chars.startswith("="):
            bar_tag = TAGS["bar2"]
        else:
            bar_tag = TAGS["bar1"]

        # To avoid comment tag confusion like <!-- ------ --> (sgml)
        if TAGS["comment"].count("--"):
            bar_chars = bar_chars.replace("--", "__")

        # Get the bar tag (may contain \a)
        result.append(regex["x"].sub(bar_chars, bar_tag))

        # Blank line after?
        if self._should_add_blank_line("after", "bar"):
            result.append("")

        return result

    def deflist(self):
        return self.list("deflist")

    def numlist(self):
        return self.list("numlist")

    def list(self, name="list"):
        result = []
        items = self.hold()
        indent = self.prop("indent")
        tagindent = indent
        listline = TAGS.get(name + "ItemLine")
        itemcount = 0

        if name == "deflist":
            itemopen = TAGS[name + "Item1Open"]
            itemclose = TAGS[name + "Item2Close"]
            itemsep = TAGS[name + "Item1Close"] + TAGS[name + "Item2Open"]
        else:
            itemopen = TAGS[name + "ItemOpen"]
            itemclose = TAGS[name + "ItemClose"]
            itemsep = ""

        # Apply rules
        if rules["tagnotindentable"]:
            tagindent = ""
        if not rules["keeplistindent"]:
            indent = tagindent = ""

        # ItemLine: number of leading chars identifies list depth
        if listline:
            itemopen = listline * self.depth + itemopen

        # Adds trailing space on opening tags
        if (name == "list" and rules["spacedlistitemopen"]) or (
            name == "numlist" and rules["spacednumlistitemopen"]
        ):
            itemopen = itemopen + " "

        # Remove two-blanks from list ending mark, to avoid <p>
        items[-1] = self._remove_twoblanks(items[-1])

        # Blank line before?
        if self._should_add_blank_line("before", name):
            result.append("")

        # Tag each list item (multiline items), store in listbody
        itemopenorig = itemopen
        listbody = []
        widelist = 0
        for item in items:

            # Add "manual" item count for noautonum targets
            itemcount += 1
            if name == "numlist" and not rules["autonumberlist"]:
                n = str(itemcount)
                itemopen = regex["x"].sub(n, itemopenorig)
                del n

            # Tag it
            item[0] = self._last_escapes(item[0])
            if name == "deflist":
                _, term, rest = item[0].split(SEPARATOR, 2)
                item[0] = rest
                if not item[0]:
                    del item[0]  # to avoid <p>
                listbody.append(tagindent + itemopen + term + itemsep)
            else:
                fullitem = tagindent + itemopen
                listbody.append(item[0].replace(SEPARATOR, fullitem))
                del item[0]

            # Process next lines for this item (if any)
            for line in item:
                if isinstance(line, list):  # sublist inside
                    listbody.extend(line)
                else:
                    line = self._last_escapes(line)

                    # Blank lines turns to <p>
                    if not line and rules["parainsidelist"]:
                        line = indent + TAGS["paragraphOpen"] + TAGS["paragraphClose"]
                        line = line.rstrip()
                        widelist = 1

                    # Some targets don't like identation here (wiki)
                    if not rules["keeplistindent"] or (
                        name == "deflist" and rules["deflisttextstrip"]
                    ):
                        line = line.lstrip()

                    # Maybe we have a line prefix to add? (wiki)
                    if name == "deflist" and TAGS["deflistItem2LinePrefix"]:
                        line = TAGS["deflistItem2LinePrefix"] + line

                    listbody.append(line)

            # Close item (if needed)
            if itemclose:
                listbody.append(tagindent + itemclose)

        if not widelist and rules["compactlist"]:
            listopen = TAGS.get(name + "OpenCompact")
            listclose = TAGS.get(name + "CloseCompact")
        else:
            listopen = TAGS.get(name + "Open")
            listclose = TAGS.get(name + "Close")

        # Open list (not nestable lists are only opened at mother)
        if listopen and not (rules["listnotnested"] and BLOCK.depth != 1):
            result.append(tagindent + listopen)

        result.extend(listbody)

        # Close list (not nestable lists are only closed at mother)
        if listclose and not (rules["listnotnested"] and self.depth != 1):
            result.append(tagindent + listclose)

        # Blank line after?
        if self._should_add_blank_line("after", name):
            result.append("")

        return result


##############################################################################


def listTargets():
    """List available targets."""
    for target, name in sorted(TARGET_NAMES.items()):
        print("{:8}{}".format(target, name))


def get_file_body(file_):
    "Returns all the document BODY lines"
    return process_source_file(file_, noconf=1)[1][2]


def finish_him(outlist, config):
    "Writing output to screen or file"
    outfile = config["outfile"]
    outlist = unmaskEscapeChar(outlist)
    outlist = expandLineBreaks(outlist)

    # Apply PostProc filters
    if config["postproc"]:
        filters = compile_filters(config["postproc"], "Invalid PostProc filter regex")
        postoutlist = []
        errmsg = "Invalid PostProc filter replacement"
        for line in outlist:
            for rgx, repl in filters:
                try:
                    line = rgx.sub(repl, line)
                except Exception:
                    Error("{}: '{}'".format(errmsg, repl))
            postoutlist.append(line)
        outlist = postoutlist[:]

    if outfile == MODULEOUT:
        return outlist
    elif outfile == STDOUT:
        Message("Saving results to the output file", 1)
        for line in outlist:
            print(line)
    else:
        Message("Saving results to the output file", 1)
        Savefile(outfile, outlist)
        if not QUIET:
            print("{} wrote {}".format(my_name, outfile))


def toc_tagger(toc, config):
    "Returns the tagged TOC, as a single tag or a tagged list"
    if not config["toc"]:
        return []
    elif TAGS["TOC"]:
        # Our TOC list is not needed, the target already knows how to do a TOC
        ret = [TAGS["TOC"]]
    # Convert the TOC list (t2t-marked) to the target's list format
    else:
        fakeconf = config.copy()
        fakeconf["headers"] = 0
        fakeconf["preproc"] = []
        fakeconf["postproc"] = []
        ret, _ = convert(toc, fakeconf)
        set_global_config(config)  # restore config
    return ret


def toc_formatter(toc, config):
    "Formats TOC for automatic placement between headers and body"

    if not config["toc"]:
        return []  # TOC disabled
    ret = toc

    # TOC open/close tags (if any)
    if TAGS["tocOpen"]:
        ret.insert(0, TAGS["tocOpen"])
    if TAGS["tocClose"]:
        ret.append(TAGS["tocClose"])

    # Autotoc specific formatting
    if rules["autotocwithbars"]:  # TOC between bars
        para = TAGS["paragraphOpen"] + TAGS["paragraphClose"]
        bar = regex["x"].sub("-" * DFT_TEXT_WIDTH, TAGS["bar1"])
        tocbar = [para, bar, para]
        ret = tocbar + ret + tocbar
    if rules["blankendautotoc"]:  # blank line after TOC
        ret.append("")
    if rules["autotocnewpagebefore"]:  # page break before TOC
        ret.insert(0, TAGS["pageBreak"])
    if rules["autotocnewpageafter"]:  # page break after TOC
        ret.append(TAGS["pageBreak"])
    return ret


def doHeader(headers, config):
    if not config["headers"]:
        return []
    if not headers:
        headers = ["", "", ""]
    target = config["target"]

    template = HEADER_TEMPLATE[target].split("\n")

    style = config.get("style")
    # Tex: strip .sty extension from each style filename.
    if target == "tex":
        style = [os.path.splitext(x)[0] for x in style]

    head_data = {"STYLE": style, "ENCODING": get_encoding_string(target)}

    # Parse header contents
    for i in 0, 1, 2:
        contents = headers[i]
        # Escapes - on tex, just do it if any \tag{} present
        if target != "tex" or (target == "tex" and re.search(r"\\\w+{", contents)):
            contents = doEscape(target, contents)
        if target in ["lout", "tex"]:
            contents = doFinalEscape(target, contents)

        head_data["HEADER%d" % (i + 1)] = contents

    Debug("Header Data: %s" % head_data, 1)

    # Scan for empty dictionary keys
    # If found, scan template lines for that key reference
    # If found, remove the reference
    # If there isn't any other key reference on the same line, remove it
    # TODO loop by template line > key
    for key, value in head_data.items():
        if value:
            continue
        for line in template:
            if line.count("%%(%s)s" % key):
                sline = line.replace("%%(%s)s" % key, "")
                if not re.search(r"%\([A-Z0-9]+\)s", sline):
                    template.remove(line)
    # Style is a multiple tag.
    # - If none or just one, use default template
    # - If two or more, insert extra lines in a loop (and remove original)
    styles = head_data["STYLE"]
    if len(styles) == 1:
        head_data["STYLE"] = styles[0]
    elif len(styles) > 1:
        style_mark = "%(STYLE)s"
        for i in range(len(template)):
            if template[i].count(style_mark):
                while styles:
                    template.insert(
                        i + 1, template[i].replace(style_mark, styles.pop())
                    )
                del template[i]
                break
    # Populate template with data (dict expansion)
    template = "\n".join(template) % head_data

    return template.split("\n")


def doFooter(config):
    ret = []

    # No footer. The --no-headers option hides header AND footer
    if not config["headers"]:
        return []

    # Only add blank line before footer if last block doesn't added by itself
    if not rules.get("blanksaround" + BLOCK.last):
        ret.append("")

    # Maybe we have a specific tag to close the document?
    if TAGS["EOD"]:
        ret.append(TAGS["EOD"])

    return ret


def doEscape(target, txt):
    "Target-specific special escapes. Apply *before* insert any tag."
    tmpmask = "vvvvThisEscapingSuxvvvv"
    if target in ("html", "sgml", "dbk"):
        txt = re.sub("&", "&amp;", txt)
        txt = re.sub("<", "&lt;", txt)
        txt = re.sub(">", "&gt;", txt)
        if target == "sgml":
            txt = re.sub("\xff", "&yuml;", txt)  # "+y
    elif target == "mgp":
        txt = re.sub("^%", " %", txt)  # add leading blank to avoid parse
    elif target == "man":
        txt = re.sub("^([.'])", "\\&\\1", txt)  # command ID
        txt = txt.replace(ESCCHAR, ESCCHAR + "e")  # \e
    elif target == "lout":
        # TIP: / moved to FinalEscape to avoid //italic//
        # TIP: these are also converted by lout:  ...  ---  --
        txt = txt.replace(ESCCHAR, tmpmask)  # \
        txt = txt.replace('"', '"%s""' % ESCCHAR)  # "\""
        txt = re.sub("([|&{}@#^~])", '"\\1"', txt)  # "@"
        txt = txt.replace(tmpmask, '"%s"' % (ESCCHAR * 2))  # "\\"
    elif target in ("tex", "ctx"):
        # Mark literal \ to be changed to $\backslash$ later
        txt = txt.replace(ESCCHAR, tmpmask)
        txt = re.sub("([#$&%{}])", ESCCHAR + r"\1", txt)  # \%
        txt = re.sub("([~^])", ESCCHAR + r"\1{}", txt)  # \~{}
        txt = re.sub("([<|>])", r"$\1$", txt)  # $>$
        txt = txt.replace(tmpmask, maskEscapeChar(r"$\backslash$"))
        # TIP the _ is escaped at the end
    return txt


# TODO man: where - really needs to be escaped?
def doFinalEscape(target, txt):
    "Last escapes of each line"
    if target == "man":
        txt = txt.replace("-", r"\-")
    elif target == "sgml":
        txt = txt.replace("[", "&lsqb;")
    elif target == "lout":
        txt = txt.replace("/", '"/"')
    elif target == "tex":
        txt = txt.replace("_", r"\_")
        txt = txt.replace("vvvvTexUndervvvv", "_")  # shame!
        txt = txt.replace("vvvUnderscoreInRawTextvvv", "_")
        txt = txt.replace("vvvUnderscoreInTaggedTextvvv", "_")
    return txt


def EscapeCharHandler(action, data):
    "Mask/Unmask the Escape Char on the given string"
    if not data.strip():
        return data
    if action not in ("mask", "unmask"):
        Error("EscapeCharHandler: Invalid action '%s'" % action)
    if action == "mask":
        return data.replace("\\", ESCCHAR)
    else:
        return data.replace(ESCCHAR, "\\")


def maskEscapeChar(data):
    "Replace any escape char with a text mask (Input: str or list)"
    if isinstance(data, list):
        return [EscapeCharHandler("mask", x) for x in data]
    return EscapeCharHandler("mask", data)


def unmaskEscapeChar(data):
    "Undo the escape char masking (Input: str or list)"
    if isinstance(data, list):
        return [EscapeCharHandler("unmask", x) for x in data]
    return EscapeCharHandler("unmask", data)


# Convert ['foo\nbar'] to ['foo', 'bar']
def expandLineBreaks(mylist):
    ret = []
    for line in mylist:
        ret.extend(line.split("\n"))
    return ret


def compile_filters(filters, errmsg="Filter"):
    if filters:
        for i in range(len(filters)):
            patt, repl = filters[i]
            try:
                rgx = re.compile(patt)
            except Exception:
                Error("{}: '{}'".format(errmsg, patt))
            filters[i] = (rgx, repl)
    return filters


def enclose_me(tagname, txt):
    return TAGS.get(tagname + "Open") + txt + TAGS.get(tagname + "Close")


def beautify_me(name, font, line):
    "where name is: bold, italic, underline or strike"

    # Exception: Doesn't parse an horizontal bar as strike
    if name == "strike" and regex["bar"].search(line):
        return line

    open_ = TAGS["%sOpen" % font]
    close = TAGS["%sClose" % font]
    txt = r"{}\1{}".format(open_, close)
    line = regex[font].sub(txt, line)
    return line


def get_tagged_link(label, url):
    ret = ""
    target = CONF["target"]
    image_re = regex["img"]

    # Set link type
    if regex["email"].match(url):
        linktype = "email"
    else:
        linktype = "url"

    # Escape specials from TEXT parts
    label = doEscape(target, label)

    # Escape specials from link URL
    if not rules["linkable"] or rules["escapeurl"]:
        url = doEscape(target, url)

    # Adding protocol to guessed link
    guessurl = ""
    if linktype == "url" and re.match("(?i)" + regex["_urlskel"]["guess"], url):
        if url[0] in "Ww":
            guessurl = "http://" + url
        else:
            guessurl = "ftp://" + url

        # Not link aware targets -> protocol is useless
        if not rules["linkable"]:
            guessurl = ""

    # Simple link (not guessed)
    if not label and not guessurl:
        # Just add link data to tag
        tag = TAGS[linktype]
        ret = regex["x"].sub(url, tag)

    # Named link or guessed simple link
    else:
        # Adjusts for guessed link
        if not label:
            label = url  # no protocol
        if guessurl:
            url = guessurl  # with protocol

        # Image inside link!
        if image_re.match(label):
            if rules["imglinkable"]:  # get image tag
                label = parse_images(label)
            else:
                # img@link !supported
                label = "(%s)" % image_re.match(label).group(1)

        # Putting data on the right appearance order
        if rules["labelbeforelink"] or not rules["linkable"]:
            urlorder = [label, url]  # label before link
        else:
            urlorder = [url, label]  # link before label

        # Add link data to tag (replace \a's)
        ret = TAGS["%sMark" % linktype]
        for data in urlorder:
            ret = regex["x"].sub(data, ret, 1)

    return ret


def parse_deflist_term(line):
    "Extract and parse definition list term contents"
    img_re = regex["img"]
    term = regex["deflist"].search(line).group(3)

    # Mask image inside term as (image.jpg), where not supported
    if not rules["imgasdefterm"] and img_re.search(term):
        while img_re.search(term):
            imgfile = img_re.search(term).group(1)
            term = img_re.sub("(%s)" % imgfile, term, 1)

    # TODO tex: escape ] on term. \], \rbrack{} and \verb!]! don't work :(
    return term


def get_image_align(line):
    "Return the image (first found) align for the given line"

    # First clear marks that can mess align detection
    line = re.sub(SEPARATOR + "$", "", line)  # remove deflist sep
    line = re.sub("^" + SEPARATOR, "", line)  # remove list sep
    line = re.sub("^[\t]+", "", line)  # remove quote mark

    # Get image position on the line
    m = regex["img"].search(line)
    ini = m.start()
    head = 0
    end = m.end()
    tail = len(line)

    # The align detection algorithm
    if ini == head and end != tail:
        align = "left"  # ^img + text$
    elif ini != head and end == tail:
        align = "right"  # ^text + img$
    else:
        align = "center"  # default align

    # Some special cases
    if BLOCK.isblock("table"):
        align = "center"  # ignore when table

    return align


def get_encoding_string(target):
    return "utf8" if target == "tex" else "utf-8"


def process_source_file(file_="", noconf=0, contents=None):
    """
    Find and Join all the configuration available for a source file.
    No sanity checking is done on this step.
    It also extracts the source document parts into separate holders.

    The config scan order is:
            1. The user configuration file (i.e. $HOME/.txt2tagsrc)
            2. The source document's CONF area
            3. The command line options

    The return data is a tuple of two items:
            1. The parsed config dictionary
            2. The document's parts, as a (head, conf, body) tuple

    All the conversion process will be based on the data and
    configuration returned by this function.
    The source file is read in this step only.
    """
    if contents:
        source = SourceDocument(contents=contents)
    else:
        source = SourceDocument(file_)
    head, conf, body = source.split()
    Message("Source document contents stored", 2)
    if not noconf:
        # Read document config
        source_raw = source.get_raw_config()
        # Join all the config directives found, then parse it
        full_raw = RC_RAW + source_raw + CMDLINE_RAW
        Message("Parsing and saving all config found (%03d items)" % (len(full_raw)), 1)
        full_parsed = ConfigMaster(full_raw).parse()
        # Add manually the filename to the conf dic
        if contents:
            full_parsed["sourcefile"] = MODULEIN
            full_parsed["infile"] = MODULEIN
            full_parsed["outfile"] = MODULEOUT
        else:
            full_parsed["sourcefile"] = file_
        Debug("Complete config: %s" % full_parsed, 1)
    else:
        full_parsed = {}
    return full_parsed, (head, conf, body)


def convert_file(headers, body, config, first_body_lineno=1):
    config = ConfigMaster().sanity(config)
    # Compose the target file Headers
    # TODO escape line before?
    # TODO see exceptions by tex and mgp
    Message("Composing target Headers", 1)
    target_head = doHeader(headers, config)
    # Parse the full marked body into tagged target

    Message("Composing target Body", 1)
    target_body, marked_toc = convert(body, config, firstlinenr=first_body_lineno)

    # Compose the target file Footer
    Message("Composing target Footer", 1)
    target_foot = doFooter(config)

    # Make TOC (if needed)
    Message("Composing target TOC", 1)
    tagged_toc = toc_tagger(marked_toc, config)
    target_toc = toc_formatter(tagged_toc, config)

    # Finally, we have our document
    outlist = target_head + target_toc + target_body + target_foot
    return finish_him(outlist, config)


def parse_images(line):
    "Tag all images found"
    while regex["img"].search(line) and TAGS["img"] != "[\a]":
        txt = regex["img"].search(line).group(1)
        tag = TAGS["img"]

        # If target supports image alignment, here we go
        if rules["imgalignable"]:

            align = get_image_align(line)  # right
            align_name = align.capitalize()  # Right

            # The align is a full tag, or part of the image tag (~A~)
            if TAGS["imgAlign" + align_name]:
                tag = TAGS["imgAlign" + align_name]
            else:
                align_tag = TAGS["_imgAlign" + align_name]
                tag = regex["_imgAlign"].sub(align_tag, tag, 1)

        if TARGET == "tex":
            tag = re.sub(r"\\b", r"\\\\b", tag)
            txt = txt.replace("_", "vvvvTexUndervvvv")

        # Ugly hack to avoid infinite loop when target's image tag contains []
        tag = tag.replace("[", "vvvvEscapeSquareBracketvvvv")

        line = regex["img"].sub(tag, line, 1)
        line = regex["x"].sub(txt, line, 1)
    return line.replace("vvvvEscapeSquareBracketvvvv", "[")


def add_inline_tags(line):
    # Beautifiers
    for beauti, font in [
        ("bold", "fontBold"),
        ("italic", "fontItalic"),
        ("underline", "fontUnderline"),
        ("strike", "fontStrike"),
    ]:
        if regex[font].search(line):
            line = beautify_me(beauti, font, line)

    line = parse_images(line)
    return line


def get_include_contents(file_, path=""):
    "Parses %!include: value and extract file contents"
    ids = {"`": "verb", '"': "raw", "'": "tagged"}
    id_ = "t2t"
    # Set include type and remove identifier marks
    mark = file_[0]
    if mark in ids.keys():
        if file_[:2] == file_[-2:] == mark * 2:
            id_ = ids[mark]  # set type
            file_ = file_[2:-2]  # remove marks
    # Handle remote dir execution
    filepath = os.path.join(path, file_)
    # Read included file contents
    lines = Readfile(filepath)
    # Default txt2tags marked text, just BODY matters
    if id_ == "t2t":
        lines = get_file_body(filepath)
        # TODO fix images relative path if file has a path, ie.:
        # chapter1/index.t2t (wait until tree parsing)
        # TODO for the images path fix, also respect outfile path,
        # if different from infile (wait until tree parsing)
        lines.insert(0, "%INCLUDED({}) starts here: {}".format(id_, file_))
        # This appears when included hit EOF with verbatim area open
        # lines.append('%%INCLUDED(%s) ends here: %s'%(id_,file_))
    return id_, lines


def set_global_config(config):
    global CONF, TAGS, regex, rules, TARGET
    CONF = config
    rules = getRules(CONF)
    TAGS = getTags(CONF)
    regex = getRegexes()
    TARGET = config["target"]  # save for buggy functions that need global


def convert(bodylines, config, firstlinenr=1):
    global BLOCK, TITLE

    set_global_config(config)

    target = config["target"]
    BLOCK = BlockMaster()
    MASK = MaskMaster()
    TITLE = TitleMaster()

    ret = []
    f_lastwasblank = 0

    # Compiling all PreProc regexes
    pre_filter = compile_filters(CONF["preproc"], "Invalid PreProc filter regex")

    # Let's mark it up!
    linenr = firstlinenr - 1
    lineref = 0
    while lineref < len(bodylines):
        # Defaults
        MASK.reset()
        results_box = ""

        untouchedline = bodylines[lineref]

        line = re.sub("[\n\r]+$", "", untouchedline)  # del line break

        # Apply PreProc filters
        if pre_filter:
            errmsg = "Invalid PreProc filter replacement"
            for rgx, repl in pre_filter:
                try:
                    line = rgx.sub(repl, line)
                except Exception:
                    Error("{}: '{}'".format(errmsg, repl))

        line = maskEscapeChar(line)  # protect \ char
        linenr += 1
        lineref += 1

        Debug(repr(line), 2, linenr)  # heavy debug: show each line

        # ------------------[ Comment Block ]------------------------

        # We're already on a comment block
        if BLOCK.block() == "comment":

            # Closing comment
            if regex["blockCommentClose"].search(line):
                ret.extend(BLOCK.blockout() or [])
                continue

            # Normal comment-inside line. Ignore it.
            continue

        # Detecting comment block init
        if (
            regex["blockCommentOpen"].search(line)
            and BLOCK.block() not in BLOCK.exclusive
        ):
            ret.extend(BLOCK.blockin("comment"))
            continue

        # -------------------------[ Tagged Text ]----------------------

        # We're already on a tagged block
        if BLOCK.block() == "tagged":

            # Closing tagged
            if regex["blockTaggedClose"].search(line):
                ret.extend(BLOCK.blockout())
                continue

            # Normal tagged-inside line
            BLOCK.holdadd(line)
            continue

        # Detecting tagged block init
        if (
            regex["blockTaggedOpen"].search(line)
            and BLOCK.block() not in BLOCK.exclusive
        ):
            ret.extend(BLOCK.blockin("tagged"))
            continue

        # One line tagged text
        if regex["1lineTagged"].search(line) and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin("tagged"))
            line = regex["1lineTagged"].sub("", line)
            BLOCK.holdadd(line)
            ret.extend(BLOCK.blockout())
            continue

        # -------------------------[ Raw Text ]----------------------

        # We're already on a raw block
        if BLOCK.block() == "raw":

            # Closing raw
            if regex["blockRawClose"].search(line):
                ret.extend(BLOCK.blockout())
                continue

            # Normal raw-inside line
            BLOCK.holdadd(line)
            continue

        # Detecting raw block init
        if regex["blockRawOpen"].search(line) and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin("raw"))
            continue

        # One line raw text
        if regex["1lineRaw"].search(line) and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin("raw"))
            line = regex["1lineRaw"].sub("", line)
            BLOCK.holdadd(line)
            ret.extend(BLOCK.blockout())
            continue

        # ------------------------[ Verbatim  ]----------------------

        # TIP We'll never support beautifiers inside verbatim

        # Closing table mapped to verb
        if (
            BLOCK.block() == "verb"
            and BLOCK.prop("mapped") == "table"
            and not regex["table"].search(line)
        ):
            ret.extend(BLOCK.blockout())

        # We're already on a verb block
        if BLOCK.block() == "verb":

            # Closing verb
            if regex["blockVerbClose"].search(line):
                ret.extend(BLOCK.blockout())
                continue

            # Normal verb-inside line
            BLOCK.holdadd(line)
            continue

        # Detecting verb block init
        if regex["blockVerbOpen"].search(line) and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin("verb"))
            f_lastwasblank = 0
            continue

        # One line verb-formatted text
        if regex["1lineVerb"].search(line) and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin("verb"))
            line = regex["1lineVerb"].sub("", line)
            BLOCK.holdadd(line)
            ret.extend(BLOCK.blockout())
            f_lastwasblank = 0
            continue

        # Tables are mapped to verb when target is not table-aware
        if not rules["tableable"] and regex["table"].search(line):
            if not BLOCK.isblock("verb"):
                ret.extend(BLOCK.blockin("verb"))
                BLOCK.propset("mapped", "table")
                BLOCK.holdadd(line)
                continue

        # ---------------------[ blank lines ]-----------------------

        if regex["blankline"].search(line):

            # Close open paragraph
            if BLOCK.isblock("para"):
                ret.extend(BLOCK.blockout())
                f_lastwasblank = 1
                continue

            # Close all open tables
            if BLOCK.isblock("table"):
                ret.extend(BLOCK.blockout())
                f_lastwasblank = 1
                continue

            # Close all open quotes
            while BLOCK.isblock("quote"):
                ret.extend(BLOCK.blockout())

            # Closing all open lists
            if f_lastwasblank:  # 2nd consecutive blank
                if BLOCK.block().endswith("list"):
                    BLOCK.holdaddsub("")  # helps parser
                while BLOCK.depth:  # closes list (if any)
                    ret.extend(BLOCK.blockout())
                continue  # ignore consecutive blanks

            # Paragraph (if any) is wanted inside lists also
            if BLOCK.block().endswith("list"):
                BLOCK.holdaddsub("")

            f_lastwasblank = 1
            continue

        # ---------------------[ special ]---------------------------

        if regex["special"].search(line):

            targ, key, val = ConfigLines().parse_line(line, None, target)

            if key:
                Debug("Found config '{}', value '{}'".format(key, val), 1, linenr)
            else:
                Debug("Bogus Special Line", 1, linenr)

            # %!include command
            if key == "include":
                incpath = os.path.dirname(CONF["sourcefile"])
                incfile = val
                err = "A file cannot include itself (loop!)"
                if CONF["sourcefile"] == incfile:
                    Error("{}: {}".format(err, incfile))
                inctype, inclines = get_include_contents(incfile, incpath)

                # Verb, raw and tagged are easy
                if inctype != "t2t":
                    ret.extend(BLOCK.blockin(inctype))
                    BLOCK.holdextend(inclines)
                    ret.extend(BLOCK.blockout())
                else:
                    # Insert include lines into body
                    # TODO include maxdepth limit
                    bodylines = bodylines[:lineref] + inclines + bodylines[lineref:]

                # This line is done, go to next
                continue

        # ---------------------[ Comments ]--------------------------

        # Just skip them
        if regex["comment"].search(line):
            continue

        # ---------------------[ Triggers ]--------------------------

        # Valid line, reset blank status
        f_lastwasblank = 0

        # Any NOT quote line closes all open quotes
        if BLOCK.isblock("quote") and not regex["quote"].search(line):
            while BLOCK.isblock("quote"):
                ret.extend(BLOCK.blockout())

        # Any NOT table line closes an open table
        if BLOCK.isblock("table") and not regex["table"].search(line):
            ret.extend(BLOCK.blockout())

        # ---------------------[ Horizontal Bar ]--------------------

        if regex["bar"].search(line):

            # Bars inside quotes are handled on the Quote processing
            # Otherwise we parse the bars right here
            #
            if not (BLOCK.isblock("quote") or regex["quote"].search(line)) or (
                BLOCK.isblock("quote") and not rules["barinsidequote"]
            ):

                # Close all the opened blocks
                ret.extend(BLOCK.blockin("bar"))

                # Extract the bar chars (- or =)
                m = regex["bar"].search(line)
                bar_chars = m.group(2)

                # Process and dump the tagged bar
                BLOCK.holdadd(bar_chars)
                ret.extend(BLOCK.blockout())
                Debug("BAR: %s" % line, 6)

                # We're done, nothing more to process
                continue

        # ---------------------[ Title ]-----------------------------

        if (
            regex["title"].search(line) or regex["numtitle"].search(line)
        ) and not BLOCK.block().endswith("list"):

            if regex["title"].search(line):
                name = "title"
            else:
                name = "numtitle"

            # Close all the opened blocks
            ret.extend(BLOCK.blockin(name))

            # Process title
            TITLE.add(line)
            ret.extend(BLOCK.blockout())

            # We're done, nothing more to process
            continue

        # ---------------------[ apply masks ]-----------------------

        line = MASK.mask(line)

        # XXX from here, only block-inside lines will pass

        # ---------------------[ Quote ]-----------------------------

        if regex["quote"].search(line):

            # Store number of leading TABS
            quotedepth = len(regex["quote"].search(line).group(0))

            # SGML doesn't support nested quotes
            if rules["quotenotnested"]:
                quotedepth = 1

            # Don't cross depth limit
            maxdepth = rules["quotemaxdepth"]
            if maxdepth and quotedepth > maxdepth:
                quotedepth = maxdepth

            # New quote
            if not BLOCK.isblock("quote"):
                ret.extend(BLOCK.blockin("quote"))

            # New subquotes
            while BLOCK.depth < quotedepth:
                BLOCK.blockin("quote")

            # Closing quotes
            while quotedepth < BLOCK.depth:
                ret.extend(BLOCK.blockout())

            # Bar inside quote
            if regex["bar"].search(line) and rules["barinsidequote"]:
                tempBlock = BlockMaster()
                tagged_bar = []
                tagged_bar.extend(tempBlock.blockin("bar"))
                tempBlock.holdadd(line)
                tagged_bar.extend(tempBlock.blockout())
                BLOCK.holdextend(tagged_bar)
                continue

        # ---------------------[ Lists ]-----------------------------

        # An empty item also closes the current list
        if BLOCK.block().endswith("list"):
            m = regex["listclose"].match(line)
            if m:
                listindent = m.group(1)
                listtype = m.group(2)
                currlisttype = BLOCK.prop("type")
                currlistindent = BLOCK.prop("indent")
                if listindent == currlistindent and listtype == currlisttype:
                    ret.extend(BLOCK.blockout())
                    continue

        if (
            regex["list"].search(line)
            or regex["numlist"].search(line)
            or regex["deflist"].search(line)
        ):

            listindent = BLOCK.prop("indent")
            listids = "".join(LISTNAMES.keys())
            m = re.match("^( *)([%s]) " % re.escape(listids), line)
            listitemindent = m.group(1)
            listtype = m.group(2)
            listname = LISTNAMES[listtype]
            results_box = BLOCK.holdadd

            # Del list ID (and separate term from definition)
            if listname == "deflist":
                term = parse_deflist_term(line)
                line = regex["deflist"].sub(SEPARATOR + term + SEPARATOR, line)
            else:
                line = regex[listname].sub(SEPARATOR, line)

            # Don't cross depth limit
            maxdepth = rules["listmaxdepth"]
            if maxdepth and BLOCK.depth == maxdepth:
                if len(listitemindent) > len(listindent):
                    listitemindent = listindent

            # List bumping (same indent, diff mark)
            # Close the currently open list to clear the mess
            if (
                BLOCK.block().endswith("list")
                and listname != BLOCK.block()
                and len(listitemindent) == len(listindent)
            ):
                ret.extend(BLOCK.blockout())
                listindent = BLOCK.prop("indent")

            # Open mother list or sublist
            if not BLOCK.block().endswith("list") or len(listitemindent) > len(
                listindent
            ):
                ret.extend(BLOCK.blockin(listname))
                BLOCK.propset("indent", listitemindent)
                BLOCK.propset("type", listtype)

            # Closing sublists
            while len(listitemindent) < len(BLOCK.prop("indent")):
                ret.extend(BLOCK.blockout())

            # O-oh, sublist before list ("\n\n  - foo\n- foo")
            # Fix: close sublist (as mother), open another list
            if not BLOCK.block().endswith("list"):
                ret.extend(BLOCK.blockin(listname))
                BLOCK.propset("indent", listitemindent)
                BLOCK.propset("type", listtype)

        # ---------------------[ Table ]-----------------------------

        # TODO escape undesired format inside table
        if regex["table"].search(line):

            if not BLOCK.isblock("table"):  # first table line!
                ret.extend(BLOCK.blockin("table"))
                BLOCK.tableparser.__init__(line)

            tablerow = TableMaster().parse_row(line)
            BLOCK.tableparser.add_row(tablerow)  # save config

            # Maintain line to unmask and inlines
            # XXX Bug: | **bo | ld** | turns **bo\x01ld** and gets converted :(
            # TODO isolate unmask+inlines parsing to use here
            line = SEPARATOR.join(tablerow["cells"])

        # ---------------------[ Paragraph ]-------------------------

        if not BLOCK.block():  # new para!
            ret.extend(BLOCK.blockin("para"))

        ############################################################
        ############################################################
        ############################################################

        # ---------------------[ Final Parses ]----------------------

        # The target-specific special char escapes for body lines
        line = doEscape(target, line)

        line = add_inline_tags(line)
        line = MASK.undo(line)

        # ---------------------[ Hold or Return? ]-------------------

        # Now we must choose where to put the parsed line
        #
        if not results_box:
            # List item extra lines
            if BLOCK.block().endswith("list"):
                results_box = BLOCK.holdaddsub
            # Other blocks
            elif BLOCK.block():
                results_box = BLOCK.holdadd
            # No blocks
            else:
                line = doFinalEscape(target, line)
                results_box = ret.append

        results_box(line)

    # EOF: close any open para/verb/lists/table/quotes
    Debug("EOF", 7)
    while BLOCK.block():
        ret.extend(BLOCK.blockout())

    # Maybe close some opened title area?
    if rules["titleblocks"]:
        ret.extend(TITLE.close_all())

    # Maybe a major tag to enclose body? (like DIV for CSS)
    if TAGS["bodyOpen"]:
        ret.insert(0, TAGS["bodyOpen"])
    if TAGS["bodyClose"]:
        ret.append(TAGS["bodyClose"])

    marked_toc = TITLE.dump_marked_toc()

    return ret, marked_toc


def exec_command_line(user_cmdline=None):
    global CMDLINE_RAW, RC_RAW, DEBUG, VERBOSE, QUIET, Error

    # Extract command line data
    cmdline_data = user_cmdline or sys.argv[1:]
    CMDLINE_RAW = CommandLine().get_raw_config(cmdline_data, relative=True)
    cmdline_parsed = ConfigMaster(CMDLINE_RAW).parse()
    DEBUG = cmdline_parsed.get("debug") or 0
    VERBOSE = cmdline_parsed.get("verbose") or 0
    QUIET = cmdline_parsed.get("quiet") or 0
    infiles = cmdline_parsed.get("infile") or []

    Message("Processing begins", 1)

    # The easy ones
    if cmdline_parsed.get("help"):
        Quit(USAGE)
    if cmdline_parsed.get("version"):
        Quit(VERSIONSTR)
    if cmdline_parsed.get("targets"):
        listTargets()
        Quit()

    Debug("system platform: %s" % sys.platform)
    Debug("python version: %s" % (sys.version.split("(")[0]))
    Debug("command line: %s" % sys.argv)
    Debug("command line raw config: %s" % CMDLINE_RAW, 1)

    # Extract RC file config
    if cmdline_parsed.get("rc") == 0:
        Message("Ignoring user configuration file", 1)
    else:
        rc_file = get_rc_path()
        if os.path.isfile(rc_file):
            Message("Loading user configuration file", 1)
            RC_RAW = ConfigLines(file_=rc_file).get_raw_config()

        Debug("rc file: %s" % rc_file)
        Debug("rc file raw config: %s" % RC_RAW, 1)

    # TODO#1: this checking should be only in ConfigMaster.sanity()
    if len(infiles) == 1:
        infile = infiles[0]
    else:
        Error(
            "Pass exactly one input file (see --help). "
            "Example: {} -t html file.t2t".format(my_name)
        )

    config, doc = process_source_file(infile)
    headers, config_source, body = doc

    first_body_lineno = (len(headers) or 1) + len(config_source) + 1
    convert_file(headers, body, config, first_body_lineno=first_body_lineno)

    Message("Txt2tags finished successfully", 1)


if __name__ == "__main__":
    try:
        exec_command_line()
    except error as msg:
        sys.exit(msg)
    except Exception:
        sys.exit(getUnknownErrorMessage())
    else:
        Quit()
