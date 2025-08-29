#! /usr/bin/env python3

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("locale_dir", help="root directory for the resulting .mo files")
    return parser.parse_args()


def build_translation_files(po_dir: Path, locale_dir: Path):
    assert po_dir.is_dir(), po_dir
    msgfmt_path = shutil.which("msgfmt")
    if not msgfmt_path:
        sys.exit(
            "Error: 'msgfmt' not found. Install gettext (e.g. 'sudo apt install gettext' on Linux"
            " or 'choco install gettext' on Windows) before building."
        )
    for src in sorted(po_dir.glob("*.po")):
        lang = src.stem
        dest = Path(locale_dir) / lang / "LC_MESSAGES" / "rednotebook.mo"
        dest_dir = dest.parent
        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.check_call([msgfmt_path, "--output-file", dest, src])
        except subprocess.CalledProcessError:
            sys.exit(f"Compilation failed for {src}")


def main():
    args = _parse_args()
    po_dir = REPO / "po"
    locale_dir = Path(args.locale_dir).resolve()
    print("Building translations")
    print(po_dir, "-->", locale_dir)
    build_translation_files(po_dir, locale_dir)
    print("Finished building translations")


if __name__ == "__main__":
    main()
