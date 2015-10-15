#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")"
cd ../

py.test tests

set +eo pipefail
pyflakes rednotebook tests | grep -v "undefined name '_'" | grep -v "rednotebook/external/"
retval=$?
set -eo pipefail
if [[ $retval == 0 ]]; then
    echo "pyflakes found errors."
    exit 1
fi

# Check for PEP8 errors:
# E402: module level import not at top of file
PEP8_OPTS="--max-line-length=110"
pep8 $PEP8_OPTS --exclude=external,journal.py rednotebook tests
pep8 $PEP8_OPTS --ignore=E402 rednotebook/journal.py

./dev/find-dead-code

echo "All tests passed"
