import gettext
import os.path
import sys

import gi
gi.require_version('Gtk', '3.0')

gettext.install('dummy')

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)

sys.path.insert(0, BASE_DIR)

from gi.repository import Gtk
cell = Gtk.CellRendererText()
cell.props.wrap_mode

from rednotebook.gui import imports
imports.ImportAssistant
imports.PlainTextImporter
imports.RedNotebookBackupImporter
imports.Importer._check_modules
