import logging
import os
import re
import subprocess
import sys
import urllib.parse
import webbrowser

from rednotebook.util.filesystem import IS_WIN, LOCAL_FILE_PEFIX, system_call


ENTRY_REFERENCE_URI_PATTERN = re.compile(
    r"^file:///#(?P<date>\d{4}-\d{2}-\d{2})$")


def get_local_url(url):
    """
    Sanitize url, make it absolute and normalize it, then add file://(/) scheme

    Links and images only work in webkit on windows if the files have
    file:/// (3 slashes) in front of the filename.
    Strangely when clicking a link that has two slashes (file://C:\file.ext),
    webkit returns the path file://C/file.ext .
    """
    orig_url = url
    if url.startswith("file:///") and IS_WIN:
        url = url.replace("file:///", "")
    if url.startswith("file://"):
        url = url.replace("file://", "")
    url = os.path.normpath(url)

    url = LOCAL_FILE_PEFIX + url
    logging.debug(f"Transformed local URI {orig_url} to {url}")
    return url


def open_url_in_browser(url):
    try:
        logging.info(f"Trying to open {url} with webbrowser")
        webbrowser.open(url)
    except webbrowser.Error:
        logging.exception("Failed to open web browser")


def unquote_url(url):
    return urllib.parse.unquote(url)


def _open_url_with_call(url, prog):
    try:
        logging.info(f"Trying to open {url} with {prog}")
        system_call([prog, url])
    except (OSError, subprocess.CalledProcessError):
        logging.exception(f"Opening {url} with {prog} failed")
        # If everything failed, try the webbrowser
        open_url_in_browser(url)


def open_url(url):
    """
    Opens a file with the platform's preferred method
    """
    if url.lower().startswith("http"):
        open_url_in_browser(url)
        return

    # Try opening the file locally
    if IS_WIN:
        try:
            url = unquote_url(url)
            if url.startswith("file:") or os.path.exists(url):
                url = get_local_url(url)
            logging.info(f'Trying to open {url} with "os.startfile"')
            # os.startfile is only available on windows
            os.startfile(url)
        except OSError:
            logging.exception(f'Opening {url} with "os.startfile" failed')
    elif sys.platform == "darwin":
        _open_url_with_call(url, "open")
    else:
        _open_url_with_call(url, "xdg-open")


def is_entry_reference_uri(uri):
    """
    Check if provided URI was generated from an entry reference.
    """
    return ENTRY_REFERENCE_URI_PATTERN.match(uri)
