#!/bin/bash

set -ue

cd "$(dirname "$0")"
cd ../

rm -rf dist/

# Force recalculation of files so that none is missed.
rm -f MANIFEST

python setup.py sdist
