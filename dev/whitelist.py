import gettext
import os.path
import sys

import gi

gi.require_version("Gtk", "3.0")


class Dummy:
    def __getattr__(self, _):
        pass


gettext.install("dummy")

DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR)

sys.path.insert(0, BASE_DIR)

from rednotebook.journal import Journal

Journal.do_activate
Journal.do_startup

from gi.repository import Gtk

cell = Gtk.CellRendererText()
cell.props.wrap_mode

Dummy()._get_content
Dummy()._set_content
Dummy()._get_text
Dummy()._set_text
Dummy().insert_handler_wrapper

# CEF Browser
from ctypes import _CFuncPtr

_CFuncPtr.argtypes
_CFuncPtr.restype
Dummy().OnBeforeBrowse
sys.excepthook
