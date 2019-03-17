# -*- mode: python -*-
import os
import os.path

block_cipher = None

# v: log imports, u: unbuffered output
options = [] # [('v', None, 'OPTION'), ('u', None, 'OPTION')]

drive_c = DISTPATH
basedir = os.path.join(drive_c, 'repo')
srcdir = os.path.join(basedir, 'rednotebook')
bindir = os.path.join(drive_c, 'gtk')
icon = os.path.join(basedir, 'win', 'rednotebook.ico')

MISSED_BINARIES = [
    os.path.join(drive_c, path) for path in [
        'gtk/bin/gspawn-win32-helper.exe',
    ]
]

for path in [drive_c, basedir, srcdir, bindir, icon] + MISSED_BINARIES:
    assert os.path.exists(path), "{} does not exist".format(path)

print('PATH:', os.environ['PATH'])


def Dir(path, excludes=None):
    assert os.path.isdir(path), path
    return Tree(path, prefix=os.path.basename(path), excludes=excludes or [])

a = Analysis([os.path.join(srcdir, 'journal.py')],
             pathex=[basedir],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=["."],  # To find custom hooks.
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
# Adding these files in the ctor mangles up the paths.
a.binaries += [(os.path.basename(path), path, 'BINARY') for path in MISSED_BINARIES]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          options,
          exclude_binaries=True,
          name='rednotebook.exe',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon=icon)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               Dir(os.path.join(srcdir, 'files')),
               Dir(os.path.join(srcdir, 'images')),
               strip=False,
               upx=True,
               name='dist')
