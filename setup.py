#/usr/bin/python

import os
import sys

#print dir(sys)

from distutils.core import setup

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
)
