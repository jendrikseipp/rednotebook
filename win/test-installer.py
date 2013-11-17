#! /usr/bin/env python

import argparse
import logging
import os
import tempfile

from utils import run

logging.basicConfig(level=logging.INFO)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('installer')
    return parser.parse_args()

args = parse_args()

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)
WINE_DIR = tempfile.mkdtemp(suffix='-wine')

logging.info('Temporary wine dir: %s' % WINE_DIR)
os.environ['WINEPREFIX'] = WINE_DIR
run(['wine', os.path.abspath(args.installer)])
