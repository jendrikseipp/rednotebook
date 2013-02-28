REM Load key
C:\Users\Jendrik\Downloads\pageant.exe C:\Users\Jendrik\private-key.ppk

REM Update RedNotebook code
bzr update C:\Users\Jendrik\RedNotebook

C:\Python27\Scripts\py.test.exe C:\Users\Jendrik\RedNotebook\tests

python build-translations.py

python remove-build-dirs.py
python C:\pyinstaller\pyinstaller.py rednotebook.spec

dist\rednotebook.exe
