#! /usr/bin/env python3

"""
tar -czvf build-tar.gz build-dir:             1:40 min
tar -xzvf build-dir.tar.gz:                   0:32 min
cp -r build-dir build-dir-copy:               1:00 min
shutil.copytree(build-dir, build-dir-copy): >11:00 min
"""

import argparse
import logging
import os
import shutil

import utils
from utils import run

logging.basicConfig(level=logging.INFO)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('build_dir')
    parser.add_argument('dist_dir')
    parser.add_argument('--test', action='store_true')
    return parser.parse_args()

args = parse_args()

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)
DIST_DIR = os.path.abspath(args.dist_dir)
DRIVE_C = os.path.join(DIST_DIR, 'drive_c')
BUILD_DIR = os.path.abspath(args.build_dir)
assert os.path.exists(BUILD_DIR), BUILD_DIR
WINE_RN_DIR = os.path.join(DRIVE_C, 'rednotebook')
SPEC = os.path.join(BASE_DIR, 'win', 'rednotebook.spec')
WINE_BUILD = os.path.join(DRIVE_C, 'build')
WINE_DIST = os.path.join(DRIVE_C, 'dist')
LOCALE_DIR = os.path.join(WINE_DIST, 'share', 'locale')
WINE_RN_EXE = os.path.join(WINE_DIST, 'rednotebook.exe')
WINE_PYTHON = os.path.join(DRIVE_C, utils.PYTHON_DIRNAME, 'python.exe')

utils.confirm_overwrite(DIST_DIR)
os.environ['WINEPREFIX'] = DIST_DIR
utils.ensure_path(os.path.dirname(DIST_DIR))
print('Start copying {} to {}'.format(BUILD_DIR, DIST_DIR))
utils.fast_copytree(BUILD_DIR, DIST_DIR)
print('Finished copying')

archive = '/tmp/rednotebook-archive.tar'
stash_name = utils.get_output(['git', 'stash', 'create'], cwd=BASE_DIR)
stash_name = stash_name or 'HEAD'
run(['git', 'archive', stash_name, '-o', archive], cwd=BASE_DIR)
utils.ensure_path(WINE_RN_DIR)
run(['tar', '-xf', archive], cwd=WINE_RN_DIR)

os.mkdir(os.path.join(DRIVE_C, 'Python34/share'))
shutil.copytree(os.path.join(DRIVE_C, 'Python34/Lib/site-packages/gnome/share/gir-1.0/'), os.path.join(DRIVE_C, 'Python34/share/gir-1.0/'))

run(['wine', WINE_PYTHON, '-m', 'PyInstaller', '--workpath', WINE_BUILD,
     '--distpath', DRIVE_C, SPEC])  # will be built at ...DRIVE_C/dist
run(['python3', 'build-translations.py', LOCALE_DIR], cwd=DIR)

if args.test:
    run(['wine', WINE_RN_EXE])
