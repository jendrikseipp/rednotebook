[![Build Status](https://travis-ci.org/jendrikseipp/rednotebook.svg?branch=master)](https://travis-ci.org/jendrikseipp/rednotebook)

RedNotebook is a modern desktop journal. It lets you format, tag and
search your entries. You can also add pictures, links and customizable
templates, spell check your notes, and export to plain text, HTML,
Latex or PDF.

# Run under Linux

    $ ./run

Installs all dependencies, translates the application and runs
RedNotebook without installation.

# Run under Windows

Install Python 2.7 (32-bit version), change into the `win` directory,
run

    C:\path\to\rednotebook\win> python create-build-env.py

and follow the instruction to add `C:\gtkbin` to your path. Now change
back into the rednotebook directory and run

    C:\path\to\rednotebook> python rednotebook/journal.py

Be sure to use the **32-bit version** of Python! (Or install the 64-bit
versions of the various dependencies required for the project.)


# Installation

It is recommended to install RedNotebook with your package manager.
Follow the steps below only if your distribution has no RedNotebook
package or you want to use a newer RedNotebook version.

In order not to mess up your package system, you might want to run
RedNotebook without installing it. If so, use the `run` script.

## Requirements
  - Python 2.7 (3.x not supported)
  - PyYaml (>=3.05)
  - PyGTK (>=2.16)
  - pywebkitgtk (>=1.1.5)

  - Optionally:
    - python-chardet (http://chardet.feedparser.org)
      Better recognition of file encodings

Please note: Installing is very easy, uninstalling however can only be
done by removing the installed files manually. It is therefore
recommended to save the list of installed files. Install RedNotebook
into your global `site-packages` directory:

    $ sudo python setup.py install --record installed-files


# Thanks to

- The authors of the programs listed under 'Requirements'. Remember that
  without them, RedNotebook would not be possible.
- Everaldo Coelho (www.everaldo.com) for the original icon
  (easymoblog.png) and Ciaran for the excellent redesign.
- The txt2tags team (http://txt2tags.net) for their super cool markup tool.
- The people behind the Tango Icon Project and the creators of the Human
  Theme. Their work can be downloaded from http://tango.freedesktop.org/.
- Ahmet Öztürk and Lifeograph for his markup highlighting idea
- Hannes Matuschek: The code for markup highlighting uses a specialized
  version of his pygtkcodebuffer module
  (http://code.google.com/p/pygtkcodebuffer/).
- Dieter Verfaillie for his elib.intl module
  (https://github.com/dieterv/elib.intl)
- Eitan Isaacson: RedNotebook took his idea and some code for converting
  HTML documents to PDF (http://github.com/eeejay/interwibble/).


# License notes

RedNotebook is published under the GPLv2+. Since it includes the
elib.intl module (https://github.com/dieterv/elib.intl) which is
released under the LGPLv3+, the resulting work is licensed under the
GPLv3+.


Enjoy!
