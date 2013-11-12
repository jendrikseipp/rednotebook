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

def install(path, dest=None):
    cmd = ['wine']
    if path.lower().endswith('.exe'):
        cmd.extend([path, '/S'])
    elif path.lower().endswith('.msi'):
        cmd.extend(['msiexec', '/i', path])
    else:
        sys.exit('Don\'t know how to install {0}'.format(path))
    run(cmd)

def extract(archive, dest):
    if archive.endswith('gz'):
        run(['tar', '-xzvf', archive, '--directory', dest])
    elif archive.endswith('.zip'):
        run(['unzip', archive, '-d', dest])
    else:
        sys.exit('Don\'t know how to extract {0}'.format(archive))

