import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

print("Gtk import works")

from gi.repository import GObject

print("GObject import works")

gi.require_version("GtkSource", "4")
from gi.repository import GtkSource

print("GtkSource import works")

import os


def find_library(name):
    # See MSDN for the REAL search order.
    print("PATH", os.environ["PATH"])
    for directory in os.environ["PATH"].split(os.pathsep):
        fname = os.path.join(directory, name)
        print("DIR", directory)
        print("FNAME1", fname, os.path.isfile(fname))
        if os.path.isfile(fname):
            return fname
        if fname.lower().endswith(".dll"):
            continue
        fname = fname + ".dll"
        print("FNAME2", fname, os.path.isfile(fname))
        if os.path.isfile(fname):
            return fname
    return None


find_library("libenchant")

import enchant

print(enchant.list_languages())
print(enchant.list_dicts())
print("Enchant import works")
