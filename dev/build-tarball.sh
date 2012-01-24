#!/bin/bash
set -e

cd ../
py.test
rm -rf dist/

# Force recalculation of files so that none is missed
rm MANIFEST

python setup.py sdist
