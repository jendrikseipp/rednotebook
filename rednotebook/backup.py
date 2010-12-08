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

class Archiver(object):
    def __init__(self, journal):
        self.journal = journal
    
    def backup(self, backup_file):
        data_dir = self.journal.dirs.data_dir
        archive_files = []
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if not file.endswith('~'):
                    archive_files.append(os.path.join(root, file))
        
        filesystem.write_archive(backup_file, archive_files, data_dir)
        
        logging.info('The content has been exported to %s' % backup_file)
