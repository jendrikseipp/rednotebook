REM Change into main directory
cd ../

python setup.py py2exe

cd dist

REM try the exe
redNotebook.exe
