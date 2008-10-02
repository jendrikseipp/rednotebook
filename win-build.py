from distutils.core import setup
import py2exe

setup(name          = "rednotebook",
      version       = "0.1.0",
      description   = """A Simple Desktop Diary""",
      author        = "Jendrik Seipp",
      author_email  = "jendrikseipp@web.de",
      url           = "http://rednotebook.sourceforge.net",
      license       = "GPL",
      keywords      = "diary",
	  #package_dir   = {'rednotebook': 'rednotebook'},
      packages      = ['rednotebook', 'rednotebook.gui', 'rednotebook.util'],
      #include_package_data = True,
      package_data  = {'rednotebook': ['images/*.png']},
	  #copies the files into the subdirectory of dist
	  data_files=[('images', ['rednotebook/images/redNotebook-16.png']),
					('images', ['rednotebook/images/redNotebook-128.png']),
					('images', ['rednotebook/images/arrowUp.png']),
					('images', ['rednotebook/images/arrowDown.png']),
					('images', ['rednotebook/images/today-22.png'])],
       #           ('config', ['cfg/data.cfg']),
        #          ('/etc/init.d', ['init-script'])],

      #install_requires = ['wxpython>=2.8.8.1'],
      #entry_points = {
        #'console_scripts': [
        #    'foo = rednotebook.redNotebook:main',
        #],
        #'gui_scripts': [
        #    'rednotebook = rednotebook.redNotebook:main', # : or . before main?
        #]
    #}
	#windows for gui, console for cli
	windows=['rednotebook/redNotebook.py'],
	#zipfile = 'library',
	#3 (default) don't bundle, 2: bundle everything but the Python interpreter, 1: bundle everything, including the Python interpreter 
	options = {'py2exe': {'bundle_files': 1}}, 
	#include library in exe
	zipfile = None,

)
#setup(console=['rednotebook/redNotebook.py'])
