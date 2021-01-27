import logging
import os
import shutil
import sys
import subprocess
import urllib.request


def ensure_path(path):
    if not os.path.exists(path):
        os.mkdir(path)


def confirm_overwrite(dir):
    if os.path.exists(dir):
        answer = input(
            "The directory {} exists. Overwrite it? (Y/n): ".format(dir)
        ).strip()
        if answer and answer.lower() != "y":
            sys.exit("Aborting")
        shutil.rmtree(dir)


def fast_copytree(src_dir, dest_dir):
    subprocess.check_call(["cp", "-r", src_dir, dest_dir])


def fetch(url, path):
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    if not os.path.exists(path):
        logging.info("Fetch {} to {}".format(url, path))
        with urllib.request.urlopen(url) as response, open(path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
    if not os.path.exists(path):
        sys.exit("Download unsuccessful.")


def run(*args, **kwargs):
    logging.info("Run command: {} ({})".format(args, kwargs))
    retcode = subprocess.call(*args, **kwargs)
    if retcode != 0:
        sys.exit("Command failed.")


def get_output(*args, **kwargs):
    return subprocess.check_output(*args, **kwargs).decode().strip()
