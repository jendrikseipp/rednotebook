#! /usr/bin/env python 
import os

src = os.path.abspath(os.path.join(os.path.abspath(__file__), '../'))
print 'SOURCE:     ', src
os.chdir(src)

dest = os.path.abspath(os.path.join(os.path.abspath(__file__), '../../'))
print 'DESTINATION:', dest

if not os.path.exists(dest):
    os.mkdir(dest)
    

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
    html = html.replace('***CONTENT***', page['content'])
    if 'scripts' in page:
        scripts = page['scripts']
    else:
        scripts = ''
    html = html.replace('***SCRIPTS***', scripts)
    with open(os.path.join(dest, filename), 'w') as file:
        file.write(html)
