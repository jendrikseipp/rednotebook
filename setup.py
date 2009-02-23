#!/usr/bin/env python

import os
import sys

#print dir(sys)

from distutils.core import setup

if sys.platform == 'win32':
	print 'running on win32. Importing py2exe'
	import py2exe

#Testinstall with: python setup.py install --root=test

baseDir = os.path.dirname(sys.argv[0])
sys.path.insert(0, baseDir)

from rednotebook import info

parameters = {'name'          : 'rednotebook', 
      				'version'       : info.version, 
          			'description'   : "Graphical daily journal with calendar, templates and keyword searching", 
             		'long_description' : info.comments, 
               		'author'        : info.author, 
                 	'author_email'  : info.authorMail, 
                  	'maintainer'        : info.author, 
                   	'maintainer_email'  : info.authorMail, 
                    'url'           : info.url, 
                    'license'       : "GPL", 
                    'keywords'      : "diary", 
                    'scripts'       : ['rednotebook/rednotebook'], 
                    'packages'      : ['rednotebook', 'rednotebook.gui', 'rednotebook.util'], 
                    'package_data'  : {'rednotebook': ['images/*.png', 'images/redNotebookIcon/*.png',
														'files/*.css', 'files/*.glade', 'files/*.cfg',]},
                   }

#Debian parameters
if os.path.exists('/usr/share/applications/'):
	parameters['data_files'] = [('/usr/share/applications/', ['rednotebook.desktop']),
							    ('/usr/share/pixmaps/', ['rednotebook.png'])]

#For the use of py2exe you have to checkout the repository.
#To create Windows Installers have a look at the file 'win/win-build.txt'
py2exeParameters = {
	  				#3 (default) don't bundle, 
					#2: bundle everything but the Python interpreter, 
					#1: bundle everything, including the Python interpreter
					#It seems that only option 3 works with PyGTK
	  	  			'options' : {'py2exe': {'bundle_files': 3, 
											'includes': 'rednotebook.gui, rednotebook.util, cairo, pango, pangocairo, atk, gobject',
											'packages':'encodings',
											}
								}, 
	  				#include library in exe
	  	  			'zipfile' : None, 
	  				#windows for gui, console for cli
	  	  			'windows' : [{
									'script': 'rednotebook/redNotebook.py',
									'icon_resources': [(1, 'win/rednotebook.ico')],
									#Adding manifest seems to have no effect
									#"other_resources": [(24,1,manifest)], 
								}],
					'data_files' : [('files',['rednotebook/files/mainWindow.glade',
												'rednotebook/files/stylesheet.css',])],
	  	  			}

if 'py2exe' in sys.argv:
	parameters.update(py2exeParameters)   

#Additionally use MANIFEST.in for image files
setup(**parameters)
