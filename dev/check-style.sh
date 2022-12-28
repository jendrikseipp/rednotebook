#!/bin/bash

set -exuo pipefail

cd "$(dirname "$0")"
cd ../

black --check --diff .

# E203: whitespace before ':' (not compliant with PEP 8)
# E402: module level import not at top of file
python3 -m flake8 --exclude=external --extend-ignore=E203,E402 --max-line-length=110 --builtins="_" rednotebook tests setup.py dev/whitelist.py

isort --check-only rednotebook/ tests/

python3 -m pyupgrade --py36-plus `find rednotebook tests -name "*.py" -not -path "*external*"`

python3 -m vulture --exclude=external rednotebook dev/whitelist.py

python3 setup.py --root=test-install

echo "All tests passed"
