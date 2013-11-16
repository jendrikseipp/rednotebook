#! /usr/bin/env python

import argparse
import logging
import os
from subprocess import call
import sys

logging.basicConfig(level=logging.INFO)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('src')
    parser.add_argument('--destdir', default='')
    return parser.parse_args()

args = parse_args()

src = os.path.abspath(args.src)
srcname = os.path.basename(src)
dest = os.path.join('/home/frs/project/r/re/rednotebook/', args.destdir.lstrip('/'), srcname)
call(['scp', src, 'jseipp,rednotebook@frs.sourceforge.net:%s' % dest])
