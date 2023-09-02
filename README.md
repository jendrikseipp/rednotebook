# RedNotebook

RedNotebook is a modern desktop journal. It lets you format, tag and
search your entries. You can also add pictures, links and customizable
templates, spell check your notes, and export to plain text, HTML,
Latex or PDF.


**Installers for Linux and Windows**:
[rednotebook.app/downloads.html](https://www.rednotebook.app/downloads.html)


## Requirements

Needed for running RedNotebook:

  * GTK (3.18+): https://www.gtk.org
  * GtkSourceView (3.0+): https://wiki.gnome.org/Projects/GtkSourceView
  * Python (3.8+): https://www.python.org
  * PyYAML (3.10+): https://pyyaml.org
  * WebKitGTK (2.16+): https://webkitgtk.org (only on Linux and macOS)
  * PyEnchant for spell checking (1.6+): https://pypi.org/project/pyenchant/ (optional)

Needed for installing RedNotebook:

  * GNU gettext: https://www.gnu.org/software/gettext
  * Setuptools (60.0+): https://pypi.org/project/setuptools


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
  * The [txt2tags](https://txt2tags.org) team for their markup conversion tool.
  * Dieter Verfaillie for his [elib.intl](https://github.com/dieterv/elib.intl) module.
  * Maximilian Köhl for his [pygtkspellcheck](https://github.com/koehlma/pygtkspellcheck) project.
  * The Weblate team for hosting [translations for RedNotebook](https://hosted.weblate.org/engage/rednotebook/).


## License notes

RedNotebook is published under the GPLv2+. Since it bundles code
released under the LGPLv3+, the resulting work is licensed under the
GPLv3+. See `debian/copyright` for detailed license information.


Enjoy!
