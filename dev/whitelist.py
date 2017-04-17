import builtins

import os.path
import sys

if not hasattr(builtins, '_'):
    builtins._ = lambda x: x

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)

sys.path.insert(0, BASE_DIR)

sys.stderr

from rednotebook.backup import Archiver
Archiver.check_last_backup_date

from gi.repository import Gtk
cell = Gtk.CellRendererText()
cell.props.wrap_mode

from rednotebook.gui import imports
imports.ImportAssistant
imports.PlainTextImporter
imports.RedNotebookBackupImporter
imports.TomboyImporter
imports.Importer._check_modules

__builtins__._
