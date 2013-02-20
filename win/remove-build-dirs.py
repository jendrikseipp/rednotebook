#! /usr/bin/env python

import shutil

# Run multiple times to remove left-over dirs.
for run in range(5):
    for path in ('build', 'dist'):
        shutil.rmtree(path, ignore_errors=True)
