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

from __future__ import with_statement

import os
import logging

from rednotebook.util import filesystem



def delete_comment(line):
    '''
    delete comment, do not alter the line, 
    if no comment sign is found
    '''
    comment_pos = line.find('#')
    if comment_pos >= 0:
        return line[:comment_pos]
    else:
        return line
        
        
def get_config(dirs):
    default_config_file = os.path.join(dirs.files_dir, 'default.cfg')
    default_config = Config(default_config_file)
    
    user_config = Config(dirs.config_file)
    
    config = Config()
    
    #Add the defaults
    if default_config:
        config.update(default_config)
    
    #Overwrite existing values with user options
    if user_config:
        config.update(user_config)
        
    return config
    

class Config(dict):
    
    def __init__(self, config_file):
        dict.__init__(self)
        
        #self.dirs = dirs
        self.file = config_file
        
        self.obsolete_keys = ['useWebkit', 'useGTKMozembed', 
                                'LD_LIBRARY_PATH', 'MOZILLA_FIVE_HOME']
        
        # Allow changing the value of portable only in default.cfg
        self.suppressed_keys = ['portable', 'user_dir']
        
        #default_config_file = os.path.join(dirs.files_dir, 'default.cfg')
        #default_config = self._read_file(default_config_file)
        
        self.update(self._read_file(self.file))
        
        #Add the defaults
        #if default_config:
        #   self.update(default_config)
        
        #Overwrite existing values with user options
        #if user_config:
        #   self.update(user_config)
            
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
        
                        
    def _read_file(self, file):
        
        key_value_pairs = []
        
        content = filesystem.read_file(file)
        if not content:
            return {}
            
        lines = content.split('\n')
        lines = map(str, lines)
    
        # delete comments
        key_value_pairs = map(lambda line: delete_comment(line), lines)
        
        #delete whitespace
        key_value_pairs = map(str.strip, key_value_pairs)
        
        #delete empty lines
        key_value_pairs = filter(lambda line: len(line) > 0, key_value_pairs)
        
        dictionary = {}
        
        #read keys and values
        for key_value_pair in key_value_pairs:
            if '=' in key_value_pair:
                try:
                    # Delete whitespace around =
                    pair = key_value_pair.split('=')
                    key, value = map(str.strip, pair)
                    
                    # Do not add obsolete keys -> they will not be rewritten
                    # to disk
                    if key in self.obsolete_keys:
                        continue
                    
                    try:
                        #Save value as int if possible
                        value_int = int(value)
                        dictionary[key] = value_int
                    except ValueError:
                        dictionary[key] = value
                        
                except Exception:
                    logging.error('The line "' + key_value_pair + \
                                    '" in the config file contains errors')
                    
        return dictionary
        
    
    def read(self, key, default):
        if self.has_key(key):
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
        string = str(string)
        if not string:
            return []
        
        # Try to convert the string to a list
        separators = [',', ';']
        for separator in separators:
            string = string.replace(separator, ' ')
        
        list = string.split(' ')
        
        # Remove whitespace
        list = map(str.strip, list)
        
        # Remove empty items
        list = filter(lambda item: len(item) > 0, list)
        
        return list
    
    def write_list(self, key, list):
        self[key] = ', '.join(list)
        
    def changed(self):
        return not (self == self.old_config)
                        
    def save_to_disk(self):
        assert self.changed()
        
        try:
            with open(self.file, 'w') as config_file:
                for key, value in sorted(self.iteritems()):
                    if key not in self.suppressed_keys:
                        config_file.write('%s=%s\n' % (key, value))
                logging.info('Configuration has been saved to disk')
                self.old_config = self.copy()
        except IOError:
            logging.error('Configuration could not be saved')
            

