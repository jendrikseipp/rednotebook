#! /usr/bin/env python3

import argparse
import os.path
import shutil

import utils

DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DIR = os.path.join(DIR, "dicts")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "url", help="URL from ftp://ftp.gnu.org/gnu/aspell/dict/0index.html"
    )
    parser.add_argument("dest", help="Destination directory")
    return parser.parse_args()


def fetch_dict(url, dest):
    assert url.endswith(".tar.bz2"), url
    filename = os.path.basename(url)
    utils.fetch(url, os.path.join(DICT_DIR, filename))
    utils.run(["tar", "xjvf", filename], cwd=DICT_DIR)
    name = filename[: -len(".tar.bz2")]
    path = os.path.join(DICT_DIR, name)
    utils.run(["./configure", "--vars", "DESTDIR=tmp"], cwd=path)
    utils.run(["make"], cwd=path)
    utils.run(["make", "install"], cwd=path)
    result_dir = os.path.join(path, "tmp/usr/lib/aspell")
    utils.ensure_path(dest)
    for dict_file in os.listdir(result_dir):
        shutil.copy2(os.path.join(result_dir, dict_file), os.path.join(dest, dict_file))


def main():
    args = parse_args()
    fetch_dict(args.url, args.dest)


main()
