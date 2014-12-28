# -*- mode: python -*-
import inspect
import os

filename = inspect.getframeinfo(inspect.currentframe()).filename
specdir = os.path.dirname(os.path.abspath(filename))

drive_c = os.path.abspath(os.path.join(specdir, '..', '..'))
pyinstaller_dir = os.path.join(drive_c, 'PyInstaller-2.1')
basedir = os.path.join(drive_c, 'rednotebook')
srcdir = os.path.join(basedir, 'rednotebook')
bindir = os.path.join(drive_c, 'gtkbin')
icon = os.path.join(basedir, 'win', 'rednotebook.ico')

MISSED_DLLS = ['iconv.dll', 'libcroco-0.6-3.dll', 'librsvg-2-2.dll']

for path in [drive_c, pyinstaller_dir, basedir, srcdir, bindir, icon]:
    assert os.path.exists(path), path

os.environ['PATH'] += os.pathsep + bindir


def Dir(path):
    assert os.path.isdir(path), path
    return Tree(path, prefix=os.path.basename(path))

a = Analysis([os.path.join(srcdir, 'journal.py')],
             pathex=[pyinstaller_dir, basedir],
             hiddenimports=[],
             hookspath=None)
a.binaries += [(dll, os.path.join(bindir, dll), 'BINARY')
               for dll in MISSED_DLLS]
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name='rednotebook.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon=icon)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               Dir(os.path.join(srcdir, 'files')),
               Dir(os.path.join(srcdir, 'images')),
               Dir(os.path.join(bindir, 'etc')),
               Dir(os.path.join(bindir, 'lib')),
               Dir(os.path.join(bindir, 'share')),
               strip=None,
               upx=True,
               name='dist')
