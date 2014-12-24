#! /bin/bash

set -e

cd "$(dirname "$0")"
cd ..

python dev/whitelist.py
vulture --exclude=external rednotebook dev/whitelist.py
