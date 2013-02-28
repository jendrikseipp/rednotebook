# -*- mode: python -*-
basedir = 'C:\\Users\\Jendrik\\RedNotebook'
rndir = os.path.join(basedir, 'rednotebook')
gtkdir = os.path.join(basedir, 'dist')
icon = os.path.join(basedir, 'win', 'rednotebook.ico')

def Dir(path):
    assert os.path.isdir(path), path
    return Tree(path, prefix=os.path.basename(path))

a = Analysis([os.path.join(rndir, 'journal.py')],
             pathex=['C:\\pyinstaller', basedir],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\rednotebook', 'rednotebook.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=False,
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
               [('librsvg-2-2.dll', os.path.join(gtkdir, 'librsvg-2-2.dll'), 'DATA')],
               [('libcroco-0.6-3.dll', os.path.join(gtkdir, 'libcroco-0.6-3.dll'), 'DATA')],
               strip=None,
               upx=True,
               name='dist')
