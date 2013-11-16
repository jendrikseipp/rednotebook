#! /usr/bin/env python

import argparse
import logging
import os
import shutil
import sys

from utils import run

logging.basicConfig(level=logging.INFO)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('wine_tarball')
    parser.add_argument('build_dir')
    return parser.parse_args()

args = parse_args()

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)
WINE_DIR = os.path.abspath(args.build_dir)
DRIVE_C = os.path.join(WINE_DIR, 'drive_c')
WINE_TARBALL = os.path.abspath(args.wine_tarball)
assert os.path.exists(WINE_TARBALL), WINE_TARBALL
WINE_RN_DIR = os.path.join(DRIVE_C, 'rednotebook')
WINE_RN_WIN_DIR = os.path.join(WINE_RN_DIR, 'win')
PYINSTALLER = os.path.join(DRIVE_C, 'PyInstaller-2.1', 'pyinstaller.py')
SPEC = os.path.join(BASE_DIR, 'win', 'rednotebook.spec')
WINE_SPEC = os.path.join(WINE_RN_WIN_DIR, 'rednotebook.spec')
WINE_BUILD = os.path.join(DRIVE_C, 'build')
WINE_DIST = os.path.join(DRIVE_C, 'dist')
LOCALE_DIR = os.path.join(WINE_DIST, 'share', 'locale')
WINE_RN_EXE = os.path.join(WINE_DIST, 'rednotebook.exe')
WINE_PYTHON = os.path.join(DRIVE_C, 'Python27', 'python.exe')

if os.path.exists(WINE_DIR):
    answer = raw_input('The build dir exists. Overwrite it? (Y/n): ').strip()
    if answer and answer.lower() != 'y':
        sys.exit('Aborting')
    shutil.rmtree(WINE_DIR)
os.environ['WINEPREFIX'] = WINE_DIR
os.mkdir(WINE_DIR)
run(['tar', '-xzf', WINE_TARBALL, '--directory', WINE_DIR])

run(['bzr', 'co', '--lightweight', BASE_DIR, WINE_RN_DIR])
shutil.copy2(SPEC, WINE_SPEC)

run(['wine', WINE_PYTHON, PYINSTALLER, '--workpath', WINE_BUILD,
     '--distpath', DRIVE_C, WINE_SPEC])  # will be built at ...DRIVE_C/dist
run(['./build-translations.py', LOCALE_DIR], cwd=DIR)

#run(['wine', WINE_RN_EXE])
