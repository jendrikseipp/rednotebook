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

from glob import glob
import os
import os.path
import subprocess
import sys

from setuptools import setup

REPO = os.path.dirname(os.path.abspath(__file__))
MSGFMT = os.path.join(REPO, "rednotebook", "external", "msgfmt.py")

sys.path.insert(0, REPO)

from rednotebook import info


def _build_translation_files():
    po_dir = os.path.join(REPO, "po")
    locale_dir = os.path.join(REPO, "build", "locale")
    assert os.path.isdir(po_dir), po_dir
    for src in sorted(glob(os.path.join(po_dir, "*.po"))):
        lang, _ = os.path.splitext(os.path.basename(src))
        dest = os.path.join(locale_dir, lang, "LC_MESSAGES", "rednotebook.mo")
        dest_dir = os.path.dirname(dest)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        print(f"Compiling {src} to {dest}")
        subprocess.check_call([sys.executable, MSGFMT, "--output-file", dest, src])


def get_translation_files():
    _build_translation_files()
    data_files = []
    for lang in os.listdir("build/locale/"):
        lang_dir = os.path.join("share", "locale", lang, "LC_MESSAGES")
        lang_file = os.path.join(
            "build", "locale", lang, "LC_MESSAGES", "rednotebook.mo"
        )
        data_files.append((lang_dir, [lang_file]))
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
