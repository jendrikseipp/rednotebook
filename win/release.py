#! /usr/bin/env python

import argparse
import os
import sys

from utils import run

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--beta', action='store_true')
    return parser.parse_args()

args = parse_args()

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)
BUILD_ENV_TARBALL = os.path.join(DIR, 'build-env.tar.gz')
BUILD_ENV = os.path.join(DIR, 'build-env')
DRIVE_C = os.path.join(BUILD_ENV, 'drive_c')
RN_DIR = os.path.join(DRIVE_C, 'rednotebook')

os.environ['WINEPREFIX'] = BUILD_ENV

if not os.path.exists(BUILD_ENV_TARBALL):
    run(['./create-build-env.py', BUILD_ENV_TARBALL], cwd=DIR)
run(['./cross-compile-exe.py', BUILD_ENV_TARBALL, BUILD_ENV], cwd=DIR)

sys.path.insert(0, RN_DIR)
from rednotebook import info

def get_rev():
    revfile = os.path.join(RN_DIR, 'rednotebook', 'rev.py')
    with open(revfile, 'w') as f:
        run(['bzr', 'version-info', '--format', 'python'], stdout=f, cwd=RN_DIR)
    from rednotebook import rev
    return rev.version_info['revno']

version = info.version
if args.beta:
    version += '-r%s' % get_rev()
run(['./build-installer.py', BUILD_ENV, version], cwd=DIR)
INSTALLER = os.path.join(DRIVE_C, 'rednotebook-%s.exe' % version)
if not args.beta:
    run(['./test-installer.py', INSTALLER], cwd=DIR)
destdir = 'beta' if args.beta else ''
run(['./upload-file.py', INSTALLER, '--destdir', destdir], cwd=os.path.join(BASE_DIR, 'dev'))

#run(['7z', 'a', 'rednotebook-%s.7z' % version, 'dist'], cwd=DRIVE_C)
