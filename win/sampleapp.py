import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
print('Gtk import works')

from gi.repository import GObject
print('GObject import works')

gi.require_version('GtkSource', '3.0')
from gi.repository import GtkSource
print('GtkSource import works')

import enchant
print(enchant.list_languages())
print('Enchant import works')
