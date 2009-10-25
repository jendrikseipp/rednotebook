#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, shutil
from optparse import OptionParser, OptionValueError
from subprocess import call

current_dir = os.path.dirname(sys.argv[0])
base_dir = os.path.join(current_dir, os.pardir)
base_dir = os.path.abspath(base_dir)
sys.path.insert(0, base_dir)

from rednotebook import info

rednotebook_po_dir = os.path.join(base_dir, 'po')

def parse_options():
	parser = OptionParser(usage="usage: %prog",
						  description='Release Script for RedNotebook',
						  #option_class=ExtOption,
						  #formatter=utils.IndentedHelpFormatterWithNL(),
						  )	
	parser.add_option(
		'-p', '--po_dir', dest='po_dir', \
		default=None, action='store',
		help='From where shell I import the po_files? ' \
			'')
	
	options, args = parser.parse_args()
		
	return options, args

options, args = parse_options()

if not options.po_dir:
	sys.exit('Please provide a po-file dir')
	
if not os.path.exists(options.po_dir):
	sys.exit('po-file dir does not exist')
	
def import_po_files(dir):
	for base, dirs, files in os.walk(dir):
		for file in files:
			if file.endswith('.po'):
				old_filename = os.path.join(base, file)
				new_file = file.split('-')[-1]
				new_filename = os.path.join(rednotebook_po_dir, new_file)
				print 'Copying %s to %s' % (old_filename, new_filename)
				shutil.copy(old_filename, new_filename)
				
import_po_files(options.po_dir)
	


# delete dist dir
#dist_dir = os.path.join(base_dir, 'dist')
#if os.path.exists(dist_dir):
#	shutil.rmtree(dist_dir)

# Force recalculation of files so that none is missed
#manifest_file = os.path.join(base_dir, 'MANIFEST')
#if os.path.exists(manifest_file):
#	os.remove(manifest_file)
	
#call(['cd', base_dir])
#call(['python', os.path.join(base_dir, 'setup.py'), 'sdist'])


#cd dist/


#cp -f rednotebook-$VERSION.tar.gz ../releases/

#cd ../releases/

# Example: rsync -avP -e ssh FILE jsmith,fooproject@frs.sourceforge.net:/home/frs/project/f/fo/fooproject/Rel_1/
#rsync -avP -e ssh rednotebook-$VERSION.tar.gz jseipp,rednotebook@frs.sourceforge.net:/home/frs/project/r/re/rednotebook/



