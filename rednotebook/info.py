# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2009-2015  Jendrik Seipp
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

import argparse

# This is required for setup.py to be able to import this module.
import builtins
if not hasattr(builtins, '_'):
    def _(string):
        return string


program_name = 'RedNotebook'
tagline = _('A Desktop Journal')
version = '2.11.1'
author = 'Jendrik Seipp'
author_mail = 'jendrikseipp@gmail.com'
copyright_ = 'Copyright (c) 2008-2018 Jendrik Seipp'
url = 'https://rednotebook.sourceforge.io'
downloads_url = 'https://rednotebook.sourceforge.io/downloads.html'
answers_url = 'https://answers.launchpad.net/rednotebook'
translation_url = 'https://translations.launchpad.net/rednotebook/'
bug_url = 'https://github.com/jendrikseipp/rednotebook/issues'
version_url = 'https://raw.githubusercontent.com/jendrikseipp/rednotebook/master/rednotebook/info.py'
contributors_url = 'https://github.com/jendrikseipp/rednotebook/graphs/contributors'

developers = ['%(author)s <%(author_mail)s>' % locals()]
artists = ['Ciaran']

comments = '''\
RedNotebook is a modern desktop journal. It lets you format, tag and
search your entries. You can also add pictures, links and customizable
templates, spell check your notes, and export to plain text, HTML,
Latex or PDF.
'''

journal_path_help = '''\
(optional) Specify the directory storing the journal data.
The journal argument can be one of the following:
 - An absolute path (e.g. /home/username/myjournal)
 - A relative path (e.g. ../dir/myjournal)
 - The name of a directory under $HOME/.rednotebook/ (e.g. myjournal)

If the journal argument is omitted then the last session's journal
path will be used. At the first program start, this defaults to
"$HOME/.rednotebook/data".
'''


def get_commandline_parser():
    parser = argparse.ArgumentParser(
        description=comments,
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        '--version', action='version', version='RedNotebook %s' % version)
    parser.add_argument(
        '--date', dest='start_date',
        help='load specified date (format: YYYY-MM-DD)')
    parser.add_argument('journal', nargs='?', help=journal_path_help)
    return parser


desktop_file = '''\
[Desktop Entry]
Version=1.0
Name=RedNotebook
GenericName=Journal
Comment=Daily journal with calendar, templates and keyword search
Exec=rednotebook
Icon=rednotebook
Terminal=false
Type=Application
Categories=Office;
StartupNotify=true
'''
