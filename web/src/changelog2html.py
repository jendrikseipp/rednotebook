#! /usr/bin/env python

import re
import sys


MAX_RELEASES = 10
CHANGELOG = sys.argv[1]
OUTFILE = "news.txt"
VERSIONFILE = "version.txt"

release_header = re.compile(r"^# ([0-9.]+) \(((?:[0-9]{4}|[0-9]{2})-[0-9]{2}-[0-9]{2})\)$")

html = []

news = """\
<h1>News</h1>
<a name="news"></a>
<div>
%(html)s
For the full list of changes have a look at the
<a href="https://github.com/jendrikseipp/rednotebook/blob/master/CHANGELOG.md">Changelog</a>.
</div>
"""

template_start = """\
<h3>Version %(version)s released - %(date)s</h3>
<p class="content">
<ul>"""

template_end = """\
</ul>
</p>
"""

releases = 0
item_open = False
with open(CHANGELOG) as f:
    for line in f:
        line = line.strip()
        # Skip unreleased changes.
        if line.startswith("# next"):
            line = next(f)
            while not line.startswith("# "):
                line = next(f)
        if line.startswith("# "):
            if releases > 0:
                if item_open:
                    html.append("</li>")
                    item_open = False
                html.append(template_end)
            if releases == MAX_RELEASES:
                break
            match = release_header.match(line)
            assert match, line
            version = match.group(1)
            date = match.group(2)
            html.append(template_start % locals())
            releases += 1
            if releases == 1:
                print("Newest release in changelog:", version)
                with open(VERSIONFILE, "w") as f:
                    f.write(version)
        elif line:
            if line.startswith("* "):
                if item_open:
                    html.append("</li>")
                    item_open = False
                html.append(f"<li>{line[2:]}")
                item_open = True
            else:
                html.append("    " + line)

html = "\n".join(html)

with open(OUTFILE, "w") as f:
    f.write(news % locals())
