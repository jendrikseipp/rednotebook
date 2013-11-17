#! /usr/bin/env python

import argparse
import os
import sys

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('locale_dir')
    return parser.parse_args()

args = parse_args()

basedir = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..'))
sys.path.insert(0, basedir)

import setup

po_dir = os.path.join(basedir, 'po')
locale_dir = os.path.abspath(args.locale_dir)
print 'Building translations'
print po_dir, '-->', locale_dir
setup.build_translation_files(po_dir, locale_dir)
