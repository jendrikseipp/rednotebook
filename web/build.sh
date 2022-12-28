#! /bin/bash

set -euo pipefail

cd `dirname $0`

./../dev/generate-help.py > help.html

cd src/
# Use the "stable" changelog to omit unreleased changes.
wget https://raw.githubusercontent.com/jendrikseipp/rednotebook/stable/CHANGELOG.md
./changelog2html.py CHANGELOG.md
python spider.py
cd ../
