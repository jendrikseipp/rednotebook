'''apport package hook for rednotebook.

Code adapted from the novacut project.

(c) 2012 Novacut Inc
Author: Jason Gerard DeRose <jderose@novacut.com>
'''

import os
from os import path

from apport.hookutils import attach_file_if_exists

LOGS = (
    ('DebugLog', 'rednotebook.log'),
)

def add_info(report):
    report['CrashDB'] = 'rednotebook'
    rednotebook_dir = path.join(os.environ['HOME'], '.rednotebook')
    for (key, name) in LOGS:
        log = path.join(rednotebook_dir, name)
        attach_file_if_exists(report, log, key)
