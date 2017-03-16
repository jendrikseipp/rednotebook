import logging
import os
import shutil
import sys
import subprocess
import urllib


def ensure_path(path):
    if not os.path.exists(path):
        os.mkdir(path)

def confirm_overwrite(dir):
    if os.path.exists(dir):
        answer = raw_input(
            'The directory {} exists. Overwrite it? (Y/n): '.format(dir)).strip()
        if answer and answer.lower() != 'y':
            sys.exit('Aborting')
        shutil.rmtree(dir)

def fast_copytree(src_dir, dest_dir):
    subprocess.check_call(['cp', '-r', src_dir, dest_dir])

def fetch(url, path):
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    if not os.path.exists(path):
        logging.info('Fetch {0} to {1}'.format(url, path))
        urllib.urlretrieve(url, filename=path)
    if not os.path.exists(path):
        sys.exit('Download unsuccessful.')

def run(*args, **kwargs):
    logging.info('Run command: {0} ({1})'.format(args, kwargs))
    retcode = subprocess.call(*args, **kwargs)
    if retcode != 0:
        sys.exit('Command failed.')

def install(path, use_wine):
    cmd = []
    if use_wine:
        cmd.append('wine')
    if path.lower().endswith('.exe'):
        cmd.extend([path])
    elif path.lower().endswith('.msi'):
        cmd.extend(['msiexec', '/i', path])
    else:
        sys.exit('Don\'t know how to install {0}'.format(path))
    run(cmd)
