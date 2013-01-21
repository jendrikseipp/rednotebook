#! /usr/bin/env python

import os
import subprocess
import sys

basedir = 'C:\\Users\\Jendrik\\RedNotebook'
sys.path.insert(0, basedir)

from rednotebook import info

ISCC = 'C:\\Program Files (x86)\\Inno Setup 5\\ISCC.exe'
WIN_DIR = os.path.join(basedir, 'win')
ISS_SCRIPT = os.path.join(WIN_DIR, 'rednotebook.iss')
#NAME_PARAM = '/Frednotebook-%s' % info.version
VERSION_PARAM = '/dREDNOTEBOOK_VERSION=%s' % info.version

subprocess.call([ISCC, VERSION_PARAM, ISS_SCRIPT], cwd=WIN_DIR)
