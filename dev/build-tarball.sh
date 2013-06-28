#!/bin/bash

# We cannot "set -e", because we need to check grep's exit code.
set -u

cd "$(dirname "$0")"
cd ../

# Run tests
py.test-2.7
pyflakes rednotebook | grep -v "undefined name '_'" | grep -v "rednotebook/external/"
NOTHING_FOUND=$?
if [ $NOTHING_FOUND == 0 ]; then
    echo Pyflake found errors.
    exit 1
fi

# Check for PEP8 errors:
# E302: expected 2 blank lines, found 1
# E303: too many blank lines
# E241: multiple spaces after ':' (for t2t_highlight.py)
# E128: continuation line under-indented for visual indent
PEP8_OPTS="--ignore=E302,E303,E241,E128 --max-line-length=120"
pep8 $PEP8_OPTS --exclude=*external* rednotebook
if [ $? == 1 ]; then
    echo PEP8 errors detected.
    exit 1
fi

rm -rf dist/

# Force recalculation of files so that none is missed
rm -f MANIFEST

python setup.py sdist
