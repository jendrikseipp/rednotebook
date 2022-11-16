# -*- mode: python -*-

import os
import os.path

block_cipher = None
debug = False

drive_c = DISTPATH
basedir = os.path.join(drive_c, 'repo')
gtkdir = os.path.join(drive_c, 'gtk')
srcdir = os.path.join(basedir, 'rednotebook')
icon = os.path.join(basedir, 'win', 'rednotebook.ico')

MISSED_BINARIES = [
    (os.path.join(gtkdir, src), destdir) for src, destdir in [
        ("bin/gdbus.exe", "."),
        ("bin/libenchant.dll", "."),
        ("lib/enchant/libenchant_myspell.dll", "lib/enchant/"),
    ]
]

for path in [drive_c, basedir, srcdir, icon] + [src for src, _ in MISSED_BINARIES]:
    assert os.path.exists(path), "{} does not exist".format(path)

print('PATH:', os.environ['PATH'])


def Dir(path, excludes=None):
    assert os.path.isdir(path), path
    return Tree(path, prefix=os.path.basename(path), excludes=excludes or [])

a = Analysis(
    [os.path.join(srcdir, 'journal.py')],
    pathex=[basedir],
    binaries=MISSED_BINARIES,
    datas=[],
    hiddenimports=[],
    hookspath=["."],  # To find custom hooks.
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='rednotebook.exe',
    debug=debug,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=debug,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    Dir(os.path.join(srcdir, 'files')),
    Dir(os.path.join(srcdir, 'images')),
    strip=False,
    upx=True,
    upx_exclude=[],
    name='dist',
)
