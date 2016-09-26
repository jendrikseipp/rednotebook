# -*- mode: python -*-

import os

drive_c = DISTPATH
basedir = os.path.join(drive_c, 'rednotebook')
srcdir = os.path.join(basedir, 'rednotebook')
bindir = os.path.join(drive_c, 'gtkbin')
icon = os.path.join(basedir, 'win', 'rednotebook.ico')
localesdb = os.path.join(drive_c, 'Python27', 'Lib', 'site-packages', 'pylocales', 'locales.db')

MISSED_DLLS = ['iconv.dll', 'libcroco-0.6-3.dll', 'librsvg-2-2.dll']

for path in [drive_c, basedir, srcdir, bindir, icon, localesdb]:
    assert os.path.exists(path), path

os.environ['PATH'] += os.pathsep + bindir


def Dir(path):
    assert os.path.isdir(path), path
    return Tree(path, prefix=os.path.basename(path))

a = Analysis([os.path.join(srcdir, 'journal.py')],
             pathex=[basedir],
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
               [(os.path.basename(localesdb), localesdb, 'DATA')],
               Dir(os.path.join(srcdir, 'files')),
               Dir(os.path.join(srcdir, 'images')),
               Dir(os.path.join(bindir, 'etc')),
               Dir(os.path.join(bindir, 'lib')),
               Dir(os.path.join(bindir, 'share')),
               strip=None,
               upx=True,
               name='dist')
