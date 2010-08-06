# -*- coding: utf-8 -*-
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

'''
This module takes the ideas and some code from the highlighting module
PyGTKCodeBuffer by Hannes Matuschek (http://code.google.com/p/pygtkcodebuffer/).
'''

import gtk
import sys
import os.path
import pango
import logging
import re

if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath("./../../"))
    logging.getLogger('').setLevel(logging.DEBUG)

#from rednotebook.external import gtkcodebuffer
from rednotebook.external import txt2tags
#from rednotebook.gui.richtext import HtmlEditor
from rednotebook.gui.browser import HtmlView
from rednotebook.util import markup




class Pattern(object):
    '''
    A pattern object allows a regex-pattern to have
    subgroups with different formatting
    '''
    def __init__(self, pattern, group_tag_pairs, regex=None, flags=""):
        # assemble re-flag
        flags += "ML"
        flag = 0
        
        for char in flags:
            if char == 'M': flag |= re.M
            if char == 'L': flag |= re.L
            if char == 'S': flag |= re.S
            if char == 'I': flag |= re.I
            if char == 'U': flag |= re.U
            if char == 'X': flag |= re.X
        
        if regex:
            self._regexp = regex
        else:
            # compile re
            try:
                self._regexp = re.compile(pattern, flag)
            except re.error, e:
                raise Exception("Invalid regexp \"%s\": %s"%(pattern,str(e)))

        self.group_tag_pairs = group_tag_pairs

    def __call__(self, txt, start, end):
        m = self._regexp.search(txt)
        if not m: return None

        iter_pairs = []

        for group, tag_name in self.group_tag_pairs:
            group_matched = bool(m.group(group))
            if not group_matched:
                continue
            mstart, mend = m.start(group), m.end(group)
            s = start.copy(); s.forward_chars(mstart)
            e = start.copy(); e.forward_chars(mend)
            iter_pairs.append([s, e, tag_name])

        return iter_pairs


class MarkupDefinition(object):
    
    def __init__(self, rules):
        self.rules = rules
        self.styles = dict()
        
    def get_styles(self):
        return self.styles

    def __call__(self, buf, start, end):
        mstart = end.copy()
        mend = end.copy()
        
        txt = buf.get_slice(start, end)

        selected_pairs = None

        # search min match
        for rule in self._successful_rules[:]:
            # search pattern
            iter_pairs = rule(txt, start, end)
            if not iter_pairs:
                ## This rule will not find anything in the next round either
                self._successful_rules.remove(rule)
                continue

            key = lambda iter: iter.get_offset()

            min_start = min([start_iter for start_iter, end_iter, tag_name in iter_pairs], key=key)
            max_end = max([end_iter for start_iter, end_iter, tag_name in iter_pairs], key=key)
            
            # prefer match with smallest start-iter
            if min_start.compare(mstart) == -1:
                mstart, mend = min_start, max_end
                selected_pairs = iter_pairs
                continue

            if min_start.equal(mstart) and max_end.compare(mend) == 1:
                mstart, mend = min_start, max_end
                selected_pairs = iter_pairs
        return selected_pairs


class MarkupBuffer(gtk.TextBuffer):
    
    def __init__(self, table=None, lang=None, styles={}):
        gtk.TextBuffer.__init__(self, table)
        
        # update styles with user-defined
        self.styles = styles
        
        # create tags
        for name, props in self.styles.items():
            style = {}#dict(self.styles['DEFAULT']) # take default
            style.update(props)                  # and update with props
            self.create_tag(name, **style)
        
        # store lang-definition
        self._lang_def = lang
        
        self.connect_after("insert-text", self._on_insert_text)
        self.connect_after("delete-range", self._on_delete_range)

    def get_slice(self, start, end):
        '''
        We have to search for the regexes in utf-8 text
        '''
        slice_text = gtk.TextBuffer.get_slice(self, start, end)
        slice_text = slice_text.decode('utf-8')
        return slice_text

    def _on_insert_text(self, buf, it, text, length):
        end = it.copy()
        start = it.copy()
        start.backward_chars(length)

        self.update_syntax(start, end)

    def _on_delete_range(self, buf, start, end):
        start = start.copy()

        self.update_syntax(start, start)
        
    def remove_all_syntax_tags(self, start, end):
        '''
        Do not remove the gtkspell highlighting
        '''
        for style in self.styles:
            self.remove_tag_by_name(style, start, end)

    def update_syntax(self, start, end):
        """ More or less internal used method to update the
            syntax-highlighting. """
        '''
        Use two categories of rules: one-line and multiline
        
        Before running multiline rules: Check if e.g. - is present in changed string
        '''
            
        # Just update from the start of the first edited line 
        # to the end of the last edited line, because we can
        # guarantee that there's no multiline rule
        start_line_number = start.get_line()
        start_line_iter = self.get_iter_at_line(start_line_number)
        start = start_line_iter
        
        end.forward_to_line_end()
        
        text = self.get_text(start, end)
        
        # We can omit those rules without occurrences in later searches

        # Reset rules
        self._lang_def._successful_rules = self._lang_def.rules[:]
        
        # remove all tags from start to end
        self.remove_all_syntax_tags(start, end)

        # We do not use recursion -> long files exceed rec-limit!
        #finished = False
        while not start == end:#not finished:
            
            # search first rule matching txt[start..end]
            group_iters_and_tags = self._lang_def(self, start, end)

            if not group_iters_and_tags:
                return

            key = lambda iter: iter.get_offset()

            #min_start = min([start_iter for start_iter, end_iter, tag_name \
            #                           in group_iters_and_tags], key=key)
            max_end = max([end_iter for start_iter, end_iter, tag_name \
                                        in group_iters_and_tags], key=key)

            for mstart, mend, tagname in group_iters_and_tags:
                # apply tag
                self.apply_tag_by_name(tagname, mstart, mend)

            # Set new start
            start = max_end





# additional style definitions:
# the update_syntax() method of CodeBuffer allows you to define new and modify
# already defined styles. Think of it like CSS.
styles = {  'DEFAULT':          {'font': 'sans'},#{'font': 'serif'},
            'bold':             {'weight': pango.WEIGHT_BOLD},
            'comment':          {'foreground': 'gray'},
            'underlined':       {'underline': pango.UNDERLINE_SINGLE},
            'grey':             {'foreground': 'gray'},
            'red':              {'foreground': 'red'},
            'italic':           {   # Just to be sure we live this in
                                    'style': pango.STYLE_ITALIC,
                                    # The font:Italic is actually needed
                                    'font': 'Italic'},
            'strikethrough':    {'strikethrough': True},
            'header':           {'weight': pango.WEIGHT_ULTRABOLD,
                                'scale': pango.SCALE_XX_LARGE,
                                # causes PangoWarnings on Windows
                                #'variant': pango.VARIANT_SMALL_CAPS,
                                },
            'raw':              {'font': 'Oblique'},
            'verbatim':         {'font': 'monospace'},
            'tagged':           {},
            'link':             {'foreground': 'blue',
                                'underline': pango.UNDERLINE_SINGLE,},
            }
def add_header_styles():
    sizes = [
            pango.SCALE_XX_LARGE,
            pango.SCALE_X_LARGE,
            pango.SCALE_LARGE,
            pango.SCALE_MEDIUM,
            pango.SCALE_SMALL,
            ]
    for level, size in enumerate(sizes):
        style = {'weight': pango.WEIGHT_ULTRABOLD,
                'scale': size}
        name = 'title%s' % (level+1)
        styles[name] = style
add_header_styles()

# Syntax definition

bank = txt2tags.getRegexes()

def get_pattern(char, style):
    # original strikethrough in txt2tags: r'--([^\s](|.*?[^\s])-*)--'
    # txt2tags docs say that format markup is greedy, but
    # that doesn't seem to be the case
    
    # Either one char, or two chars with (maybe empty) content
    # between them
    # In both cases no whitespaces between chars and markup
    #regex = r'(%s)(\S.*\S)(%s)' % ((markup_symbols, ) * 2)
    regex = r'(%s%s)(\S|.*?\S%s*)(%s%s)' % ((char, ) * 5)
    group_style_pairs = [(1, 'grey'), (2, style), (3, 'grey')]
    return Pattern(regex, group_style_pairs)


list    = Pattern(r"^ *(- )[^ ].*$",  [(1, 'red'), (1, 'bold')])
numlist = Pattern(r"^ *(\+ )[^ ].*$", [(1, 'red'), (1, 'bold')])

comment = Pattern(r'^(\%.*)$', [(1, 'comment')])

line = Pattern(r'^[\s]*([_=-]{20,})[\s]*$', [(1, 'bold')])

# Whitespace is allowed, but nothing else
#header = Pattern(r'^[\s]*(===)([^=]|[^=].*[^=])(===)[\s]*$', \
#                       [(1, 'grey'), (2, 'header'), (3, 'grey')])

title_style = [(1, 'grey'), (2, 'header'), (3, 'grey'), (4, 'grey')]
titskel = r'^ *(%s)(%s)(\1)(\[[\w-]*\])?\s*$'
title_pattern   = titskel % ('[=]{1,5}','[^=]|.*[^=]')
numtitle_pattern = titskel % ('[+]{1,5}','[^+]|.*[^+]')
title = Pattern(title_pattern, title_style)
numtitle = Pattern(numtitle_pattern, title_style)

title_patterns = []
title_style = [(1, 'grey'), (3, 'grey'), (4, 'grey')]
titskel = r'^ *(%s)(%s)(\1)(\[[\w-]*\])?\s*$'
for level in range(1, 6):
    title_pattern    = titskel % ('[=]{%s}'%(level),'[^=]|[^=].*[^=]')
    numtitle_pattern = titskel % ('[+]{%s}'%(level),'[^+]|[^+].*[^+]')
    style_name = 'title%s' % level
    title = Pattern(title_pattern, title_style + [(2, style_name)])
    numtitle = Pattern(numtitle_pattern, title_style + [(2, style_name)])
    title_patterns += [title, numtitle]

linebreak = Pattern(r'(\\\\)', [(1, 'grey')])

# pic [""/home/user/Desktop/RedNotebook pic"".png]
# \w = [a-zA-Z0-9_]
# Added ":-" for "file://5-5.jpg"
# filename = One char or two chars with possibly whitespace in the middle
#filename = r'\S[\w\s_,.+%$#@!?+~/-:-\(\)]*\S|\S'
filename = r'\S.*?\S|\S'
ext = r'png|jpe?g|gif|eps|bmp'
pic = Pattern(r'(\["")(%s)("")(\.%s)(\?\d+)?(\])' % (filename, ext), \
        [(1, 'grey'), (2, 'bold'), (3, 'grey'), (4, 'bold'), (5, 'grey'), (6, 'grey')], flags='I')

# named link on hdd [hs err_pid9204.log ""file:///home/jendrik/hs err_pid9204.log""]
# named link in web [heise ""http://heise.de""]
named_link = Pattern(r'(\[)(.*?)\s("")(\S.*?\S)(""\])', \
        [(1, 'grey'), (2, 'link'), (3, 'grey'), (4, 'grey'), (5, 'grey')], flags='LI')

# link http://heise.de
# Use txt2tags link guessing mechanism
#link_regex = 
link = Pattern('OVERWRITE', [(0, 'link')], regex=bank['link'])
#link._regexp = link_regex

# We do not support multiline regexes
#blockverbatim = Pattern(r'^(```)\s*$\n(.*)$\n(```)\s*$', [(1, 'grey'), (2, 'verbatim'), (3, 'grey')])


patterns = [
        get_pattern('\*', 'bold'),
        get_pattern('_', 'underlined'),
        get_pattern('/', 'italic'),
        get_pattern('-', 'strikethrough'),
        list,
        numlist,
        comment,
        line,
        get_pattern('"', 'raw'),
        get_pattern('`', 'verbatim'),
        get_pattern("'", 'tagged'),
        linebreak,
        pic,
        named_link,
        link,
        ] + title_patterns


def get_highlight_buffer():
    # create lexer:
    lang = MarkupDefinition(patterns)

    # create buffer and update style-definition
    buff = MarkupBuffer(lang=lang, styles=styles)

    return buff

# Testing
if __name__ == '__main__':
    
    txt = """
text [link 1 ""http://en.wikipedia.org/wiki/Personal_wiki#Free_software""] another text [link2 ""http://digitaldump.wordpress.com/projects/rednotebook/""] end

pic [""/home/user/Desktop/RedNotebook pic"".png] pic [""/home/user/Desktop/RedNotebook pic"".png]
== Main==[oho] 
= Header1 =
== Header2 ==
=== Header3 ===
==== Header4 ====
===== Header5 =====
+++++ d +++++
++++ c ++++
+++ a +++
++ b ++
 **bold**, //italic//,/italic/__underlined__, --strikethrough--

[""/home/user/Desktop/RedNotebook pic"".png]

[hs error.log ""file:///home/user/hs error.log""]
```
[heise ""http://heise.de""]
```
www.heise.de, alex@web.de

''$a^2$''  ""über oblique""  ``code mit python``

====================

% list-support
- a simple list item
- an other


+ An ordered list
+ other item


"""

    buff = get_highlight_buffer()

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    scr = gtk.ScrolledWindow()

    html_editor = HtmlView()

    def change_text(widget):
        html = markup.convert(widget.get_text(widget.get_start_iter(), \
                                widget.get_end_iter()), \
                              'xhtml', append_whitespace=True)

        html_editor.load_html(html)

    buff.connect('changed', change_text)

    vbox = gtk.VBox()
    vbox.pack_start(scr)
    vbox.pack_start(html_editor)
    win.add(vbox)
    scr.add(gtk.TextView(buff))

    win.set_default_size(900,1000)
    win.set_position(gtk.WIN_POS_CENTER)
    win.show_all()
    win.connect("destroy", lambda w: gtk.main_quit())

    buff.set_text(txt)

    gtk.main()
