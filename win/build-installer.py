#! /usr/bin/env python

import argparse
import logging
import os

from utils import run

logging.basicConfig(level=logging.INFO)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('build_dir')
    parser.add_argument('version')
    return parser.parse_args()

args = parse_args()

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)
BUILD_DIR = os.path.abspath(args.build_dir)
DRIVE_C = os.path.join(BUILD_DIR, 'drive_c')
WINE_RN_DIR = os.path.join(DRIVE_C, 'rednotebook')
WINE_RN_WIN_DIR = os.path.join(WINE_RN_DIR, 'win')

os.environ['WINEPREFIX'] = BUILD_DIR
ISCC = os.path.join(DRIVE_C, 'Program Files (x86)', 'Inno Setup 5', 'ISCC.exe')
VERSION_PARAM = '/dREDNOTEBOOK_VERSION=%s' % args.version
run(['wine', ISCC, VERSION_PARAM, 'rednotebook.iss'], cwd=WINE_RN_WIN_DIR)
