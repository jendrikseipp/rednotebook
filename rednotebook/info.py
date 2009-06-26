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
from rednotebook.util import filesystem

version = '0.7.5'
author = 'Jendrik Seipp'
authorMail = 'jendrikseipp@web.de'
url = 'http://rednotebook.sourceforge.net'
developers = 	['Jendrik Seipp <jendrikseipp@web.de>',
				'',
				'Contributors:',
				'Alexandre Cucumel <superkiouk@gmail.com>',
				]
comments = '''\
RedNotebook is a graphical diary and journal to keep track of notes and \
thoughts. It includes a calendar navigation, customizable \ 
templates for each day, export functionality and word clouds. You can also \
tag and search your entries.\
'''

licenseText = '''\
Copyright (c) 2009  Jendrik Seipp

RedNotebook is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

RedNotebook is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with RedNotebook; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''
            
completeWelcomeText = '''\
Hello, 
this is RedNotebook, a desktop journal/diary. Thank you very much for giving it a try. 
This text field is the container for your normal entries like this one: 

Today I went to a //pet shop// and bought a **tiger**. Then we went to the \
--pool-- park and had a nice time playing \
ultimate frisbee. Afterwards we watched "__Life of Brian__".

=== Format ===
As you see you can format your text **bold**, //italic//, --stricken-- and __underlined__. \
To see the results, just click on the "Preview" button. 

=== Extra Content ===
On the right there is space for extra content, things that can easily be sorted into categories.
For example you could add the category "Ideas" and then today's ideas to it.

=== Templates ===
RedNotebook supports a template system: In the directory "''' + filesystem.templateDir + '''" you find several \
text files. The files "1.txt", "2.txt" etc. correspond to the days of the week. 
Additionally you can have arbitrarily named templates. 
Template files can be edited with your favourite text editor \
and inserted by selecting them in the "Insert Template" drop-down menu.

=== Tags ===
Tagging an entry (e.g. with the tag "Work") is also easy: On the right, click on "Add Tag" and insert \
"Work" into the lower textbox. You can see a tag cloud on the left by activating the "Clouds" tab and \
selecting "Tags".

=== Search ===
On the left you find the fancy search field. You can search for text, display a \
category's content or show all days with a given tag.

=== Save and Export ===
Everything you enter will be saved automatically at regular intervals and when you exit the program. \
If you want to double check you can save your contents by pressing "Ctrl-S" \
or using the menu entry under "File" in the top left corner. 
To avoid data loss you should also backup your content regularly. "Backup" in the "File" menu saves \
all your entered data in a zip file. 
In the same menu you also find an "Export"-Button. \
Click on it and export your diary to Plain Text, HTML or Latex.

=== Help ===
Now you can erase this help text and enter e.g. what you have done today. To read the instructions again, \
go to "Help -> Help" in the menu bar.

There are many features I have planned to add in the future so stay tuned.
I hope you enjoy the program!'''

helpText = '''\n
=== Text ===
This text field is the container for your normal diary entries like this one: 

Today I went to a //pet shop// and bought a **tiger**. Then we went to the \
--pool-- park and had a nice time playing \
ultimate frisbee. Afterwards we watched "__Life of Brian__".

=== Format ===
As you see you can format your text ""**""**bold**""**"", ""//""//italic//""//"", \
""--""--stricken--""--"" and ""__""__underlined__""__"".

% Formatting commands inside two pairs of "" are not interpreted
% Comments can be inserted after percent signs (%)

To see the results, just click on the "Preview" button. 
You can also see how \
this text was formatted by looking at its [source source.txt].

=== Extra Content ===
On the right there is space for extra content, things that can easily be sorted into categories.
For example you could add the category Ideas and then add your ideas \
of that day to it:

- Ideas
  - Invent Anti-Hangover-Machine


=== Images, Files and Links ===
RedNotebook lets you insert images, files and links into your entries. To do so, select the \
appropriate option in the "Insert" pull-down menu above the main text field. The text will \
be inserted at the current cursor position.

=== Templates ===
RedNotebook supports a template system: In the directory "''' + filesystem.templateDir + '''" you find several \
text files. The files "1.txt", "2.txt" etc. correspond to the days of the week. 
Additionally you can have arbitrarily named templates. 
Template files can be edited with your favourite text editor \
and inserted by selecting them in the "Insert Template" drop-down menu.

=== Tags ===
Tagging an entry (e.g. with the tag "Work") is also easy: On the right, click on "Add Tag" and insert \
"Work" into the lower textbox. The result looks like:

- Tags
  - Work
  

You can see a tag cloud on the left by activating the "Clouds" tab and \
selecting "Tags". Get a list of all tags with a given name by clicking on that tag in the cloud.

=== Search ===
On the left you find the fancy search field. You can search for text, display a \
category's content or show all days with a given tag. Double-clicking on a day takes you directly \
to it. 

=== Clouds ===
Clicking on the "Clouds" tab on the left lets you view the most often used words in your journal.
You can select to view your category or tag clouds by clicking on the scroll-down menu.

=== Save ===
Everything you enter will be saved automatically at regular intervals and when you exit the program. \
If you want to double check you can save your contents by pressing "Strg-S" \
or using the menu entry under "File" in the top left corner. 
To avoid data loss you should also backup your content regularly. "Backup" in the "File" menu saves \
all your entered data in a zip file.

=== Export ===
In the same menu you also find an "Export"-Button. Click on it and export your diary to Plain Text, HTML or Latex.

=== Keyboard Shortcuts ===
||   Action   |   Shortcut    |
| Go back one day    | <Ctrl> + PageDown      |
| Go forward one day | <Ctrl> + PageUp        |
| Insert picture | <Ctrl> + P        |
| Insert file | <Ctrl> + F        |
| Insert link | <Ctrl> + L        |
| Insert date/time | <Ctrl> + D        |

You can find other shortcuts in the menus.

=== Questions ===
If you have any questions or comments, feel free to post them in the forum or \
contact me directly.
'''

#**Linux**
#
#If you are on Linux, you can also export your diary directly to PDF. All you have to do is to install the packages \
#texlive-latex-base and texlive-latex-recommended. Those contain the pdflatex program and are available in the \
#repositories of most Linux distros.
#
#However there are some pitfalls: Not all characters can be exported to pdf. E.g. problems occur when exporting \
#the euro sign or other "non-standard" characters to pdf.
#
#When you export to PDF, RedNotebook will create a Latex file (.tex) and then make an attempt to convert that file to pdf \
#using pdflatex. If the .tex file contains odd characters this might or might not fail. Most of the time a pdf is created \
#even if RedNotebook tells you that an error occured.
#
#**Windows**
#
#Windows users cannot export directly to pdf as of now. However you can open an exported \
#Latex file with Texniccenter and MikTex and export it to pdf (Look over at www.toolscenter.org and www.miktex.org \
#for programs and instructions).
