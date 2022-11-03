# RedNotebook

RedNotebook is a modern desktop journal. It lets you format, tag and
search your entries. You can also add pictures, links and customizable
templates, spell check your notes, and export to plain text, HTML,
Latex or PDF.


**Installers for Linux and Windows**:
[rednotebook.app/downloads.html](https://www.rednotebook.app/downloads.html)


## Requirements

  * Python (>= 3.4): https://www.python.org
  * GTK (>= 3.18): https://www.gtk.org
  * GtkSourceView (>= 3.18): https://wiki.gnome.org/Projects/GtkSourceView
  * WebKitGTK (>= 2.16, not needed for Windows): https://webkitgtk.org
  * PyYAML (>= 3.10): https://pyyaml.org

Recommended libraries:

  * PyEnchant for spell checking (>= 1.6): https://pypi.org/project/pyenchant/

## Run from source

Install all dependencies:

  * Linux/macOS: [run-tests.yml](.github/workflows/run-tests.yml)
  * Windows: [appveyor.yml](appveyor.yml)

Start RedNotebook:

  * Linux/macOS: `python3 rednotebook/journal.py`
  * Windows: `py rednotebook/journal.py`


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
