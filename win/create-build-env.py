#! /usr/bin/env python3

HELP = """\
Installation instructions:

For later wine versions installing the suggested gecko and mono packages
is optional. When asked to install them, you can click "Cancel".

Python installer:
  * Select "Add Python X.Y to PATH".
  * Click "Customize installation".
  * Customize install location to "C:\PythonXY".

PyGTK All-In-One Installer: Select the following packages on the
respective pages:
  1) GSpell, GTK+, Pango
  2) GtkSpell, GtkSourceView
  3) GIR

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

IS_WIN = sys.platform in ['cygwin', 'msys', 'win32']
USE_WINE = not IS_WIN

def parse_args():
    parser = argparse.ArgumentParser(description=HELP)
    if USE_WINE:
        parser.add_argument('build_dir')
    return parser.parse_args()

args = parse_args()

DIR = os.path.dirname(os.path.abspath(__file__))
INSTALLERS_DIR = os.path.join(DIR, 'installers')
REQUIREMENTS = os.path.join(DIR, 'requirements.txt')
DRIVE_C = 'C:\\'
SITE_PACKAGES = os.path.join(DRIVE_C, utils.PYTHON_DIRNAME, 'Lib', 'site-packages')
SEVEN_ZIP = os.path.join(DRIVE_C, 'Program Files (x86)', '7-Zip', '7z.exe')
if USE_WINE:
    BUILD_DIR = args.build_dir
    utils.confirm_overwrite(BUILD_DIR)
    os.environ['WINEPREFIX'] = BUILD_DIR
    DRIVE_C_REAL = os.path.join(BUILD_DIR, 'drive_c')
    PYTHON = ['wine', os.path.join(DRIVE_C_REAL, utils.PYTHON_DIRNAME, 'python.exe')]
else:
    DRIVE_C_REAL = DRIVE_C
    PYTHON = [os.path.join(DRIVE_C, utils.PYTHON_DIRNAME, 'python.exe')]


INSTALLERS = [
    #('http://downloads.sourceforge.net/project/sevenzip/7-Zip/9.20/7z920.exe?r=&ts=1384687929&use_mirror=netcologne',
    # '7z920.exe'),
    # Python 3.5 and 3.6 not supported by PyGObject AIO package. Also,
    # Python 3.5 needs wine-staging >= 2.8 and Python 3.6 fails for wine-staging 2.8.
    # Python 3.4.4 is the last version of 3.4 with an installer.
    # Python 3.4.4 works with wine-staging 2.14.
    # Python 3.6 does not work under wine 3.20.
    # Windows 7 makes distributing Python >= 3.5 easier (https://pyinstaller.readthedocs.io/en/stable/usage.html#platform-specific-notes-windows)
    ('https://www.python.org/ftp/python/3.6.7/python-3.6.7.exe',
     'python-3.6.7.exe'),
    #('https://downloads.sourceforge.net/project/pygobjectwin32/pygi-aio-3.18.2_rev12-setup_549872deadabb77a91efbc56c50fe15f969e5681.exe?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Fpygobjectwin32%2Ffiles%2F&ts=1495353417&use_mirror=vorboss',
    # 'pygi-aio-3.18.2_rev12-setup_549872deadabb77a91efbc56c50fe15f969e5681.exe'),
    ('http://files.jrsoftware.org/is/5/innosetup-5.6.1-unicode.exe',
     'innosetup-5.6.1-unicode.exe'),
]

TARBALLS = [
    #('https://www.dropbox.com/s/kljn5gsxm1fxa10/aspell-dicts.zip?dl=1',
    # 'aspell-dicts.zip',
    # os.path.join(SITE_PACKAGES, 'gnome/lib/aspell-0.60/')),
]

FILES = [
]

print(HELP)

# For Python >= 3.5 set Windows Version to at least Windows 7.
# run(['winecfg'])

for url, filename in INSTALLERS:
    path = os.path.join(INSTALLERS_DIR, filename)
    fetch(url, path)
    install(path, use_wine=USE_WINE)

for url, filename, dest in TARBALLS:
    path = os.path.join(INSTALLERS_DIR, filename)
    fetch(url, path)
    cmd = ['wine'] if USE_WINE else []
    assert path.endswith('.zip'), path
    cmd.extend([SEVEN_ZIP, 'x', '-o' + dest, path])
    run(cmd)

for url, dest in FILES:
    fetch(url, dest)

run(PYTHON + ['-m', 'pip', 'install', '-r', REQUIREMENTS])

if IS_WIN:
    logging.info('Make sure to add the directory %s to the system PATH.' %
        os.path.join(DRIVE_C, 'gtkbin'))
