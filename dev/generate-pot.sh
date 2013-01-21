#! /bin/bash
#
# Needs intltool package.

set -e
set -u

cd "$(dirname "$0")"
cd ../po

# Get strings from glade file into helper file
intltool-extract --local --type=gettext/glade ../rednotebook/files/main_window.glade

# Remove gtk-ok and gtk-cancel lines
sed -i '/"gtk-/d' tmp/main_window.glade.h

# Replace "/* abc */" with "### abc"
# The first character after the s is the separation character (!)
sed -i 's!/\*!###!g' tmp/main_window.glade.h
sed -i 's!\*/!!g' tmp/main_window.glade.h

# Get strings from both glade helper file and the python files

# Write a list of all sourcefiles
find ../rednotebook -name "*.py" -not -path "*external*" -not -path "*imports*"> sourcefiles.txt

xgettext    --output=rednotebook.pot \
            --language=Python \
            --keyword=_ \
            --keyword=N_ \
            --add-comments=\#\# \
            --from-code=utf-8 \
            --files-from=sourcefiles.txt \
            tmp/main_window.glade.h
