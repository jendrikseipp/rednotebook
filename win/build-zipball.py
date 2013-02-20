#! /usr/bin/env python

import os
import subprocess
import sys
import zipfile

basedir = 'C:\\Users\\Jendrik\\RedNotebook'
sys.path.insert(0, basedir)

from rednotebook import info

DIST_DIR = os.path.join(basedir, 'win', 'dist')
assert os.path.exists(DIST_DIR), 'build-exe must be run before build-zipball'
ARCHIVE = 'C:\\Users\\Jendrik\\Dropbox\\Public\\rednotebook-%s.zip' % info.version

archive = zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED)
archive_files = []
for root, dirs, files in os.walk(DIST_DIR):
    for file in files:
        archive_files.append(os.path.join(root, file))
for file in archive_files:
    archive.write(file, os.path.relpath(file, start=DIST_DIR))
archive.close()
