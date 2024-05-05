#! /usr/bin/env python3

from pathlib import Path
import sys


DIR = Path(__file__).resolve().parent
REPO = DIR.parent
DEFAULT_DATA_DIR = Path.home() / ".rednotebook" / "data"

sys.path.insert(0, str(REPO))

from rednotebook.help import help_text
from rednotebook.info import version
from rednotebook.util import markup


print(
    markup.convert(
        help_text,
        "xhtml",
        DEFAULT_DATA_DIR,
        headers=["RedNotebook Documentation", version, ""],
        options={"toc": 1},
    )
)
