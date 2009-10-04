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
import glob
import fnmatch
from subprocess import call
from os.path import join

from distutils.core import setup, Extension
import distutils.command.install_data


if sys.platform == 'win32':
	print 'running on win32. Importing py2exe'
	import py2exe



baseDir = os.path.dirname(sys.argv[0])
sys.path.insert(0, baseDir)

from rednotebook import info
from rednotebook.external import msgfmt


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
		#cmd = ['msgfmt', '--output-file=%s' % mo_file, po_file]
		#print 'cmd', cmd
		
		for dir in [lang_dir, mo_dir]:
			if not os.path.exists(dir):
				os.mkdir(dir)
		
		#call(cmd)
		print 'Compiling %s to %s' % (po_file, mo_file)
		msgfmt.make(po_file, mo_file)
		
if 'i18n' in sys.argv:
	build_mo_files()
	sys.exit()
	
build_mo_files()

def get_data_base_dir():
	class helper_install_data(distutils.command.install_data.install_data):
		"""need to change self.install_dir to the actual library dir"""
		def get_data_dir(self):
			install_cmd = self.get_finalized_command('install')
			data_base_dir = getattr(install_cmd, 'install_data')
			return data_base_dir
	from distutils.dist import Distribution
	return helper_install_data(Distribution()).get_data_dir()

data_base_dir = get_data_base_dir()
print 'data_base_dir', data_base_dir


## Code borrowed from wxPython's setup and config files
## Thanks to Robin Dunn for the suggestion.
## I am not 100% sure what's going on, but it works!
def opj(*args):
	path = os.path.join(*args)
	return os.path.normpath(path)

## Added 10 Jan 2008
# Specializations of some distutils command classes
class wx_smart_install_data(distutils.command.install_data.install_data):
	"""need to change self.install_dir to the actual library dir"""
	def run(self):
		install_cmd = self.get_finalized_command('install')
		self.install_dir = getattr(install_cmd, 'install_lib')
		print self.install_dir
		print
		print dir(install_cmd)
		print
		#global data_base_dir
		#data_base_dir = getattr(install_cmd, 'install_data')
		#sys.exit()
		return distutils.command.install_data.install_data.run(self)

def find_data_files(srcdir, *wildcards, **kw):
	# get a list of all files under the srcdir matching wildcards,
	# returned in a format to be used for install_data
	def walk_helper(arg, dirname, files):
		if '.svn' in dirname:
			return
		names = []
		lst, wildcards = arg
		for wc in wildcards:
			wc_name = opj(dirname, wc)
			for f in files:
				filename = opj(dirname, f)

				if fnmatch.fnmatch(filename, wc_name) and not os.path.isdir(filename):
					names.append(filename)
		if names:
			lst.append( (dirname, names ) )

	file_list = []
	recursive = kw.get('recursive', True)
	if recursive:
		os.path.walk(srcdir, walk_helper, (file_list, wildcards))
	else:
		walk_helper((file_list, wildcards),
					srcdir,
					[os.path.basename(f) for f in glob.glob(opj(srcdir, '*'))])
	return file_list



parameters = {	'name'				: 'rednotebook', 
				'version'			: info.version, 
				'description'		: 'Graphical daily journal with calendar, ' \
										'templates and keyword searching', 
				'long_description'	: info.comments, 
				'author'			: info.author, 
				'author_email'		: info.authorMail, 
				'maintainer'		: info.author, 
				'maintainer_email'	: info.authorMail, 
				'url'				: info.url, 
				'license'			: "GPL", 
				'keywords'			: "journal, diary", 
				'scripts'			: ['rednotebook/rednotebook'], 
				'packages'			: ['rednotebook', 'rednotebook.util', 'rednotebook.gui', \
										'rednotebook.external',
										'rednotebook.gui.keepnote', 'rednotebook.gui.keepnote.gui', \
										'rednotebook.gui.keepnote.gui.richtext'],
				'package_data'		: {'rednotebook': 
										['images/*.png', 'images/redNotebookIcon/*.png',
										'files/*.css', 'files/*.glade', 'files/*.cfg',]},
				'data_files'		: [],
				
				## Borrowed from wxPython too:
				## Causes the data_files to be installed into the modules directory.
				## Override some of the default distutils command classes with my own.
				'cmdclass'			: {'install_data': wx_smart_install_data},
			}
			


## This is a list of files to install, and where:
## Make sure the MANIFEST.in file points to all the right 
## directories too.
mo_files = find_data_files('rednotebook/i18n', '*.mo')

print 'mo_files', mo_files
			
if 'install' in sys.argv:
	parameters['data_files'].extend(mo_files)

# Freedesktop parameters
if os.path.exists(os.path.join(sys.prefix, 'share/applications/')):
	share_dir = join(data_base_dir, 'share')
	parameters['data_files'].extend([
			(join(share_dir, 'applications'), ['rednotebook.desktop']),
			(join(share_dir, 'icons/hicolor/48x48/apps'), ['rednotebook.png']),# new freedesktop.org spec
			(join(share_dir, 'pixmaps'), ['rednotebook.png']),				# for older configurations
			])

def get_image_files():
	image_dir = 'rednotebook/images/'
	all_files_in_pic_dir = os.listdir('rednotebook/images/')
	all_files_in_pic_dir = map(lambda file: os.path.join(image_dir, file), all_files_in_pic_dir)
	return filter(lambda file: file.endswith('.png'), all_files_in_pic_dir)

# For the use of py2exe you have to checkout the repository.
# To create Windows Installers have a look at the file 'win/win-build.txt'
if 'py2exe' in sys.argv:
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
	  	  			}

	parameters['data_files'].extend([('files', ['rednotebook/files/mainWindow.glade',
												'rednotebook/files/stylesheet.css',
												'rednotebook/files/default.cfg']),
									('images', get_image_files()),
									('images/redNotebookIcon', \
										['rednotebook/images/redNotebookIcon/rn-32.png']),])
	parameters.update(py2exeParameters)
	
print parameters['data_files']
#sys.exit()


#Additionally use MANIFEST.in for image files
setup(**parameters)






