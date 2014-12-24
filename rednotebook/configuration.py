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
import logging

from rednotebook.util import filesystem



def delete_comment(line):
    if line.startswith('#'):
        return u''
    return line



class Config(dict):
    def __init__(self, config_file):
        dict.__init__(self)

        self.filename = config_file

        self.obsolete_keys = [
            u'useGTKMozembed', u'useWebkit', u'LD_LIBRARY_PATH',
            u'MOZILLA_FIVE_HOME', u'cloudTabActive', u'mainFontSize',
            u'running']

        # Allow changing the value of portable only in default.cfg
        self.suppressed_keys = ['portable', 'user_dir']

        self.update(self._read_file(self.filename))

        self.set_default_values()


    def save_state(self):
        ''' Save a copy of the dir to check for changes later '''
        self.old_config = self.copy()


    def set_default_values(self):
        '''
        Sets some default values that are not automatically set so that
        they appear in the config file
        '''
        #self.read('export_date_format', '%A, %x')


    def _read_file(self, filename):
        content = filesystem.read_file(filename)
        if not content:
            return {}

        lines = content.splitlines()

        # Delete comments and whitespace.
        lines = [delete_comment(line.strip()) for line in lines]

        dictionary = {}

        for line in lines:
            if '=' not in line:
                continue
            pair = line.partition('=')[::2]
            key, value = [s.strip() for s in pair]
            # Skip obsolete keys to prevent rewriting them to disk.
            if key in self.obsolete_keys:
                continue

            try:
                value = int(value)
            except ValueError:
                pass

            dictionary[key] = value

        return dictionary


    def read(self, key, default):
        if key in self:
            return self.get(key)
        else:
            self[key] = default
            return default


    def read_list(self, key, default):
        '''
        Reads the string corresponding to key and converts it to a list

        alpha,beta gamma;delta -> ['alpha', 'beta', 'gamma', 'delta']

        default should be of the form 'alpha,beta gamma;delta'
        '''
        string = self.read(key, default)
        string = unicode(string)
        if not string:
            return []

        # Try to convert the string to a list
        separators = [',', ';']
        for separator in separators:
            string = string.replace(separator, ' ')

        list = string.split()

        # Remove whitespace
        list = map(unicode.strip, list)

        # Remove empty items
        list = filter(bool, list)

        return list


    def write_list(self, key, list):
        self[key] = ', '.join(list)


    def changed(self):
        return not (self == self.old_config)


    def save_to_disk(self):
        if not self.changed():
            return

        content = ''
        for key, value in sorted(self.iteritems()):
            if key not in self.suppressed_keys:
                content += ('%s=%s\n' % (key, value))

        try:
            filesystem.make_directory(os.path.dirname(self.filename))
            filesystem.write_file(self.filename, content)
        except IOError:
            logging.error('Configuration could not be saved. Please check '
                          'your permissions')
            return

        logging.info('Configuration has been saved to %s' % self.filename)
        self.save_state()
