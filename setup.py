#/usr/bin/python
#DISTUTILS_DEBUG = 'TRUE'
from distutils.core import setup

#Testinstall with: python setup.py install --root=test

import os
if os.environ['DISTUTILS_DEBUG']:
        print 'Hello, ', os.environ['DISTUTILS_DEBUG']


#funktioniert so (nur ein Verzeichnis in site-packages)
#don't use MANIFEST.in
setup(name          = "rednotebook",
      version       = "0.1.0",
      description   = "A Simple Desktop Diary",
      author        = "Jendrik Seipp",
      author_email  = "jendrikseipp@web.de",
      url           = "http://rednotebook.sourceforge.net",
      license       = "GPL",
      keywords      = "diary",
      scripts       = ['rednotebook/rednotebook'],
      packages      = ['rednotebook', 'rednotebook.gui', 'rednotebook.uti'],
      package_data  = {'rednotebook': ['images/*']},
)