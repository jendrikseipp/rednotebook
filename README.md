[![Build Status](https://travis-ci.org/jendrikseipp/rednotebook.svg?branch=master)](https://travis-ci.org/jendrikseipp/rednotebook)

RedNotebook is a modern desktop journal. It lets you format, tag and
search your entries. You can also add pictures, links and customizable
templates, spell check your notes, and export to plain text, HTML,
Latex or PDF.

# Requirements
  - Python 2.7 (3.x not supported)
  - PyYaml (>=3.05)
  - PyGTK (>=2.16)
  - pywebkitgtk (>=1.1.5)
  - python-enchant (optional, needed for spell checking)

# Run under Linux (without installation)

    $ ./run

# Run under Windows

Install Python 2.7 (32-bit version), change into the `win` directory,
run

    C:\path\to\rednotebook\win> python create-build-env.py

and add `C:\gtkbin` to your path. Now change back into the rednotebook
directory and run

    C:\path\to\rednotebook> python rednotebook/journal.py

Be sure to use the **32-bit version** of Python! (Or install the 64-bit
versions of the various dependencies required for the project.)


# Install

It is recommended to install RedNotebook with your package manager or
to download the Windows installer. Follow the steps below only if your
distribution has no RedNotebook package or you want to use a newer
RedNotebook version.

Install RedNotebook in the global `site-packages` directory and make
`rednotebook` command available globally:

    sudo apt-get install python-pip
    # Change into RedNotebook directory.
    sudo pip install .

Install RedNotebook locally under
`~/.local/lib/python2.7/site-packages/` and create
`~/.local/bin/rednotebook` executable:

    sudo apt-get install python-pip
    # Change into RedNotebook directory.
    pip install --user .


# Thanks to

- The authors of the programs listed under 'Requirements'.
- Ciaran for creating the RedNotebook icon.
- The txt2tags team (http://txt2tags.net) for their markup conversion tool.
- Ahmet Öztürk and Lifeograph for his markup highlighting idea
- Hannes Matuschek: The code for markup highlighting uses a specialized
  version of his pygtkcodebuffer module
  (http://code.google.com/p/pygtkcodebuffer/).
- Dieter Verfaillie for his elib.intl module
  (https://github.com/dieterv/elib.intl)


# License notes

RedNotebook is published under the GPLv2+. Since it includes the
elib.intl module (https://github.com/dieterv/elib.intl) which is
released under the LGPLv3+, the resulting work is licensed under the
GPLv3+.


Enjoy!
