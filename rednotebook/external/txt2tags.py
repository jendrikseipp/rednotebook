# txt2tags - generic text conversion tool
# http://txt2tags.sf.net
#
# Copyright 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008 Aurelio Jargas
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, version 2.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You have received a copy of the GNU General Public License along
#   with this program, on the COPYING file.
#
########################################################################
#
#   BORING CODE EXPLANATION AHEAD
#
# Just read it if you wish to understand how the txt2tags code works.
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
# get_infiles_config(), process_source_file() and convert_this_files()
#
########################################################################

#XXX Python coding warning
# Avoid common mistakes:
# - do NOT use newlist=list instead newlist=list[:]
# - do NOT use newdic=dic   instead newdic=dic.copy()
# - do NOT use dic[key]     instead dic.get(key)
# - do NOT use del dic[key] without has_key() before

#XXX Smart Image Align don't work if the image is a link
# Can't fix that because the image is expanded together with the
# link, at the linkbank filling moment. Only the image is passed
# to parse_images(), not the full line, so it is always 'middle'.

#XXX Paragraph separation not valid inside Quote
# Quote will not have <p></p> inside, instead will close and open
# again the <blockquote>. This really sux in CSS, when defining a
# different background color. Still don't know how to fix it.

#XXX TODO (maybe)
# New mark or macro which expands to an anchor full title.
# It is necessary to parse the full document in this order:
#  DONE  1st scan: HEAD: get all settings, including %!includeconf
#  DONE  2nd scan: BODY: expand includes & apply %!preproc
#        3rd scan: BODY: read titles and compose TOC info
#        4th scan: BODY: full parsing, expanding [#anchor] 1st
# Steps 2 and 3 can be made together, with no tag adding.
# Two complete body scans will be *slow*, don't know if it worths.
# One solution may be add the titles as postproc rules


##############################################################################

# User config (1=ON, 0=OFF)

USE_I18N    = 1   # use gettext for i18ned messages?        (default is 1)
COLOR_DEBUG = 1   # show debug messages in colors?          (default is 1)
BG_LIGHT    = 0   # your terminal background color is light (default is 0)
HTML_LOWER  = 0   # use lowercased HTML tags instead upper? (default is 0)

##############################################################################


# These are all the core Python modules used by txt2tags (KISS!)
import re, os, sys, time, getopt

# Program information
my_url = 'http://txt2tags.sf.net'
my_name = 'txt2tags'
my_email = 'verde@aurelio.net'
my_version = '2.6b'

# i18n - just use if available
if USE_I18N:
    try:
        import gettext
        # If your locale dir is different, change it here
        cat = gettext.Catalog('txt2tags',localedir='/usr/share/locale/')
        _ = cat.gettext
    except:
        _ = lambda x:x
else:
    _ = lambda x:x

# FLAGS   : the conversion related flags  , may be used in %!options
# OPTIONS : the conversion related options, may be used in %!options
# ACTIONS : the other behavior modifiers, valid on command line only
# MACROS  : the valid macros with their default values for formatting
# SETTINGS: global miscellaneous settings, valid on RC file only
# NO_TARGET: actions that don't require a target specification
# NO_MULTI_INPUT: actions that don't accept more than one input file
# CONFIG_KEYWORDS: the valid %!key:val keywords
#
# FLAGS and OPTIONS are configs that affect the converted document.
# They usually have also a --no-<option> to turn them OFF.
#
# ACTIONS are needed because when doing multiple input files, strange
# behavior would be found, as use command line interface for the
# first file and gui for the second. There is no --no-<action>.
# --version and --help inside %!options are also odd
#
TARGETS  = 'html xhtml sgml dbk tex lout man mgp wiki gwiki doku pmw moin pm6 txt art adoc'.split()

FLAGS    = {'headers'    :1 , 'enum-title' :0 , 'mask-email' :0 ,
            'toc-only'   :0 , 'toc'        :0 , 'rc'         :1 ,
            'css-sugar'  :0 , 'css-suggar' :0 , 'css-inside' :0 ,
            'quiet'      :0 }
OPTIONS  = {'target'     :'', 'toc-level'  :3 , 'style'      :'',
            'infile'     :'', 'outfile'    :'', 'encoding'   :'',
            'config-file':'', 'split'      :0 , 'lang'       :'',
            'show-config-value':'', 'ascii-art' :''}
ACTIONS  = {'help'       :0 , 'version'    :0 , 'gui'        :0 ,
            'verbose'    :0 , 'debug'      :0 , 'dump-config':0 ,
            'dump-source':0 }
MACROS   = {'date' : '%Y%m%d',  'infile': '%f',
            'mtime': '%Y%m%d', 'outfile': '%f'}
SETTINGS = {}         # for future use
NO_TARGET = ['help', 'version', 'gui', 'toc-only', 'dump-config', 'dump-source']
NO_MULTI_INPUT = ['gui','dump-config','dump-source']
CONFIG_KEYWORDS = [
            'target', 'encoding', 'style', 'options', 'preproc','postproc',
            'guicolors']

TARGET_NAMES = {
  'html' : _('HTML page'),
  'xhtml': _('XHTML page'),
  'sgml' : _('SGML document'),
  'dbk'  : _('DocBook document'),
  'tex'  : _('LaTeX document'),
  'lout' : _('Lout document'),
  'man'  : _('UNIX Manual page'),
  'mgp'  : _('MagicPoint presentation'),
  'wiki' : _('Wikipedia page'),
  'gwiki': _('Google Wiki page'),
  'doku' : _('DokuWiki page'),
  'pmw'  : _('pmWiki page'),
  'moin' : _('MoinMoin page'),
  'pm6'  : _('PageMaker document'),
  'txt'  : _('Plain Text'),
  'art'  : _('Ascii Art'),
  'adoc' : _('AsciiDoc'),
}

DEBUG = 0     # do not edit here, please use --debug
VERBOSE = 0   # do not edit here, please use -v, -vv or -vvv
QUIET = 0     # do not edit here, please use --quiet
GUI = 0       # do not edit here, please use --gui
AUTOTOC = 1   # do not edit here, please use --no-toc or %%toc

AA_LCHARS = ['coin','line','border','bar1','bar2','level2','level3','level4','level5']
AA_CHARS = dict(zip(AA_LCHARS,'+-|-==-^"')) # do not edit here, please use --ascii-art or -a

RC_RAW = []
CMDLINE_RAW = []
CONF = {}
BLOCK = None
regex = {}
TAGS = {}
rules = {}

lang = 'english'
TARGET = ''

STDIN = STDOUT = '-'
MODULEIN = MODULEOUT = '-module-'
ESCCHAR   = '\x00'
SEPARATOR = '\x01'
LISTNAMES = {'-':'list', '+':'numlist', ':':'deflist'}
LINEBREAK = {'default':'\n', 'win':'\r\n', 'mac':'\r'}

# Platform specific settings
LB = LINEBREAK.get(sys.platform[:3]) or LINEBREAK['default']

VERSIONSTR = _("%s version %s <%s>")%(my_name,my_version,my_url)

USAGE =  '\n'.join([
'',
_("Usage: %s [OPTIONS] [infile.t2t ...]") % my_name,
'',
_("  -t, --target=TYPE   set target document type. currently supported:"),
'                      %s,' % ', '.join(TARGETS[:8]),
'                      %s'  % ', '.join(TARGETS[8:]),
_("  -i, --infile=FILE   set FILE as the input file name ('-' for STDIN)"),
_("  -o, --outfile=FILE  set FILE as the output file name ('-' for STDOUT)"),
_("  -H, --no-headers    suppress header, title and footer contents"),
_("      --headers       show header, title and footer contents (default ON)"),
_("      --encoding=ENC  set target file encoding (utf-8, iso-8859-1, etc)"),
_("      --style=FILE    use FILE as the document style (like HTML CSS)"),
_("      --css-sugar     insert CSS-friendly tags for HTML and XHTML targets"),
_("      --css-inside    insert CSS file contents inside HTML/XHTML headers"),
_("      --mask-email    hide email from spam robots. x@y.z turns <x (a) y z>"),
_("      --toc           add TOC (Table of Contents) to target document"),
_("      --toc-only      print document TOC and exit"),
_("      --toc-level=N   set maximum TOC level (depth) to N"),
_("  -n, --enum-title    enumerate all titles as 1, 1.1, 1.1.1, etc"),
_("  -a, --ascii-art=S   set the ascii art chars with the string S. in the order:"),
'                      %s' % ', '.join(AA_LCHARS),
_("  -C, --config-file=F read config from file F"),
_("      --rc            read user config file ~/.txt2tagsrc (default ON)"),
_("      --gui           invoke Graphical Tk Interface"),
_("  -q, --quiet         quiet mode, suppress all output (except errors)"),
_("  -v, --verbose       print informative messages during conversion"),
_("  -h, --help          print this help information and exit"),
_("  -V, --version       print program version and exit"),
_("      --dump-config   print all the config found and exit"),
_("      --dump-source   print the document source, with includes expanded"),
'',
_("Turn OFF options:"),
"     --no-outfile, --no-infile, --no-style, --no-encoding, --no-headers",
"     --no-toc, --no-toc-only, --no-mask-email, --no-enum-title, --no-rc",
"     --no-css-sugar, --no-css-inside, --no-quiet, --no-dump-config",
"     --no-dump-source",
'',
_("Example:\n     %s -t html --toc myfile.t2t") % my_name,
'',
_("By default, converted output is saved to 'infile.<target>'."),
_("Use --outfile to force an output file name."),
_("If  input file is '-', reads from STDIN."),
_("If output file is '-', dumps output to STDOUT."),
'',
'http://txt2tags.sourceforge.net',
''
])


##############################################################################


# Here is all the target's templates
# You may edit them to fit your needs
#  - the %(HEADERn)s strings represent the Header lines
#  - the %(STYLE)s string is changed by --style contents
#  - the %(ENCODING)s string is changed by --encoding contents
#  - if any of the above is empty, the full line is removed
#  - use %% to represent a literal %
#
HEADER_TEMPLATE = {
    'art':"""
Fake template to respect the general process.
""",
    'txt': """\
%(HEADER1)s
%(HEADER2)s
%(HEADER3)s
""",

    'sgml': """\
<!doctype linuxdoc system>
<article>
<title>%(HEADER1)s
<author>%(HEADER2)s
<date>%(HEADER3)s
""",

    'html': """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<HEAD>
<META NAME="generator" CONTENT="http://txt2tags.sf.net">
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=%(ENCODING)s">
<LINK REL="stylesheet" TYPE="text/css" HREF="%(STYLE)s">
<TITLE>%(HEADER1)s</TITLE>
</HEAD><BODY BGCOLOR="white" TEXT="black">
<CENTER>
<H1>%(HEADER1)s</H1>
<FONT SIZE="4"><I>%(HEADER2)s</I></FONT><BR>
<FONT SIZE="4">%(HEADER3)s</FONT>
</CENTER>
""",

    'htmlcss': """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<HEAD>
<META NAME="generator" CONTENT="http://txt2tags.sf.net">
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=%(ENCODING)s">
<LINK REL="stylesheet" TYPE="text/css" HREF="%(STYLE)s">
<TITLE>%(HEADER1)s</TITLE>
</HEAD>
<BODY>

<DIV CLASS="header" ID="header">
<H1>%(HEADER1)s</H1>
<H2>%(HEADER2)s</H2>
<H3>%(HEADER3)s</H3>
</DIV>
""",

    'xhtml': """\
<?xml version="1.0"
      encoding="%(ENCODING)s"
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>%(HEADER1)s</title>
<meta name="generator" content="http://txt2tags.sf.net" />
<link rel="stylesheet" type="text/css" href="%(STYLE)s" />
</head>
<body bgcolor="white" text="black">
<div align="center">
<h1>%(HEADER1)s</h1>
<h2>%(HEADER2)s</h2>
<h3>%(HEADER3)s</h3>
</div>
""",

    'xhtmlcss': """\
<?xml version="1.0"
      encoding="%(ENCODING)s"
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>%(HEADER1)s</title>
<meta name="generator" content="http://txt2tags.sf.net" />
<link rel="stylesheet" type="text/css" href="%(STYLE)s" />
</head>
<body>

<div class="header" id="header">
<h1>%(HEADER1)s</h1>
<h2>%(HEADER2)s</h2>
<h3>%(HEADER3)s</h3>
</div>
""",

    'dbk': """\
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

    'man': """\
.TH "%(HEADER1)s" 1 "%(HEADER3)s" "%(HEADER2)s"
""",

# TODO style to <HR>
    'pm6': """\
<PMTags1.0 win><C-COLORTABLE ("Preto" 1 0 0 0)
><@Normal=
  <FONT "Times New Roman"><CCOLOR "Preto"><SIZE 11>
  <HORIZONTAL 100><LETTERSPACE 0><CTRACK 127><CSSIZE 70><C+SIZE 58.3>
  <C-POSITION 33.3><C+POSITION 33.3><P><CBASELINE 0><CNOBREAK 0><CLEADING -0.05>
  <GGRID 0><GLEFT 7.2><GRIGHT 0><GFIRST 0><G+BEFORE 7.2><G+AFTER 0>
  <GALIGNMENT "justify"><GMETHOD "proportional"><G& "ENGLISH">
  <GPAIRS 12><G%% 120><GKNEXT 0><GKWIDOW 0><GKORPHAN 0><GTABS $>
  <GHYPHENATION 2 34 0><GWORDSPACE 75 100 150><GSPACE -5 0 25>
><@Bullet=<@-PARENT "Normal"><FONT "Abadi MT Condensed Light">
  <GLEFT 14.4><G+BEFORE 2.15><G%% 110><GTABS(25.2 l "")>
><@PreFormat=<@-PARENT "Normal"><FONT "Lucida Console"><SIZE 8><CTRACK 0>
  <GLEFT 0><G+BEFORE 0><GALIGNMENT "left"><GWORDSPACE 100 100 100><GSPACE 0 0 0>
><@Title1=<@-PARENT "Normal"><FONT "Arial"><SIZE 14><B>
  <GCONTENTS><GLEFT 0><G+BEFORE 0><GALIGNMENT "left">
><@Title2=<@-PARENT "Title1"><SIZE 12><G+BEFORE 3.6>
><@Title3=<@-PARENT "Title1"><SIZE 10><GLEFT 7.2><G+BEFORE 7.2>
><@Title4=<@-PARENT "Title3">
><@Title5=<@-PARENT "Title3">
><@Quote=<@-PARENT "Normal"><SIZE 10><I>>

%(HEADER1)s
%(HEADER2)s
%(HEADER3)s
""",

    'mgp': """\
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

    'moin': """\
'''%(HEADER1)s'''

''%(HEADER2)s''

%(HEADER3)s
""",

    'gwiki': """\
*%(HEADER1)s*

%(HEADER2)s

_%(HEADER3)s_
""",

    'adoc': """\
%(HEADER1)s
%(HEADER2)s
%(HEADER3)s
""",

    'doku': """\
===== %(HEADER1)s =====

**//%(HEADER2)s//**

//%(HEADER3)s//
""",

    'pmw': """\
(:Title %(HEADER1)s:)

(:Description %(HEADER2)s:)

(:Summary %(HEADER3)s:)
""",

    'wiki': """\
'''%(HEADER1)s'''

%(HEADER2)s

''%(HEADER3)s''
""",

    'tex': \
r"""\documentclass{article}
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

    'lout': """\
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
"""
# @SysInclude { tbl }                   # Tables support
# setup: @MakeContents { Yes }          # show TOC
# setup: @SectionGap                    # break page at each section
}


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
    blocktitle1Open     blocktitle1Close
    blocktitle2Open     blocktitle2Close
    blocktitle3Open     blocktitle3Close

    paragraphOpen       paragraphClose
    blockVerbOpen       blockVerbClose
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

    # TIP: \a represents the current text on the mark
    # TIP: ~A~, ~B~ and ~C~ are expanded to other tags parts

    alltags = {

    'art': {
        'title1'               : '\a'                     ,
        'title2'               : '\a'                     ,
        'title3'               : '\a'                     ,
        'title4'               : '\a'                     ,
        'title5'               : '\a'                     ,
        'blockQuoteLine'       : '\t'                     ,
        'listItemOpen'         : '- '                     ,
        'numlistItemOpen'      : '\a. '                   ,
        'bar1'                 : aa_line(AA_CHARS['bar1']),
        'bar2'                 : aa_line(AA_CHARS['bar2']),
        'url'                  : '\a'                     ,
        'urlMark'              : '\a (\a)'                ,
        'email'                : '\a'                     ,
        'emailMark'            : '\a (\a)'                ,
        'img'                  : '[\a]'                   ,
    },

    'txt': {
        'title1'               : '  \a'      ,
        'title2'               : '\t\a'      ,
        'title3'               : '\t\t\a'    ,
        'title4'               : '\t\t\t\a'  ,
        'title5'               : '\t\t\t\t\a',
        'blockQuoteLine'       : '\t'        ,
        'listItemOpen'         : '- '        ,
        'numlistItemOpen'      : '\a. '      ,
        'bar1'                 : '\a'        ,
        'url'                  : '\a'        ,
        'urlMark'              : '\a (\a)'   ,
        'email'                : '\a'        ,
        'emailMark'            : '\a (\a)'   ,
        'img'                  : '[\a]'      ,
    },

    'html': {
        'paragraphOpen'        : '<P>'            ,
        'paragraphClose'       : '</P>'           ,
        'title1'               : '~A~<H1>\a</H1>' ,
        'title2'               : '~A~<H2>\a</H2>' ,
        'title3'               : '~A~<H3>\a</H3>' ,
        'title4'               : '~A~<H4>\a</H4>' ,
        'title5'               : '~A~<H5>\a</H5>' ,
        'anchor'               : '<A NAME="\a"></A>\n',
        'blockVerbOpen'        : '<PRE>'          ,
        'blockVerbClose'       : '</PRE>'         ,
        'blockQuoteOpen'       : '<BLOCKQUOTE>'   ,
        'blockQuoteClose'      : '</BLOCKQUOTE>'  ,
        'fontMonoOpen'         : '<CODE>'         ,
        'fontMonoClose'        : '</CODE>'        ,
        'fontBoldOpen'         : '<B>'            ,
        'fontBoldClose'        : '</B>'           ,
        'fontItalicOpen'       : '<I>'            ,
        'fontItalicClose'      : '</I>'           ,
        'fontUnderlineOpen'    : '<U>'            ,
        'fontUnderlineClose'   : '</U>'           ,
        'fontStrikeOpen'       : '<S>'            ,
        'fontStrikeClose'      : '</S>'           ,
        'listOpen'             : '<UL>'           ,
        'listClose'            : '</UL>'          ,
        'listItemOpen'         : '<LI>'           ,
        'numlistOpen'          : '<OL>'           ,
        'numlistClose'         : '</OL>'          ,
        'numlistItemOpen'      : '<LI>'           ,
        'deflistOpen'          : '<DL>'           ,
        'deflistClose'         : '</DL>'          ,
        'deflistItem1Open'     : '<DT>'           ,
        'deflistItem1Close'    : '</DT>'          ,
        'deflistItem2Open'     : '<DD>'           ,
        'bar1'                 : '<HR NOSHADE SIZE=1>'        ,
        'bar2'                 : '<HR NOSHADE SIZE=5>'        ,
        'url'                  : '<A HREF="\a">\a</A>'        ,
        'urlMark'              : '<A HREF="\a">\a</A>'        ,
        'email'                : '<A HREF="mailto:\a">\a</A>' ,
        'emailMark'            : '<A HREF="mailto:\a">\a</A>' ,
        'img'                  : '<IMG~A~ SRC="\a" BORDER="0" ALT="">',
        '_imgAlignLeft'        : ' ALIGN="left"'  ,
        '_imgAlignCenter'      : ' ALIGN="middle"',
        '_imgAlignRight'       : ' ALIGN="right"' ,
        'tableOpen'            : '<TABLE~A~~B~ CELLPADDING="4">',
        'tableClose'           : '</TABLE>'       ,
        'tableRowOpen'         : '<TR>'           ,
        'tableRowClose'        : '</TR>'          ,
        'tableCellOpen'        : '<TD~A~~S~>'     ,
        'tableCellClose'       : '</TD>'          ,
        'tableTitleCellOpen'   : '<TH~S~>'        ,
        'tableTitleCellClose'  : '</TH>'          ,
        '_tableBorder'         : ' BORDER="1"'    ,
        '_tableAlignCenter'    : ' ALIGN="center"',
        '_tableCellAlignRight' : ' ALIGN="right"' ,
        '_tableCellAlignCenter': ' ALIGN="center"',
        '_tableCellColSpan'    : ' COLSPAN="\a"'  ,
        'cssOpen'              : '<STYLE TYPE="text/css">',
        'cssClose'             : '</STYLE>'       ,
        'comment'              : '<!-- \a -->'    ,
        'EOD'                  : '</BODY></HTML>'
    },

    #TIP xhtml inherits all HTML definitions (lowercased)
    #TIP http://www.w3.org/TR/xhtml1/#guidelines
    #TIP http://www.htmlref.com/samples/Chapt17/17_08.htm
    'xhtml': {
        'listItemClose'        : '</li>'          ,
        'numlistItemClose'     : '</li>'          ,
        'deflistItem2Close'    : '</dd>'          ,
        'bar1'                 : '<hr class="light" />',
        'bar2'                 : '<hr class="heavy" />',
        'anchor'               : '<a id="\a" name="\a"></a>\n',
        'img'                  : '<img~A~ src="\a" border="0" alt=""/>',
    },

    'sgml': {
        'paragraphOpen'        : '<p>'                ,
        'title1'               : '<sect>\a~A~<p>'     ,
        'title2'               : '<sect1>\a~A~<p>'    ,
        'title3'               : '<sect2>\a~A~<p>'    ,
        'title4'               : '<sect3>\a~A~<p>'    ,
        'title5'               : '<sect4>\a~A~<p>'    ,
        'anchor'               : '<label id="\a">'    ,
        'blockVerbOpen'        : '<tscreen><verb>'    ,
        'blockVerbClose'       : '</verb></tscreen>'  ,
        'blockQuoteOpen'       : '<quote>'            ,
        'blockQuoteClose'      : '</quote>'           ,
        'fontMonoOpen'         : '<tt>'               ,
        'fontMonoClose'        : '</tt>'              ,
        'fontBoldOpen'         : '<bf>'               ,
        'fontBoldClose'        : '</bf>'              ,
        'fontItalicOpen'       : '<em>'               ,
        'fontItalicClose'      : '</em>'              ,
        'fontUnderlineOpen'    : '<bf><em>'           ,
        'fontUnderlineClose'   : '</em></bf>'         ,
        'listOpen'             : '<itemize>'          ,
        'listClose'            : '</itemize>'         ,
        'listItemOpen'         : '<item>'             ,
        'numlistOpen'          : '<enum>'             ,
        'numlistClose'         : '</enum>'            ,
        'numlistItemOpen'      : '<item>'             ,
        'deflistOpen'          : '<descrip>'          ,
        'deflistClose'         : '</descrip>'         ,
        'deflistItem1Open'     : '<tag>'              ,
        'deflistItem1Close'    : '</tag>'             ,
        'bar1'                 : '<!-- \a -->'        ,
        'url'                  : '<htmlurl url="\a" name="\a">'        ,
        'urlMark'              : '<htmlurl url="\a" name="\a">'        ,
        'email'                : '<htmlurl url="mailto:\a" name="\a">' ,
        'emailMark'            : '<htmlurl url="mailto:\a" name="\a">' ,
        'img'                  : '<figure><ph vspace=""><img src="\a"></figure>',
        'tableOpen'            : '<table><tabular ca="~C~">'           ,
        'tableClose'           : '</tabular></table>' ,
        'tableRowSep'          : '<rowsep>'           ,
        'tableCellSep'         : '<colsep>'           ,
        '_tableColAlignLeft'   : 'l'                  ,
        '_tableColAlignRight'  : 'r'                  ,
        '_tableColAlignCenter' : 'c'                  ,
        'comment'              : '<!-- \a -->'        ,
        'TOC'                  : '<toc>'              ,
        'EOD'                  : '</article>'
    },

    'dbk': {
        'paragraphOpen'        : '<para>'                            ,
        'paragraphClose'       : '</para>'                           ,
        'title1Open'           : '~A~<sect1><title>\a</title>'       ,
        'title1Close'          : '</sect1>'                          ,
        'title2Open'           : '~A~  <sect2><title>\a</title>'     ,
        'title2Close'          : '  </sect2>'                        ,
        'title3Open'           : '~A~    <sect3><title>\a</title>'   ,
        'title3Close'          : '    </sect3>'                      ,
        'title4Open'           : '~A~      <sect4><title>\a</title>' ,
        'title4Close'          : '      </sect4>'                    ,
        'title5Open'           : '~A~        <sect5><title>\a</title>',
        'title5Close'          : '        </sect5>'                  ,
        'anchor'               : '<anchor id="\a"/>\n'               ,
        'blockVerbOpen'        : '<programlisting>'                  ,
        'blockVerbClose'       : '</programlisting>'                 ,
        'blockQuoteOpen'       : '<blockquote><para>'                ,
        'blockQuoteClose'      : '</para></blockquote>'              ,
        'fontMonoOpen'         : '<code>'                            ,
        'fontMonoClose'        : '</code>'                           ,
        'fontBoldOpen'         : '<emphasis role="bold">'            ,
        'fontBoldClose'        : '</emphasis>'                       ,
        'fontItalicOpen'       : '<emphasis>'                        ,
        'fontItalicClose'      : '</emphasis>'                       ,
        'fontUnderlineOpen'    : '<emphasis role="underline">'       ,
        'fontUnderlineClose'   : '</emphasis>'                       ,
        # 'fontStrikeOpen'       : '<emphasis role="strikethrough">'   , # Don't know
        # 'fontStrikeClose'      : '</emphasis>'                       ,
        'listOpen'             : '<itemizedlist>'                    ,
        'listClose'            : '</itemizedlist>'                   ,
        'listItemOpen'         : '<listitem><para>'                  ,
        'listItemClose'        : '</para></listitem>'                ,
        'numlistOpen'          : '<orderedlist numeration="arabic">' ,
        'numlistClose'         : '</orderedlist>'                    ,
        'numlistItemOpen'      : '<listitem><para>'                  ,
        'numlistItemClose'     : '</para></listitem>'                ,
        'deflistOpen'          : '<variablelist>'                    ,
        'deflistClose'         : '</variablelist>'                   ,
        'deflistItem1Open'     : '<varlistentry><term>'              ,
        'deflistItem1Close'    : '</term>'                           ,
        'deflistItem2Open'     : '<listitem><para>'                  ,
        'deflistItem2Close'    : '</para></listitem></varlistentry>' ,
        # 'bar1'                 : '<>'                                , # Don't know
        # 'bar2'                 : '<>'                                , # Don't know
        'url'                  : '<ulink url="\a">\a</ulink>'        ,
        'urlMark'              : '<ulink url="\a">\a</ulink>'        ,
        'email'                : '<email>\a</email>'                 ,
        'emailMark'            : '<email>\a</email>'                 ,
        'img'                  : '<mediaobject><imageobject><imagedata fileref="\a"/></imageobject></mediaobject>',
        # '_imgAlignLeft'        : ''                                 , # Don't know
        # '_imgAlignCenter'      : ''                                 , # Don't know
        # '_imgAlignRight'       : ''                                 , # Don't know
        'tableOpen'            : '<para>', # just to have something...
        'tableClose'           : '</para>',
        # 'tableOpen'            : '<informaltable><tgroup cols=""><tbody>', # Don't work, need to know number of cols
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
        'TOC'                  : '</index>'                          ,
        'comment'              : '<!-- \a -->'                       ,
        'EOD'                  : '</article>'
    },

    'tex': {
        'title1'               : '~A~\section*{\a}'     ,
        'title2'               : '~A~\\subsection*{\a}'   ,
        'title3'               : '~A~\\subsubsection*{\a}',
        # title 4/5: DIRTY: para+BF+\\+\n
        'title4'               : '~A~\\paragraph{}\\textbf{\a}\\\\\n',
        'title5'               : '~A~\\paragraph{}\\textbf{\a}\\\\\n',
        'numtitle1'            : '\n~A~\section{\a}'      ,
        'numtitle2'            : '~A~\\subsection{\a}'    ,
        'numtitle3'            : '~A~\\subsubsection{\a}' ,
        'anchor'               : '\\hypertarget{\a}{}\n'  ,
        'blockVerbOpen'        : '\\begin{verbatim}'   ,
        'blockVerbClose'       : '\\end{verbatim}'     ,
        'blockQuoteOpen'       : '\\begin{quotation}'  ,
        'blockQuoteClose'      : '\\end{quotation}'    ,
        'fontMonoOpen'         : '\\texttt{'           ,
        'fontMonoClose'        : '}'                   ,
        'fontBoldOpen'         : '\\textbf{'           ,
        'fontBoldClose'        : '}'                   ,
        'fontItalicOpen'       : '\\textit{'           ,
        'fontItalicClose'      : '}'                   ,
        'fontUnderlineOpen'    : '\\underline{'        ,
        'fontUnderlineClose'   : '}'                   ,
        'fontStrikeOpen'       : '\\sout{'             ,
        'fontStrikeClose'      : '}'                   ,
        'listOpen'             : '\\begin{itemize}'    ,
        'listClose'            : '\\end{itemize}'      ,
        'listOpenCompact'      : '\\begin{compactitem}',
        'listCloseCompact'     : '\\end{compactitem}'  ,
        'listItemOpen'         : '\\item '             ,
        'numlistOpen'          : '\\begin{enumerate}'  ,
        'numlistClose'         : '\\end{enumerate}'    ,
        'numlistOpenCompact'   : '\\begin{compactenum}',
        'numlistCloseCompact'  : '\\end{compactenum}'  ,
        'numlistItemOpen'      : '\\item '             ,
        'deflistOpen'          : '\\begin{description}',
        'deflistClose'         : '\\end{description}'  ,
        'deflistOpenCompact'   : '\\begin{compactdesc}',
        'deflistCloseCompact'  : '\\end{compactdesc}'  ,
        'deflistItem1Open'     : '\\item['             ,
        'deflistItem1Close'    : ']'                   ,
        'bar1'                 : '\\hrulefill{}'       ,
        'bar2'                 : '\\rule{\linewidth}{1mm}',
        'url'                  : '\\htmladdnormallink{\a}{\a}',
        'urlMark'              : '\\htmladdnormallink{\a}{\a}',
        'email'                : '\\htmladdnormallink{\a}{mailto:\a}',
        'emailMark'            : '\\htmladdnormallink{\a}{mailto:\a}',
        'img'                  : '\\includegraphics{\a}',
        'tableOpen'            : '\\begin{center}\\begin{tabular}{|~C~|}',
        'tableClose'           : '\\end{tabular}\\end{center}',
        'tableRowOpen'         : '\\hline ' ,
        'tableRowClose'        : ' \\\\'    ,
        'tableCellSep'         : ' & '      ,
        '_tableColAlignLeft'   : 'l'        ,
        '_tableColAlignRight'  : 'r'        ,
        '_tableColAlignCenter' : 'c'        ,
        '_tableCellAlignLeft'  : 'l'        ,
        '_tableCellAlignRight' : 'r'        ,
        '_tableCellAlignCenter': 'c'        ,
        '_tableCellColSpan'    : '\a'       ,
        '_tableCellMulticolOpen'  : '\\multicolumn{\a}{|~C~|}{',
        '_tableCellMulticolClose' : '}',
        'tableColAlignSep'     : '|'        ,
        'comment'              : '% \a'     ,
        'TOC'                  : '\\tableofcontents',
        'pageBreak'            : '\\clearpage',
        'EOD'                  : '\\end{document}'
    },

    'lout': {
        'paragraphOpen'        : '@LP'                     ,
        'blockTitle1Open'      : '@BeginSections'          ,
        'blockTitle1Close'     : '@EndSections'            ,
        'blockTitle2Open'      : ' @BeginSubSections'      ,
        'blockTitle2Close'     : ' @EndSubSections'        ,
        'blockTitle3Open'      : '  @BeginSubSubSections'  ,
        'blockTitle3Close'     : '  @EndSubSubSections'    ,
        'title1Open'           : '~A~@Section @Title { \a } @Begin',
        'title1Close'          : '@End @Section'           ,
        'title2Open'           : '~A~ @SubSection @Title { \a } @Begin',
        'title2Close'          : ' @End @SubSection'       ,
        'title3Open'           : '~A~  @SubSubSection @Title { \a } @Begin',
        'title3Close'          : '  @End @SubSubSection'   ,
        'title4Open'           : '~A~@LP @LeftDisplay @B { \a }',
        'title5Open'           : '~A~@LP @LeftDisplay @B { \a }',
        'anchor'               : '@Tag { \a }\n'       ,
        'blockVerbOpen'        : '@LP @ID @F @RawVerbatim @Begin',
        'blockVerbClose'       : '@End @RawVerbatim'   ,
        'blockQuoteOpen'       : '@QD {'               ,
        'blockQuoteClose'      : '}'                   ,
        # enclosed inside {} to deal with joined**words**
        'fontMonoOpen'         : '{@F {'               ,
        'fontMonoClose'        : '}}'                  ,
        'fontBoldOpen'         : '{@B {'               ,
        'fontBoldClose'        : '}}'                  ,
        'fontItalicOpen'       : '{@II {'              ,
        'fontItalicClose'      : '}}'                  ,
        'fontUnderlineOpen'    : '{@Underline{'        ,
        'fontUnderlineClose'   : '}}'                  ,
        # the full form is more readable, but could be BL EL LI NL TL DTI
        'listOpen'             : '@BulletList'         ,
        'listClose'            : '@EndList'            ,
        'listItemOpen'         : '@ListItem{'          ,
        'listItemClose'        : '}'                   ,
        'numlistOpen'          : '@NumberedList'       ,
        'numlistClose'         : '@EndList'            ,
        'numlistItemOpen'      : '@ListItem{'          ,
        'numlistItemClose'     : '}'                   ,
        'deflistOpen'          : '@TaggedList'         ,
        'deflistClose'         : '@EndList'            ,
        'deflistItem1Open'     : '@DropTagItem {'      ,
        'deflistItem1Close'    : '}'                   ,
        'deflistItem2Open'     : '{'                   ,
        'deflistItem2Close'    : '}'                   ,
        'bar1'                 : '@DP @FullWidthRule'  ,
        'url'                  : '{blue @Colour { \a }}'      ,
        'urlMark'              : '\a ({blue @Colour { \a }})' ,
        'email'                : '{blue @Colour { \a }}'      ,
        'emailMark'            : '\a ({blue Colour{ \a }})'   ,
        'img'                  : '~A~@IncludeGraphic { \a }'  , # eps only!
        '_imgAlignLeft'        : '@LeftDisplay '              ,
        '_imgAlignRight'       : '@RightDisplay '             ,
        '_imgAlignCenter'      : '@CentredDisplay '           ,
        # lout tables are *way* complicated, no support for now
        #'tableOpen'            : '~A~@Tbl~B~\naformat{ @Cell A | @Cell B } {',
        #'tableClose'           : '}'     ,
        #'tableRowOpen'         : '@Rowa\n'       ,
        #'tableTitleRowOpen'    : '@HeaderRowa'       ,
        #'tableCenterAlign'     : '@CentredDisplay '         ,
        #'tableCellOpen'        : '\a {'                     ,  # A, B, ...
        #'tableCellClose'       : '}'                        ,
        #'_tableBorder'         : '\nrule {yes}'             ,
        'comment'              : '# \a'                     ,
        # @MakeContents must be on the config file
        'TOC'                  : '@DP @ContentsGoesHere @DP',
        'pageBreak'            : '@NP'                      ,
        'EOD'                  : '@End @Text'
    },

    # http://moinmo.in/SyntaxReference
    'moin': {
        'title1'                : '= \a ='        ,
        'title2'                : '== \a =='      ,
        'title3'                : '=== \a ==='    ,
        'title4'                : '==== \a ===='  ,
        'title5'                : '===== \a =====',
        'blockVerbOpen'         : '{{{'           ,
        'blockVerbClose'        : '}}}'           ,
        'blockQuoteLine'        : '  '            ,
        'fontMonoOpen'          : '{{{'           ,
        'fontMonoClose'         : '}}}'           ,
        'fontBoldOpen'          : "'''"           ,
        'fontBoldClose'         : "'''"           ,
        'fontItalicOpen'        : "''"            ,
        'fontItalicClose'       : "''"            ,
        'fontUnderlineOpen'     : '__'            ,
        'fontUnderlineClose'    : '__'            ,
        'fontStrikeOpen'        : '--('           ,
        'fontStrikeClose'       : ')--'           ,
        'listItemOpen'          : ' * '           ,
        'numlistItemOpen'       : ' \a. '         ,
        'deflistItem1Open'      : ' '             ,
        'deflistItem1Close'     : '::'            ,
        'deflistItem2LinePrefix': ' :: '          ,
        'bar1'                  : '----'          ,
        'bar2'                  : '--------'      ,
        'url'                   : '[\a]'          ,
        'urlMark'               : '[\a \a]'       ,
        'email'                 : '[\a]'          ,
        'emailMark'             : '[\a \a]'       ,
        'img'                   : '[\a]'          ,
        'tableRowOpen'          : '||'            ,
        'tableCellOpen'         : '~A~'           ,
        'tableCellClose'        : '||'            ,
        'tableTitleCellClose'   : '||'            ,
        '_tableCellAlignRight'  : '<)>'           ,
        '_tableCellAlignCenter' : '<:>'           ,
        'comment'               : '/* \a */'      ,
        'TOC'                   : '[[TableOfContents]]'
    },

    # http://code.google.com/p/support/wiki/WikiSyntax
    'gwiki': {
        'title1'               : '= \a ='        ,
        'title2'               : '== \a =='      ,
        'title3'               : '=== \a ==='    ,
        'title4'               : '==== \a ===='  ,
        'title5'               : '===== \a =====',
        'blockVerbOpen'        : '{{{'           ,
        'blockVerbClose'       : '}}}'           ,
        'blockQuoteLine'       : '  '            ,
        'fontMonoOpen'         : '{{{'           ,
        'fontMonoClose'        : '}}}'           ,
        'fontBoldOpen'         : '*'             ,
        'fontBoldClose'        : '*'             ,
        'fontItalicOpen'       : '_'             , # underline == italic
        'fontItalicClose'      : '_'             ,
        'fontStrikeOpen'       : '~~'            ,
        'fontStrikeClose'      : '~~'            ,
        'listItemOpen'         : ' * '           ,
        'numlistItemOpen'      : ' # '           ,
        'url'                  : '\a'            ,
        'urlMark'              : '[\a \a]'       ,
        'email'                : 'mailto:\a'     ,
        'emailMark'            : '[mailto:\a \a]',
        'img'                  : '[\a]'          ,
        'tableRowOpen'         : '|| '           ,
        'tableRowClose'        : ' ||'           ,
        'tableCellSep'         : ' || '          ,
    },

    # http://powerman.name/doc/asciidoc
    'adoc': {
        'title1'               : '== \a'         ,
        'title2'               : '=== \a'        ,
        'title3'               : '==== \a'       ,
        'title4'               : '===== \a'      ,
        'title5'               : '===== \a'      ,
        'blockVerbOpen'        : '----'          ,
        'blockVerbClose'       : '----'          ,
        'fontMonoOpen'         : '+'             ,
        'fontMonoClose'        : '+'             ,
        'fontBoldOpen'         : '*'             ,
        'fontBoldClose'        : '*'             ,
        'fontItalicOpen'       : '_'             ,
        'fontItalicClose'      : '_'             ,
        'listItemOpen'         : '- '            ,
        'listItemLine'         : '\t'            ,
        'numlistItemOpen'      : '. '            ,
        'url'                  : '\a'            ,
        'urlMark'              : '\a[\a]'        ,
        'email'                : 'mailto:\a'     ,
        'emailMark'            : 'mailto:\a[\a]' ,
        'img'                  : 'image::\a[]'   ,
    },

    # http://wiki.splitbrain.org/wiki:syntax
    # Hint: <br> is \\ $
    # Hint: You can add footnotes ((This is a footnote))
    'doku': {
        'title1'               : '===== \a =====',
        'title2'               : '==== \a ===='  ,
        'title3'               : '=== \a ==='    ,
        'title4'               : '== \a =='      ,
        'title5'               : '= \a ='        ,
        # DokuWiki uses '  ' identation to mark verb blocks (see indentverbblock)
        'blockQuoteLine'       : '>'             ,
        'fontMonoOpen'         : "''"            ,
        'fontMonoClose'        : "''"            ,
        'fontBoldOpen'         : "**"            ,
        'fontBoldClose'        : "**"            ,
        'fontItalicOpen'       : "//"            ,
        'fontItalicClose'      : "//"            ,
        'fontUnderlineOpen'    : "__"            ,
        'fontUnderlineClose'   : "__"            ,
        'fontStrikeOpen'       : '<del>'         ,
        'fontStrikeClose'      : '</del>'        ,
        'listItemOpen'         : '  * '          ,
        'numlistItemOpen'      : '  - '          ,
        'bar1'                 : '----'          ,
        'url'                  : '[[\a]]'        ,
        'urlMark'              : '[[\a|\a]]'     ,
        'email'                : '[[\a]]'        ,
        'emailMark'            : '[[\a|\a]]'     ,
        'img'                  : '{{\a}}'        ,
        'imgAlignLeft'         : '{{\a }}'       ,
        'imgAlignRight'        : '{{ \a}}'       ,
        'imgAlignCenter'       : '{{ \a }}'      ,
        'tableTitleRowOpen'    : '^ '            ,
        'tableTitleRowClose'   : ' ^'            ,
        'tableTitleCellSep'    : ' ^ '           ,
        'tableRowOpen'         : '| '            ,
        'tableRowClose'        : ' |'            ,
        'tableCellSep'         : ' | '           ,
        # DokuWiki has no attributes. The content must be aligned!
        # '_tableCellAlignRight' : '<)>'           , # ??
        # '_tableCellAlignCenter': '<:>'           , # ??
        # DokuWiki colspan is the same as txt2tags' with multiple |||
        # 'comment'             : '## \a'         , # ??
        # TOC is automatic
    },

    # http://www.pmwiki.org/wiki/PmWiki/TextFormattingRules
    'pmw': {
        'title1'               : '~A~! \a '      ,
        'title2'               : '~A~!! \a '     ,
        'title3'               : '~A~!!! \a '    ,
        'title4'               : '~A~!!!! \a '   ,
        'title5'               : '~A~!!!!! \a '  ,
        'blockQuoteOpen'       : '->'            ,
        'blockQuoteClose'      : '\n'            ,
        # In-text font
        'fontLargeOpen'        : "[+"            ,
        'fontLargeClose'       : "+]"            ,
        'fontLargerOpen'       : "[++"           ,
        'fontLargerClose'      : "++]"           ,
        'fontSmallOpen'        : "[-"            ,
        'fontSmallClose'       : "-]"            ,
        'fontLargerOpen'       : "[--"           ,
        'fontLargerClose'      : "--]"           ,
        'fontMonoOpen'         : "@@"            ,
        'fontMonoClose'        : "@@"            ,
        'fontBoldOpen'         : "'''"           ,
        'fontBoldClose'        : "'''"           ,
        'fontItalicOpen'       : "''"            ,
        'fontItalicClose'      : "''"            ,
        'fontUnderlineOpen'    : "{+"            ,
        'fontUnderlineClose'   : "+}"            ,
        'fontStrikeOpen'       : '{-'            ,
        'fontStrikeClose'      : '-}'            ,
        # Lists
        'listItemOpen'          : '* '           ,
        'numlistItemOpen'       : '# '           ,
        'deflistItem1Open'      : ': '           ,
        'deflistItem1Close'     : ':'            ,
        'deflistItem2LineOpen'  : '::'           ,
        'deflistItem2LineClose' : ':'            ,
        # Verbatim block
        'blockVerbOpen'        : '[@'            ,
        'blockVerbClose'       : '@]'            ,
        'bar1'                 : '----'          ,
        # URL, email and anchor
        'url'                   : '\a'           ,
        'urlMark'               : '[[\a -> \a]]' ,
        'email'                 : '\a'           ,
        'emailMark'             : '[[\a -> mailto:\a]]',
        'anchor'                : '[[#\a]]\n'    ,
        # Image markup
        'img'                   : '\a'           ,
        #'imgAlignLeft'         : '{{\a }}'       ,
        #'imgAlignRight'        : '{{ \a}}'       ,
        #'imgAlignCenter'       : '{{ \a }}'      ,
        # Table attributes
        'tableTitleRowOpen'    : '||! '          ,
        'tableTitleRowClose'   : '||'            ,
        'tableTitleCellSep'    : ' ||!'          ,
        'tableRowOpen'         : '||'            ,
        'tableRowClose'        : '||'            ,
        'tableCellSep'         : ' ||'           ,
    },

    # http://en.wikipedia.org/wiki/Help:Editing
    'wiki': {
        'title1'                : '== \a =='        ,
        'title2'                : '=== \a ==='      ,
        'title3'                : '==== \a ===='    ,
        'title4'                : '===== \a ====='  ,
        'title5'                : '====== \a ======',
        'blockVerbOpen'         : '<pre>'           ,
        'blockVerbClose'        : '</pre>'          ,
        'blockQuoteOpen'        : '<blockquote>'    ,
        'blockQuoteClose'       : '</blockquote>'   ,
        'fontMonoOpen'          : '<tt>'            ,
        'fontMonoClose'         : '</tt>'           ,
        'fontBoldOpen'          : "'''"             ,
        'fontBoldClose'         : "'''"             ,
        'fontItalicOpen'        : "''"              ,
        'fontItalicClose'       : "''"              ,
        'fontUnderlineOpen'     : '<u>'             ,
        'fontUnderlineClose'    : '</u>'            ,
        'fontStrikeOpen'        : '<s>'             ,
        'fontStrikeClose'       : '</s>'            ,
        #XXX Mixed lists not working: *#* list inside numlist inside list
        'listItemLine'          : '*'               ,
        'numlistItemLine'       : '#'               ,
        'deflistItem1Open'      : '; '              ,
        'deflistItem2LinePrefix': ': '            ,
        'bar1'                  : '----'            ,
        'url'                   : '[\a]'            ,
        'urlMark'               : '[\a \a]'         ,
        'email'                 : 'mailto:\a'       ,
        'emailMark'             : '[mailto:\a \a]'  ,
        # [[Image:foo.png|right|Optional alt/caption text]] (right, left, center, none)
        'img'                   : '[[Image:\a~A~]]' ,
        '_imgAlignLeft'         : '|left'           ,
        '_imgAlignCenter'       : '|center'         ,
        '_imgAlignRight'        : '|right'          ,
        # {| border="1" cellspacing="0" cellpadding="4" align="center"
        'tableOpen'             : '{|~A~~B~ cellpadding="4"',
        'tableClose'            : '|}'              ,
        'tableRowOpen'          : '|-\n| '          ,
        'tableTitleRowOpen'     : '|-\n! '          ,
        'tableCellSep'          : ' || '            ,
        'tableTitleCellSep'     : ' !! '            ,
        '_tableBorder'          : ' border="1"'     ,
        '_tableAlignCenter'     : ' align="center"' ,
        'comment'               : '<!-- \a -->'     ,
        'TOC'                   : '__TOC__'         ,
    },

    # http://www.inference.phy.cam.ac.uk/mackay/mgp/SYNTAX
    # http://en.wikipedia.org/wiki/MagicPoint
    'mgp': {
        'paragraphOpen'         : '%font "normal", size 5'     ,
        'title1'                : '%page\n\n\a\n'              ,
        'title2'                : '%page\n\n\a\n'              ,
        'title3'                : '%page\n\n\a\n'              ,
        'title4'                : '%page\n\n\a\n'              ,
        'title5'                : '%page\n\n\a\n'              ,
        'blockVerbOpen'         : '%font "mono"'               ,
        'blockVerbClose'        : '%font "normal"'             ,
        'blockQuoteOpen'        : '%prefix "       "'          ,
        'blockQuoteClose'       : '%prefix "  "'               ,
        'fontMonoOpen'          : '\n%cont, font "mono"\n'     ,
        'fontMonoClose'         : '\n%cont, font "normal"\n'   ,
        'fontBoldOpen'          : '\n%cont, font "normal-b"\n' ,
        'fontBoldClose'         : '\n%cont, font "normal"\n'   ,
        'fontItalicOpen'        : '\n%cont, font "normal-i"\n' ,
        'fontItalicClose'       : '\n%cont, font "normal"\n'   ,
        'fontUnderlineOpen'     : '\n%cont, fore "cyan"\n'     ,
        'fontUnderlineClose'    : '\n%cont, fore "white"\n'    ,
        'listItemLine'          : '\t'                         ,
        'numlistItemLine'       : '\t'                         ,
        'numlistItemOpen'       : '\a. '                       ,
        'deflistItem1Open'      : '\t\n%cont, font "normal-b"\n',
        'deflistItem1Close'     : '\n%cont, font "normal"\n'   ,
        'bar1'                  : '%bar "white" 5'             ,
        'bar2'                  : '%pause'                     ,
        'url'                   : '\n%cont, fore "cyan"\n\a'   +\
                                  '\n%cont, fore "white"\n'    ,
        'urlMark'               : '\a \n%cont, fore "cyan"\n\a'+\
                                  '\n%cont, fore "white"\n'    ,
        'email'                 : '\n%cont, fore "cyan"\n\a'   +\
                                  '\n%cont, fore "white"\n'    ,
        'emailMark'             : '\a \n%cont, fore "cyan"\n\a'+\
                                  '\n%cont, fore "white"\n'    ,
        'img'                   : '~A~\n%newimage "\a"\n%left\n',
        '_imgAlignLeft'         : '\n%left'                    ,
        '_imgAlignRight'        : '\n%right'                   ,
        '_imgAlignCenter'       : '\n%center'                  ,
        'comment'               : '%% \a'                      ,
        'pageBreak'             : '%page\n\n\n'                ,
        'EOD'                   : '%%EOD'
    },

    # man groff_man ; man 7 groff
    'man': {
        'paragraphOpen'         : '.P'     ,
        'title1'                : '.SH \a' ,
        'title2'                : '.SS \a' ,
        'title3'                : '.SS \a' ,
        'title4'                : '.SS \a' ,
        'title5'                : '.SS \a' ,
        'blockVerbOpen'         : '.nf'    ,
        'blockVerbClose'        : '.fi\n'  ,
        'blockQuoteOpen'        : '.RS'    ,
        'blockQuoteClose'       : '.RE'    ,
        'fontBoldOpen'          : '\\fB'   ,
        'fontBoldClose'         : '\\fR'   ,
        'fontItalicOpen'        : '\\fI'   ,
        'fontItalicClose'       : '\\fR'   ,
        'listOpen'              : '.RS'    ,
        'listItemOpen'          : '.IP \(bu 3\n',
        'listClose'             : '.RE'    ,
        'numlistOpen'           : '.RS'    ,
        'numlistItemOpen'       : '.IP \a. 3\n',
        'numlistClose'          : '.RE'    ,
        'deflistItem1Open'      : '.TP\n'  ,
        'bar1'                  : '\n\n'   ,
        'url'                   : '\a'     ,
        'urlMark'               : '\a (\a)',
        'email'                 : '\a'     ,
        'emailMark'             : '\a (\a)',
        'img'                   : '\a'     ,
        'tableOpen'             : '.TS\n~A~~B~tab(^); ~C~.',
        'tableClose'            : '.TE'     ,
        'tableRowOpen'          : ' '       ,
        'tableCellSep'          : '^'       ,
        '_tableAlignCenter'     : 'center, ',
        '_tableBorder'          : 'allbox, ',
        '_tableColAlignLeft'    : 'l'       ,
        '_tableColAlignRight'   : 'r'       ,
        '_tableColAlignCenter'  : 'c'       ,
        'comment'               : '.\\" \a'
    },

    'pm6': {
        'paragraphOpen'         : '<@Normal:>'    ,
        'title1'                : '<@Title1:>\a',
        'title2'                : '<@Title2:>\a',
        'title3'                : '<@Title3:>\a',
        'title4'                : '<@Title4:>\a',
        'title5'                : '<@Title5:>\a',
        'blockVerbOpen'         : '<@PreFormat:>' ,
        'blockQuoteLine'        : '<@Quote:>'     ,
        'fontMonoOpen'          : '<FONT "Lucida Console"><SIZE 9>' ,
        'fontMonoClose'         : '<SIZE$><FONT$>',
        'fontBoldOpen'          : '<B>'           ,
        'fontBoldClose'         : '<P>'           ,
        'fontItalicOpen'        : '<I>'           ,
        'fontItalicClose'       : '<P>'           ,
        'fontUnderlineOpen'     : '<U>'           ,
        'fontUnderlineClose'    : '<P>'           ,
        'listOpen'              : '<@Bullet:>'    ,
        'listItemOpen'          : '\x95\t'        ,  # \x95 == ~U
        'numlistOpen'           : '<@Bullet:>'    ,
        'numlistItemOpen'       : '\x95\t'        ,
        'bar1'                  : '\a'            ,
        'url'                   : '<U>\a<P>'      ,  # underline
        'urlMark'               : '\a <U>\a<P>'   ,
        'email'                 : '\a'            ,
        'emailMark'             : '\a \a'         ,
        'img'                   : '\a'
    }
    }

    # Exceptions for --css-sugar
    if config['css-sugar'] and config['target'] in ('html','xhtml'):
        # Change just HTML because XHTML inherits it
        htmltags = alltags['html']
        # Table with no cellpadding
        htmltags['tableOpen'] = htmltags['tableOpen'].replace(' CELLPADDING="4"', '')
        # DIVs
        htmltags['tocOpen' ] = '<DIV CLASS="toc" ID="toc">'
        htmltags['tocClose'] = '</DIV>'
        htmltags['bodyOpen'] = '<DIV CLASS="body" ID="body">'
        htmltags['bodyClose']= '</DIV>'

    # Make the HTML -> XHTML inheritance
    xhtml = alltags['html'].copy()
    for key in xhtml.keys(): xhtml[key] = xhtml[key].lower()
    # Some like HTML tags as lowercase, some don't... (headers out)
    if HTML_LOWER: alltags['html'] = xhtml.copy()
    xhtml.update(alltags['xhtml'])
    alltags['xhtml'] = xhtml.copy()

    # Compose the target tags dictionary
    tags = {}
    target_tags = alltags[config['target']].copy()

    for key in keys: tags[key] = '' # create empty keys
    for key in target_tags.keys():
        tags[key] = maskEscapeChar(target_tags[key]) # populate

    # Map strong line to pagebreak
    if rules['mapbar2pagebreak'] and tags['pageBreak']:
        tags['bar2'] = tags['pageBreak']

    # Map strong line to separator if not defined
    if not tags['bar2'] and tags['bar1']:
        tags['bar2'] = tags['bar1']

    return tags


##############################################################################


def getRules(config):
    "Returns all the target-specific syntax rules"

    ret = {}
    allrules = [

        # target rules (ON/OFF)
        'linkable',             # target supports external links
        'tableable',            # target supports tables
        'imglinkable',          # target supports images as links
        'imgalignable',         # target supports image alignment
        'imgasdefterm',         # target supports image as definition term
        'autonumberlist',       # target supports numbered lists natively
        'autonumbertitle',      # target supports numbered titles natively
        'stylable',             # target supports external style files
        'parainsidelist',       # lists items supports paragraph
        'compactlist',          # separate enclosing tags for compact lists
        'spacedlistitem',       # lists support blank lines between items
        'listnotnested',        # lists cannot be nested
        'quotenotnested',       # quotes cannot be nested
        'verbblocknotescaped',  # don't escape specials in verb block
        'verbblockfinalescape', # do final escapes in verb block
        'escapeurl',            # escape special in link URL
        'labelbeforelink',      # label comes before the link on the tag
        'onelinepara',          # dump paragraph as a single long line
        'tabletitlerowinbold',  # manually bold any cell on table titles
        'tablecellstrip',       # strip extra spaces from each table cell
        'tablecellspannable',   # the table cells can have span attribute
        'tablecellmulticol',    # separate open+close tags for multicol cells
        'barinsidequote',       # bars are allowed inside quote blocks
        'finalescapetitle',     # perform final escapes on title lines
        'autotocnewpagebefore', # break page before automatic TOC
        'autotocnewpageafter',  # break page after automatic TOC
        'autotocwithbars',      # automatic TOC surrounded by bars
        'mapbar2pagebreak',     # map the strong bar to a page break
        'titleblocks',          # titles must be on open/close section blocks

        # Target code beautify (ON/OFF)
        'indentverbblock',      # add leading spaces to verb block lines
        'breaktablecell',       # break lines after any table cell
        'breaktablelineopen',   # break line after opening table line
        'notbreaklistopen',     # don't break line after opening a new list
        'keepquoteindent',      # don't remove the leading TABs on quotes
        'keeplistindent',       # don't remove the leading spaces on lists
        'blankendautotoc',      # append a blank line at the auto TOC end
        'tagnotindentable',     # tags must be placed at the line begining
        'spacedlistitemopen',   # append a space after the list item open tag
        'spacednumlistitemopen',# append a space after the numlist item open tag
        'deflisttextstrip',     # strip the contents of the deflist text
        'blanksaroundpara',     # put a blank line before and after paragraphs
        'blanksaroundverb',     # put a blank line before and after verb blocks
        'blanksaroundquote',    # put a blank line before and after quotes
        'blanksaroundlist',     # put a blank line before and after lists
        'blanksaroundnumlist',  # put a blank line before and after numlists
        'blanksarounddeflist',  # put a blank line before and after deflists
        'blanksaroundtable',    # put a blank line before and after tables
        'blanksaroundbar',      # put a blank line before and after bars
        'blanksaroundtitle',    # put a blank line before and after titles
        'blanksaroundnumtitle', # put a blank line before and after numtitles

        # Value settings
        'listmaxdepth',         # maximum depth for lists
        'quotemaxdepth',        # maximum depth for quotes
        'tablecellaligntype',   # type of table cell align: cell, column
    ]

    rules_bank = {
        'txt': {
            'indentverbblock':1,
            'spacedlistitem':1,
            'parainsidelist':1,
            'keeplistindent':1,
            'barinsidequote':1,
            'autotocwithbars':1,

            'blanksaroundpara':1,
            'blanksaroundverb':1,
            'blanksaroundquote':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            'blanksaroundtable':1,
            'blanksaroundbar':1,
            'blanksaroundtitle':1,
            'blanksaroundnumtitle':1,
        },
        'art': {
            #TIP art inherits all TXT rules
        },
        'html': {
            'indentverbblock':1,
            'linkable':1,
            'stylable':1,
            'escapeurl':1,
            'imglinkable':1,
            'imgalignable':1,
            'imgasdefterm':1,
            'autonumberlist':1,
            'spacedlistitem':1,
            'parainsidelist':1,
            'tableable':1,
            'tablecellstrip':1,
            'breaktablecell':1,
            'breaktablelineopen':1,
            'keeplistindent':1,
            'keepquoteindent':1,
            'barinsidequote':1,
            'autotocwithbars':1,
            'tablecellspannable':1,
            'tablecellaligntype':'cell',

            # 'blanksaroundpara':1,
            'blanksaroundverb':1,
            # 'blanksaroundquote':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            'blanksaroundtable':1,
            'blanksaroundbar':1,
            'blanksaroundtitle':1,
            'blanksaroundnumtitle':1,
        },
        'xhtml': {
            #TIP xhtml inherits all HTML rules
        },
        'sgml': {
            'linkable':1,
            'escapeurl':1,
            'autonumberlist':1,
            'spacedlistitem':1,
            'tableable':1,
            'tablecellstrip':1,
            'blankendautotoc':1,
            'quotenotnested':1,
            'keeplistindent':1,
            'keepquoteindent':1,
            'barinsidequote':1,
            'finalescapetitle':1,
            'tablecellaligntype':'column',

            'blanksaroundpara':1,
            'blanksaroundverb':1,
            'blanksaroundquote':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            'blanksaroundtable':1,
            'blanksaroundbar':1,
            'blanksaroundtitle':1,
            'blanksaroundnumtitle':1,
        },
        'dbk': {
            'linkable':1,
            'tableable':1,
            'imglinkable':1,
            'imgalignable':1,
            'imgasdefterm':1,
            'autonumberlist':1,
            'autonumbertitle':1,
            'parainsidelist':1,
            'spacedlistitem':1,
            'titleblocks':1,
        },
        'mgp': {
            'tagnotindentable':1,
            'spacedlistitem':1,
            'imgalignable':1,
            'autotocnewpagebefore':1,

            'blanksaroundpara':1,
            'blanksaroundverb':1,
            # 'blanksaroundquote':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            'blanksaroundtable':1,
            'blanksaroundbar':1,
            # 'blanksaroundtitle':1,
            # 'blanksaroundnumtitle':1,
        },
        'tex': {
            'stylable':1,
            'escapeurl':1,
            'autonumberlist':1,
            'autonumbertitle':1,
            'spacedlistitem':1,
            'compactlist':1,
            'parainsidelist':1,
            'tableable':1,
            'tablecellstrip':1,
            'tabletitlerowinbold':1,
            'verbblocknotescaped':1,
            'keeplistindent':1,
            'listmaxdepth':4,  # deflist is 6
            'quotemaxdepth':6,
            'barinsidequote':1,
            'finalescapetitle':1,
            'autotocnewpageafter':1,
            'mapbar2pagebreak':1,
            'tablecellaligntype':'column',
            'tablecellmulticol':1,

            'blanksaroundpara':1,
            'blanksaroundverb':1,
            # 'blanksaroundquote':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            'blanksaroundtable':1,
            'blanksaroundbar':1,
            'blanksaroundtitle':1,
            'blanksaroundnumtitle':1,
        },
        'lout': {
            'keepquoteindent':1,
            'deflisttextstrip':1,
            'escapeurl':1,
            'verbblocknotescaped':1,
            'imgalignable':1,
            'mapbar2pagebreak':1,
            'titleblocks':1,
            'autonumberlist':1,
            'parainsidelist':1,

            'blanksaroundpara':1,
            'blanksaroundverb':1,
            # 'blanksaroundquote':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            'blanksaroundtable':1,
            'blanksaroundbar':1,
            'blanksaroundtitle':1,
            'blanksaroundnumtitle':1,
        },
        'moin': {
            'spacedlistitem':1,
            'linkable':1,
            'keeplistindent':1,
            'tableable':1,
            'barinsidequote':1,
            'tabletitlerowinbold':1,
            'tablecellstrip':1,
            'autotocwithbars':1,
            'tablecellaligntype':'cell',
            'deflisttextstrip':1,

            'blanksaroundpara':1,
            'blanksaroundverb':1,
            # 'blanksaroundquote':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            'blanksaroundtable':1,
            # 'blanksaroundbar':1,
            'blanksaroundtitle':1,
            'blanksaroundnumtitle':1,
        },
        'gwiki': {
            'spacedlistitem':1,
            'linkable':1,
            'keeplistindent':1,
            'tableable':1,
            'tabletitlerowinbold':1,
            'tablecellstrip':1,
            'autonumberlist':1,

            'blanksaroundpara':1,
            'blanksaroundverb':1,
            # 'blanksaroundquote':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            'blanksaroundtable':1,
            # 'blanksaroundbar':1,
            'blanksaroundtitle':1,
            'blanksaroundnumtitle':1,
        },
        'adoc': {
            'spacedlistitem':1,
            'linkable':1,
            'keeplistindent':1,
            'autonumberlist':1,
            'autonumbertitle':1,
            'listnotnested':1,
            'blanksaroundpara':1,
            'blanksaroundverb':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            'blanksaroundtable':1,
            'blanksaroundtitle':1,
            'blanksaroundnumtitle':1,
        },
        'doku': {
            'indentverbblock':1, # DokuWiki uses '  ' to mark verb blocks
            'spacedlistitem':1,
            'linkable':1,
            'keeplistindent':1,
            'tableable':1,
            'barinsidequote':1,
            'tablecellstrip':1,
            'autotocwithbars':1,
            'autonumberlist':1,
            'imgalignable':1,
            'tablecellaligntype':'cell',

            'blanksaroundpara':1,
            'blanksaroundverb':1,
            # 'blanksaroundquote':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            'blanksaroundtable':1,
            'blanksaroundbar':1,
            'blanksaroundtitle':1,
            'blanksaroundnumtitle':1,
        },
        'pmw': {
            'indentverbblock':1,
            'spacedlistitem':1,
            'linkable':1,
            'labelbeforelink':1,
            'keeplistindent':1,
            'tableable':1,
            'barinsidequote':1,
            'tablecellstrip':1,
            'autotocwithbars':1,
            'autonumberlist':1,
            'imgalignable':1,
            'tabletitlerowinbold':1,
            'tablecellaligntype':'cell',

            'blanksaroundpara':1,
            'blanksaroundverb':1,
            'blanksaroundquote':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            'blanksaroundtable':1,
            'blanksaroundbar':1,
            'blanksaroundtitle':1,
            'blanksaroundnumtitle':1,
        },
        'wiki': {
            'linkable':1,
            'tableable':1,
            'tablecellstrip':1,
            'autotocwithbars':1,
            'spacedlistitemopen':1,
            'spacednumlistitemopen':1,
            'deflisttextstrip':1,
            'autonumberlist':1,
            'imgalignable':1,

            'blanksaroundpara':1,
            'blanksaroundverb':1,
            # 'blanksaroundquote':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            'blanksaroundtable':1,
            'blanksaroundbar':1,
            'blanksaroundtitle':1,
            'blanksaroundnumtitle':1,
        },
        'man': {
            'spacedlistitem':1,
            'indentverbblock':1,
            'tagnotindentable':1,
            'tableable':1,
            'tablecellaligntype':'column',
            'tabletitlerowinbold':1,
            'tablecellstrip':1,
            'barinsidequote':1,
            'parainsidelist':0,

            'blanksaroundpara':1,
            'blanksaroundverb':1,
            # 'blanksaroundquote':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            'blanksaroundtable':1,
            # 'blanksaroundbar':1,
            'blanksaroundtitle':1,
            'blanksaroundnumtitle':1,
        },
        'pm6': {
            'keeplistindent':1,
            'verbblockfinalescape':1,
            #TODO add support for these
            # maybe set a JOINNEXT char and do it on addLineBreaks()
            'notbreaklistopen':1,
            'barinsidequote':1,
            'autotocwithbars':1,
            'onelinepara':1,

            'blanksaroundpara':1,
            'blanksaroundverb':1,
            # 'blanksaroundquote':1,
            'blanksaroundlist':1,
            'blanksaroundnumlist':1,
            'blanksarounddeflist':1,
            # 'blanksaroundtable':1,
            # 'blanksaroundbar':1,
            'blanksaroundtitle':1,
            'blanksaroundnumtitle':1,
        }
    }

    # Exceptions for --css-sugar
    if config['css-sugar'] and config['target'] in ('html','xhtml'):
        rules_bank['html']['indentverbblock'] = 0
        rules_bank['html']['autotocwithbars'] = 0

    # Get the target specific rules
    if config['target'] == 'xhtml':
        myrules = rules_bank['html'].copy()   # inheritance
        myrules.update(rules_bank['xhtml'])   # get XHTML specific
    elif config['target'] == 'art':
        myrules = rules_bank['txt'].copy()    # inheritance
    else:
        myrules = rules_bank[config['target']].copy()

    # Populate return dictionary
    for key in allrules: ret[key] = 0        # reset all
    ret.update(myrules)                      # get rules

    return ret


##############################################################################


def getRegexes():
    "Returns all the regexes used to find the t2t marks"

    bank = {
    'blockVerbOpen':
        re.compile(r'^```\s*$'),
    'blockVerbClose':
        re.compile(r'^```\s*$'),
    'blockRawOpen':
        re.compile(r'^"""\s*$'),
    'blockRawClose':
        re.compile(r'^"""\s*$'),
    'blockTaggedOpen':
        re.compile(r"^'''\s*$"),
    'blockTaggedClose':
        re.compile(r"^'''\s*$"),
    'blockCommentOpen':
        re.compile(r'^%%%\s*$'),
    'blockCommentClose':
        re.compile(r'^%%%\s*$'),
    'quote':
        re.compile(r'^\t+'),
    '1lineVerb':
        re.compile(r'^``` (?=.)'),
    '1lineRaw':
        re.compile(r'^""" (?=.)'),
    '1lineTagged':
        re.compile(r"^''' (?=.)"),
    # mono, raw, bold, italic, underline:
    # - marks must be glued with the contents, no boundary spaces
    # - they are greedy, so in ****bold****, turns to <b>**bold**</b>
    'fontMono':
        re.compile(  r'``([^\s](|.*?[^\s])`*)``'),
    'raw':
        re.compile(  r'""([^\s](|.*?[^\s])"*)""'),
    'tagged':
        re.compile(  r"''([^\s](|.*?[^\s])'*)''"),
    'fontBold':
        re.compile(r'\*\*([^\s](|.*?[^\s])\**)\*\*'),
    'fontItalic':
        re.compile(  r'//([^\s](|.*?[^\s])/*)//'),
    'fontUnderline':
        re.compile(  r'__([^\s](|.*?[^\s])_*)__'),
    'fontStrike':
        re.compile(  r'--([^\s](|.*?[^\s])-*)--'),
    'list':
        re.compile(r'^( *)(-) (?=[^ ])'),
    'numlist':
        re.compile(r'^( *)(\+) (?=[^ ])'),
    'deflist':
        re.compile(r'^( *)(:) (.*)$'),
    'listclose':
        re.compile(r'^( *)([-+:])\s*$'),
    'bar':
        re.compile(r'^(\s*)([_=-]{20,})\s*$'),
    'table':
        re.compile(r'^ *\|\|? '),
    'blankline':
        re.compile(r'^\s*$'),
    'comment':
        re.compile(r'^%'),

    # Auxiliary tag regexes
    '_imgAlign'        : re.compile(r'~A~', re.I),
    '_tableAlign'      : re.compile(r'~A~', re.I),
    '_anchor'          : re.compile(r'~A~', re.I),
    '_tableBorder'     : re.compile(r'~B~', re.I),
    '_tableColAlign'   : re.compile(r'~C~', re.I),
    '_tableCellColSpan': re.compile(r'~S~', re.I),
    '_tableCellAlign'  : re.compile(r'~A~', re.I),
    }

    # Special char to place data on TAGs contents  (\a == bell)
    bank['x'] = re.compile('\a')

    # %%macroname [ (formatting) ]
    bank['macros'] = re.compile(r'%%%%(?P<name>%s)\b(\((?P<fmt>.*?)\))?' % (
        '|'.join(MACROS.keys())), re.I)

    # %%TOC special macro for TOC positioning
    bank['toc'] = re.compile(r'^ *%%toc\s*$', re.I)

    # Almost complicated title regexes ;)
    titskel = r'^ *(?P<id>%s)(?P<txt>%s)\1(\[(?P<label>[\w-]*)\])?\s*$'
    bank[   'title'] = re.compile(titskel%('[=]{1,5}','[^=](|.*[^=])'))
    bank['numtitle'] = re.compile(titskel%('[+]{1,5}','[^+](|.*[^+])'))

    ### Complicated regexes begin here ;)
    #
    # Textual descriptions on --help's style: [...] is optional, | is OR


    ### First, some auxiliary variables
    #

    # [image.EXT]
    patt_img = r'\[([\w_,.+%$#@!?+~/-]+\.(png|jpe?g|gif|eps|bmp))\]'

    # Link things
    # http://www.gbiv.com/protocols/uri/rfc/rfc3986.html
    # pchar: A-Za-z._~- / %FF / !$&'()*+,;= / :@
    # Recomended order: scheme://user:pass@domain/path?query=foo#anchor
    # Also works      : scheme://user:pass@domain/path#anchor?query=foo
    # TODO form: !'():
    ## JS: Add support for irc protocol.
    ## JS: Allow ampersands in e-mail addresses.
    urlskel = {
        'proto' : r'(https?|ftp|news|telnet|gopher|wais|irc[6s]?)://',
        'guess' : r'(www[23]?|ftp)\.',         # w/out proto, try to guess
        'login' : r'A-Za-z0-9_.\-&',           # for ftp://login@domain.com
        'pass'  : r'[^ @]*',                   # for ftp://login:pass@dom.com
        'chars' : r'A-Za-z0-9%._/~:,=$@&+-',   # %20(space), :80(port), D&D
        'anchor': r'A-Za-z0-9%._-',            # %nn(encoded)
        'form'  : r'A-Za-z0-9/%&=+:;.,$@*_-',   # .,@*_-(as is)
        'punct' : r'.,;:!?'
    }

    # username [ :password ] @
    patt_url_login = r'([%s]+(:%s)?@)?'%(urlskel['login'],urlskel['pass'])

    # [ http:// ] [ username:password@ ] domain.com [ / ]
    #     [ #anchor | ?form=data ]
    retxt_url = r'\b(%s%s|%s)[%s]+\b/*(\?[%s]+)?(#[%s]*)?'%(
        urlskel['proto'],patt_url_login, urlskel['guess'],
        urlskel['chars'],urlskel['form'],urlskel['anchor'])

    # filename | [ filename ] #anchor
    retxt_url_local = r'[%s]+|[%s]*(#[%s]*)'%(
        urlskel['chars'],urlskel['chars'],urlskel['anchor'])

    # user@domain [ ?form=data ]
    patt_email = r'\b[%s]+@([A-Za-z0-9_-]+\.)+[A-Za-z]{2,4}\b(\?[%s]+)?'%(
        urlskel['login'],urlskel['form'])

    # Saving for future use
    bank['_urlskel'] = urlskel

    ### And now the real regexes
    #

    bank['email'] = re.compile(patt_email,re.I)

    # email | url
    bank['link'] = re.compile(r'%s|%s'%(retxt_url,patt_email), re.I)

    # \[ label | imagetag    url | email | filename \]
    bank['linkmark'] = re.compile(
        r'\[(?P<label>%s|[^]]+) (?P<link>%s|%s|%s)\]'%(
            patt_img, retxt_url, patt_email, retxt_url_local),
        re.L+re.I)

    # Image
    bank['img'] = re.compile(patt_img, re.L+re.I)

    # Special things
    bank['special'] = re.compile(r'^%!\s*')
    return bank
### END OF regex nightmares

################# functions for the Ascii Art backend ########################

def aa_line(char):
    return char*72 + LB

def aa_box(txt):
    len_txt = len(txt)
    nspace = (72-len_txt-4)/2
    line_box = " "*nspace + AA_CHARS['coin'] + AA_CHARS['line']*(len_txt+2) + AA_CHARS['coin'] + LB
    # <----- nspace " " -----> "+" <----- len_txt+2 "-" -----> "+"
    #                           +-------------------------------+
    #                           | all theeeeeeeeeeeeeeeeee text |
    # <----- nspace " " -----> "| " <--------- txt ---------> " |"
    line_txt = " "*nspace + AA_CHARS['border'] + ' ' + txt + ' ' + AA_CHARS['border'] + LB
    return line_box + line_txt + line_box

def aa_header(header_data):
    header= aa_line(AA_CHARS['bar2'])+\
        LB+\
        LB
    for h in 'HEADER1', 'HEADER2', 'HEADER3' :
        if header_data[h]: header +=\
        aa_box(header_data[h])+\
        LB+\
        LB
    header+=aa_line(AA_CHARS['bar2'])
    return header

##############################################################################

class error(Exception):
    pass
def echo(msg):   # for quick debug
    print('\033[32;1m%s\033[m'%msg)
def Quit(msg=''):
    if msg: print(msg)
    sys.exit(0)
def Error(msg):
    msg = _("%s: Error: ")%my_name + msg
    raise error(msg)
def getTraceback():
    try:
        from traceback import format_exception
        etype, value, tb = sys.exc_info()
        return ''.join(format_exception(etype, value, tb))
    except: pass
def getUnknownErrorMessage():
    msg = '%s\n%s (%s):\n\n%s'%(
        _('Sorry! Txt2tags aborted by an unknown error.'),
        _('Please send the following Error Traceback to the author'),
        my_email, getTraceback())
    return msg
def Message(msg,level):
    if level <= VERBOSE and not QUIET:
        prefix = '-'*5
        print("%s %s"%(prefix*level, msg))
def Debug(msg,id=0,linenr=None):
    "Show debug messages, categorized (colored or not)"
    if QUIET or not DEBUG: return
    if int(id) not in list(range(8)): id = 0
    # 0:black 1:red 2:green 3:yellow 4:blue 5:pink 6:cyan 7:white ;1:light
    ids            = ['INI','CFG','SRC','BLK','HLD','GUI','OUT','DET']
    colors_bgdark  = ['7;1','1;1','3;1','6;1','4;1','5;1','2;1','7;1']
    colors_bglight = ['0'  ,'1'  ,'3'  ,'6'  ,'4'  ,'5'  ,'2'  ,'0'  ]
    if linenr is not None: msg = "LINE %04d: %s"%(linenr,msg)
    if COLOR_DEBUG:
        if BG_LIGHT: color = colors_bglight[id]
        else       : color = colors_bgdark[id]
        msg = '\033[3%sm%s\033[m'%(color,msg)
    print("++ %s: %s"%(ids[id],msg))
def Readfile(file, remove_linebreaks=0, ignore_error=0):
    data = []
    if file == '-':
        try: data = sys.stdin.readlines()
        except:
            if not ignore_error:
                Error(_('You must feed me with data on STDIN!'))
    else:
        try: f = open(file); data = f.readlines() ; f.close()
        except:
            ## Jendrik: Do not raise Error if file cannot be read.
            msg = _("Cannot read file:") + " %s" % file
            return ['', '', '', msg]
    if remove_linebreaks:
        data = [re.sub('[\n\r]+$','',x) for x in data]
    Message(_("File read (%d lines): %s")%(len(data),file),2)
    return data
def Savefile(file, contents):
    try: f = open(file, 'wb')
    except: Error(_("Cannot open file for writing:")+" %s"%file)
    if type(contents) == type([]): doit = f.writelines
    else: doit = f.write
    doit(contents) ; f.close()

def showdic(dic):
    for k in dic.keys(): print("%15s : %s" % (k,dic[k]))
def dotted_spaces(txt=''):
    return txt.replace(' ', '.')

# TIP: win env vars http://www.winnetmag.com/Article/ArticleID/23873/23873.html
def get_rc_path():
    "Return the full path for the users' RC file"
    # Try to get the path from an env var. if yes, we're done
    user_defined = os.environ.get('T2TCONFIG')
    if user_defined: return user_defined
    # Env var not found, so perform automatic path composing
    # Set default filename according system platform
    rc_names = {'default':'.txt2tagsrc', 'win':'_t2trc'}
    rc_file = rc_names.get(sys.platform[:3]) or rc_names['default']
    # The file must be on the user directory, but where is this dir?
    rc_dir_search = ['HOME', 'HOMEPATH']
    for var in rc_dir_search:
        rc_dir = os.environ.get(var)
        if rc_dir: break
    # rc dir found, now we must join dir+file to compose the full path
    if rc_dir:
        # Compose path and return it if the file exists
        rc_path = os.path.join(rc_dir, rc_file)
        # On windows, prefix with the drive (%homedrive%: 2k/XP/NT)
        if sys.platform.startswith('win'):
            rc_drive = os.environ.get('HOMEDRIVE')
            rc_path = os.path.join(rc_drive,rc_path)
        return rc_path
    # Sorry, not found
    return ''



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
        Optional 'ignore' and 'filter' arguments are used to filter
        in or out specified keys.

    compose_cmdline(dict) -> [Command line]
        Compose a command line list from an already parsed config
        dictionary, generated from RAW by ConfigMaster(). Use
        this to compose an optimal command line for a group of
        options.

    The get_raw_config() calls parse(), so the tipical use of this
    class is:

            raw = CommandLine().get_raw_config(sys.argv[1:])
    """
    def __init__(self):
        self.all_options = list(OPTIONS.keys())
        self.all_flags   = list(FLAGS.keys())
        self.all_actions = list(ACTIONS.keys())

        # short:long options equivalence
        self.short_long = {
            'a':'ascii-art',
            'C':'config-file',
            'h':'help',
            'H':'no-headers',
            'i':'infile',
            'n':'enum-title',
            'o':'outfile',
            'q':'quiet',
            't':'target',
            'v':'verbose',
            'V':'version',
        }

        # Compose valid short and long options data for getopt
        self.short_opts = self._compose_short_opts()
        self.long_opts  = self._compose_long_opts()

    def _compose_short_opts(self):
        "Returns a string like 'hVt:o' with all short options/flags"
        ret = []
        for opt in self.short_long.keys():
            long = self.short_long[opt]
            if long in self.all_options: # is flag or option?
                opt = opt+':'        # option: have param
            ret.append(opt)
        #Debug('Valid SHORT options: %s'%ret)
        return ''.join(ret)

    def _compose_long_opts(self):
        "Returns a list with all the valid long options/flags"
        ret = [x+'=' for x in self.all_options]              # add =
        ret.extend(self.all_flags)                           # flag ON
        ret.extend(self.all_actions)                         # acts
        ret.extend(['no-'+x for x in self.all_flags])        # add no-*
        ret.extend(['no-style','no-encoding'])               # turn OFF
        ret.extend(['no-outfile','no-infile'])               # turn OFF
        ret.extend(['no-dump-config', 'no-dump-source'])     # turn OFF
        #Debug('Valid LONG options: %s'%ret)
        return ret

    def _tokenize(self, cmd_string=''):
        "Convert a command line string to a list"
        #TODO protect quotes contents -- Don't use it, pass cmdline as list
        return cmd_string.split()

    def parse(self, cmdline=[]):
        "Check/Parse a command line list     TIP: no program name!"
        # Get the valid options
        short, long = self.short_opts, self.long_opts
        # Parse it!
        try:
            opts, args = getopt.getopt(cmdline, short, long)
        except getopt.error as errmsg:
            Error(_("%s (try --help)")%errmsg)
        return (opts, args)

    def get_raw_config(self, cmdline=[], ignore=[], filter=[], relative=0):
        "Returns the options/arguments found as RAW config"
        if not cmdline: return []
        ret = []
        # We need lists, not strings
        if isinstance(cmdline, str):
            cmdline = self._tokenize(cmdline)
        opts, args = self.parse(cmdline[:])
        # Parse all options
        for name,value in opts:
            # Remove leading - and --
            name = re.sub('^--?', '', name)
            # Alias to old misspelled 'suGGar'
            if   name ==    'css-suggar': name =    'css-sugar'
            elif name == 'no-css-suggar': name = 'no-css-sugar'
            # Translate short opt to long
            if len(name) == 1: name = self.short_long.get(name)
            # Outfile exception: path relative to PWD
            if name == 'outfile' and relative \
               and value not in [STDOUT, MODULEOUT]:
                value = os.path.abspath(value)
            # config-file inclusion, path relative to PWD
            if name == 'config-file':
                configs = ConfigLines().include_config_file(value)
                # Remove the 'target' item of all configs
                configs = [[c[1], c[2]] for c in configs]
                ret.extend(configs)
                continue
            # Save it
            ret.append([name, value])
        # Get infile, if any
        while args:
            infile = args.pop(0)
            ret.append(['infile', infile])
        # Apply 'ignore' and 'filter' rules (filter is stronger)
        temp = ret[:] ; ret = []
        for name,value in temp:
            if (not filter and not ignore) or \
               (filter and name in filter) or \
               (ignore and name not in ignore):
                ret.append( ['all', name, value] )
        # Add the original command line string as 'realcmdline'
        ret.append( ['all', 'realcmdline', cmdline] )
        return ret

    def compose_cmdline(self, conf={}, no_check=0):
        "compose a full (and diet) command line from CONF dict"
        if not conf: return []
        args = []
        dft_options = OPTIONS.copy()
        cfg = conf.copy()
        valid_opts = self.all_options + self.all_flags
        use_short = {'no-headers':'H', 'enum-title':'n'}
        # Remove useless options
        if not no_check and cfg.get('toc-only'):
            if 'no-headers' in cfg:
                del cfg['no-headers']
            if 'outfile' in cfg:
                del cfg['outfile']      # defaults to STDOUT
            if cfg.get('target') == 'txt':
                del cfg['target']       # already default
            args.append('--toc-only')  # must be the first
            del cfg['toc-only']
        # Add target type
        if 'target' in cfg:
            args.append('-t '+cfg['target'])
            del cfg['target']
        # Add other options
        for key in cfg.keys():
            if key not in valid_opts: continue  # may be a %!setting
            if key == 'outfile' or key == 'infile': continue # later
            val = cfg[key]
            if not val: continue
            # Default values are useless on cmdline
            if val == dft_options.get(key): continue
            # -short format
            if key in use_short.keys():
                args.append('-'+use_short[key])
                continue
            # --long format
            if key in self.all_flags: # add --option
                args.append('--'+key)
            else:                     # add --option=value
                args.append('--%s=%s'%(key,val))
        # The outfile using -o
        if 'outfile' in cfg and \
           cfg['outfile'] != dft_options.get('outfile'):
            args.append('-o '+cfg['outfile'])
        # Place input file(s) always at the end
        if 'infile' in cfg:
            args.append(' '.join(cfg['infile']))
        # Return as a nice list
        Debug("Diet command line: %s"%' '.join(args), 1)
        return args

##############################################################################

class SourceDocument:
    """
    SourceDocument class - scan document structure, extract data

    It knows about full files. It reads a file and identify all
    the areas begining (Head,Conf,Body). With this info it can
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
    def __init__(self, filename='', contents=[]):
        self.areas = ['head','conf','body']
        self.arearef = []
        self.areas_fancy = ''
        self.filename = filename
        self.buffer = []
        if filename:
            self.scan_file(filename)
        elif contents:
            self.scan(contents)

    def split(self):
        "Returns all document parts, splitted into lists."
        return self.get('head'), self.get('conf'), self.get('body')

    def get(self, areaname):
        "Returns head|conf|body contents from self.buffer"
        # Sanity
        if areaname not in self.areas: return []
        if not self.buffer           : return []
        # Go get it
        bufini = 1
        bufend = len(self.buffer)
        if   areaname == 'head':
            ini = bufini
            end = self.arearef[1] or self.arearef[2] or bufend
        elif areaname == 'conf':
            ini = self.arearef[1]
            end = self.arearef[2] or bufend
        elif areaname == 'body':
            ini = self.arearef[2]
            end = bufend
        else:
            Error("Unknown Area name '%s'"%areaname)
        lines = self.buffer[ini:end]
        # Make sure head will always have 3 lines
        while areaname == 'head' and len(lines) < 3:
            lines.append('')
        return lines

    def scan_file(self, filename):
        Debug("source file: %s"%filename)
        Message(_("Loading source document"),1)
        buf = Readfile(filename, remove_linebreaks=1)
        self.scan(buf)

    def scan(self, lines):
        "Run through source file and identify head/conf/body areas"
        buf = lines
        if len(buf) == 0:
            Error(_('The input file is empty: %s')%self.filename)
        cfg_parser = ConfigLines().parse_line
        buf.insert(0, '')                         # text start at pos 1
        ref = [1,4,0]
        if not buf[1].strip():                    # no header
            ref[0] = 0 ; ref[1] = 2
        rgx = getRegexes()
        on_comment_block = 0
        for i in range(ref[1], len(buf)):         # find body init:
            # Handle comment blocks inside config area
            if not on_comment_block \
               and rgx['blockCommentOpen'].search(buf[i]):
                on_comment_block = 1
                continue
            if on_comment_block \
               and rgx['blockCommentOpen'].search(buf[i]):
                on_comment_block = 0
                continue
            if on_comment_block: continue

            if buf[i].strip() and (           # ... not blank and
               buf[i][0] != '%' or            # ... not comment or
               rgx['macros'].match(buf[i]) or # ... %%macro
               rgx['toc'].match(buf[i])    or # ... %%toc
               cfg_parser(buf[i],'include')[1]): # ... %!include
                ref[2] = i ; break
        if ref[1] == ref[2]: ref[1] = 0           # no conf area
        for i in 0,1,2:                           # del !existent
            if ref[i] >= len(buf): ref[i] = 0 # title-only
            if not ref[i]: self.areas[i] = ''
        Debug('Head,Conf,Body start line: %s'%ref)
        self.arearef = ref                        # save results
        self.buffer  = buf
        # Fancyness sample: head conf body (1 4 8)
        self.areas_fancy = "%s (%s)"%(
            ' '.join(self.areas),
            ' '.join(map(str, [x or '' for x in ref])))
        Message(_("Areas found: %s")%self.areas_fancy, 2)

    def get_raw_config(self):
        "Handy method to get the CONF area RAW config (if any)"
        if not self.areas.count('conf'): return []
        Message(_("Scanning source document CONF area"),1)
        raw = ConfigLines(
            file=self.filename, lines=self.get('conf'),
            first_line=self.arearef[1]).get_raw_config()
        Debug("document raw config: %s"%raw, 1)
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
      self.numeric     - List of keys which value must be a number
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
    def __init__(self, raw=[], target=''):
        self.raw          = raw
        self.target       = target
        self.parsed       = {}
        self.dft_options  = OPTIONS.copy()
        self.dft_flags    = FLAGS.copy()
        self.dft_actions  = ACTIONS.copy()
        self.dft_settings = SETTINGS.copy()
        self.defaults     = self._get_defaults()
        self.off          = self._get_off()
        self.incremental  = ['verbose']
        self.numeric      = ['toc-level','split']
        self.multi        = ['infile', 'preproc', 'postproc', 'options', 'style']

    def _get_defaults(self):
        "Get the default values for all config/options/flags"
        empty = {}
        for kw in CONFIG_KEYWORDS: empty[kw] = ''
        empty.update(self.dft_options)
        empty.update(self.dft_flags)
        empty.update(self.dft_actions)
        empty.update(self.dft_settings)
        empty['realcmdline'] = ''  # internal use only
        empty['sourcefile']  = ''  # internal use only
        return empty

    def _get_off(self):
        "Turns OFF all the config/options/flags"
        off = {}
        for key in self.defaults.keys():
            kind = type(self.defaults[key])
            if kind == int:
                off[key] = 0
            elif kind == str:
                off[key] = ''
            elif kind == list:
                off[key] = []
            else:
                Error('ConfigMaster: %s: Unknown type'+key)
        return off

    def _check_target(self):
        "Checks if the target is already defined. If not, do it"
        if not self.target:
            self.target = self.find_value('target')

    def get_target_raw(self):
        "Returns the raw config for self.target or 'all'"
        ret = []
        self._check_target()
        for entry in self.raw:
            if entry[0] == self.target or entry[0] == 'all':
                ret.append(entry)
        return ret

    def add(self, key, val):
        "Adds the key:value pair to the config dictionary (if needed)"
        # %!options
        if key == 'options':
            ignoreme = list(self.dft_actions.keys()) + ['target']
            ignoreme.remove('dump-config')
            ignoreme.remove('dump-source')
            raw_opts = CommandLine().get_raw_config(
                val, ignore=ignoreme)
            for target, key, val in raw_opts:
                self.add(key, val)
            return
        # The no- prefix turns OFF this key
        if key.startswith('no-'):
            key = key[3:]              # remove prefix
            val = self.off.get(key)    # turn key OFF
        # Is this key valid?
        if key not in self.defaults:
            Debug('Bogus Config %s:%s'%(key,val),1)
            return
        # Is this value the default one?
        if val == self.defaults.get(key):
            # If default value, remove previous key:val
            if key in self.parsed:
                del self.parsed[key]
            # Nothing more to do
            return
        # Flags ON comes empty. we'll add the 1 value now
        if val == '' and (
           key in self.dft_flags.keys() or
           key in self.dft_actions.keys()):
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
        fancykey = dotted_spaces("%12s"%key)
        Message(_("Added config %s : %s")%(fancykey,val),3)

    def get_outfile_name(self, config={}):
        "Dirname is the same for {in,out}file"
        infile, outfile = config['sourcefile'], config['outfile']
        if outfile and outfile not in (STDOUT, MODULEOUT) \
           and not os.path.isabs(outfile):
            outfile = os.path.join(os.path.dirname(infile), outfile)
        if infile == STDIN    and not outfile: outfile = STDOUT
        if infile == MODULEIN and not outfile: outfile = MODULEOUT
        if not outfile and (infile and config.get('target')):
            basename = re.sub('\.(txt|t2t)$','',infile)
            outfile = "%s.%s"%(basename, config['target'])
        Debug(" infile: '%s'"%infile , 1)
        Debug("outfile: '%s'"%outfile, 1)
        return outfile

    def sanity(self, config, gui=0):
        "Basic config sanity checking"
        if not config: return {}
        target = config.get('target')
        # Some actions don't require target specification
        if not target:
            for action in NO_TARGET:
                if config.get(action):
                    target = 'txt'
                    break
        # On GUI, some checking are skipped
        if not gui:
            # We *need* a target
            if not target:
                Error(_('No target specified (try --help)') + '\n\n' +
                _('Maybe trying to convert an old v1.x file?'))
            # And of course, an infile also
            if not config.get('infile'):
                Error(_('Missing input file (try --help)'))
            # Is the target valid?
            if not TARGETS.count(target):
                Error(_("Invalid target '%s' (try --help)") % target)
        # Ensure all keys are present
        empty = self.defaults.copy() ; empty.update(config)
        config = empty.copy()
        # Check integers options
        for key in config:
            if key in self.numeric:
                try: config[key] = int(config[key])
                except: Error(_('--%s value must be a number') % key)
        # Check split level value
        if config['split'] not in (0,1,2):
            Error(_('Option --split must be 0, 1 or 2'))
        # --toc-only is stronger than others
        if config['toc-only']:
            config['headers'] = 0
            config['toc']     = 0
            config['split']   = 0
            config['gui']     = 0
            config['outfile'] = config['outfile'] or STDOUT
        # Splitting is disable for now (future: HTML only, no STDOUT)
        config['split'] = 0
        # Restore target
        config['target'] = target
        # Set output file name
        config['outfile'] = self.get_outfile_name(config)
        # Checking suicide
        if config['sourcefile'] == config['outfile'] and \
           config['outfile'] not in [STDOUT,MODULEOUT] and not gui:
            Error(_("Input and Output files are the same: %s") % config['outfile'])
        return config

    def parse(self):
        "Returns the parsed config for the current target"
        raw = self.get_target_raw()
        for target, key, value in raw:
            self.add(key, value)
        Message(_("Added the following keys: %s") % ', '.join(self.parsed.keys()), 2)
        return self.parsed.copy()

    def find_value(self, key='', target=''):
        "Scans ALL raw config to find the desired key"
        ret = []
        # Scan and save all values found
        for targ, k, val in self.raw:
            if k == key and (targ == target or targ == 'all'):
                ret.append(val)
        if not ret: return ''
        # If not multi value, return only the last found
        if key in self.multi: return ret
        else                : return ret[-1]

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
    def __init__(self, file='', lines=[], first_line=1):
        self.file = file or 'NOFILE'
        self.lines = lines
        self.first_line = first_line

    def load_lines(self):
        "Make sure we've loaded the file contents into buffer"
        if not self.lines and not self.file:
            Error("ConfigLines: No file or lines provided")
        if not self.lines:
            self.lines = self.read_config_file(self.file)

    def read_config_file(self, filename=''):
        "Read a Config File contents, aborting on invalid line"
        if not filename: return []
        errormsg = _("Invalid CONFIG line on %s")+"\n%03d:%s"
        lines = Readfile(filename, remove_linebreaks=1)
        # Sanity: try to find invalid config lines
        for i in range(len(lines)):
            line = lines[i].rstrip()
            if not line: continue  # empty
            if line[0] != '%': Error(errormsg%(filename,i+1,line))
        return lines

    def include_config_file(self, file=''):
        "Perform the %!includeconf action, returning RAW config"
        if not file: return []
        # Current dir relative to the current file (self.file)
        current_dir = os.path.dirname(self.file)
        file = os.path.join(current_dir, file)
        # Read and parse included config file contents
        lines = self.read_config_file(file)
        return ConfigLines(file=file, lines=lines).get_raw_config()

    def get_raw_config(self):
        "Scan buffer and extract all config as RAW (including includes)"
        ret = []
        self.load_lines()
        first = self.first_line
        for i in range(len(self.lines)):
            line = self.lines[i]
            Message(_("Processing line %03d: %s")%(first+i,line),2)
            target, key, val = self.parse_line(line)
            if not key: continue    # no config on this line
            if key == 'includeconf':
                err = _('A file cannot include itself (loop!)')
                if val == self.file:
                    Error("%s: %%!includeconf: %s" % (err, self.file))
                more_raw = self.include_config_file(val)
                ret.extend(more_raw)
                Message(_("Finished Config file inclusion: %s") % val, 2)
            else:
                ret.append([target, key, val])
                Message(_("Added %s")%key,3)
        return ret

    def parse_line(self, line='', keyname='', target=''):
        "Detects %!key:val config lines and extract data from it"
        empty = ['', '', '']
        if not line: return empty
        no_target = ['target', 'includeconf']
        re_name   = keyname or '[a-z]+'
        re_target = target  or '[a-z]*'
        # XXX TODO <value>\S.+?  requires TWO chars, breaks %!include:a
        cfgregex  = re.compile("""
            ^%%!\s*               # leading id with opt spaces
            (?P<name>%s)\s*       # config name
            (\((?P<target>%s)\))? # optional target spec inside ()
            \s*:\s*               # key:value delimiter with opt spaces
            (?P<value>\S.+?)      # config value
            \s*$                  # rstrip() spaces and hit EOL
            """%(re_name, re_target), re.I+re.VERBOSE)
        prepostregex = re.compile("""
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
            """, re.VERBOSE)
        guicolors = re.compile("^([^\s]+\s+){3}[^\s]+") # 4 tokens
        match = cfgregex.match(line)
        if not match: return empty

        name   = (match.group('name') or '').lower()
        target = (match.group('target') or 'all').lower()
        value  = match.group('value')

        # NO target keywords: force all targets
        if name in no_target: target = 'all'

        # Special config for GUI colors
        if name == 'guicolors':
            valmatch = guicolors.search(value)
            if not valmatch: return empty
            value = re.split('\s+', value)

        # Special config with two quoted values (%!preproc: "foo" 'bar')
        if name == 'preproc' or name == 'postproc':
            valmatch = prepostregex.search(value)
            if not valmatch: return empty
            getval = valmatch.group
            patt   = getval(2) or getval(3) or getval(4) or ''
            repl   = getval(6) or getval(7) or getval(8) or ''
            value  = (patt, repl)
        return [target, name, value]

##############################################################################

class MaskMaster:
    "(Un)Protect important structures from escaping and formatting"
    def __init__(self):
        self.linkmask  = 'vvvLINKvvv'
        self.monomask  = 'vvvMONOvvv'
        self.macromask = 'vvvMACROvvv'
        self.rawmask   = 'vvvRAWvvv'
        self.taggedmask= 'vvvTAGGEDvvv'
        self.tocmask   = 'vvvTOCvvv'
        self.macroman  = MacroMaster()
        self.reset()

    def reset(self):
        self.linkbank = []
        self.monobank = []
        self.macrobank = []
        self.rawbank = []
        self.taggedbank = []

    def mask(self, line=''):
        global AUTOTOC

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
                t = regex['tagged'].search(line).start()
            except:
                t = -1

            try:
                r = regex['raw'].search(line).start()
            except:
                r = -1

            try:
                v = regex['fontMono'].search(line).start()
            except:
                v = -1

            # Protect tagged text
            if t >= 0 and (r == -1 or t < r) and (v == -1 or t < v):
                txt = regex['tagged'].search(line).group(1)
                ## Jendrik
                if TARGET == 'tex':
                    txt = txt.replace('_', 'vvvUnderscoreInTaggedTextvvv')
                self.taggedbank.append(txt)
                line = regex['tagged'].sub(self.taggedmask,line,1)

            # Protect raw text
            elif r >= 0 and (t == -1 or r < t) and (v == -1 or r < v):
                txt = regex['raw'].search(line).group(1)
                txt = doEscape(TARGET,txt)
                ## Jendrik
                if TARGET == 'tex':
                    txt = txt.replace('_', 'vvvUnderscoreInRawTextvvv')

                self.rawbank.append(txt)
                line = regex['raw'].sub(self.rawmask,line,1)

            # Protect verbatim text
            elif v >= 0 and (t == -1 or v < t) and (r == -1 or v < r):
                txt = regex['fontMono'].search(line).group(1)
                txt = doEscape(TARGET,txt)
                self.monobank.append(txt)
                line = regex['fontMono'].sub(self.monomask,line,1)
            else:
                break

        # Protect macros
        while regex['macros'].search(line):
            txt = regex['macros'].search(line).group()
            self.macrobank.append(txt)
            line = regex['macros'].sub(self.macromask,line,1)

        # Protect TOC location
        while regex['toc'].search(line):
            line = regex['toc'].sub(self.tocmask,line)
            AUTOTOC = 0

        # Protect URLs and emails
        while regex['linkmark'].search(line) or \
              regex['link'    ].search(line):

            # Try to match plain or named links
            match_link  = regex['link'].search(line)
            match_named = regex['linkmark'].search(line)

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
            if m == match_link:              # plain link
                link = m.group()
                label = ''
                link_re = regex['link']
            else:                            # named link
                link = m.group('link')
                label = m.group('label').rstrip()
                link_re = regex['linkmark']
            line = link_re.sub(self.linkmask,line,1)

            # Save link data to the link bank
            self.linkbank.append((label, link))
        return line

    def undo(self, line):

        # url & email
        for label,url in self.linkbank:
            link = get_tagged_link(label, url)
            line = line.replace(self.linkmask, link, 1)

        # Expand macros
        for macro in self.macrobank:
            macro = self.macroman.expand(macro)
            line = line.replace(self.macromask, macro, 1)

        # Expand verb
        for mono in self.monobank:
            open,close = TAGS['fontMonoOpen'],TAGS['fontMonoClose']
            line = line.replace(self.monomask, open+mono+close, 1)

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
        self.count = ['',0,0,0,0,0]
        self.toc   = []
        self.level = 0
        self.kind  = ''
        self.txt   = ''
        self.label = ''
        self.tag   = ''
        self.tag_hold = []
        self.last_level = 0
        self.count_id = ''
        self.user_labels = {}
        self.anchor_count = 0
        self.anchor_prefix = 'toc'

    def _open_close_blocks(self):
        "Open new title blocks, closing the previous (if any)"
        if not rules['titleblocks']: return
        tag = ''
        last = self.last_level
        curr = self.level

        # Same level, just close the previous
        if curr == last:
            tag = TAGS.get('title%dClose'%last)
            if tag: self.tag_hold.append(tag)

        # Section -> subsection, more depth
        while curr > last:
            last += 1

            # Open the new block of subsections
            tag = TAGS.get('blockTitle%dOpen'%last)
            if tag: self.tag_hold.append(tag)

            # Jump from title1 to title3 or more
            # Fill the gap with an empty section
            if curr - last > 0:
                tag = TAGS.get('title%dOpen'%last)
                tag = regex['x'].sub('', tag)      # del \a
                if tag: self.tag_hold.append(tag)

        # Section <- subsection, less depth
        while curr < last:
            # Close the current opened subsection
            tag = TAGS.get('title%dClose'%last)
            if tag: self.tag_hold.append(tag)

            # Close the current opened block of subsections
            tag = TAGS.get('blockTitle%dClose'%last)
            if tag: self.tag_hold.append(tag)

            last -= 1

            # Close the previous section of the same level
            # The subsections were under it
            if curr == last:
                tag = TAGS.get('title%dClose'%last)
                if tag: self.tag_hold.append(tag)

    def add(self, line):
        "Parses a new title line."
        if not line: return
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
            tag = TAGS.get('title%dClose'%self.level)
            if tag: ret.append(tag)
            tag = TAGS.get('blockTitle%dClose'%self.level)
            if tag: ret.append(tag)
            self.level -= 1
        return ret

    def _save_toc_info(self):
        "Save TOC info, used by self.dump_marked_toc()"
        self.toc.append((self.level, self.count_id, self.txt, self.label))

    def _set_prop(self, line=''):
        "Extract info from original line and set data holders."
        # Detect title type (numbered or not)
        id = line.lstrip()[0]
        if   id == '=': kind = 'title'
        elif id == '+': kind = 'numtitle'
        else: Error("Unknown Title ID '%s'"%id)
        # Extract line info
        match = regex[kind].search(line)
        level = len(match.group('id'))
        txt   = match.group('txt').strip()
        label = match.group('label')
        # Parse info & save
        if CONF['enum-title']: kind = 'numtitle'  # force
        if rules['titleblocks']:
            self.tag = TAGS.get('%s%dOpen'%(kind,level)) or \
                       TAGS.get('title%dOpen'%level)
        else:
            self.tag = TAGS.get(kind+repr(level)) or \
                       TAGS.get('title'+repr(level))
        self.last_level = self.level
        self.kind  = kind
        self.level = level
        self.txt   = txt
        self.label = label

    def _set_count_id(self):
        "Compose and save the title count identifier (if needed)."
        count_id = ''
        if self.kind == 'numtitle' and not rules['autonumbertitle']:
            # Manually increase title count
            self.count[self.level] += 1
            # Reset sublevels count (if any)
            max_levels = len(self.count)
            if self.level < max_levels-1:
                for i in range(self.level+1, max_levels):
                    self.count[i] = 0
            # Compose count id from hierarchy
            for i in range(self.level):
                count_id= "%s%d."%(count_id, self.count[i+1])
        self.count_id = count_id

    def _set_label(self):
        "Compose and save title label, used by anchors."
        # Remove invalid chars from label set by user
        self.label = re.sub('[^A-Za-z0-9_-]', '', self.label or '')
        # Generate name as 15 first :alnum: chars
        #TODO how to translate safely accented chars to plain?
        #self.label = re.sub('[^A-Za-z0-9]', '', self.txt)[:15]
        # 'tocN' label - sequential count, ignoring 'toc-level'
        #self.label = self.anchor_prefix + str(len(self.toc)+1)

    def _get_tagged_anchor(self):
        "Return anchor if user defined a label, or TOC is on."
        ret = ''
        label = self.label
        if CONF['toc'] and self.level <= CONF['toc-level']:
            # This count is needed bcos self.toc stores all
            # titles, regardless of the 'toc-level' setting,
            # so we can't use self.toc length to number anchors
            self.anchor_count += 1
            # Autonumber label (if needed)
            label = label or '%s%s' % (self.anchor_prefix, self.anchor_count)
        if label and TAGS['anchor']:
            ret = regex['x'].sub(label,TAGS['anchor'])
        return ret

    def _get_full_title_text(self):
        "Returns the full title contents, already escaped."
        ret = self.txt
        # Insert count_id (if any) before text
        if self.count_id:
            ret = '%s %s'%(self.count_id, ret)
        # Escape specials
        ret = doEscape(TARGET, ret)
        # Same targets needs final escapes on title lines
        # It's here because there is a 'continue' after title
        if rules['finalescapetitle']:
            ret = doFinalEscape(TARGET, ret)
        return ret

    def get(self):
        "Returns the tagged title as a list."
        ret = []

        # Maybe some anchoring before?
        anchor = self._get_tagged_anchor()
        self.tag = regex['_anchor'].sub(anchor, self.tag)

        ### Compose & escape title text (TOC uses unescaped)
        full_title = self._get_full_title_text()

        # Close previous section area
        ret.extend(self.tag_hold)
        self.tag_hold = []

        tagged = regex['x'].sub(full_title, self.tag)

        # Adds "underline" on TXT target
        if TARGET == 'txt':
            if BLOCK.count > 1: ret.append('') # blank line before
            ret.append(tagged)
            # Get the right letter count for UTF
            if CONF['encoding'].lower() == 'utf-8':
                i = len(full_title.decode('utf-8'))
            else:
                i = len(full_title)
            ret.append(regex['x'].sub('='*i, self.tag))
        elif TARGET == 'art' and self.level == 1:
            if BLOCK.count > 1: ret.append('') # blank line before
            ret.append(aa_box(tagged))
        elif TARGET == 'art':
            level = 'level'+str(self.level)
            if BLOCK.count > 1: ret.append('') # blank line before
            ret.append(tagged)
            ret.append(AA_CHARS[level]*len(full_title))
        else:
            ret.append(tagged)
        return ret

    def dump_marked_toc(self, max_level=99):
        "Dumps all toc itens as a valid t2t markup list"
        ret = []
        toc_count = 1
        for level, count_id, txt, label in self.toc:
            if level > max_level: continue   # ignore
            indent = '  '*level
            id_txt = ('%s %s'%(count_id, txt)).lstrip()
            label = label or self.anchor_prefix+repr(toc_count)
            toc_count += 1
            # TOC will have links
            if TAGS['anchor']:
                # TOC is more readable with master topics
                # not linked at number. This is a stoled
                # idea from Windows .CHM help files
                if CONF['enum-title'] and level == 1:
                    tocitem = '%s+ [""%s"" #%s]' % (indent, txt, label)
                else:
                    tocitem = '%s- [""%s"" #%s]' % (indent, id_txt, label)
            # No links on TOC, just text
            else:
                # man don't reformat TOC lines, cool!
                if TARGET in ['txt', 'man', 'art']:
                    tocitem = '%s""%s""' % (indent, id_txt)
                else:
                    tocitem = '%s- ""%s""' % (indent, id_txt)
            ret.append(tocitem)
        return ret


##############################################################################

#TODO check all this table mess
# Trata linhas TABLE, com as prop do parse_row
# O metodo table() do BLOCK xunxa e troca as celulas pelas parseadas
class TableMaster:
    def __init__(self, line=''):
        self.rows      = []
        self.border    = 0
        self.align     = 'Left'
        self.cellalign = []
        self.colalign  = []
        self.cellspan  = []
        if line:
            prop = self.parse_row(line)
            self.border    = prop['border']
            self.align     = prop['align']
            self.cellalign = prop['cellalign']
            self.cellspan  = prop['cellspan']
            self.colalign  = self._get_col_align()

    def _get_col_align(self):
        colalign = []
        for cell in range(0,len(self.cellalign)):
            align = self.cellalign[cell]
            span  = self.cellspan[cell]
            colalign.extend([align] * span)
        return colalign

    def _get_open_tag(self):
        topen     = TAGS['tableOpen']
        tborder   = TAGS['_tableBorder']
        talign    = TAGS['_tableAlign'+self.align]
        calignsep = TAGS['tableColAlignSep']
        calign    = ''

        # The first line defines if table has border or not
        if not self.border: tborder = ''
        # Set the columns alignment
        if rules['tablecellaligntype'] == 'column':
            calign = [TAGS['_tableColAlign%s'%x] for x in self.colalign]
            calign = calignsep.join(calign)
        # Align full table, set border and Column align (if any)
        topen = regex['_tableAlign'   ].sub(talign , topen)
        topen = regex['_tableBorder'  ].sub(tborder, topen)
        topen = regex['_tableColAlign'].sub(calign , topen)
        # Tex table spec, border or not: {|l|c|r|} , {lcr}
        if calignsep and not self.border:
            # Remove cell align separator
            topen = topen.replace(calignsep, '')
        return topen

    def _get_cell_align(self, cells):
        ret = []
        for cell in cells:
            align = 'Left'
            if cell.strip():
                if cell[0] == ' ' and cell[-1] == ' ':
                    align = 'Center'
                elif cell[0] == ' ':
                    align = 'Right'
            ret.append(align)
        return ret

    def _get_cell_span(self, cells):
        ret = []
        for cell in cells:
            span = 1
            m = re.search('\a(\|+)$', cell)
            if m: span = len(m.group(1))+1
            ret.append(span)
        return ret

    def _tag_cells(self, rowdata):
        row = []
        cells  = rowdata['cells']
        open   = TAGS['tableCellOpen']
        close  = TAGS['tableCellClose']
        sep    = TAGS['tableCellSep']
        calign    = [TAGS['_tableCellAlign'+x] for x in rowdata['cellalign']]
        calignsep = TAGS['tableColAlignSep']
        ncolumns = len(self.colalign)

        # Populate the span and multicol open tags
        cspan = []
        multicol = []
        colindex = 0
        for cellindex in range(0,len(rowdata['cellspan'])):

            span = rowdata['cellspan'][cellindex]
            align = rowdata['cellalign'][cellindex]

            if span > 1:
                cspan.append(regex['x'].sub(
                str(span), TAGS['_tableCellColSpan']))

                mcopen = regex['x'].sub(str(span), TAGS['_tableCellMulticolOpen'])
                multicol.append(mcopen)
            else:
                cspan.append('')

                if colindex < ncolumns and align != self.colalign[colindex]:
                    mcopen = regex['x'].sub('1', TAGS['_tableCellMulticolOpen'])
                    multicol.append(mcopen)
                else:
                    multicol.append('')

            if not self.border:
                multicol[-1] = multicol[-1].replace(calignsep, '')

            colindex += span

        # Maybe is it a title row?
        if rowdata['title']:
            open  = TAGS['tableTitleCellOpen']  or open
            close = TAGS['tableTitleCellClose'] or close
            sep   = TAGS['tableTitleCellSep']   or sep

        # Should we break the line on *each* table cell?
        if rules['breaktablecell']: close = close+'\n'

        # Cells pre processing
        if rules['tablecellstrip']:
            cells = [x.strip() for x in cells]
        if rowdata['title'] and rules['tabletitlerowinbold']:
            cells = [enclose_me('fontBold',x) for x in cells]

        # Add cell BEGIN/END tags
        for cell in cells:
            copen = open
            cclose = close
            # Make sure we will pop from some filled lists
            # Fixes empty line bug '| |'
            this_align = this_span = this_mcopen = ''
            if calign: this_align = calign.pop(0)
            if cspan : this_span = cspan.pop(0)
            if multicol: this_mcopen = multicol.pop(0)

            # Insert cell align into open tag (if cell is alignable)
            if rules['tablecellaligntype'] == 'cell':
                copen = regex['_tableCellAlign'].sub(
                    this_align, copen)

            # Insert cell span into open tag (if cell is spannable)
            if rules['tablecellspannable']:
                copen = regex['_tableCellColSpan'].sub(
                    this_span, copen)

            # Use multicol tags instead (if multicol supported, and if
            # cell has a span or is aligned differently to column)
            if rules['tablecellmulticol']:
                if this_mcopen:
                    copen = regex['_tableColAlign'].sub(this_align, this_mcopen)
                    cclose = TAGS['_tableCellMulticolClose']

            row.append(copen + cell + cclose)

        # Maybe there are cell separators?
        return sep.join(row)

    def add_row(self, cells):
        self.rows.append(cells)

    def parse_row(self, line):
        # Default table properties
        ret = {
            'border':0, 'title':0, 'align':'Left',
            'cells':[], 'cellalign':[], 'cellspan':[]
        }
        # Detect table align (and remove spaces mark)
        if line[0] == ' ': ret['align'] = 'Center'
        line = line.lstrip()
        # Detect title mark
        if line[1] == '|': ret['title'] = 1
        # Detect border mark and normalize the EOL
        m = re.search(' (\|+) *$', line)
        if m: line = line+' ' ; ret['border'] = 1
        else: line = line+' | '
        # Delete table mark
        line = regex['table'].sub('', line)
        # Detect colspan  | foo | bar baz |||
        line = re.sub(' (\|+)\| ', '\a\\1 | ', line)
        # Split cells (the last is fake)
        ret['cells'] = line.split(' | ')[:-1]
        # Find cells span
        ret['cellspan'] = self._get_cell_span(ret['cells'])
        # Remove span ID
        ret['cells'] = [re.sub('\a\|+$','',x) for x in ret['cells']]
        # Find cells align
        ret['cellalign'] = self._get_cell_align(ret['cells'])
        # Hooray!
        Debug('Table Prop: %s' % ret, 7)
        return ret

    def dump(self):
        open  = self._get_open_tag()
        rows  = self.rows
        close = TAGS['tableClose']

        rowopen     = TAGS['tableRowOpen']
        rowclose    = TAGS['tableRowClose']
        rowsep      = TAGS['tableRowSep']
        titrowopen  = TAGS['tableTitleRowOpen']  or rowopen
        titrowclose = TAGS['tableTitleRowClose'] or rowclose

        if rules['breaktablelineopen']:
            rowopen = rowopen + '\n'
            titrowopen = titrowopen + '\n'

        # Tex gotchas
        if TARGET == 'tex':
            if not self.border:
                rowopen = titrowopen = ''
            else:
                close = rowopen + close

        # Now we tag all the table cells on each row
        #tagged_cells = map(lambda x: self._tag_cells(x), rows) #!py15
        tagged_cells = []
        for cell in rows: tagged_cells.append(self._tag_cells(cell))

        # Add row separator tags between lines
        tagged_rows = []
        if rowsep:
            #!py15
            #tagged_rows = map(lambda x:x+rowsep, tagged_cells)
            for cell in tagged_cells:
                tagged_rows.append(cell+rowsep)
            # Remove last rowsep, because the table is over
            tagged_rows[-1] = tagged_rows[-1].replace(rowsep, '')
        # Add row BEGIN/END tags for each line
        else:
            for rowdata in rows:
                if rowdata['title']:
                    o,c = titrowopen, titrowclose
                else:
                    o,c = rowopen, rowclose
                row = tagged_cells.pop(0)
                tagged_rows.append(o + row + c)

        # Join the pieces together
        fulltable = []
        if open: fulltable.append(open)
        fulltable.extend(tagged_rows)
        if close: fulltable.append(close)

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
        self.last = ''
        self.tableparser = None
        self.contains = {
            'para'    :['comment','raw','tagged'],
            'verb'    :[],
            'table'   :['comment'],
            'raw'     :[],
            'tagged'  :[],
            'comment' :[],
            'quote'   :['quote','comment','raw','tagged'],
            'list'    :['list','numlist','deflist','para','verb','comment','raw','tagged'],
            'numlist' :['list','numlist','deflist','para','verb','comment','raw','tagged'],
            'deflist' :['list','numlist','deflist','para','verb','comment','raw','tagged'],
            'bar'     :[],
            'title'   :[],
            'numtitle':[],
        }
        self.allblocks = list(self.contains.keys())

        # If one is found inside another, ignore the marks
        self.exclusive = ['comment','verb','raw','tagged']

        # May we include bars inside quotes?
        if rules['barinsidequote']:
            self.contains['quote'].append('bar')

    def block(self):
        if not self.BLK: return ''
        return self.BLK[-1]

    def isblock(self, name=''):
        return self.block() == name

    def prop(self, key):
        if not self.PRP: return ''
        return self.PRP[-1].get(key) or ''

    def propset(self, key, val):
        self.PRP[-1][key] = val
        #Debug('BLOCK prop ++: %s->%s'%(key,repr(val)), 1)
        #Debug('BLOCK props: %s'%(repr(self.PRP)), 1)

    def hold(self):
        if not self.HLD: return []
        return self.HLD[-1]

    def holdadd(self, line):
        if self.block().endswith('list'): line = [line]
        self.HLD[-1].append(line)
        #Debug('HOLD add: %s'%repr(line), 4)
        #Debug('FULL HOLD: %s'%self.HLD, 4)

    def holdaddsub(self, line):
        self.HLD[-1][-1].append(line)
        Debug('HOLD addsub: %s'%repr(line), 4)
        Debug('FULL HOLD: %s'%self.HLD, 4)

    def holdextend(self, lines):
        if self.block().endswith('list'): lines = [lines]
        self.HLD[-1].extend(lines)
        Debug('HOLD extend: %s'%repr(lines), 4)
        Debug('FULL HOLD: %s'%self.HLD, 4)

    def blockin(self, block):
        ret = []
        if block not in self.allblocks:
            Error("Invalid block '%s'"%block)

        # First, let's close other possible open blocks
        while self.block() and block not in self.contains[self.block()]:
            ret.extend(self.blockout())

        # Now we can gladly add this new one
        self.BLK.append(block)
        self.HLD.append([])
        self.PRP.append({})
        self.count += 1
        if block == 'table': self.tableparser = TableMaster()
        # Deeper and deeper
        self.depth = len(self.BLK)
        Debug('block ++ (%s): %s' % (block,self.BLK), 3)
        return ret

    def blockout(self):
        if not self.BLK: Error('No block to pop')
        blockname = self.BLK.pop()
        result = getattr(self, blockname)()
        parsed = self.HLD.pop()
        self.PRP.pop()
        self.depth = len(self.BLK)
        if blockname == 'table': del self.tableparser

        # Inserting a nested block into mother
        if self.block():
            if blockname != 'comment': # ignore comment blocks
                if self.block().endswith('list'):
                    self.HLD[-1][-1].append(result)
                else:
                    self.HLD[-1].append(result)
            # Reset now. Mother block will have it all
            result = []

        Debug('block -- (%s): %s' % (blockname,self.BLK), 3)
        Debug('RELEASED (%s): %s' % (blockname,parsed), 3)

        # Save this top level block name (produced output)
        # The next block will use it
        if result:
            self.last = blockname
            Debug('BLOCK: %s'%result, 6)

        return result

    def _last_escapes(self, line):
        return doFinalEscape(TARGET, line)

    def _get_escaped_hold(self):
        ret = []
        for line in self.hold():
            linetype = type(line)
            if linetype == str:
                ret.append(self._last_escapes(line))
            elif linetype == list:
                ret.extend(line)
            else:
                Error("BlockMaster: Unknown HOLD item type: %s" % linetype)
        return ret

    def _remove_twoblanks(self, lastitem):
        if len(lastitem) > 1 and lastitem[-2:] == ['','']:
            return lastitem[:-2]
        return lastitem

    def _should_add_blank_line(self, where, blockname):
        "Validates the blanksaround* rules"

        # Nestable blocks: only mother blocks (level 1) are spaced
        if blockname.endswith('list') and self.depth > 1:
            return False

        # The blank line after the block is always added
        if where == 'after' \
            and rules['blanksaround'+blockname]:
            return True

        # The blank line before the block is only added if
        # the previous block haven't added a blank line
        # (to avoid consecutive blanks)
        elif where == 'before' \
            and rules['blanksaround'+blockname] \
            and not rules.get('blanksaround'+self.last):
            return True

        # Nested quotes are handled here,
        # because the mother quote isn't closed yet
        elif where == 'before' \
            and blockname == 'quote' \
            and rules['blanksaround'+blockname] \
            and self.depth > 1:
            return True

        return False

    def comment(self):
        return ''

    def raw(self):
        lines = self.hold()
        return [doEscape(TARGET, x) for x in lines]

    def tagged(self):
        return self.hold()

    def para(self):
        result = []
        open  = TAGS['paragraphOpen']
        close = TAGS['paragraphClose']
        lines = self._get_escaped_hold()

        # Blank line before?
        if self._should_add_blank_line('before', 'para'): result.append('')

        # Open tag
        if open: result.append(open)

        # Pagemaker likes a paragraph as a single long line
        if rules['onelinepara']:
            result.append(' '.join(lines))
        # Others are normal :)
        else:
            result.extend(lines)

        # Close tag
        if close: result.append(close)

        # Blank line after?
        if self._should_add_blank_line('after', 'para'): result.append('')

        # Very very very very very very very very very UGLY fix
        # Needed because <center> can't appear inside <p>
        try:
            if len(lines) == 1 and \
               TARGET in ('html', 'xhtml') and \
               re.match('^\s*<center>.*</center>\s*$', lines[0]):
                result = [lines[0]]
        except: pass

        return result

    def verb(self):
        "Verbatim lines are not masked, so there's no need to unmask"
        result = []
        open  = TAGS['blockVerbOpen']
        close = TAGS['blockVerbClose']

        # Blank line before?
        if self._should_add_blank_line('before', 'verb'): result.append('')

        # Open tag
        if open: result.append(open)

        # Get contents
        for line in self.hold():
            if self.prop('mapped') == 'table':
                line = MacroMaster().expand(line)
            if not rules['verbblocknotescaped']:
                line = doEscape(TARGET,line)
            if rules['indentverbblock']:
                line = '  '+line
            if rules['verbblockfinalescape']:
                line = doFinalEscape(TARGET, line)
            result.append(line)

        # Close tag
        if close: result.append(close)

        # Blank line after?
        if self._should_add_blank_line('after', 'verb'): result.append('')

        return result

    def numtitle(self): return self.title('numtitle')
    def title(self, name='title'):
        result = []

        # Blank line before?
        if self._should_add_blank_line('before', name): result.append('')

        # Get contents
        result.extend(TITLE.get())

        # Blank line after?
        if self._should_add_blank_line('after', name): result.append('')

        return result

    def table(self):
        result = []

        # Blank line before?
        if self._should_add_blank_line('before', 'table'): result.append('')

        # Rewrite all table cells by the unmasked and escaped data
        lines = self._get_escaped_hold()
        for i in range(len(lines)):
            cells = lines[i].split(SEPARATOR)
            self.tableparser.rows[i]['cells'] = cells
        result.extend(self.tableparser.dump())

        # Blank line after?
        if self._should_add_blank_line('after', 'table'): result.append('')

        return result

    def quote(self):
        result = []
        open   = TAGS['blockQuoteOpen']            # block based
        close  = TAGS['blockQuoteClose']
        qline  = TAGS['blockQuoteLine']            # line based
        indent = tagindent = '\t'*self.depth

        # Apply rules
        if rules['tagnotindentable']: tagindent = ''
        if not rules['keepquoteindent']: indent = ''

        # Blank line before?
        if self._should_add_blank_line('before', 'quote'): result.append('')

        # Open tag
        if open: result.append(tagindent+open)

        # Get contents
        for item in self.hold():
            if type(item) == type([]):
                result.extend(item)        # subquotes
            else:
                item = regex['quote'].sub('', item)  # del TABs
                item = self._last_escapes(item)
                item = qline*self.depth + item
                result.append(indent+item) # quote line

        # Close tag
        if close: result.append(tagindent+close)

        # Blank line after?
        if self._should_add_blank_line('after', 'quote'): result.append('')

        return result

    def bar(self):
        result = []
        bar_tag = ''

        # Blank line before?
        if self._should_add_blank_line('before', 'bar'): result.append('')

        # Get the original bar chars
        bar_chars = self.hold()[0].strip()

        # Set bar type
        if bar_chars.startswith('='): bar_tag = TAGS['bar2']
        else                        : bar_tag = TAGS['bar1']

        # To avoid comment tag confusion like <!-- ------ --> (sgml)
        if TAGS['comment'].count('--'):
            bar_chars = bar_chars.replace('--', '__')

        # Get the bar tag (may contain \a)
        result.append(regex['x'].sub(bar_chars, bar_tag))

        # Blank line after?
        if self._should_add_blank_line('after', 'bar'): result.append('')

        return result

    def deflist(self): return self.list('deflist')
    def numlist(self): return self.list('numlist')
    def list(self, name='list'):
        result    = []
        items     = self.hold()
        indent    = self.prop('indent')
        tagindent = indent
        listline  = TAGS.get(name+'ItemLine')
        itemcount = 0

        if name == 'deflist':
            itemopen  = TAGS[name+'Item1Open']
            itemclose = TAGS[name+'Item2Close']
            itemsep   = TAGS[name+'Item1Close']+\
                        TAGS[name+'Item2Open']
        else:
            itemopen  = TAGS[name+'ItemOpen']
            itemclose = TAGS[name+'ItemClose']
            itemsep   = ''

        # Apply rules
        if rules['tagnotindentable']: tagindent = ''
        if not rules['keeplistindent']: indent = tagindent = ''

        # ItemLine: number of leading chars identifies list depth
        if listline:
            itemopen  = listline*self.depth + itemopen

        # Adds trailing space on opening tags
        if (name == 'list'    and rules['spacedlistitemopen']) or \
           (name == 'numlist' and rules['spacednumlistitemopen']):
            itemopen = itemopen + ' '

        # Remove two-blanks from list ending mark, to avoid <p>
        items[-1] = self._remove_twoblanks(items[-1])

        # Blank line before?
        if self._should_add_blank_line('before', name): result.append('')

        # Tag each list item (multiline items), store in listbody
        itemopenorig = itemopen
        listbody = []
        widelist = 0
        for item in items:

            # Add "manual" item count for noautonum targets
            itemcount += 1
            if name == 'numlist' and not rules['autonumberlist']:
                n = str(itemcount)
                itemopen = regex['x'].sub(n, itemopenorig)
                del n

            # Tag it
            item[0] = self._last_escapes(item[0])
            if name == 'deflist':
                z,term,rest = item[0].split(SEPARATOR, 2)
                item[0] = rest
                if not item[0]: del item[0]      # to avoid <p>
                listbody.append(tagindent+itemopen+term+itemsep)
            else:
                fullitem = tagindent+itemopen
                listbody.append(item[0].replace(SEPARATOR, fullitem))
                del item[0]

            # Process next lines for this item (if any)
            for line in item:
                if type(line) == type([]): # sublist inside
                    listbody.extend(line)
                else:
                    line = self._last_escapes(line)

                    # Blank lines turns to <p>
                    if not line and rules['parainsidelist']:
                        line = indent + TAGS['paragraphOpen'] + TAGS['paragraphClose']
                        line = line.rstrip()
                        widelist = 1

                    # Some targets don't like identation here (wiki)
                    if not rules['keeplistindent'] or (name == 'deflist' and rules['deflisttextstrip']):
                        line = line.lstrip()

                    # Maybe we have a line prefix to add? (wiki)
                    if name == 'deflist' and TAGS['deflistItem2LinePrefix']:
                        line = TAGS['deflistItem2LinePrefix'] + line

                    listbody.append(line)

            # Close item (if needed)
            if itemclose: listbody.append(tagindent+itemclose)

        if not widelist and rules['compactlist']:
            listopen = TAGS.get(name+'OpenCompact')
            listclose = TAGS.get(name+'CloseCompact')
        else:
            listopen  = TAGS.get(name+'Open')
            listclose = TAGS.get(name+'Close')

        # Open list (not nestable lists are only opened at mother)
        if listopen and not \
           (rules['listnotnested'] and BLOCK.depth != 1):
            result.append(tagindent+listopen)

        result.extend(listbody)

        # Close list (not nestable lists are only closed at mother)
        if listclose and not \
           (rules['listnotnested'] and self.depth != 1):
            result.append(tagindent+listclose)

        # Blank line after?
        if self._should_add_blank_line('after', name): result.append('')

        return result


##############################################################################


class MacroMaster:
    def __init__(self, config={}):
        self.name     = ''
        self.config   = config or CONF
        self.infile   = self.config['sourcefile']
        self.outfile  = self.config['outfile']
        self.currdate = time.localtime(time.time())
        self.rgx      = regex.get('macros') or getRegexes()['macros']
        self.fileinfo = { 'infile': None, 'outfile': None }
        self.dft_fmt  = MACROS

    def walk_file_format(self, fmt):
        "Walks the %%{in/out}file format string, expanding the % flags"
        i = 0; ret = ''                                 # counter/hold
        while i < len(fmt):                             # char by char
            c = fmt[i]; i += 1
            if c == '%':                            # hot char!
                if i == len(fmt):               # % at the end
                    ret = ret + c
                    break
                c = fmt[i]; i += 1              # read next
                ret = ret + self.expand_file_flag(c)
            else:
                ret = ret +c                    # common char
        return ret

    def expand_file_flag(self, flag):
        "%f: filename          %F: filename (w/o extension)"
        "%d: dirname           %D: dirname (only parent dir)"
        "%p: file path         %e: extension"
        info = self.fileinfo[self.name]           # get dict
        if   flag == '%': x = '%'                 # %% -> %
        elif flag == 'f': x = info['name']
        elif flag == 'F': x = re.sub('\.[^.]*$','',info['name'])
        elif flag == 'd': x = info['dir']
        elif flag == 'D': x = os.path.split(info['dir'])[-1]
        elif flag == 'p': x = info['path']
        elif flag == 'e': x = re.search('.(\.([^.]+))?$', info['name']).group(2) or ''
        #TODO simpler way for %e ?
        else            : x = '%'+flag            # false alarm
        return x

    def set_file_info(self, macroname):
        if self.fileinfo.get(macroname): return   # already done
        file = getattr(self, self.name)           # self.infile
        if file == STDOUT or file == MODULEOUT:
            dir = ''; path = name = file
        else:
            path = os.path.abspath(file)
            dir  = os.path.dirname(path)
            name = os.path.basename(path)
        self.fileinfo[macroname] = {'path':path,'dir':dir,'name':name}

    def expand(self, line=''):
        "Expand all macros found on the line"
        while self.rgx.search(line):
            m = self.rgx.search(line)
            name = self.name = m.group('name').lower()
            fmt = m.group('fmt') or self.dft_fmt.get(name)
            if name == 'date':
                txt = time.strftime(fmt,self.currdate)
            elif name == 'mtime':
                if self.infile in (STDIN, MODULEIN):
                    fdate = self.currdate
                else:
                    mtime = os.path.getmtime(self.infile)
                    fdate = time.localtime(mtime)
                txt = time.strftime(fmt,fdate)
            elif name == 'infile' or name == 'outfile':
                self.set_file_info(name)
                txt = self.walk_file_format(fmt)
            else:
                Error("Unknown macro name '%s'"%name)
            line = self.rgx.sub(txt,line,1)
        return line


##############################################################################


def dumpConfig(source_raw, parsed_config):
    onoff = {1:_('ON'), 0:_('OFF')}
    data = [
        (_('RC file')        , RC_RAW     ),
        (_('source document'), source_raw ),
        (_('command line')   , CMDLINE_RAW)
    ]
    # First show all RAW data found
    for label, cfg in data:
        print(_('RAW config for %s')%label)
        for target,key,val in cfg:
            target = '(%s)'%target
            key    = dotted_spaces("%-14s"%key)
            val    = val or _('ON')
            print('  %-8s %s: %s'%(target,key,val))
        print()
    # Then the parsed results of all of them
    print(_('Full PARSED config'))
    keys = list(parsed_config.keys()) ; keys.sort()  # sorted
    for key in keys:
        val = parsed_config[key]
        # Filters are the last
        if key == 'preproc' or key == 'postproc':
            continue
        # Flag beautifier
        if key in list(FLAGS.keys()) or key in list(ACTIONS.keys()):
            val = onoff.get(val) or val
        # List beautifier
        if type(val) == type([]):
            if key == 'options': sep = ' '
            else               : sep = ', '
            val = sep.join(val)
        print("%25s: %s"%(dotted_spaces("%-14s"%key),val))
    print()
    print(_('Active filters'))
    for filter in ['preproc', 'postproc']:
        for rule in parsed_config.get(filter) or []:
            print("%25s: %s  ->  %s" % (
                dotted_spaces("%-14s"%filter), rule[0], rule[1]))


def get_file_body(file):
    "Returns all the document BODY lines"
    return process_source_file(file, noconf=1)[1][2]


def finish_him(outlist, config):
    "Writing output to screen or file"
    outfile = config['outfile']
    outlist = unmaskEscapeChar(outlist)
    outlist = expandLineBreaks(outlist)

    # Apply PostProc filters
    if config['postproc']:
        filters = compile_filters(config['postproc'],
            _('Invalid PostProc filter regex'))
        postoutlist = []
        errmsg = _('Invalid PostProc filter replacement')
        for line in outlist:
            for rgx,repl in filters:
                try: line = rgx.sub(repl, line)
                except: Error("%s: '%s'"%(errmsg, repl))
            postoutlist.append(line)
        outlist = postoutlist[:]

    if outfile == MODULEOUT:
        return outlist
    elif outfile == STDOUT:
        if GUI:
            return outlist, config
        else:
            for line in outlist: print(line)
    else:
        Savefile(outfile, addLineBreaks(outlist))
        if not GUI and not QUIET:
            print(_('%s wrote %s')%(my_name,outfile))

    if config['split']:
        if not QUIET: print("--- html...")
        sgml2html = 'sgml2html -s %s -l %s %s' % (
            config['split'], config['lang'] or lang, outfile)
        if not QUIET: print("Running system command:", sgml2html)
        os.system(sgml2html)


def toc_inside_body(body, toc, config):
    ret = []
    if AUTOTOC: return body                     # nothing to expand
    toc_mark = MaskMaster().tocmask
    # Expand toc mark with TOC contents
    for line in body:
        if line.count(toc_mark):            # toc mark found
            if config['toc']:
                ret.extend(toc)     # include if --toc
            else:
                pass                # or remove %%toc line
        else:
            ret.append(line)            # common line
    return ret

def toc_tagger(toc, config):
    "Convert t2t-marked TOC (it is a list) to target-tagged TOC"
    ret = []
    # Tag if TOC-only TOC "by hand" (target don't have a TOC tag)
    if config['toc-only'] or (config['toc'] and not TAGS['TOC']):
        fakeconf = config.copy()
        fakeconf['headers']    = 0
        fakeconf['toc-only']   = 0
        fakeconf['mask-email'] = 0
        fakeconf['preproc']    = []
        fakeconf['postproc']   = []
        fakeconf['css-sugar']  = 0
        ret,foo = convert(toc, fakeconf)
        set_global_config(config)   # restore config
    # Target TOC is a tag
    elif config['toc'] and TAGS['TOC']:
        ret = [TAGS['TOC']]
    return ret

def toc_formatter(toc, config):
    "Formats TOC for automatic placement between headers and body"
    if config['toc-only']: return toc              # no formatting needed
    if not config['toc'] : return []               # TOC disabled
    ret = toc
    # TOC open/close tags (if any)
    if TAGS['tocOpen' ]: ret.insert(0, TAGS['tocOpen'])
    if TAGS['tocClose']: ret.append(TAGS['tocClose'])
    # Autotoc specific formatting
    if AUTOTOC:
        if rules['autotocwithbars']:           # TOC between bars
            para = TAGS['paragraphOpen']+TAGS['paragraphClose']
            bar  = regex['x'].sub('-'*72,TAGS['bar1'])
            tocbar = [para, bar, para]
            ret = tocbar + ret + tocbar
        if rules['blankendautotoc']:           # blank line after TOC
            ret.append('')
        if rules['autotocnewpagebefore']:      # page break before TOC
            ret.insert(0,TAGS['pageBreak'])
        if rules['autotocnewpageafter']:       # page break after TOC
            ret.append(TAGS['pageBreak'])
    return ret


def doHeader(headers, config):
    if not config['headers']: return []
    if not headers: headers = ['','','']
    target = config['target']
    if target not in HEADER_TEMPLATE:
        Error("doHeader: Unknown target '%s'"%target)

    if target in ('html','xhtml') and config.get('css-sugar'):
        template = HEADER_TEMPLATE[target+'css'].split('\n')
    else:
        template = HEADER_TEMPLATE[target].split('\n')

    head_data = {'STYLE':[], 'ENCODING':''}
    for key in head_data.keys():
        val = config.get(key.lower())
        # Remove .sty extension from each style filename (freaking tex)
        # XXX Can't handle --style foo.sty,bar.sty
        if target == 'tex' and key == 'STYLE':
            val = [re.sub('(?i)\.sty$','',x) for x in val]
        if key == 'ENCODING':
            val = get_encoding_string(val, target)
        head_data[key] = val
    # Parse header contents
    for i in 0,1,2:
        # Expand macros
        contents = MacroMaster(config=config).expand(headers[i])
        # Escapes - on tex, just do it if any \tag{} present
        if target != 'tex' or \
          (target == 'tex' and re.search(r'\\\w+{', contents)):
            contents = doEscape(target, contents)
        if target == 'lout':
            contents = doFinalEscape(target, contents)

        head_data['HEADER%d'%(i+1)] = contents

    if target == 'art':
        if not [v for v in head_data.values() if v]:
            return []
        template = aa_header(head_data)
        return template.split('\n')

    # css-inside removes STYLE line
    #XXX In tex, this also removes the modules call (%!style:amsfonts)
    if target in ('html','xhtml') and config.get('css-inside') and \
       config.get('style'):
        head_data['STYLE'] = []
    Debug("Header Data: %s"%head_data, 1)
    # Scan for empty dictionary keys
    # If found, scan template lines for that key reference
    # If found, remove the reference
    # If there isn't any other key reference on the same line, remove it
    #TODO loop by template line > key
    for key in head_data:
        if head_data.get(key): continue
        for line in template:
            if line.count('%%(%s)s'%key):
                sline = line.replace('%%(%s)s'%key, '')
                if not re.search(r'%\([A-Z0-9]+\)s', sline):
                    template.remove(line)
    # Style is a multiple tag.
    # - If none or just one, use default template
    # - If two or more, insert extra lines in a loop (and remove original)
    styles = head_data['STYLE']
    if len(styles) == 1:
        head_data['STYLE'] = styles[0]
    elif len(styles) > 1:
        style_mark = '%(STYLE)s'
        for i in range(len(template)):
            if template[i].count(style_mark):
                while styles:
                    template.insert(i+1, template[i].replace(style_mark, styles.pop()))
                del template[i]
                break
    # Populate template with data (dict expansion)
    template = '\n'.join(template) % head_data

    # Adding CSS contents into template (for --css-inside)
    # This code sux. Dirty++
    if target in ('html','xhtml') and config.get('css-inside') and \
       config.get('style'):
        set_global_config(config) # usually on convert(), needed here
        for i in range(len(config['style'])):
            cssfile = config['style'][i]
            if not os.path.isabs(cssfile):
                infile = config.get('sourcefile')
                cssfile = os.path.join(
                    os.path.dirname(infile), cssfile)
            try:
                contents = Readfile(cssfile, 1)
                css = "\n%s\n%s\n%s\n%s\n" % (
                    ## Jendrik: We do not need the css filename
                    #doCommentLine("Included %s" % cssfile),
                    doCommentLine("Included css file"),
                    TAGS['cssOpen'],
                    '\n'.join(contents),
                    TAGS['cssClose'])
                # Style now is content, needs escaping (tex)
                #css = maskEscapeChar(css)
            except:
                errmsg = "CSS include failed for %s" % cssfile
                css = "\n%s\n" % (doCommentLine(errmsg))
            # Insert this CSS file contents on the template
            template = re.sub('(?i)(</HEAD>)', css+r'\1', template)
            # template = re.sub(r'(?i)(\\begin{document})',
            #       css+'\n'+r'\1', template) # tex

        # The last blank line to keep everything separated
        template = re.sub('(?i)(</HEAD>)', '\n'+r'\1', template)

    return template.split('\n')

def doCommentLine(txt):
    # The -- string ends a (h|sg|xht)ml comment :(
    txt = maskEscapeChar(txt)
    if TAGS['comment'].count('--') and txt.count('--'):
        txt = re.sub('-(?=-)', r'-\\', txt)

    if TAGS['comment']:
        return regex['x'].sub(txt, TAGS['comment'])
    return ''

def doFooter(config):
    if not config['headers']: return []
    ret = []
    target = config['target']
    cmdline = config['realcmdline']
    typename = target
    if target == 'tex': typename = 'LaTeX2e'
    ppgd = '%s code generated by %s %s (%s)' % (typename, my_name, my_version, my_url)
    cmdline = 'cmdline: %s %s' % (my_name, ' '.join(cmdline))
    ret.append('')
    ret.append(doCommentLine(ppgd))
    ret.append(doCommentLine(cmdline))
    ret.append(TAGS['EOD'])
    return ret

def doEscape(target,txt):
    "Target-specific special escapes. Apply *before* insert any tag."
    tmpmask = 'vvvvThisEscapingSuxvvvv'
    if target in ('html','sgml','xhtml'):
        txt = re.sub('&','&amp;',txt)
        txt = re.sub('<','&lt;',txt)
        txt = re.sub('>','&gt;',txt)
        if target == 'sgml':
            txt = re.sub('\xff','&yuml;',txt)  # "+y
    elif target == 'pm6':
        txt = re.sub('<','<\#60>',txt)
    elif target == 'mgp':
        txt = re.sub('^%',' %',txt)  # add leading blank to avoid parse
    elif target == 'man':
        txt = re.sub("^([.'])", '\\&\\1',txt)           # command ID
        txt = txt.replace(ESCCHAR, ESCCHAR+'e')         # \e
    elif target == 'lout':
        # TIP: / moved to FinalEscape to avoid //italic//
        # TIP: these are also converted by lout:  ...  ---  --
        txt = txt.replace(ESCCHAR, tmpmask)             # \
        txt = txt.replace('"', '"%s""'%ESCCHAR)         # "\""
        txt = re.sub('([|&{}@#^~])', '"\\1"', txt)      # "@"
        txt = txt.replace(tmpmask, '"%s"'%(ESCCHAR*2))  # "\\"
    elif target == 'tex':
        # Mark literal \ to be changed to $\backslash$ later
        txt = txt.replace(ESCCHAR, tmpmask)
        txt = re.sub('([#$&%{}])', ESCCHAR+r'\1'  , txt)  # \%
        txt = re.sub('([~^])'    , ESCCHAR+r'\1{}', txt)  # \~{}
        txt = re.sub('([<|>])'   ,         r'$\1$', txt)  # $>$
        txt = txt.replace(tmpmask, maskEscapeChar(r'$\backslash$'))
        ##
        ##txt = txt.replace('_', 'vvvvTexUndervvvv')
        # TIP the _ is escaped at the end
    return txt

# TODO man: where - really needs to be escaped?
def doFinalEscape(target, txt):
    "Last escapes of each line"
    if   target == 'pm6' : txt = txt.replace(ESCCHAR+'<', r'<\#92><')
    elif target == 'man' : txt = txt.replace('-', r'\-')
    elif target == 'sgml': txt = txt.replace('[', '&lsqb;')
    elif target == 'lout': txt = txt.replace('/', '"/"')
    elif target == 'tex' :
        txt = txt.replace('_', r'\_')
        txt = txt.replace('vvvvTexUndervvvv', '_')  # shame!
        ## Jendrik
        txt = txt.replace('vvvUnderscoreInRawTextvvv', '_')
        txt = txt.replace('vvvUnderscoreInTaggedTextvvv', '_')
    return txt

def EscapeCharHandler(action, data):
    "Mask/Unmask the Escape Char on the given string"
    if not data.strip(): return data
    if action not in ('mask','unmask'):
        Error("EscapeCharHandler: Invalid action '%s'"%action)
    if action == 'mask': return data.replace('\\', ESCCHAR)
    else:                return data.replace(ESCCHAR, '\\')

def maskEscapeChar(data):
    "Replace any Escape Char \ with a text mask (Input: str or list)"
    if type(data) == type([]):
        return [EscapeCharHandler('mask', x) for x in data]
    return EscapeCharHandler('mask',data)

def unmaskEscapeChar(data):
    "Undo the Escape char \ masking (Input: str or list)"
    if type(data) == type([]):
        return [EscapeCharHandler('unmask', x) for x in data]
    return EscapeCharHandler('unmask',data)

def addLineBreaks(mylist):
    "use LB to respect sys.platform"
    ret = []
    for line in mylist:
        line = line.replace('\n', LB)        # embedded \n's
        ret.append(line+LB)                  # add final line break
    return ret

# Convert ['foo\nbar'] to ['foo', 'bar']
def expandLineBreaks(mylist):
    ret = []
    for line in mylist:
        ret.extend(line.split('\n'))
    return ret

def compile_filters(filters, errmsg='Filter'):
    if filters:
        for i in range(len(filters)):
            patt,repl = filters[i]
            ## JS: Make filters Unicode-aware.
            try: rgx = re.compile(patt, re.U)
            except: Error("%s: '%s'"%(errmsg, patt))
            filters[i] = (rgx,repl)
    return filters

def enclose_me(tagname, txt):
    return TAGS.get(tagname+'Open') + txt + TAGS.get(tagname+'Close')

def beautify_me(name, font, line):
    "where name is: bold, italic, underline or strike"

    # Exception: Doesn't parse an horizontal bar as strike
    if name == 'strike' and regex['bar'].search(line): return line

    open  = TAGS['%sOpen' % font]
    close = TAGS['%sClose' % font]
    txt = r'%s\1%s'%(open, close)
    line = regex[font].sub(txt, line)
    return line

def get_tagged_link(label, url):
    ret = ''
    target = CONF['target']
    image_re = regex['img']

    # Set link type
    if regex['email'].match(url):
        linktype = 'email'
    else:
        linktype = 'url';

    # Escape specials from TEXT parts
    label = doEscape(target,label)

    # Escape specials from link URL
    if not rules['linkable'] or rules['escapeurl']:
        url = doEscape(target, url)

    # Adding protocol to guessed link
    guessurl = ''
    if linktype == 'url' and \
       re.match('(?i)'+regex['_urlskel']['guess'], url):
        if url[0] in 'Ww': guessurl = 'http://' +url
        else             : guessurl =  'ftp://' +url

        # Not link aware targets -> protocol is useless
        if not rules['linkable']: guessurl = ''

    # Simple link (not guessed)
    if not label and not guessurl:
        if CONF['mask-email'] and linktype == 'email':
            # Do the email mask feature (no TAGs, just text)
            url = url.replace('@', ' (a) ')
            url = url.replace('.', ' ')
            url = "<%s>" % url
            if rules['linkable']: url = doEscape(target, url)
            ret = url
        else:
            # Just add link data to tag
            tag = TAGS[linktype]
            ret = regex['x'].sub(url,tag)

    # Named link or guessed simple link
    else:
        # Adjusts for guessed link
        if not label: label = url         # no   protocol
        if guessurl : url   = guessurl    # with protocol

        # Image inside link!
        if image_re.match(label):
            if rules['imglinkable']:  # get image tag
                label = parse_images(label)
            else:                     #  img@link !supported
                label = "(%s)"%image_re.match(label).group(1)

        # Putting data on the right appearance order
        if rules['labelbeforelink'] or not rules['linkable']:
            urlorder = [label, url]   # label before link
        else:
            urlorder = [url, label]   # link before label

        # Add link data to tag (replace \a's)
        ret = TAGS["%sMark"%linktype]
        for data in urlorder:
            ret = regex['x'].sub(data,ret,1)

    return ret


def parse_deflist_term(line):
    "Extract and parse definition list term contents"
    img_re = regex['img']
    term   = regex['deflist'].search(line).group(3)

    # Mask image inside term as (image.jpg), where not supported
    if not rules['imgasdefterm'] and img_re.search(term):
        while img_re.search(term):
            imgfile = img_re.search(term).group(1)
            term = img_re.sub('(%s)'%imgfile, term, 1)

    #TODO tex: escape ] on term. \], \rbrack{} and \verb!]! don't work :(
    return term


def get_image_align(line):
    "Return the image (first found) align for the given line"

    # First clear marks that can mess align detection
    line = re.sub(SEPARATOR+'$', '', line)  # remove deflist sep
    line = re.sub('^'+SEPARATOR, '', line)  # remove list sep
    line = re.sub('^[\t]+'     , '', line)  # remove quote mark

    # Get image position on the line
    m = regex['img'].search(line)
    ini = m.start() ; head = 0
    end = m.end()   ; tail = len(line)

    # The align detection algorithm
    if   ini == head and end != tail: align = 'left'   # ^img + text$
    elif ini != head and end == tail: align = 'right'  # ^text + img$
    else                            : align = 'center' # default align

    # Some special cases
    if BLOCK.isblock('table'): align = 'center'    # ignore when table
#   if TARGET == 'mgp' and align == 'center': align = 'center'

    return align


# Reference: http://www.iana.org/assignments/character-sets
# http://www.drclue.net/F1.cgi/HTML/META/META.html
def get_encoding_string(enc, target):
    if not enc: return ''
    # Target specific translation table
    translate = {
        'tex': {
            # missing: ansinew , applemac , cp437 , cp437de , cp865
            'utf-8'       : 'utf8',
            'us-ascii'    : 'ascii',
            'windows-1250': 'cp1250',
            'windows-1252': 'cp1252',
            'ibm850'      : 'cp850',
            'ibm852'      : 'cp852',
            'iso-8859-1'  : 'latin1',
            'iso-8859-2'  : 'latin2',
            'iso-8859-3'  : 'latin3',
            'iso-8859-4'  : 'latin4',
            'iso-8859-5'  : 'latin5',
            'iso-8859-9'  : 'latin9',
            'koi8-r'      : 'koi8-r'
        }
    }
    # Normalization
    enc = re.sub('(?i)(us[-_]?)?ascii|us|ibm367','us-ascii'  , enc)
    enc = re.sub('(?i)(ibm|cp)?85([02])'        ,'ibm85\\2'  , enc)
    enc = re.sub('(?i)(iso[_-]?)?8859[_-]?'     ,'iso-8859-' , enc)
    enc = re.sub('iso-8859-($|[^1-9]).*'        ,'iso-8859-1', enc)
    # Apply translation table
    try: enc = translate[target][enc.lower()]
    except: pass
    return enc


##############################################################################
##MerryChristmas,IdontwanttofighttonightwithyouImissyourbodyandIneedyourlove##
##############################################################################


def process_source_file(file='', noconf=0, contents=[]):
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
    The source files is read on this step only.
    """
    if contents:
        source = SourceDocument(contents=contents)
    else:
        source = SourceDocument(file)
    head, conf, body = source.split()
    Message(_("Source document contents stored"),2)
    if not noconf:
        # Read document config
        source_raw = source.get_raw_config()
        # Join all the config directives found, then parse it
        full_raw = RC_RAW + source_raw + CMDLINE_RAW
        Message(_("Parsing and saving all config found (%03d items)") % (len(full_raw)), 1)
        full_parsed = ConfigMaster(full_raw).parse()
        # Add manually the filename to the conf dic
        if contents:
            full_parsed['sourcefile'] = MODULEIN
            full_parsed['infile'] = MODULEIN
            full_parsed['outfile'] = MODULEOUT
        else:
            full_parsed['sourcefile'] = file
        # Maybe should we dump the config found?
        if full_parsed.get('dump-config'):
            dumpConfig(source_raw, full_parsed)
            Quit()
        # The user just want to know a single config value (hidden feature)
        #TODO pick a better name than --show-config-value
        elif full_parsed.get('show-config-value'):
            config_value = full_parsed.get(full_parsed['show-config-value'])
            if config_value:
                if type(config_value) == type([]):
                    print('\n'.join(config_value))
                else:
                    print(config_value)
            Quit()
        # Okay, all done
        Debug("FULL config for this file: %s"%full_parsed, 1)
    else:
        full_parsed = {}
    return full_parsed, (head,conf,body)

def get_infiles_config(infiles):
    """
    Find and Join into a single list, all configuration available
    for each input file. This function is supposed to be the very
    first one to be called, before any processing.
    """
    return list(map(process_source_file, infiles))

def convert_this_files(configs):
    global CONF
    for myconf,doc in configs:                 # multifile support
        target_head = []
        target_toc  = []
        target_body = []
        target_foot = []
        source_head, source_conf, source_body = doc
        myconf = ConfigMaster().sanity(myconf)
        # Compose the target file Headers
        #TODO escape line before?
        #TODO see exceptions by tex and mgp
        Message(_("Composing target Headers"),1)
        target_head = doHeader(source_head, myconf)
        # Parse the full marked body into tagged target
        first_body_line = (len(source_head) or 1)+ len(source_conf) + 1
        Message(_("Composing target Body"),1)
        target_body, marked_toc = convert(source_body, myconf, firstlinenr=first_body_line)
        # If dump-source, we're done
        if myconf['dump-source']:
            for line in source_head+source_conf+target_body:
                print(line)
            return
        # Make TOC (if needed)
        Message(_("Composing target TOC"),1)
        tagged_toc  = toc_tagger(marked_toc, myconf)
        target_toc  = toc_formatter(tagged_toc, myconf)
        target_body = toc_inside_body(target_body, target_toc, myconf)
        if not AUTOTOC and not myconf['toc-only']: target_toc = []
        # Compose the target file Footer
        Message(_("Composing target Footer"),1)
        if TARGET not in ['txt', 'art']:
            target_foot = doFooter(myconf)
        # Finally, we have our document
        outlist = target_head + target_toc + target_body + target_foot
        # If on GUI, abort before finish_him
        # If module, return finish_him as list
        # Else, write results to file or STDOUT
        if GUI:
            return outlist, myconf
        elif myconf.get('outfile') == MODULEOUT:
            return finish_him(outlist, myconf), myconf
        else:
            Message(_("Saving results to the output file"),1)
            finish_him(outlist, myconf)


def parse_images(line):
    "Tag all images found"
    while regex['img'].search(line) and TAGS['img'] != '[\a]':
        txt = regex['img'].search(line).group(1)
        tag = TAGS['img']

        # If target supports image alignment, here we go
        if rules['imgalignable']:

            align = get_image_align(line)         # right
            align_name = align.capitalize()       # Right

            # The align is a full tag, or part of the image tag (~A~)
            if TAGS['imgAlign'+align_name]:
                tag = TAGS['imgAlign'+align_name]
            else:
                align_tag = TAGS['_imgAlign'+align_name]
                tag = regex['_imgAlign'].sub(align_tag, tag, 1)

            # Dirty fix to allow centered solo images
            if align == 'center' and TARGET in ('html','xhtml'):
                rest = regex['img'].sub('',line,1)
                if re.match('^\s+$', rest):
                    tag = "<center>%s</center>" %tag

        if TARGET == 'tex':
            tag = re.sub(r'\\b',r'\\\\b',tag)
            txt = txt.replace('_', 'vvvvTexUndervvvv')

        line = regex['img'].sub(tag,line,1)
        line = regex['x'].sub(txt,line,1)
    return line


def add_inline_tags(line):
    # Beautifiers
    for beauti, font in [('bold', 'fontBold'), ('italic', 'fontItalic'),
                         ('underline', 'fontUnderline'), ('strike', 'fontStrike')]:
        if regex[font].search(line):
            line = beautify_me(beauti, font, line)

    line = parse_images(line)
    return line


def get_include_contents(file, path=''):
    "Parses %!include: value and extract file contents"
    ids = {'`':'verb', '"':'raw', "'":'tagged' }
    id = 't2t'
    # Set include type and remove identifier marks
    mark = file[0]
    if mark in ids.keys():
        if file[:2] == file[-2:] == mark*2:
            id = ids[mark]     # set type
            file = file[2:-2]  # remove marks
    # Handle remote dir execution
    filepath = os.path.join(path, file)
    # Read included file contents
    lines = Readfile(filepath, remove_linebreaks=1)
    # Default txt2tags marked text, just BODY matters
    if id == 't2t':
        lines = get_file_body(filepath)
        #TODO fix images relative path if file has a path, ie.: chapter1/index.t2t (wait until tree parsing)
        #TODO for the images path fix, also respect outfile path, if different from infile (wait until tree parsing)
        lines.insert(0, '%%INCLUDED(%s) starts here: %s'%(id,file))
        # This appears when included hit EOF with verbatim area open
        #lines.append('%%INCLUDED(%s) ends here: %s'%(id,file))
    return id, lines


def set_global_config(config):
    global CONF, TAGS, regex, rules, TARGET
    CONF   = config
    rules  = getRules(CONF)
    TAGS   = getTags(CONF)
    regex  = getRegexes()
    TARGET = config['target']  # save for buggy functions that need global


def convert(bodylines, config, firstlinenr=1):
    global BLOCK, TITLE

    set_global_config(config)

    target = config['target']
    BLOCK = BlockMaster()
    MASK  =  MaskMaster()
    TITLE = TitleMaster()

    ret = []
    dump_source = []
    f_lastwasblank = 0

    # Compiling all PreProc regexes
    pre_filter = compile_filters(
        CONF['preproc'], _('Invalid PreProc filter regex'))

    # Let's mark it up!
    linenr = firstlinenr-1
    lineref = 0
    while lineref < len(bodylines):
        # Defaults
        MASK.reset()
        results_box = ''

        untouchedline = bodylines[lineref]
        dump_source.append(untouchedline)

        line = re.sub('[\n\r]+$','',untouchedline)   # del line break

        # Apply PreProc filters
        if pre_filter:
            errmsg = _('Invalid PreProc filter replacement')
            for rgx,repl in pre_filter:
                try: line = rgx.sub(repl, line)
                except: Error("%s: '%s'"%(errmsg, repl))

        line = maskEscapeChar(line)                  # protect \ char
        linenr  += 1
        lineref += 1

        Debug(repr(line), 2, linenr)  # heavy debug: show each line

        #------------------[ Comment Block ]------------------------

        # We're already on a comment block
        if BLOCK.block() == 'comment':

            # Closing comment
            if regex['blockCommentClose'].search(line):
                ret.extend(BLOCK.blockout() or [])
                continue

            # Normal comment-inside line. Ignore it.
            continue

        # Detecting comment block init
        if regex['blockCommentOpen'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('comment'))
            continue

        #-------------------------[ Tagged Text ]----------------------

        # We're already on a tagged block
        if BLOCK.block() == 'tagged':

            # Closing tagged
            if regex['blockTaggedClose'].search(line):
                ret.extend(BLOCK.blockout())
                continue

            # Normal tagged-inside line
            BLOCK.holdadd(line)
            continue

        # Detecting tagged block init
        if regex['blockTaggedOpen'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('tagged'))
            continue

        # One line tagged text
        if regex['1lineTagged'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('tagged'))
            line = regex['1lineTagged'].sub('',line)
            BLOCK.holdadd(line)
            ret.extend(BLOCK.blockout())
            continue

        #-------------------------[ Raw Text ]----------------------

        # We're already on a raw block
        if BLOCK.block() == 'raw':

            # Closing raw
            if regex['blockRawClose'].search(line):
                ret.extend(BLOCK.blockout())
                continue

            # Normal raw-inside line
            BLOCK.holdadd(line)
            continue

        # Detecting raw block init
        if regex['blockRawOpen'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('raw'))
            continue

        # One line raw text
        if regex['1lineRaw'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('raw'))
            line = regex['1lineRaw'].sub('',line)
            BLOCK.holdadd(line)
            ret.extend(BLOCK.blockout())
            continue

        #------------------------[ Verbatim  ]----------------------

        #TIP We'll never support beautifiers inside verbatim

        # Closing table mapped to verb
        if BLOCK.block() == 'verb' \
           and BLOCK.prop('mapped') == 'table' \
           and not regex['table'].search(line):
            ret.extend(BLOCK.blockout())

        # We're already on a verb block
        if BLOCK.block() == 'verb':

            # Closing verb
            if regex['blockVerbClose'].search(line):
                ret.extend(BLOCK.blockout())
                continue

            # Normal verb-inside line
            BLOCK.holdadd(line)
            continue

        # Detecting verb block init
        if regex['blockVerbOpen'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('verb'))
            f_lastwasblank = 0
            continue

        # One line verb-formatted text
        if regex['1lineVerb'].search(line) \
           and BLOCK.block() not in BLOCK.exclusive:
            ret.extend(BLOCK.blockin('verb'))
            line = regex['1lineVerb'].sub('',line)
            BLOCK.holdadd(line)
            ret.extend(BLOCK.blockout())
            f_lastwasblank = 0
            continue

        # Tables are mapped to verb when target is not table-aware
        if not rules['tableable'] and regex['table'].search(line):
            if not BLOCK.isblock('verb'):
                ret.extend(BLOCK.blockin('verb'))
                BLOCK.propset('mapped', 'table')
                BLOCK.holdadd(line)
                continue

        #---------------------[ blank lines ]-----------------------

        if regex['blankline'].search(line):

            # Close open paragraph
            if BLOCK.isblock('para'):
                ret.extend(BLOCK.blockout())
                f_lastwasblank = 1
                continue

            # Close all open tables
            if BLOCK.isblock('table'):
                ret.extend(BLOCK.blockout())
                f_lastwasblank = 1
                continue

            # Close all open quotes
            while BLOCK.isblock('quote'):
                ret.extend(BLOCK.blockout())

            # Closing all open lists
            if f_lastwasblank:          # 2nd consecutive blank
                if BLOCK.block().endswith('list'):
                    BLOCK.holdaddsub('')   # helps parser
                while BLOCK.depth:  # closes list (if any)
                    ret.extend(BLOCK.blockout())
                continue            # ignore consecutive blanks

            # Paragraph (if any) is wanted inside lists also
            if BLOCK.block().endswith('list'):
                BLOCK.holdaddsub('')

            f_lastwasblank = 1
            continue


        #---------------------[ special ]---------------------------

        if regex['special'].search(line):
            # Include command
            targ, key, val = ConfigLines().parse_line(line, 'include', target)
            if key:
                Debug("Found config '%s', value '%s'" % (key, val), 1, linenr)

                incpath = os.path.dirname(CONF['sourcefile'])
                incfile = val
                err = _('A file cannot include itself (loop!)')
                if CONF['sourcefile'] == incfile:
                    Error("%s: %s"%(err,incfile))
                inctype, inclines = get_include_contents(incfile, incpath)
                # Verb, raw and tagged are easy
                if inctype != 't2t':
                    ret.extend(BLOCK.blockin(inctype))
                    BLOCK.holdextend(inclines)
                    ret.extend(BLOCK.blockout())
                else:
                    # Insert include lines into body
                    #TODO include maxdepth limit
                    bodylines = bodylines[:lineref] + inclines + bodylines[lineref:]
                    #TODO fix path if include@include
                    # Remove %!include call
                    if CONF['dump-source']:
                        dump_source.pop()
                continue
            else:
                Debug('Bogus Special Line',1,linenr)

        #---------------------[ dump-source ]-----------------------

        # We don't need to go any further
        if CONF['dump-source']:
            continue

        #---------------------[ Comments ]--------------------------

        # Just skip them (if not macro)
        if regex['comment'].search(line) and not \
           regex['macros'].match(line) and not \
           regex['toc'].match(line):
            continue

        #---------------------[ Triggers ]--------------------------

        # Valid line, reset blank status
        f_lastwasblank = 0

        # Any NOT quote line closes all open quotes
        if BLOCK.isblock('quote') and not regex['quote'].search(line):
            while BLOCK.isblock('quote'):
                ret.extend(BLOCK.blockout())

        # Any NOT table line closes an open table
        if BLOCK.isblock('table') and not regex['table'].search(line):
            ret.extend(BLOCK.blockout())


        #---------------------[ Horizontal Bar ]--------------------

        if regex['bar'].search(line):

            # Bars inside quotes are handled on the Quote processing
            # Otherwise we parse the bars right here
            #
            if not (BLOCK.isblock('quote') or regex['quote'].search(line)) \
                or (BLOCK.isblock('quote') and not rules['barinsidequote']):

                # Close all the opened blocks
                ret.extend(BLOCK.blockin('bar'))

                # Extract the bar chars (- or =)
                m = regex['bar'].search(line)
                bar_chars = m.group(2)

                # Process and dump the tagged bar
                BLOCK.holdadd(bar_chars)
                ret.extend(BLOCK.blockout())
                Debug("BAR: %s"%line, 6)

                # We're done, nothing more to process
                continue


        #---------------------[ Title ]-----------------------------

        if (regex['title'].search(line) or regex['numtitle'].search(line)) \
            and not BLOCK.block().endswith('list'):

            if regex['title'].search(line):
                name = 'title'
            else:
                name = 'numtitle'

            # Close all the opened blocks
            ret.extend(BLOCK.blockin(name))

            # Process title
            TITLE.add(line)
            ret.extend(BLOCK.blockout())

            # We're done, nothing more to process
            continue

        #---------------------[ %%toc ]-----------------------

        # %%toc line closes paragraph
        if BLOCK.block() == 'para' and regex['toc'].search(line):
            ret.extend(BLOCK.blockout())

        #---------------------[ apply masks ]-----------------------

        line = MASK.mask(line)

        #XXX from here, only block-inside lines will pass

        #---------------------[ Quote ]-----------------------------

        if regex['quote'].search(line):

            # Store number of leading TABS
            quotedepth = len(regex['quote'].search(line).group(0))

            # SGML doesn't support nested quotes
            if rules['quotenotnested']: quotedepth = 1

            # Don't cross depth limit
            maxdepth = rules['quotemaxdepth']
            if maxdepth and quotedepth > maxdepth:
                quotedepth = maxdepth

            # New quote
            if not BLOCK.isblock('quote'):
                ret.extend(BLOCK.blockin('quote'))

            # New subquotes
            while BLOCK.depth < quotedepth:
                BLOCK.blockin('quote')

            # Closing quotes
            while quotedepth < BLOCK.depth:
                ret.extend(BLOCK.blockout())

            # Bar inside quote
            if regex['bar'].search(line) and rules['barinsidequote']:
                tempBlock = BlockMaster()
                tagged_bar = []
                tagged_bar.extend(tempBlock.blockin('bar'))
                tempBlock.holdadd(line)
                tagged_bar.extend(tempBlock.blockout())
                BLOCK.holdextend(tagged_bar)
                continue

        #---------------------[ Lists ]-----------------------------

        # An empty item also closes the current list
        if BLOCK.block().endswith('list'):
            m = regex['listclose'].match(line)
            if m:
                listindent = m.group(1)
                listtype = m.group(2)
                currlisttype = BLOCK.prop('type')
                currlistindent = BLOCK.prop('indent')
                if listindent == currlistindent and \
                   listtype == currlisttype:
                    ret.extend(BLOCK.blockout())
                    continue

        if   regex['list'].search(line) or \
          regex['numlist'].search(line) or \
          regex['deflist'].search(line):

            listindent = BLOCK.prop('indent')
            listids = ''.join(LISTNAMES.keys())
            m = re.match('^( *)([%s]) ' % re.escape(listids), line)
            listitemindent = m.group(1)
            listtype = m.group(2)
            listname = LISTNAMES[listtype]
            results_box = BLOCK.holdadd

            # Del list ID (and separate term from definition)
            if listname == 'deflist':
                term = parse_deflist_term(line)
                line = regex['deflist'].sub(
                    SEPARATOR+term+SEPARATOR,line)
            else:
                line = regex[listname].sub(SEPARATOR,line)

            # Don't cross depth limit
            maxdepth = rules['listmaxdepth']
            if maxdepth and BLOCK.depth == maxdepth:
                if len(listitemindent) > len(listindent):
                    listitemindent = listindent

            # List bumping (same indent, diff mark)
            # Close the currently open list to clear the mess
            if BLOCK.block().endswith('list') \
               and listname != BLOCK.block() \
               and len(listitemindent) == len(listindent):
                ret.extend(BLOCK.blockout())
                listindent = BLOCK.prop('indent')

            # Open mother list or sublist
            if not BLOCK.block().endswith('list') or \
               len(listitemindent) > len(listindent):
                ret.extend(BLOCK.blockin(listname))
                BLOCK.propset('indent',listitemindent)
                BLOCK.propset('type',listtype)

            # Closing sublists
            while len(listitemindent) < len(BLOCK.prop('indent')):
                ret.extend(BLOCK.blockout())

            # O-oh, sublist before list ("\n\n  - foo\n- foo")
            # Fix: close sublist (as mother), open another list
            if not BLOCK.block().endswith('list'):
                ret.extend(BLOCK.blockin(listname))
                BLOCK.propset('indent',listitemindent)
                BLOCK.propset('type',listtype)

        #---------------------[ Table ]-----------------------------

        #TODO escape undesired format inside table
        #TODO add pm6 target
        if regex['table'].search(line):

            if not BLOCK.isblock('table'):   # first table line!
                ret.extend(BLOCK.blockin('table'))
                BLOCK.tableparser.__init__(line)

            tablerow = TableMaster().parse_row(line)
            BLOCK.tableparser.add_row(tablerow)     # save config

            # Maintain line to unmask and inlines
            # XXX Bug: | **bo | ld** | turns **bo\x01ld** and gets converted :(
            # TODO isolate unmask+inlines parsing to use here
            line = SEPARATOR.join(tablerow['cells'])

        #---------------------[ Paragraph ]-------------------------

        if not BLOCK.block() and \
           not line.count(MASK.tocmask): # new para!
            ret.extend(BLOCK.blockin('para'))


        ############################################################
        ############################################################
        ############################################################


        #---------------------[ Final Parses ]----------------------

        # The target-specific special char escapes for body lines
        line = doEscape(target,line)

        line = add_inline_tags(line)
        line = MASK.undo(line)


        #---------------------[ Hold or Return? ]-------------------

        ### Now we must choose where to put the parsed line
        #
        if not results_box:
            # List item extra lines
            if BLOCK.block().endswith('list'):
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
    Debug('EOF',7)
    while BLOCK.block():
        ret.extend(BLOCK.blockout())

    # Maybe close some opened title area?
    if rules['titleblocks']:
        ret.extend(TITLE.close_all())

    # Maybe a major tag to enclose body? (like DIV for CSS)
    if TAGS['bodyOpen' ]: ret.insert(0, TAGS['bodyOpen'])
    if TAGS['bodyClose']: ret.append(TAGS['bodyClose'])

    if CONF['toc-only']: ret = []
    marked_toc = TITLE.dump_marked_toc(CONF['toc-level'])

    # If dump-source, all parsing is ignored
    if CONF['dump-source']: ret = dump_source[:]

    return ret, marked_toc


## GUI removed
## Command line parsing removed

# The End.
