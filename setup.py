#/usr/bin/python

import sys

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup#, find_packages

# check for win32 support
if sys.platform == 'win32':
	#from distutils.core import setup
	# win32 allows building of executables
	import py2exe

# check for OS X support
#if sys.platform == 'darwin':
#    import py2app
#    pkg_data.append( ('../Frameworks', 
#       ['/usr/local/lib/wxPython-unicode-2.5.3.1/lib/libwx_macud-2.5.3.rsrc'])
#    )




#else:

	

#funktioniert so (nur ein Verzeichnis in site-packages)
#don't use MANIFEST.in
setup(name          = "rednotebook",
      version       = "0.1.0",
      description   = """A Simple Desktop Diary""",
      author        = "Jendrik Seipp",
      author_email  = "jendrikseipp@web.de",
      url           = "http://rednotebook.sourceforge.net",
      license       = "GPL",
      keywords      = "diary",
      packages      = ['rednotebook', 'rednotebook.gui', 'rednotebook.util'],
      #include_package_data = True,
      package_data  = {'rednotebook': ['images/*']},
      #install_requires = ['wxpython>=2.8.8.1'],
      entry_points = {
        #'console_scripts': [
        #    'foo = rednotebook.redNotebook:main',
        #],
        'gui_scripts': [
            'rednotebook = rednotebook.redNotebook:main', # : or . before main?
        ]
    }
)
