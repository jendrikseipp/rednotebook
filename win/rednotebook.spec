# -*- mode: python -*-
import os
import site

block_cipher = None

options = [ ('v', None, 'OPTION'), ('u', None, 'OPTION') ]

drive_c = DISTPATH
basedir = os.path.join(drive_c, 'repo')
srcdir = os.path.join(basedir, 'rednotebook')
bindir = os.path.join(drive_c, 'gtk')
enchantdir = os.path.join(site.getsitepackages()[1], 'enchant')
icon = os.path.join(basedir, 'win', 'rednotebook.ico')


MISSED_BINARIES = [
    os.path.join(drive_c, path) for path in [
        'gtk/bin/gspawn-win32-helper.exe',
    ]
]

#for path in [drive_c, basedir, srcdir, bindir, icon] + MISSED_BINARIES:
#    assert os.path.exists(path), "{} does not exist".format(path)

#os.environ['PATH'] += os.pathsep + bindir
print('PATH:', os.environ['PATH'])


def Dir(path, excludes=None):
    assert os.path.isdir(path), path
    return Tree(path, prefix=os.path.basename(path), excludes=excludes or [])

def include_dll(name):
    # Exclude some unused large dlls to save space.
    return name.endswith('.dll') and name not in set([
        'libwebkit2gtk-3.0-25.dll', 'libavcodec-57.dll',
        'libjavascriptcoregtk-3.0-0.dll', 'libavformat-57.dll',
        'libgstreamer-1.0-0.dll'])


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
a.binaries += (
    [(os.path.basename(path), path, 'BINARY') for path in MISSED_BINARIES]
    #[(name, os.path.join(bindir, name), 'BINARY') for name in os.listdir(bindir) if include_dll(name)]
    )

# We need to manually copy the enchant directory, because we want to omit
# the DLLs and include the Python files. Keeping the DLLs leads to errors,
# because then there are multiple versions of the same DLL.
#a.binaries = [(dest, source, _) for (dest, source, _) in a.binaries if not dest.startswith('enchant')]
#a.datas = [(dest, source, _) for (dest, source, _) in a.datas if not dest.startswith('enchant')]

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
          console=True,
          icon=icon)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               Dir(os.path.join(srcdir, 'files')),
               Dir(os.path.join(srcdir, 'images')),
               #Dir(os.path.join(bindir, 'etc')),
               #Dir(os.path.join(bindir, 'lib'), excludes=['girepository-1.0', 'gstreamer-1.0']),
               #Dir(os.path.join(bindir, 'share'), excludes=['gir-1.0']),
               #Dir(enchantdir, excludes=['*.dll']),
               strip=False,
               upx=True,
               name='dist')
