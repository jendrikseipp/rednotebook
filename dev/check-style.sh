#!/bin/bash

set -exuo pipefail

cd "$(dirname "$0")"
cd ../

black --check .

# E203: whitespace before ':' (not compliant with PEP 8)
# E402: module level import not at top of file
python3 -m flake8 --exclude=external --extend-ignore=E203,E402 --max-line-length=110 --builtins="_" rednotebook tests setup.py

isort --check-only --recursive rednotebook/ tests/

python3 -m pyupgrade --py3-plus `find rednotebook tests -name "*.py" -not -path "*external*"`

./dev/find-dead-code.sh

python3 setup.py build_trans

echo "All tests passed"
