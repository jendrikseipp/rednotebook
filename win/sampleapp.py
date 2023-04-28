import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

print("Gtk import works")

from gi.repository import GObject

print("GObject import works")

try:
    gi.require_version("GtkSource", "4")
    print("Using GtkSourceView 4")
except ValueError:
    gi.require_version("GtkSource", "3.0")
    print("Using GtkSourceView 3.0")
from gi.repository import GtkSource

print("GtkSource import works")


# Copied from ctypes module.
def find_library(name):
    import os

    print("PATH:", os.environ["PATH"])
    for directory in os.environ["PATH"].split(os.pathsep):
        fname = os.path.join(directory, name)
        print("Check directory", directory)
        print("Check filename", fname, os.path.isfile(fname))
        if os.path.isfile(fname):
            return fname
        if fname.lower().endswith(".dll"):
            continue
        fname = f"{fname}.dll"
        print("Check filename", fname, os.path.isfile(fname))
        if os.path.isfile(fname):
            return fname
    return None


find_library("libenchant")

import enchant

print("Languages:", enchant.list_languages())
print("Dictionaries:", enchant.list_dicts())
print("Enchant import works")
assert enchant.list_languages() and enchant.list_dicts()
print("Enchant finds languages and dictionaries")
