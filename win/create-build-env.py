#! /usr/bin/env python

"""
README:

PyGTK All-In-One Installer: Select to install "PyRsvg" and "Language
Tools".

InnoSetup: Do not create a folder in the start menu. Otherwise wine
1.6 will show you a winemenubuilder.exe error which can be ignored
however.

For the other installers the default values are fine.

Important: After extracting the gtk-runtime archive, add the contained
"bin" directory to the system PATH.
"""

import argparse
import logging
import os
import shutil
import tempfile

from utils import run, fetch, install, ensure_path, extract

logging.basicConfig(level=logging.INFO)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('dest_wine_tarball')
    parser.add_argument('--keep-tmp-dir', action='store_true')
    return parser.parse_args()

args = parse_args()

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)
WINE_DIR = tempfile.mkdtemp(suffix='-wine')
DRIVE_C = os.path.join(WINE_DIR, 'drive_c')
SITE_PACKAGES = os.path.join(DRIVE_C, 'Python27', 'Lib', 'site-packages')
WINE_TARBALL = os.path.abspath(args.dest_wine_tarball)
INSTALLERS_DIR = os.path.join(DIR, 'installers')

INSTALLERS = [
    ('http://python.org/ftp/python/2.7.6/python-2.7.6.msi', 'python-2.7.6.msi'),
    ('http://downloads.sourceforge.net/project/pywin32/pywin32/Build%20218/pywin32-218.win32-py2.7.exe?'
        'r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fpywin32%2Ffiles%2Fpywin32%2FBuild%2520218%2F&ts=1384187777&use_mirror=heanet',
     'pywin32-build218.exe'),
    ('http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi',
     'pygtk-all-in-one-2.24.2.win32-py2.7.msi'),
    ('http://pyyaml.org/download/pyyaml/PyYAML-3.10.win32-py2.7.exe',
     'PyYAML-3.10.win32-py2.7.exe'),
    ('http://files.jrsoftware.org/is/5/isetup-5.5.4-unicode.exe',
     'isetup-5.5.4-unicode.exe'),
]

TARBALLS = [
    ('https://pypi.python.org/packages/source/P/PyInstaller/PyInstaller-2.1.tar.gz',
     'pyinstaller-2.1.tar.gz', DRIVE_C),
    ('https://dl.dropboxusercontent.com/u/4780737/gtk-runtime-1.7.3.tar.gz',
     'gtk-runtime-1.7.3.tar.gz', DRIVE_C),
    ('https://dl.dropboxusercontent.com/u/4780737/pywebkitgtk.zip',
     'pywebkitgtk.zip', SITE_PACKAGES),
    # TODO: Add chardet once we really use it and put it at the correct location.
    #('https://pypi.python.org/packages/source/c/chardet/chardet-2.1.1.tar.gz',
    # 'chardet-2.1.1.tar.gz', SITE_PACKAGES),
]

logging.info('Temporary wine dir: %s' % WINE_DIR)
os.environ['WINEPREFIX'] = WINE_DIR
ensure_path(WINE_DIR)
ensure_path(DRIVE_C)

for url, filename in INSTALLERS:
    path = os.path.join(INSTALLERS_DIR, filename)
    fetch(url, path)
    install(path, dest=DRIVE_C)

for url, filename, dest in TARBALLS:
    path = os.path.join(INSTALLERS_DIR, filename)
    fetch(url, path)
    extract(path, dest)

run(['tar', '-czvf', WINE_TARBALL, '--directory', WINE_DIR, '.'])
if not args.keep_tmp_dir:
    shutil.rmtree(WINE_DIR, ignore_errors=False)
