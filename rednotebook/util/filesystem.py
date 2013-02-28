# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2009  Jendrik Seipp
#
# RedNotebook is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# RedNotebook is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with RedNotebook; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# -----------------------------------------------------------------------

import os
import sys
import locale
import subprocess
import logging
import codecs
import webbrowser

ENCODING = sys.getfilesystemencoding() or locale.getlocale()[1] or 'UTF-8'
LANGUAGE = locale.getdefaultlocale()[0]
REMOTE_PROTOCOLS = ['http', 'ftp', 'irc']

IS_WIN = sys.platform.startswith('win')


def get_unicode_path(path):
    return unicode(path, ENCODING)

def get_utf8_path(path):
    return path.encode('UTF-8')


def main_is_frozen():
    return hasattr(sys, "frozen")


if main_is_frozen():
    app_dir = sys._MEIPASS  # os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app_dir = get_unicode_path(app_dir)

if IS_WIN:
    locale_dir = os.path.join(app_dir, 'share', 'locale')
else:
    locale_dir = os.path.join(sys.prefix, 'share', 'locale')

image_dir = os.path.join(app_dir, 'images')
frame_icon_dir = os.path.join(image_dir, 'rednotebook-icon')
files_dir = os.path.join(app_dir, 'files')

user_home_dir = get_unicode_path(os.path.expanduser('~'))


class Filenames(dict):
    '''
    Dictionary for dirnames and filenames
    '''
    def __init__(self, config):
        for key, value in globals().items():
            # Exclude "get_main_dir()"
            if key.lower().endswith('dir') and isinstance(value, basestring):
                value = os.path.abspath(value)
                self[key] = value
                setattr(self, key, value)

        self.portable = bool(config.read('portable', 0))

        self.journal_user_dir = self.get_user_dir(config)

        self.data_dir = self.default_data_dir

        # Assert that all dirs and files are in place so that logging can take start
        make_directories([self.journal_user_dir, self.data_dir, self.template_dir,
                          self.temp_dir])
        make_files([(self.config_file, ''), (self.log_file, '')])

        self.last_pic_dir = self.user_home_dir
        self.last_file_dir = self.user_home_dir

        self.forbidden_dirs = [user_home_dir, self.journal_user_dir]


    def get_user_dir(self, config):
        custom = config.read('userDir', '')

        if custom:
            # If a custom user dir has been set,
            # construct the absolute path (if not absolute already)
            # and use it
            if not os.path.isabs(custom):
                custom = os.path.join(self.app_dir, custom)
            user_dir = custom
        else:
            if self.portable:
                user_dir = os.path.join(self.app_dir, 'user')
            else:
                user_dir = os.path.join(self.user_home_dir, '.rednotebook')

        return user_dir


    def is_valid_journal_path(self, path):
        return os.path.isdir(path) and os.path.abspath(path) not in self.forbidden_dirs


    def __getattribute__(self, attr):
        user_paths = dict((
            ('template_dir', 'templates'),
            ('temp_dir', 'tmp'),
            ('default_data_dir', 'data'),
            ('config_file', 'configuration.cfg'),
            ('log_file', 'rednotebook.log'),
        ))

        if attr in user_paths:
            return os.path.join(self.journal_user_dir, user_paths.get(attr))

        return dict.__getattribute__(self, attr)



def read_file(filename):
    '''Tries to read a given file

    Returns None if an error is encountered
    '''
    encodings = ['utf-8']

    try:
        import chardet
        assert chardet  # silence pyflakes
    except ImportError:
        logging.info("chardet not found. 'utf-8' encoding will be assumed")
        chardet = None

    if False and chardet:
        with open(filename, 'rb') as file:
            content = file.read()
        guess = chardet.detect(content)
        logging.info('Chardet guesses %s for %s' % (guess, filename))
        encoding = guess.get('encoding')

        # chardet makes errors here sometimes
        if encoding in ['MacCyrillic', 'ISO-8859-7']:
            encoding = 'ISO-8859-2'

        if encoding:
            encodings.insert(0, encoding)

    # Only check the first encoding
    for encoding in encodings[:1]:
        try:
            # codecs.open returns a file object that can write unicode objects
            # and whose read() method also returns unicode objects
            # Internally we want to have unicode only
            with codecs.open(filename, 'rb', encoding=encoding, errors='replace') as file:
                data = file.read()
                return data
        except ValueError, err:
            logging.info(err)
        except Exception, e:
            logging.error(e)
    return ''


def write_file(filename, content):
    assert os.path.isabs(filename)
    try:
        with codecs.open(filename, 'wb', errors='replace', encoding='utf-8') as file:
            file.write(content)
    except IOError, e:
        logging.error('Error while writing to "%s": %s' % (filename, e))


def make_directory(dir):
    if not os.path.isdir(dir):
        os.makedirs(dir)

def make_directories(dirs):
    for dir in dirs:
        make_directory(dir)

def make_file(file, content=''):
    if not os.path.isfile(file):
        write_file(file, content)

def make_files(file_content_pairs):
    for file, content in file_content_pairs:
        make_file(file, content)

def make_file_with_dir(file, content):
    dir = os.path.dirname(file)
    make_directory(dir)
    make_file(file, content)

def get_relative_path(from_dir, to_dir):
    '''
    Try getting the relative path from from_dir to to_dir
    The relpath method is only available in python >= 2.6
    if we run python <= 2.5, return the absolute path to to_dir
    '''
    if getattr(os.path, 'relpath', None):
        # If the data is saved on two different windows partitions,
        # return absolute path to to_dir
        drive1, tail = os.path.splitdrive(from_dir)
        drive2, tail = os.path.splitdrive(to_dir)

        # drive1 and drive2 are always empty strings on Unix
        if not drive1.upper() == drive2.upper():
            return to_dir

        return os.path.relpath(to_dir, from_dir)
    else:
        return to_dir


def get_journal_title(dir):
    '''
    returns the last dirname in path
    '''
    dir = os.path.abspath(dir)
    # Remove double slashes and last slash
    dir = os.path.normpath(dir)

    dirname, basename = os.path.split(dir)
    # Return "/" if journal is located at /
    return basename or dirname


def get_platform_info():
    import platform
    import gtk
    import yaml

    functions = [platform.machine, platform.platform, platform.processor,
                 platform.python_version, platform.release, platform.system]
    names_values = [(func.__name__, func()) for func in functions]

    lib_values = [('GTK version', gtk, 'gtk_version'),
                  ('PyGTK version', gtk, 'pygtk_version'),
                  ('Yaml version', yaml, '__version__')]

    for name, object, value in lib_values:
        try:
            names_values.append((name, getattr(object, value)))
        except AttributeError:
            logging.info('%s could not be determined' % name)

    vals = ['%s: %s' % (name, val) for name, val in names_values]
    return 'System info: ' + ', '.join(vals)


def system_call(args):
    '''
    Asynchronous system call

    subprocess.call runs synchronously
    '''
    subprocess.Popen(args)


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
    import urllib
    return urllib.unquote(url).decode('utf-8')


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
            if url.startswith(u'file:') or os.path.exists(url):
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



if __name__ == '__main__':
    dirs = ['/home/my journal', '/my journal/', r'C:\\Dok u E\journal',
            '/home/name/journal', '/']
    for dir in dirs:
        title = get_journal_title(dir)
        print '%s -> %s' % (dir, title)
