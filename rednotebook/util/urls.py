import logging
import os
import subprocess
import sys
import webbrowser
import urllib.parse
from rednotebook.util.dates import get_date_from_date_string

from rednotebook.util.filesystem import IS_WIN, system_call

INTERNAL_URI_SCHEMA = 'notebook'


def get_local_url(url):
    '''
    Sanitize url, make it absolute and normalize it, then add file://(/) scheme

    Links and images only work in webkit on windows if the files have
    file:/// (3 slashes) in front of the filename.
    Strangely when clicking a link that has two slashes (file://C:\file.ext),
    webkit returns the path file://C/file.ext .
    '''
    orig_url = url
    if url.startswith('file:///') and IS_WIN:
        url = url.replace('file:///', '')
    if url.startswith('file://'):
        url = url.replace('file://', '')
    url = os.path.normpath(url)

    scheme = 'file:///' if IS_WIN else 'file://'
    url = scheme + url
    logging.debug('Transformed local URI %s to %s' % (orig_url, url))
    return url


def open_url_in_browser(url):
    try:
        logging.info('Trying to open %s with webbrowser' % url)
        webbrowser.open(url)
    except webbrowser.Error:
        logging.exception('Failed to open web browser')


def unquote_url(url):
    import urllib.parse
    return urllib.parse.unquote(url)


def _open_url_with_call(url, prog):
    try:
        logging.info('Trying to open %s with %s' % (url, prog))
        system_call([prog, url])
    except (OSError, subprocess.CalledProcessError):
        logging.exception('Opening %s with %s failed' % (url, prog))
        # If everything failed, try the webbrowser
        open_url_in_browser(url)


def open_url(url):
    '''
    Opens a file with the platform's preferred method
    '''
    if url.lower().startswith('http'):
        open_url_in_browser(url)
        return

    # Try opening the file locally
    if IS_WIN:
        try:
            url = unquote_url(url)
            if url.startswith('file:') or os.path.exists(url):
                url = get_local_url(url)
            logging.info('Trying to open %s with "os.startfile"' % url)
            # os.startfile is only available on windows
            os.startfile(url)
        except OSError:
            logging.exception('Opening %s with "os.startfile" failed' % url)
    elif sys.platform == 'darwin':
        _open_url_with_call(url, 'open')
    else:
        _open_url_with_call(url, 'xdg-open')


def is_internal_uri(uri):
    return uri.startswith(INTERNAL_URI_SCHEMA)


def process_internal_uri(journal, uri):
    uri = urllib.parse.urlparse(uri)
    logging.debug("Parsed internal URI: %s", uri)
    date = get_date_from_date_string(uri.path)
    journal.change_date(date)
