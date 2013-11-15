#! /usr/bin/env python

import os
import sys

from utils import run

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.basename(DIR)
BUILD_ENV_TARBALL = os.path.join(DIR, 'build-env.tar.gz')
BUILD_ENV = os.path.join(DIR, 'build-env')
DRIVE_C = os.path.join(BUILD_ENV, 'drive_c')

if not os.path.exists(BUILD_ENV_TARBALL):
    run(['./create-build-env.py', BUILD_ENV_TARBALL], cwd=DIR)
run(['./cross-compile-exe.py', BUILD_ENV_TARBALL, BUILD_ENV], cwd=DIR)

sys.path.insert(0, os.path.join(DRIVE_C, 'rednotebook'))
from rednotebook import info

INSTALLER = os.path.join(DRIVE_C, 'rednotebook-%s.exe' % info.version)
print INSTALLER
run(['./test-installer.py', INSTALLER], cwd=DIR)
#run(['./upload-file.sh', INSTALLER], cwd=os.path.join(BASE_DIR, 'dev'))

#run(['7z', 'a', 'rednotebook-%s.7z' % info.version, 'dist'], cwd=DRIVE_C)
