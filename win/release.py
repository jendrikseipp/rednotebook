#! /usr/bin/env python

import argparse
import os
import subprocess
import sys

from utils import run

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('build_dir')
    parser.add_argument('dist_dir')
    parser.add_argument('--beta', action='store_true')
    parser.add_argument('--upload', action='store_true')
    return parser.parse_args()

args = parse_args()

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)
BUILD_DIR = os.path.abspath(args.build_dir)
DIST_DIR = os.path.abspath(args.dist_dir)
DRIVE_C = os.path.join(DIST_DIR, 'drive_c')
RN_DIR = os.path.join(DRIVE_C, 'rednotebook')

os.environ['WINEPREFIX'] = DIST_DIR

run(['./cross-compile-exe.py', BUILD_DIR, DIST_DIR], cwd=DIR)

sys.path.insert(0, RN_DIR)
from rednotebook import info

def get_rev():
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=BASE_DIR)

version = info.version
if args.beta:
    version += '-r%s' % get_rev()
run(['./build-installer.py', DIST_DIR, version], cwd=DIR)
INSTALLER = os.path.join(DRIVE_C, 'rednotebook-%s.exe' % version)
if not args.beta:
    run(['./test-installer.py', INSTALLER], cwd=DIR)
destdir = 'beta' if args.beta else ''
if args.upload:
    run(['./upload-file.py', INSTALLER, '--destdir', destdir], cwd=os.path.join(BASE_DIR, 'dev'))

#run(['7z', 'a', 'rednotebook-%s.7z' % version, 'dist'], cwd=DRIVE_C)
