#! /usr/bin/env python3

import sys
from pathlib import Path


DIR = Path(__file__).resolve().parent
REPO = DIR.parent
DEFAULT_DATA_DIR = Path.home() / ".rednotebook" / "data"

sys.path.insert(0, str(REPO))

from rednotebook.help import help_text
from rednotebook.util import markup


print(
    markup.convert(
        help_text,
        "html",
        DEFAULT_DATA_DIR,
        options={"toc": 1, "title": "RedNotebook Documentation"},
    )
)
