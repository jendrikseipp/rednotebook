#! /usr/bin/env python

import logging
import os
import shutil
import subprocess

from utils import run

logging.basicConfig(level=logging.INFO)

# TODO: Use clean RedNotebook checkout.

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)
WINE_DIR = os.path.join(BASE_DIR, 'wine-test')
DRIVE_C = os.path.join(WINE_DIR, 'drive_c')
WINE_TARBALL = os.path.expanduser('~/projects/RedNotebook/wine.tar.gz')
assert os.path.exists(WINE_TARBALL), WINE_TARBALL
RN_WIN = '/media/jendrik/Windows7_OS/Users/Jendrik/RedNotebook'
WINE_RN_DIR = os.path.join(DRIVE_C, 'RedNotebook')
PYINSTALLER = os.path.join(DRIVE_C, 'PyInstaller-2.1', 'pyinstaller.py')
SPEC = os.path.join(BASE_DIR, 'win', 'rednotebook.spec')
WINE_SPEC = os.path.join(WINE_RN_DIR, 'win', 'rednotebook.spec')
WINE_BUILD = os.path.join(DRIVE_C, 'build')
WINE_DIST = os.path.join(DRIVE_C, 'dist')
WINE_RN_EXE = os.path.join(WINE_DIST, 'rednotebook.exe')
WINE_PYTHON = os.path.join(DRIVE_C, 'Python27', 'python.exe')

PATHS = ';'.join([os.path.join(WINE_RN_DIR, 'dist')])  # Effect unclear.

shutil.rmtree(WINE_DIR, ignore_errors=True)
os.environ['WINEPREFIX'] = WINE_DIR
os.mkdir(WINE_DIR)
run(['tar', '-xzvf', WINE_TARBALL, '--directory', WINE_DIR])

shutil.copytree(RN_WIN, WINE_RN_DIR, ignore=shutil.ignore_patterns('dist-bak', 'locale', '.bzr', 'build'))

import glob
DLLS = glob.glob(os.path.join(WINE_RN_DIR, 'dist', '*.dll'))

shutil.copy2(SPEC, WINE_SPEC)
run(['wine', WINE_PYTHON, PYINSTALLER, '--workpath', WINE_BUILD,
     '--distpath', DRIVE_C, '--paths', PATHS, WINE_SPEC])  # will be built at ...DRIVE_C/dist

for dll in DLLS:
    shutil.copy2(dll, WINE_DIST)

run(['wine', WINE_RN_EXE])
