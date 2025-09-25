import gi


gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: F401


print("Gtk import works")

from gi.repository import GObject  # noqa: F401


print("GObject import works")

try:
    gi.require_version("GtkSource", "4")
    print("Using GtkSourceView 4")
except ValueError:
    gi.require_version("GtkSource", "3.0")
    print("Using GtkSourceView 3.0")
from gi.repository import GtkSource  # noqa: F401


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

# Only require enchant dictionaries to work in PyInstaller bundle.
# In regular test runs, the system enchant might not be configured correctly.
import sys


if getattr(sys, "frozen", False):
    # Running in PyInstaller bundle.
    assert enchant.list_languages() and enchant.list_dicts()
    print("Enchant finds languages and dictionaries")
else:
    # Running in regular Python, enchant may not have dictionaries configured.
    languages = enchant.list_languages()
    dictionaries = enchant.list_dicts()
    if languages and dictionaries:
        print("Enchant finds languages and dictionaries")
    else:
        print("Enchant import works but no dictionaries configured (this is OK for regular tests)")
