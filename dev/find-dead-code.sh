#! /bin/bash

set -euxo pipefail

cd "$(dirname "$0")"
cd ..

python3 -m flake8 --extend-ignore=E402 dev/whitelist.py
python3 dev/whitelist.py
python3 -m vulture --exclude=external rednotebook dev/whitelist.py
