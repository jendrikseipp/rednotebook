#! /usr/bin/env python

import logging
import os
import shutil

from utils import run, fetch, install, ensure_path, extract

logging.basicConfig(level=logging.INFO)

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)
WINE_DIR = os.path.join(BASE_DIR, 'wine-tmp')
DRIVE_C = os.path.join(WINE_DIR, 'drive_c')
WINE_TARBALL = os.path.expanduser('~/projects/RedNotebook/wine.tar.gz')
INSTALLERS_DIR = os.path.join(DIR, 'installers')

INSTALLERS = [
    ('http://python.org/ftp/python/2.7.6/python-2.7.6.msi', 'python-2.7.6.msi'),
    ('http://downloads.sourceforge.net/project/pywin32/pywin32/Build%20218/pywin32-218.win32-py2.7.exe?'
        'r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fpywin32%2Ffiles%2Fpywin32%2FBuild%2520218%2F&ts=1384187777&use_mirror=heanet',
     'pywin32-build218.exe'),
    ('http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi',
     'pygtk-all-in-one-2.24.2.win32-py2.7.msi'),
    ('http://pyyaml.org/download/pyyaml/PyYAML-3.10.win32-py2.7.exe',
     'PyYAML-3.10.win32-py2.7.exe')
]

TARBALLS = [
    ('https://pypi.python.org/packages/source/P/PyInstaller/PyInstaller-2.1.tar.gz',
     'pyinstaller-2.1.tar.gz', DRIVE_C),
    ('https://dl.dropboxusercontent.com/u/4780737/pywebkitgtk.zip',
     'pywebkitgtk.zip', os.path.join(DRIVE_C, 'Python27', 'Lib', 'site-packages')),
    # TODO: Add chardet.
]

#shutil.rmtree(WINE_DIR, ignore_errors=True)
os.environ['WINEPREFIX'] = WINE_DIR
ensure_path(WINE_DIR)
ensure_path(DRIVE_C)

for url, filename in INSTALLERS:
    path = os.path.join(INSTALLERS_DIR, filename)
    fetch(url, path)
    #install(path, dest=DRIVE_C)

for url, filename, dest in TARBALLS:
    path = os.path.join(INSTALLERS_DIR, filename)
    fetch(url, path)
    extract(path, dest)

run(['tar', '-czvf', WINE_TARBALL, '--directory', WINE_DIR, '.'])
#shutil.rmtree(WINE_DIR, ignore_errors=False)
