import os.path
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)

sys.path.insert(0, BASE_DIR)

sys.stderr

from rednotebook.backup import Archiver
Archiver.check_last_backup_date

import gtk
cell = gtk.CellRendererText()
cell.props.wrap_mode

from rednotebook.gui import imports
imports.PlainTextImporter
imports.RedNotebookBackupImporter
imports.TomboyImporter
imports.Importer._check_modules

__builtins__._
