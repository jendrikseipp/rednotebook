# RedNotebook

RedNotebook is a modern desktop journal. It lets you format, tag and
search your entries. You can also add pictures, links and customizable
templates, spell check your notes, and export to plain text, HTML,
Latex or PDF.


**Installers for Linux and Windows**:
[rednotebook.app/downloads.html](https://www.rednotebook.app/downloads.html)


## Requirements

See [debian/control](debian/control) for Debian and Ubuntu package names.

  * Python (3.6+): https://www.python.org
  * GTK (3.18+): https://www.gtk.org
  * GtkSourceView (4.0+): https://wiki.gnome.org/Projects/GtkSourceView
  * PyYAML (3.10+): https://pyyaml.org
  * WebKitGTK (2.16+): https://webkitgtk.org (only on Linux and macOS)

Recommended libraries:

  * PyEnchant for spell checking (1.6+): https://pypi.org/project/pyenchant/
  * CEF Python (0.66.1+): https://github.com/cztomczak/cefpython (only on Windows)


## Run on Linux (without installation)

    ./run


## Install on Linux

We recommend to install RedNotebook with your package manager. Follow the steps
below only if your distribution has no RedNotebook package or you want to use a
newer RedNotebook version.

Install RedNotebook under `~/.local/lib/python3.x/site-packages/` and
create `~/.local/bin/rednotebook` executable:

    sudo apt install python3-pip
    # Change into RedNotebook repository.
    pip3 install .


## Run on Windows

Pre-built installers are available at
[rednotebook.app/downloads.html](https://www.rednotebook.app/downloads.html).
Developers can inspect [appveyor.yml](appveyor.yml) for setup instructions and
then run

    C:\path\to\rednotebook> py rednotebook/journal.py


## Thanks to

  * The authors of the libraries listed under 'Requirements'.
  * Ciaran for creating the RedNotebook icon.
  * The txt2tags team (https://txt2tags.org) for their markup conversion tool.
  * Dieter Verfaillie for his elib.intl module
    (https://github.com/dieterv/elib.intl)


## License notes

RedNotebook is published under the GPLv2+. Since it bundles code
released under the LGPLv3+, the resulting work is licensed under the
GPLv3+. See `debian/copyright` for detailed license information.


Enjoy!
