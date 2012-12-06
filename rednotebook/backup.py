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

import datetime
import logging
import os
import zipfile

import gtk


DATE_FORMAT = '%Y-%m-%d'
MAX_BACKUP_AGE = 30
BACKUP_NOW = 100
ASK_NEXT_TIME = 200
NEVER_ASK_AGAIN = 300


def write_archive(archive_file_name, files, base_dir='', arc_base_dir=''):
    """
    use base_dir for relative filenames, in case you don't
    want your archive to contain '/home/...'
    """
    archive = zipfile.ZipFile(archive_file_name, "w")
    for file in files:
        archive.write(file, os.path.join(arc_base_dir, file[len(base_dir):]))
    archive.close()


class Archiver(object):
    def __init__(self, journal):
        self.journal = journal

    def check_last_backup_date(self):
        if not self._backup_necessary():
            return

        logging.warning('Last backup is older than %s days.' % MAX_BACKUP_AGE)
        text1 = _('It has been a while since you made your last backup.')
        text2 = _('You can backup your journal to a zip file to avoid data loss.')
        dialog = gtk.MessageDialog(parent=self.journal.frame.main_frame,
                                   type=gtk.MESSAGE_QUESTION,
                                   flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   message_format=text1)
        dialog.set_title(_('Backup'))
        dialog.format_secondary_text(text2)
        dialog.add_buttons(_('Backup now'), BACKUP_NOW,
                           _('Ask at next start'), ASK_NEXT_TIME,
                           _('Never ask again'), NEVER_ASK_AGAIN)

        answer = dialog.run()
        dialog.hide()
        if answer == BACKUP_NOW:
            self.backup()
        elif answer == ASK_NEXT_TIME:
            pass
        elif answer == NEVER_ASK_AGAIN:
            self.journal.config['lastBackupDate'] = datetime.datetime.max.strftime(DATE_FORMAT)

    def backup(self):
        backup_file = self._get_backup_file()
        # Abort if user did not select a path
        if not backup_file:
            return

        self.journal.save_to_disk()
        data_dir = self.journal.dirs.data_dir
        archive_files = []
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if not file.endswith('~') and not 'RedNotebook-Backup' in file:
                    archive_files.append(os.path.join(root, file))

        write_archive(backup_file, archive_files, data_dir)

        logging.info('The content has been backed up at %s' % backup_file)
        self.journal.config['lastBackupDate'] = datetime.datetime.now().strftime(DATE_FORMAT)
        self.journal.config['lastBackupDir'] = os.path.dirname(backup_file)

    def _backup_necessary(self):
        now = datetime.datetime.now()
        date_string = self.journal.config.read('lastBackupDate', now.strftime(DATE_FORMAT))
        try:
            last_backup_date = datetime.datetime.strptime(date_string, DATE_FORMAT)
        except ValueError, err:
            logging.error('Last backup date could not be read: %s' % err)
            last_backup_date = now
        # We don't need to take the absolute value here, because dates in the
        # future will yield a negative days value.
        return (now - last_backup_date).days > MAX_BACKUP_AGE

    def _get_backup_file(self):
        if self.journal.title == 'data':
            name = ''
        else:
            name = '-' + self.journal.title

        proposed_filename = 'RedNotebook-Backup%s-%s.zip' % (name, datetime.date.today())
        proposed_directory = self.journal.config.read('lastBackupDir',
                                                      os.path.expanduser('~'))

        backup_dialog = self.journal.frame.builder.get_object('backup_dialog')
        backup_dialog.set_transient_for(self.journal.frame.main_frame)
        backup_dialog.set_current_folder(proposed_directory)
        backup_dialog.set_current_name(proposed_filename)

        filter = gtk.FileFilter()
        filter.set_name("Zip")
        filter.add_pattern("*.zip")
        backup_dialog.add_filter(filter)

        response = backup_dialog.run()
        backup_dialog.hide()

        if response == gtk.RESPONSE_OK:
            path = backup_dialog.get_filename().decode('utf-8')
            return path
