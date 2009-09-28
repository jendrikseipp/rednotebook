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

'''
This is the install file for RedNotebook.

To install the program, run "python setup.py install"

To do a (test) installation to a different dir: "python setup.py install --root=test-dir"

To only compile the translations, run "python setup.py i18n"
'''

import os
import sys
from subprocess import call

from distutils.core import setup

if sys.platform == 'win32':
	print 'running on win32. Importing py2exe'
	import py2exe



baseDir = os.path.dirname(sys.argv[0])
sys.path.insert(0, baseDir)

from rednotebook import info


# i18n
def build_mo_files():
	'''
	Little script that compiles all available po files into mo files
	'''
	
	po_dir = 'po'
	i18n_dir = 'rednotebook/i18n/'

	if not os.path.exists(i18n_dir):
		os.mkdir(i18n_dir)

	available_langs = os.listdir(po_dir)
	available_langs = filter(lambda file: file.endswith('.po'), available_langs)
	available_langs = map(lambda file: file[:-3], available_langs)

	print 'langs', available_langs

	for lang in available_langs:
		po_file = os.path.join(po_dir, lang+'.po')
		lang_dir = os.path.join(i18n_dir, lang)
		mo_dir = os.path.join(lang_dir, 'LC_MESSAGES')
		mo_file = os.path.join(mo_dir, 'rednotebook.mo')
		cmd = ['msgfmt', '--output-file=%s' % mo_file, po_file]
		print 'cmd', cmd
		
		for dir in [lang_dir, mo_dir]:
			if not os.path.exists(dir):
				os.mkdir(dir)
		
		call(cmd)
		
if 'i18n' in sys.argv:
	build_mo_files()
	sys.exit()



parameters = {	'name'          	: 'rednotebook', 
				'version'       	: info.version, 
				'description'   	: 'Graphical daily journal with calendar, ' \
										'templates and keyword searching', 
				'long_description' 	: info.comments, 
				'author'        	: info.author, 
				'author_email'  	: info.authorMail, 
				'maintainer'        : info.author, 
				'maintainer_email'  : info.authorMail, 
				'url'           	: info.url, 
				'license'       	: "GPL", 
				'keywords'      	: "diary", 
				'scripts'       	: ['rednotebook/rednotebook'], 

				'packages'      	: ['rednotebook', 'rednotebook.util', 'rednotebook.gui', \
										'rednotebook.gui.keepnote', 'rednotebook.gui.keepnote.gui', \
										'rednotebook.gui.keepnote.gui.richtext'],
				'package_data'  	: {'rednotebook': ['images/*.png', 'images/redNotebookIcon/*.png',
														'files/*.css', 'files/*.glade', 'files/*.cfg',]},
			}

# Freedesktop parameters
if os.path.exists(os.path.join(sys.prefix, 'share/applications/')):
	parameters['data_files'] = [('share/applications/', ['rednotebook.desktop']),
							    ('share/icons/hicolor/48x48/apps', ['rednotebook.png']),# new freedesktop.org spec
							    ('share/pixmaps/', ['rednotebook.png']),				# for older configurations
							    ]

def get_image_files():
	image_dir = 'rednotebook/images/'
	all_files_in_pic_dir = os.listdir('rednotebook/images/')
	all_files_in_pic_dir = map(lambda file: os.path.join(image_dir, file), all_files_in_pic_dir)
	return filter(lambda file: file.endswith('.png'), all_files_in_pic_dir)

# For the use of py2exe you have to checkout the repository.
# To create Windows Installers have a look at the file 'win/win-build.txt'
py2exeParameters = {
	  				#3 (default) don't bundle, 
					#2: bundle everything but the Python interpreter, 
					#1: bundle everything, including the Python interpreter
					#It seems that only option 3 works with PyGTK
	  	  			'options' : {'py2exe': {'bundle_files': 3,
											'includes': 'rednotebook.gui, rednotebook.util, cairo, pango, pangocairo, atk, gobject',
											'packages':'encodings',
											#'skip_archive': 1,
											}
								}, 
	  				#include library in exe
	  	  			'zipfile' : None, 
					
	  				#windows for gui, console for cli
	  	  			'windows' : [{
									'script': 'rednotebook/redNotebook.py',
									'icon_resources': [(1, 'win/rednotebook.ico')],
								}],
					'data_files' : [('files', ['rednotebook/files/mainWindow.glade',
												'rednotebook/files/stylesheet.css',
												'rednotebook/files/default.cfg']),
									('images', get_image_files()),
									('images/redNotebookIcon', ['rednotebook/images/redNotebookIcon/rn-32.png']),],
	  	  			}

if 'py2exe' in sys.argv:
	parameters.update(py2exeParameters)   


#Additionally use MANIFEST.in for image files
setup(**parameters)

build_mo_files()




