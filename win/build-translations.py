#! /usr/bin/env python

import os
import sys

basedir = 'C:\\Users\\Jendrik\\RedNotebook'
sys.path.insert(0, basedir)

from rednotebook.external import msgfmt
import setup

po_dir = os.path.join(basedir, 'po')
dest_path = os.path.join(basedir, 'dist', 'share', 'locale')
print 'Building translations'
print po_dir, '-->', dest_path
setup.build_translation_files(po_dir, dest_path)
