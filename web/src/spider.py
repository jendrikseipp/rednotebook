#! /usr/bin/env python 
import os
import sys

spider_dir = os.path.abspath(os.path.dirname(__file__))
rn_dir = os.path.abspath(os.path.join(spider_dir, '../../rednotebook'))
sys.path.insert(0, rn_dir)

import info

version = info.version
print version

src = spider_dir
print 'SOURCE:     ', src
os.chdir(src)

dest = os.path.abspath(os.path.dirname(spider_dir))
print 'DESTINATION:', dest

assert os.path.exists(dest)
    

about = {
    'title': 'RedNotebook',
    'filename': 'index.html',
}

downloads = {
    'title': 'Downloads | RedNotebook',
    'filename': 'downloads.html',
    'scripts': '''\
<script type="text/javascript" src="js/prototype.js"></script>
  <script type="text/javascript" src="js/download.js"></script>
'''
}

screenshots = {
    'title': 'Screenshots | RedNotebook',
    'filename': 'screenshots.html',
}

participate = {
    'title': 'Participate | RedNotebook',
    'filename': 'participate.html',
}



pages = [about, downloads, screenshots, participate]

for page in pages:
    with open('template.html') as file:
        template = file.read()
    filename = page['filename']
    with open(filename) as file:
        page['content'] = file.read()
    html = template.replace('***TITLE***', page['title'])
    #html = html.replace('***VERSION***', version)
    html = html.replace('***CONTENT***', page['content'])
    if 'scripts' in page:
        scripts = page['scripts']
    else:
        scripts = ''
    html = html.replace('***SCRIPTS***', scripts)
    with open(os.path.join(dest, filename), 'w') as file:
        file.write(html)
