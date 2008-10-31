#/usr/bin/python
#DISTUTILS_DEBUG = 'TRUE'
from distutils.core import setup

#Testinstall with: python setup.py install --root=test

#funktioniert so (nur ein Verzeichnis in site-packages)
#don't use MANIFEST.in
setup(name          = "rednotebook",
      version       = "0.1.0",
      description   = "A Simple Desktop Diary",
      long_description = "RedNotebook is a diary that helps you keep track of your activities and thoughts",
      author        = "Jendrik Seipp",
      author_email  = "jendrikseipp@web.de",
      maintainer        = "Jendrik Seipp",
      maintainer_email  = "jendrikseipp@web.de",
      url           = "http://rednotebook.sourceforge.net",
      license       = "GPL",
      keywords      = "diary",
      scripts       = ['rednotebook/rednotebook'],
      packages      = ['rednotebook', 'rednotebook.gui', 'rednotebook.util'],
      package_data  = {'rednotebook': ['images/*']},
      #data_files=[('lib/python2.5/site-packages/rednotebook/images', ['rednotebook/images/arrowUp.png', 'rednotebook/images/arrowDown.png']),
                  #('config', ['cfg/data.cfg']),
                  #('/etc/init.d', ['init-script'])
                  #],
)
