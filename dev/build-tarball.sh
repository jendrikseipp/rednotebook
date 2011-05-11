#!/bin/bash
set -e

cd ../
rm -r dist/

# Force recalculation of files so that none is missed
rm MANIFEST

python setup.py sdist

#Move files
mv -f dist/rednotebook-*.tar.gz .
