# -*- mode: python -*-
drive_c = '/home/jendrik/projects/RedNotebook/wine-test/drive_c'
basedir = os.path.join(drive_c, 'RedNotebook')
rndir = os.path.join(basedir, 'rednotebook')
gtkdir = os.path.join(basedir, 'dist')
icon = os.path.join(basedir, 'win', 'rednotebook.ico')
dlldir = os.path.join(drive_c, 'RedNotebook', 'dist')  # Effect unclear.

def Dir(path):
    assert os.path.isdir(path), path
    return Tree(path, prefix=os.path.basename(path))

a = Analysis([os.path.join(rndir, 'journal.py')],
             pathex=[basedir, dlldir],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name='rednotebook.exe',
          debug=True,
          strip=None,
          upx=True,
          console=True,
          icon=icon)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               Dir(os.path.join(rndir, 'files')),
               Dir(os.path.join(rndir, 'images')),
               Dir(os.path.join(gtkdir, 'etc')),
               Dir(os.path.join(gtkdir, 'lib')),
               Dir(os.path.join(gtkdir, 'share')),
               strip=None,
               upx=True,
               name='dist')
