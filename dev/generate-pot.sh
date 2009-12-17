cd ../po

# Get strings from glade file into helper file
intltool-extract --local --type=gettext/glade ../rednotebook/files/mainWindow.glade

# Remove gtk-ok and gtk-cancel lines
sed -i '/"gtk-/d' tmp/mainWindow.glade.h

# Get strings from both glade helper file and the python files

# Write a list of all sourcefiles
find ../rednotebook -name "*.py" -not -path "*external*" -not -path "*keepnote*" > sourcefiles.txt

xgettext 	--output=rednotebook.pot \
			--language=Python \
			--keyword=_ \
			--keyword=N_ \
			--add-comments=/* \
			--add-comments=\#\# \
			--from-code=utf-8 \
			--files-from=sourcefiles.txt \
			tmp/mainWindow.glade.h
