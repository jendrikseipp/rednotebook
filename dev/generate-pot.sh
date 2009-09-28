cd ../po

# Get strings from glade file into helper file
intltool-extract --local --type=gettext/glade ../rednotebook/files/mainWindow.glade

# Get strings from both glade helper file and the python files

# Write a list of all sourcefiles
find ../rednotebook -name "*.py" -not -name "txt2tags.py" -not -path "*keepnote*" > sourcefiles.txt

xgettext --output=rednotebook.pot --language=Python --keyword=_ --keyword=N_ --from-code=utf-8 --files-from=sourcefiles.txt tmp/mainWindow.glade.h
