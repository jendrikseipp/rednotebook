[![Build Status](https://travis-ci.org/jendrikseipp/rednotebook.svg?branch=master)](https://travis-ci.org/jendrikseipp/rednotebook)

RedNotebook is a modern desktop journal. It lets you format, tag and
search your entries. You can also add pictures, links and customizable
templates, spell check your notes, and export to plain text, HTML,
Latex or PDF.


# Requirements

See `debian/control` for Debian and Ubuntu package names.

  * Python (>= 3.4): https://www.python.org
  * GTK (>= 3.18): https://www.gtk.org
  * GtkSourceView (>= 3.18): https://wiki.gnome.org/Projects/GtkSourceView
  * WebKitGTK (>= 2.16, not needed for Windows): https://webkitgtk.org
  * PyYAML (>= 3.10): https://pyyaml.org

Recommended libraries:

  * PyEnchant for spell checking (>= 1.6): https://pypi.org/project/pyenchant/


# Run under Linux (without installation)

    $ ./run


# Run under Windows

See [appveyor.yml](appveyor.yml) for setup instructions, then run

    C:\path\to\rednotebook> python3 rednotebook/journal.py


# Install

We recommend to install RedNotebook with your package manager or
to download the Windows installer. Follow the steps below only if your
distribution has no RedNotebook package or you want to use a newer
RedNotebook version.

Install RedNotebook in the global `site-packages` directory and make
`rednotebook` command available globally:

    sudo apt-get install python3-pip
    # Change into RedNotebook directory.
    sudo pip3 install .

Install RedNotebook locally under
`~/.local/lib/python3.x/site-packages/` and create
`~/.local/bin/rednotebook` executable:

    sudo apt-get install python3-pip
    # Change into RedNotebook directory.
    pip3 install --user .


# Thanks to

  * The authors of the libraries listed under 'Requirements'.
  * Ciaran for creating the RedNotebook icon.
  * The txt2tags team (https://txt2tags.org) for their markup conversion tool.
  * Dieter Verfaillie for his elib.intl module
    (https://github.com/dieterv/elib.intl)


# License notes

RedNotebook is published under the GPLv2+. Since it bundles code
released under the LGPLv3+, the resulting work is licensed under the
GPLv3+. See `debian/copyright` for detailed license information.


Enjoy!
