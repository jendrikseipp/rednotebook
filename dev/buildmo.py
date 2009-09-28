'''
Little script that compiles all available po files into mo files
'''

import os
from subprocess import call

po_dir = '../po'
i18n_dir = '../rednotebook/i18n/'

if not os.path.exists(i18n_dir):
	os.mkdir(i18n_dir)

available_langs = os.listdir(po_dir)
available_langs = filter(lambda file: file.endswith('.po'), available_langs)
available_langs = map(lambda file: file[:-3], available_langs)

print 'langs', available_langs

for lang in available_langs:
	po_file = os.path.join(po_dir, lang+'.po')
	lang_dir = os.path.join(i18n_dir, lang)
	mo_dir = os.path.join(lang_dir, 'LC_MESSAGES')
	mo_file = os.path.join(mo_dir, 'rednotebook.mo')
	cmd = ['msgfmt', '--output-file=%s' % mo_file, po_file]
	print 'cmd', cmd
	
	for dir in [lang_dir, mo_dir]:
		if not os.path.exists(dir):
			os.mkdir(dir)
	
	call(cmd)
