import os
import site

drive_c = DISTPATH
basedir = os.path.join(drive_c, 'rednotebook')
srcdir = os.path.join(basedir, 'rednotebook')
bindir = os.path.join(site.getsitepackages()[1], 'gnome')
icon = os.path.join(basedir, 'win', 'rednotebook.ico')

# See also https://github.com/pyinstaller/pyinstaller/issues/1966
typelibdir = os.path.join(bindir, 'lib', 'girepository-1.0')

MISSED_BINARIES = [
    os.path.join(drive_c, path) for path in [
        'windows/syswow64/python34.dll',
        'Python34/DLLs/_ctypes.pyd',
        'Python34/DLLs/_socket.pyd',
        'Python34/DLLs/pyexpat.pyd',
    ]
]

for path in [drive_c, basedir, srcdir, bindir, icon] + MISSED_BINARIES:
    assert os.path.exists(path), "{} does not exist".format(path)

os.environ['PATH'] += os.pathsep + bindir
print('PATH:')
print(os.environ['PATH'])


def Dir(path):
    assert os.path.isdir(path), path
    return Tree(path, prefix=os.path.basename(path))

a = Analysis([os.path.join(srcdir, 'journal.py')],
             pathex=[basedir],
             hiddenimports=[],
             hookspath=None,
             binaries=[])
# Adding these files in the ctor mangles up the paths.
a.binaries = ([
    (os.path.join('gi_typelibs', tl), os.path.join(typelibdir, tl), 'BINARY') for tl in os.listdir(typelibdir)] + [
    (name, os.path.join(bindir, name), 'BINARY') for name in os.listdir(bindir) if name.endswith('.dll')] + [
    (os.path.basename(path), path, 'BINARY') for path in MISSED_BINARIES] + [
    (os.path.basename('gi._gi.pyd'), os.path.join(drive_c, 'Python34/Lib/site-packages/gi/_gi.pyd'), 'BINARY'),
    (os.path.basename('gi._gi_cairo.pyd'), os.path.join(drive_c, 'Python34/Lib/site-packages/gi/_gi_cairo.pyd'), 'BINARY'),
    ])
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
