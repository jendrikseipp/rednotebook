#! /usr/bin/env python

import os

spider_dir = os.path.abspath(os.path.dirname(__file__))

src = spider_dir
print("SOURCE:     ", src)
os.chdir(src)

dest = os.path.abspath(os.path.dirname(spider_dir))
print("DESTINATION:", dest)

assert os.path.exists(dest)

version = open("version.txt").read().strip()


about = {
    "title": "RedNotebook",
    "filename": "index.html",
    "news": open("news.txt").read(),
    "version": version,
}

downloads = {
    "title": "Downloads | RedNotebook",
    "filename": "downloads.html",
    "scripts": """\
<script type="text/javascript" src="js/prototype.js"></script>
  <script type="text/javascript" src="js/download.js"></script>
""",
    "version": version,
}

screenshots = {
    "title": "Testimonials | RedNotebook",
    "filename": "screenshots.html",
}

participate = {
    "title": "Participate | RedNotebook",
    "filename": "participate.html",
}

thanks = {
    "title": "Thanks | RedNotebook",
    "filename": "thanks.html",
}


pages = [about, downloads, screenshots, participate, thanks]

with open("template.html") as file:
    template = file.read()

for page in pages:
    filename = page["filename"]
    html = template
    with open(filename) as file:
        html = html.replace(f"***CONTENT***", file.read())
    for key in set(page.keys()) | {"scripts"}:
        html = html.replace(f"***{key.upper()}***", page.get(key, ""))
    with open(os.path.join(dest, filename), "w") as f:
        f.write(html)
