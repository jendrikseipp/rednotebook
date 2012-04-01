#!/bin/bash
set -e

cd ../
py.test-2.7
rm -rf dist/

# Force recalculation of files so that none is missed
rm MANIFEST

python setup.py sdist
