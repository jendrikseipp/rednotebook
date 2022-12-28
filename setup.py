# -----------------------------------------------------------------------
# Copyright (c) 2009-2022  Jendrik Seipp
#
# RedNotebook is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# RedNotebook is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with RedNotebook; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# -----------------------------------------------------------------------

"""
This is the installation script for RedNotebook.

To install RedNotebook, run "python setup.py install".
To do a (test) installation to a different dir, use "python setup.py install --root=test-dir" instead.
"""

from pathlib import Path
import sys

from setuptools import setup

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from rednotebook import info

from dev.build_translations import build_translation_files


def get_translation_files():
    po_dir = REPO / "po"
    locale_dir = REPO / "build" / "locale"
    build_translation_files(po_dir, locale_dir)
    data_files = []
    for lang_dir in Path("build/locale/").iterdir():
        lang_file = lang_dir / "LC_MESSAGES" / "rednotebook.mo"
        dest_dir = Path("share") / "locale" / lang_dir.name / "LC_MESSAGES"
        data_files.append((str(dest_dir), [str(lang_file)]))
    return data_files


parameters = {
    "name": "rednotebook",
    "version": info.version,
    "description": "Graphical daily journal with calendar, templates and keyword searching",
    "long_description": info.comments,
    "author": info.author,
    "author_email": info.author_mail,
    "maintainer": info.author,
    "maintainer_email": info.author_mail,
    "url": info.url,
    "license": "GPL",
    "keywords": "journal, diary",
    "scripts": ["rednotebook/rednotebook"],
    "packages": [
        "rednotebook",
        "rednotebook.external",
        "rednotebook.gui",
        "rednotebook.util",
    ],
    "package_data": {
        "rednotebook": [
            "images/*.png",
            "images/rednotebook-icon/*.png",
            "images/rednotebook-icon/rednotebook.svg",
            "files/*.cfg",
            "files/*.glade",
            "files/*.lang",
            "files/*.xml",
        ]
    },
    "data_files": [
        ("share/applications", ["data/rednotebook.desktop"]),
        (
            "share/icons/hicolor/scalable/apps",
            ["rednotebook/images/rednotebook-icon/rednotebook.svg"],
        ),
        ("share/metainfo", ["data/rednotebook.appdata.xml"]),
    ]
    + get_translation_files(),
    "extras_require": {
        "dev_style": [
            "black==22.3.0",
            "flake8==4.0.1",
            "flake8-2020==1.6.0",
            "flake8-bugbear==21.11.28",
            "flake8-comprehensions==3.7.0",
            "flake8-executable==2.1.1",
            "isort>=5.0,<5.1",
            "pyupgrade==2.32.0",
            "vulture==1.6",
        ],
    },
}

if __name__ == "__main__":
    # Additionally use MANIFEST.in for image files
    setup(**parameters)
