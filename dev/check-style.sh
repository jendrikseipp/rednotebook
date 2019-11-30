#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")"
cd ../

# E402: module level import not at top of file
python3 -m flake8 --exclude=external --extend-ignore=E402 --max-line-length=110 --builtins="_" rednotebook tests setup.py

python3 -m pyupgrade --py3-plus `find rednotebook tests -name "*.py" -not -path "*external*"`

./dev/find-dead-code.sh

python3 setup.py build_trans

echo "All tests passed"
