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

from __future__ import with_statement

import os
import sys
import logging

import pango
import gobject

# Testing
if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../../')
    logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)-8s %(message)s',)

from rednotebook.external import txt2tags
from rednotebook.util import filesystem
from rednotebook.util import dates
from rednotebook.util import utils



def convert_categories_to_markup(categories, with_category_title=True):
    'Only add Category title if the text is displayed'
    if with_category_title:
        markup = '== Categories ==\n'
    else:
        markup = ''
        
    for category, entry_list in categories.iteritems():
        markup += '- ' + category + '\n'
        for entry in entry_list:
            markup += '  - ' + entry + '\n'
    markup += '\n\n'
    return markup


def get_markup_for_day(day, with_text=True, categories=None, date=None):
    '''
    Used for exporting days
    '''
    export_string = ''
    
    # Add date
    if date:
        export_string += '= ' + date + ' =\n\n'
        
    # Add text
    if with_text:
        export_string += day.text
    
    # Add Categories
    category_content_pairs = day.get_category_content_pairs()
    
    if categories:
        categories = map(lambda string: str(string).lower(), categories)
        export_categories = dict((x,y) for (x, y) in category_content_pairs.items()
                        if x.lower() in categories)
    elif categories is None:
        # No restrictions
        export_categories = category_content_pairs
    else:
        # "Export no categories" selected
        export_categories = []
    
    
    if export_categories:
        export_string += '\n\n\n' + convert_categories_to_markup(export_categories, \
                                                            with_category_title=with_text)
    elif with_text:
        export_string += '\n\n'
        
    # Only return the string, when there is text or there are categories
    # We don't want to list empty dates
    if export_categories or with_text:
        export_string += '\n\n\n'
        return export_string
    
    return ''
    

def _get_config(type):
    
    config = {}
    
    # Set the configuration on the 'config' dict.
    config = txt2tags.ConfigMaster()._get_defaults()
    
    # The Pre (and Post) processing config is a list of lists:
    # [ [this, that], [foo, bar], [patt, replace] ]
    config['postproc'] = []
    config['preproc'] = []
    
    
    if type == 'xhtml' or type == 'html':
        config['encoding'] = 'UTF-8'       # document encoding
        config['toc'] = 0
        config['style'] = [os.path.join(filesystem.files_dir, 'stylesheet.css')]
        config['css-inside'] = 1
        config['css-sugar'] = 1
    
        # keepnote only recognizes "<strike>"
        config['postproc'].append(['(?i)(</?)s>', r'\1strike>'])
        
        # Allow line breaks, r'\\\\' are 2 \ for regexes
        config['postproc'].append([r'\\\\', '<br />'])
        
        # Apply image resizing
        config['postproc'].append([r'src=\"WIDTH(\d+)-', r'width="\1" src="'])
        
    elif type == 'tex':
        config['encoding'] = 'utf8'
        config['preproc'].append(['€', 'Euro'])
        
        # Latex only allows whitespace and underscores in filenames if
        # the filename is surrounded by "...". This is in turn only possible
        # if the extension is omitted
        config['preproc'].append([r'\[""', r'["""'])
        config['preproc'].append([r'""\.', r'""".'])
        
        scheme = 'file:///' if sys.platform == 'win32' else 'file://'
        
        # For images we have to omit the file:// prefix
        config['postproc'].append([r'includegraphics\{(.*)"%s' % scheme, r'includegraphics{"\1'])
        #config['postproc'].append([r'includegraphics\{"file://', r'includegraphics{"'])
        
        # Special handling for LOCAL file links (Omit scheme, add run:)
        # \htmladdnormallink{file.txt}{file:///home/user/file.txt}
        # -->
        # \htmladdnormallink{file.txt}{run:/home/user/file.txt}
        config['postproc'].append([r'htmladdnormallink\{(.*)\}\{%s(.*)\}' % scheme, 
                                   r'htmladdnormallink{\1}{run:\2}'])
        
        # Allow line breaks, r'\\\\' are 2 \ for regexes
        config['postproc'].append([r'\$\\backslash\$\$\\backslash\$', r'\\\\'])
        
        # Apply image resizing
        config['postproc'].append([r'includegraphics\{("?)WIDTH(\d+)-', r'includegraphics[width=\2px]{\1'])
        
    elif type == 'txt':
        # Allow line breaks, r'\\\\' are 2 \ for regexes
        config['postproc'].append([r'\\\\', '\n'])
        
        # Apply image resizing ([WIDTH400-file:///pathtoimage.jpg])
        config['postproc'].append([r'\[WIDTH(\d+)-(.+)\]', r'[\2?\1]'])
        
    # Allow resizing images by changing 
    # [filename.png?width] to [WIDTHwidth-filename.png]
    img_ext = r'png|jpe?g|gif|eps|bmp'
    img_name = r'\S.*\S|\S'
    
    # Apply this prepoc only after the latex image quotes have been added
    config['preproc'].append([r'\[(%s\.(%s))\?(\d+)\]' % (img_name, img_ext), r'[WIDTH\3-\1]'])
    
    return config
    

def convert(txt, target, headers=None, options=None, append_whitespace=False):
    '''
    Code partly taken from txt2tags tarball
    '''
    
    # Here is the marked body text, it must be a list.
    txt = txt.split('\n')
    
    '''
    Without this HACK "First Line\n_second Line" is rendered to
    "First LineSecond Line", but we want "First Line Second Line"
    
    We only need this for the keepnote input, the exports work fine
    '''
    if append_whitespace:
        def add_whitespace(line):
            if line.rstrip().endswith(r'\\'):
                return line.rstrip()
            else:
                return line + ' '
        txt = map(add_whitespace, txt)
    
    # Set the three header fields
    if headers is None:
        headers = ['', '', '']
    
    config = _get_config(target)
    
    config['outfile'] = txt2tags.MODULEOUT  # results as list
    config['target'] = target
    
    if options is not None:
        config.update(options)
    
    # Let's do the conversion
    try:
        headers   = txt2tags.doHeader(headers, config)
        body, toc = txt2tags.convert(txt, config)
        footer  = txt2tags.doFooter(config)
        toc = txt2tags.toc_tagger(toc, config)
        toc = txt2tags.toc_formatter(toc, config)
        full_doc  = headers + toc + body + footer
        finished  = txt2tags.finish_him(full_doc, config)
        result = '\n'.join(finished)
    
    # Txt2tags error, show the messsage to the user
    except txt2tags.error, msg:
        logging.error(msg)
        result = msg
    
    # Unknown error, show the traceback to the user
    except:
        result = txt2tags.getUnknownErrorMessage()
        logging.error(result)
    
    return result

def convert_to_pango(txt, headers=None, options=None):
    '''
    Code partly taken from txt2tags tarball
    '''    
    original_txt = txt
    
    # Here is the marked body text, it must be a list.
    txt = txt.split('\n')
    
    # Set the three header fields
    if headers is None:
        headers = ['', '', '']
    
    config = txt2tags.ConfigMaster()._get_defaults()
    
    config['outfile'] = txt2tags.MODULEOUT  # results as list
    config['target'] = 'xhtml'
    
    config['preproc'] = []
    config['preproc'].append([r'&amp;', '&'])
    
    # Allow line breaks, r'\\\\' are 2 \ for regexes
    config['postproc'] = []
    config['postproc'].append([r'\\\\', '\n'])
    
    if options is not None:
        config.update(options)
    
    # Let's do the conversion
    try:
        body, toc = txt2tags.convert(txt, config)
        full_doc  = body
        finished  = txt2tags.finish_him(full_doc, config)
        result = ''.join(finished)
    
    # Txt2tags error, show the messsage to the user
    except txt2tags.error, msg:
        logging.error(msg)
        result = msg
    
    # Unknown error, show the traceback to the user
    except:
        result = txt2tags.getUnknownErrorMessage()
        logging.error(result)
        
    # remove unwanted paragraphs
    result = result.replace('<p>', '').replace('</p>', '')
    
    logging.log(5, 'Converted "%s" text to "%s" txt2tags markup' % (original_txt, result))

    try:
        attr_list, plain, accel = pango.parse_markup(result)
        
        # result is valid pango markup, return the markup
        return result
    except gobject.GError:
        # There are unknown tags in the markup, return the original text
        logging.debug('There are unknown tags in the markup: %s' % result)
        # We have to take care of the ampersands in links 
        # (since links always contain an unknown tag, the "a" tag)        
        txt = original_txt.replace('&amp;', 'XXX_SAVE_AMPERSAND_XXX')
        txt = txt.replace('&', '&amp;')
        txt = txt.replace('XXX_SAVE_AMPERSAND_XXX', '&amp;')
        return txt
    
    
    
def convert_from_pango(pango_markup):
    original_txt = pango_markup
    replacements = dict((('<b>', '**'), ('</b>', '**'),
                        ('<i>', '//'), ('</i>', '//'),
                        ('<s>', '--'), ('</s>', '--'),
                        ('<u>', '__'), ('</u>', '__'),
                        ('&amp;', '&'), 
                        ('&lt;', '<'), ('&gt;', '>'),
                        ))
    for orig, repl in replacements.items():
        pango_markup = pango_markup.replace(orig, repl)
        
    logging.log(5, 'Converted "%s" pango to "%s" txt2tags' % \
                (original_txt, pango_markup))
    return pango_markup


def get_table_markup(table):
    '''
    table is a list of lists
    
    return the txt2tags markup for that table
    '''
    table = map(lambda row: (str(cell) for cell in row), table)
    table = map(lambda row: '| ' + ' | '.join(row) + ' |', table)
    table[0] = '|' + table[0]
    return '\n'.join(table)


if __name__ == '__main__':
    markup = '''\
normal text, normal_text_with_underscores and ""raw_text_with_underscores""

[Link ""http://www.co.whatcom.wa.us/health/environmental/site_hazard/sitehazard.jsp""]
'''

    
    
    markup =  '[""/image"".png?50]\n'
    markup += '[""/image"".jpg]\n'
    markup += '[""file:///image"".png?10]\n'
    markup += '[""file:///image"".jpg]\n'
    
    markups = ['http://site/s.php?q&c', 'http://site/s.php?q&amp;c', '&', '&amp;']
    for markup in markups:
        print 'MARKUP    ', markup
        p = convert_to_pango(markup)
        print 'PANGO     ', p
        new_markup = convert_from_pango(p)
        print 'NEW MARKUP', new_markup
        print
    
    #html = convert(markup, 'xhtml')
    #print html
    
    #latex = convert(markup, 'tex')
    #print latex
    
    
                
