#/usr/bin/python

import os
import sys

#print dir(sys)

from distutils.core import setup

if sys.platform == 'win32':
	print 'running on win32. Importing py2exe'
	import py2exe

#Testinstall with: python setup.py install --root=test

#print sys.argv[0]
baseDir = os.path.dirname(sys.argv[0])
sys.path.insert(0, baseDir)

from rednotebook import info
#rednotebookDir = os.path.join(setupDir, 'rednotebook

#Additionally use MANIFEST.in for image files
setup(name          = "rednotebook",
      version       = info.version,
      description   = "A Simple Desktop Diary",
      long_description = "RedNotebook is a diary that helps you keep track of your activities and thoughts",
      author        = info.author,
      author_email  = info.authorMail,
      maintainer        = info.author,
      maintainer_email  = info.authorMail,
      url           = info.url,
      license       = "GPL",
      keywords      = "diary",
      scripts       = ['rednotebook/rednotebook'],
      packages      = ['rednotebook', 'rednotebook.gui', 'rednotebook.util'],
      package_data  = {'rednotebook': ['images/*.png', 'images/redNotebookIcon/*.png']},
	  options = {'py2exe': {'bundle_files': 1,
	  						'includes': ['rednotebook.gui', 'rednotebook.util',]}},
	  #3 (default) don't bundle, 2: bundle everything but the Python interpreter, 1: bundle everything, including the Python interpreter 
	  options = {'py2exe': {'bundle_files': 1}}, 
	  #include library in exe
	  zipfile = None,
	  #windows for gui, console for cli
	  windows=['rednotebook/redNotebook.py'],
)
