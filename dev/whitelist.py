import __builtin__

import os.path
import sys

if not hasattr(__builtin__, '_'):
    __builtin__._ = lambda x: x

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
imports.ImportAssistant
imports.PlainTextImporter
imports.RedNotebookBackupImporter
imports.TomboyImporter
imports.Importer._check_modules

__builtins__._
