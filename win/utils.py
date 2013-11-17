import logging
import os
import sys
import subprocess
import urllib


def ensure_path(path):
    if not os.path.exists(path):
        os.mkdir(path)

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
