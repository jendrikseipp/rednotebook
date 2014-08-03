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
import shutil
import sys
import tempfile
import time

from utils import run, fetch, install

logging.basicConfig(level=logging.INFO)

IS_WIN = sys.platform.startswith('win')
IS_LINUX = not IS_WIN  # OSX currently not supported.

def parse_args():
    parser = argparse.ArgumentParser(description=HELP)
    if IS_LINUX:
        parser.add_argument('dest_tarball')
        parser.add_argument('--keep-tmp-dir', action='store_true')
    return parser.parse_args()

args = parse_args()

DIR = os.path.dirname(os.path.abspath(__file__))
INSTALLERS_DIR = os.path.join(DIR, 'installers')
DRIVE_C = r'C:\\'
SITE_PACKAGES = os.path.join(DRIVE_C, 'Python27', 'Lib', 'site-packages')
SEVEN_ZIP = os.path.join(DRIVE_C, 'Program Files (x86)', '7-Zip', '7z.exe')
if IS_LINUX:
    WINE_DIR = tempfile.mkdtemp(suffix='-wine')
    logging.info('Temporary wine dir: %s' % WINE_DIR)
    os.environ['WINEPREFIX'] = WINE_DIR
    DRIVE_C_REAL = os.path.join(WINE_DIR, 'drive_c')
else:
    DRIVE_C_REAL = DRIVE_C


INSTALLERS = [
    ('http://downloads.sourceforge.net/project/sevenzip/7-Zip/9.20/7z920.exe?r=&ts=1384687929&use_mirror=netcologne',
     '7z920.exe'),
    ('http://python.org/ftp/python/2.7.6/python-2.7.6.msi',
     'python-2.7.6.msi'),
    ('http://downloads.sourceforge.net/project/pywin32/pywin32/Build%20218/pywin32-218.win32-py2.7.exe?r=&ts=1384687967&use_mirror=garr',
     'pywin32-build218.exe'),
    ('http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi',
     'pygtk-all-in-one-2.24.2.win32-py2.7.msi'),
    ('http://pyyaml.org/download/pyyaml/PyYAML-3.10.win32-py2.7.exe',
     'PyYAML-3.10.win32-py2.7.exe'),
    ('http://files.jrsoftware.org/is/5/isetup-5.5.4-unicode.exe',
     'isetup-5.5.4-unicode.exe'),
]

TARBALLS = [
    ('https://pypi.python.org/packages/source/P/PyInstaller/PyInstaller-2.1.zip',
     'PyInstaller-2.1.zip', DRIVE_C),
    ('https://dl.dropboxusercontent.com/u/4780737/gtkbin-1.7.3.zip',
     'gtkbin-1.7.3.zip', DRIVE_C),
    ('https://dl.dropboxusercontent.com/u/4780737/pywebkitgtk.zip',
     'pywebkitgtk.zip', SITE_PACKAGES),
    # TODO: Add chardet once we really use it and put it at the correct location.
    #('https://pypi.python.org/packages/source/c/chardet/chardet-2.1.1.tar.gz',
    # 'chardet-2.1.1.tar.gz', SITE_PACKAGES),
]

FILES = [('https://dl.dropboxusercontent.com/u/4780737/gtkspell.pyd',
          os.path.join(DRIVE_C_REAL, 'Python27', 'Lib', 'site-packages', 'gtkspell.pyd'))
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

if IS_LINUX:
    time.sleep(10)  # Without this tar complains about changing files.
    dest_tarball = os.path.abspath(args.dest_tarball)
    if not os.path.exists(os.path.dirname(dest_tarball)):
        os.makedirs(os.path.dirname(dest_tarball))
    run(['tar', '-czvf', dest_tarball, '--directory', WINE_DIR, '.'])
    if not args.keep_tmp_dir:
        shutil.rmtree(WINE_DIR, ignore_errors=False)
else:
    logging.info('Make sure to add the directory %s to the system PATH.' %
        os.path.join(DRIVE_C, 'bin'))
