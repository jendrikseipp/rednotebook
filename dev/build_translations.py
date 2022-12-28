#! /usr/bin/env python3

import argparse
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO))

from rednotebook.external import msgfmt


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("locale_dir", help="root directory for the resulting .mo files")
    return parser.parse_args()


def build_translation_files(po_dir: Path, locale_dir: Path):
    assert po_dir.is_dir(), po_dir
    for src in sorted(po_dir.glob("*.po")):
        lang = src.stem
        dest = Path(locale_dir) / lang / "LC_MESSAGES" / "rednotebook.mo"
        dest_dir = dest.parent
        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
        print(f"Compiling {src} to {dest}")
        msgfmt.make(str(src), str(dest))


def main():
    args = _parse_args()
    po_dir = REPO / "po"
    locale_dir = Path(args.locale_dir).resolve()
    print("Building translations")
    print(po_dir, "-->", locale_dir)
    build_translation_files(po_dir, locale_dir)


if __name__ == "__main__":
    main()
