REM Load key
C:\Users\Jendrik\Downloads\pageant.exe C:\Users\Jendrik\private-key.ppk

REM Update RedNotebook code
bzr update C:\Users\Jendrik\RedNotebook

build-exe.bat
python build-installer.py

pause
