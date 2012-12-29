#!/bin/bash

# We cannot "set -e", because we need to check grep's exit code.
set -u

cd "$(dirname "$0")"
cd ../

# Run tests
py.test-2.7
pyflakes rednotebook | grep -v "undefined name '_'" | grep -v "rednotebook/external/txt2tags.py"
NOTHING_FOUND=$?
if [ $NOTHING_FOUND == 0 ]; then
    echo Pyflake found errors.
    exit 1
fi

rm -rf dist/

# Force recalculation of files so that none is missed
rm -f MANIFEST

python setup.py sdist
