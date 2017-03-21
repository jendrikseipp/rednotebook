#! /usr/bin/env python

HELP = """\
PyGTK All-In-One Installer: Install "PyRsvg" and "Language Tools".

InnoSetup: Do *not* create a start menu folder and do *not* associate
the .iss extension with InnoSetup. *Do* install the preprocessor.

For the other installers the default values are fine.
"""

import argparse
import logging
import os
import sys

import utils
from utils import run, fetch, install

logging.basicConfig(level=logging.INFO)

IS_WIN = sys.platform.startswith('win')
IS_LINUX = not IS_WIN  # OSX currently not supported.

def parse_args():
    parser = argparse.ArgumentParser(description=HELP)
    if IS_LINUX:
        parser.add_argument('build_dir')
    return parser.parse_args()

args = parse_args()

DIR = os.path.dirname(os.path.abspath(__file__))
INSTALLERS_DIR = os.path.join(DIR, 'installers')
REQUIREMENTS = os.path.join(DIR, 'requirements.txt')
DRIVE_C = 'C:\\'
SITE_PACKAGES = os.path.join(DRIVE_C, 'Python27', 'Lib', 'site-packages')
SEVEN_ZIP = os.path.join(DRIVE_C, 'Program Files (x86)', '7-Zip', '7z.exe')
if IS_LINUX:
    BUILD_DIR = args.build_dir
    utils.confirm_overwrite(BUILD_DIR)
    os.environ['WINEPREFIX'] = BUILD_DIR
    DRIVE_C_REAL = os.path.join(BUILD_DIR, 'drive_c')
    PYTHON = ['wine', os.path.join(DRIVE_C_REAL, 'Python27', 'python.exe')]
else:
    DRIVE_C_REAL = DRIVE_C
    PYTHON = [os.path.join(DRIVE_C,'Python27', 'python.exe')]


INSTALLERS = [
    ('http://downloads.sourceforge.net/project/sevenzip/7-Zip/9.20/7z920.exe?r=&ts=1384687929&use_mirror=netcologne',
     '7z920.exe'),
    ('https://www.python.org/ftp/python/2.7.12/python-2.7.12.msi',
     'python-2.7.12.msi'),
    ('http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi',
     'pygtk-all-in-one-2.24.2.win32-py2.7.msi'),
    ('http://files.jrsoftware.org/is/5/isetup-5.5.4-unicode.exe',
     'isetup-5.5.4-unicode.exe'),
]

TARBALLS = [
    ('https://dl.dropboxusercontent.com/u/4780737/gtkbin-1.7.3.zip',
     'gtkbin-1.7.3.zip', DRIVE_C),
    ('https://dl.dropboxusercontent.com/u/4780737/pywebkitgtk.zip',
     'pywebkitgtk.zip', SITE_PACKAGES),
]

FILES = [
    # Unneeded. Serves only as an example.
    #('https://dl.dropboxusercontent.com/u/4780737/gtkspell.pyd',
    #      os.path.join(DRIVE_C_REAL, 'Python27', 'Lib', 'site-packages', 'gtkspell.pyd'))
]

print HELP

for url, filename in INSTALLERS:
    path = os.path.join(INSTALLERS_DIR, filename)
    fetch(url, path)
    install(path, use_wine=IS_LINUX)

for url, filename, dest in TARBALLS:
    path = os.path.join(INSTALLERS_DIR, filename)
    fetch(url, path)
    cmd = ['wine'] if IS_LINUX else []
    assert path.endswith('.zip'), path
    cmd.extend([SEVEN_ZIP, 'x', '-o' + dest, path])
    run(cmd)

for url, dest in FILES:
    fetch(url, dest)

run(PYTHON + ['-m', 'pip', 'install', '-r', REQUIREMENTS])

if IS_WIN:
    logging.info('Make sure to add the directory %s to the system PATH.' %
        os.path.join(DRIVE_C, 'gtkbin'))
