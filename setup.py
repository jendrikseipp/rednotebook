#!/usr/bin/env python
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

"""
This is the install file for RedNotebook.

To install the program, run "python setup.py install"
To do a (test) installation to a different dir: "python setup.py install --root=test-dir"
To only compile the translations, run "python setup.py build_trans"
"""

import os
import sys
from glob import glob
import shutil

from distutils.core import setup
from distutils import cmd
from distutils.command.install_data import install_data as _install_data
from distutils.command.build import build as _build

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rednotebook import info
from rednotebook.external import msgfmt


def build_translation_files(po_dir, locale_dir):
    assert os.path.isdir(po_dir), po_dir
    for path, names, filenames in os.walk(po_dir):
        for f in filenames:
            if f.endswith('.po'):
                lang = os.path.splitext(f)[0]
                src = os.path.join(path, f)
                dest = os.path.join(locale_dir, lang, 'LC_MESSAGES', 'rednotebook.mo')
                dest_dir = os.path.dirname(dest)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                # Recompile only if compiled version is outdated.
                if not os.path.exists(dest):
                    print 'Compiling %s' % src
                    msgfmt.make(src, dest)
                else:
                    src_mtime = os.stat(src)[8]
                    dest_mtime = os.stat(dest)[8]
                    if src_mtime > dest_mtime:
                        print 'Compiling %s' % src
                        msgfmt.make(src, dest)


class build_trans(cmd.Command):
    """
    Code taken from mussorgsky
    (https://garage.maemo.org/plugins/ggit/browse.php/?p=mussorgsky;a=blob;f=setup.py;hb=HEAD)
    """
    description = 'Compile .po files into .mo files'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        po_dir = os.path.join(os.path.dirname(os.curdir), 'po')
        dest_path = os.path.join('build', 'locale')
        build_translation_files(po_dir, dest_path)


class build(_build):
    sub_commands = _build.sub_commands + [('build_trans', None)]

    def run(self):
        _build.run(self)


class install_data(_install_data):
    def run(self):
        for lang in os.listdir('build/locale/'):
            lang_dir = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
            lang_file = os.path.join('build', 'locale', lang, 'LC_MESSAGES', 'rednotebook.mo')
            self.data_files.append( (lang_dir, [lang_file]) )
        _install_data.run(self)


cmdclass = {
    'build': build,
    'build_trans': build_trans,
    'install_data': install_data,
}


parameters = {
    'name'              : 'rednotebook',
    'version'           : info.version,
    'description'       : 'Graphical daily journal with calendar, '
                          'templates and keyword searching',
    'long_description'  : info.comments,
    'author'            : info.author,
    'author_email'      : info.authorMail,
    'maintainer'        : info.author,
    'maintainer_email'  : info.authorMail,
    'url'               : info.url,
    'license'           : "GPL",
    'keywords'          : "journal, diary",
    'scripts'           : ['rednotebook/rednotebook'],
    'packages'          : ['rednotebook', 'rednotebook.external',
                           'rednotebook.gui', 'rednotebook.util'],
    'package_data'      : {'rednotebook':
                           ['images/*.png', 'images/rednotebook-icon/*.png',
                            'images/rednotebook-icon/rednotebook.svg',
                            'files/*.css', 'files/*.glade', 'files/*.cfg']},
    'data_files'        : [('share/applications',
                            ['rednotebook.desktop']),
                           ('share/icons/hicolor/scalable/apps',
                            ['rednotebook/images/rednotebook-icon/rednotebook.svg']),
                          ],
    'cmdclass'          : cmdclass,
}

if __name__ == '__main__':
    # Additionally use MANIFEST.in for image files
    setup(**parameters)
