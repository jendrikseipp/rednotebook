#! /bin/bash

set -e

cd "$(dirname "$0")"
cd ..

python3 -m pyflakes dev/whitelist.py
python3 dev/whitelist.py
python3 -m vulture --exclude=external rednotebook dev/whitelist.py
