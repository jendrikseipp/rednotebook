# -*- mode: python -*-

import os
import os.path

block_cipher = None
debug = False

drive_c = DISTPATH
repo = "D:\\a\\rednotebook\\rednotebook"
gtkdir = os.path.join(drive_c, 'gtk')
srcdir = os.path.join(repo, 'rednotebook')
icon = os.path.join(repo, 'win', 'rednotebook.ico')

MISSED_BINARIES = [
    (os.path.join(gtkdir, src), destdir) for src, destdir in [
        ("bin/gdbus.exe", "."),
        ("bin/libenchant.dll", "."),
        ("lib/enchant/libenchant_myspell.dll", "lib/enchant/"),
    ]
]

# Add enchant dictionary files.
import glob
ENCHANT_DICT_FILES = []
dict_source_dir = os.path.join(gtkdir, "share", "enchant", "myspell", "myspell")
if os.path.exists(dict_source_dir):
    for dict_file in glob.glob(os.path.join(dict_source_dir, "*")):
        if os.path.isfile(dict_file):
            filename = os.path.basename(dict_file)
            ENCHANT_DICT_FILES.append((dict_file, "share/enchant/myspell"))

# Ensure at least one dictionary file was found.
assert ENCHANT_DICT_FILES, "No enchant dictionary files found in {}".format(dict_source_dir)

for path in [drive_c, repo, srcdir, icon] + [src for src, _ in MISSED_BINARIES]:
    assert os.path.exists(path), "{} does not exist".format(path)

print('PATH:', os.environ['PATH'])


def Dir(path, excludes=None):
    assert os.path.isdir(path), path
    return Tree(path, prefix=os.path.basename(path), excludes=excludes or [])

a = Analysis(
    [os.path.join(srcdir, 'journal.py')],
    pathex=[repo],
    binaries=MISSED_BINARIES,
    datas=ENCHANT_DICT_FILES,
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
