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

version = '0.8.4'
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
As you see you can format your text ""**""**bold**""**"", ""//""//italic//""//"", \
""--""--stricken--""--"" and ""__""__underlined__""__"". \
To see the results, just click on the "Preview" button. 

=== Extra Content ===
On the right there is space for extra content, things that can easily be sorted into categories.
For example you could add the category "Ideas" and then today's ideas to it.

=== Templates ===
RedNotebook supports a template system. Click on the arrow next to the \
"Template" button to see the available options. You can have one template for every day \
of the week and unlimited arbitrarily named templates.

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
Now you can erase this help text and enter e.g. what you have done today. \
To restore these instructions click on "Help" -> "Restore example content". \
The examples will be added after the last edited day in the journal.
Alternatively you can find some documentation under "Help" -> "Help".

If you encounter any errors, please drop me a note so I can fix them.

There are many features I have planned to add in the future so stay tuned.
I hope you enjoy the program!'''

welcome_day = {'text': completeWelcomeText,
u'Cool Stuff': {u'Ate **two** cans of spam': None},
u'Ideas': {u'Use a cool journal app': None},
u'Tags': {u'Work': None, u'Documentation': None},
}

example_day1 = {
'text': '''\
===Categories===
On the right there is space for extra content, things that can easily be sorted into categories.
For example you could add the category Ideas and then add your ideas \
of that day to it:

- Ideas
  - Invent Anti-Hangover-Machine
  
  
The name "Categories" is a little bit confusing. It does not mean that a day is \
put into a category, but that there is additional content on the right, \
sorted into categories. "Topics" would probably be a better name.

Those topics have several items distributed over various days.

I’ll give you an example: I like to maintain a list of cool things I have done. \
So if I did a cool thing on some day, I navigate to that day, add the category \
"Cool Stuff" and add an entry "Visit the pope" (Sadly I haven’t done that, yet ;-) ). \
When I have done more cool things on many days, they all have a category "Cool Stuff" \
and many different entries. It is possible to export only that category and \
get a list of the cool stuff that happened to me with the respective dates.

Additionally you can select the "Cool Stuff" category in the word cloud window \
to get a list of all the cool things.''',
u'Cool Stuff': {u'Went to see the pope': None},
u'Ideas': {u'Invent Anti-Hangover-Machine': None},
u'Tags': {u'Documentation': None, u'Projects': None},
u'Todo': {u'**Wash the dishes**': None},
}

example_day2 = {
'text': '''\
=== Multiple Entries ===
You can add multiple entries to one day in two ways:
- Use two different journals (one named “Work”, the other “Play”)
- Separate your two entries by different titles (===Work===, ===Play===) 
- Use a horizontal separator line (20 “=”s)


====================

=== Work ===
Here goes the first entry.

====================

=== Play ===
Here comes the entry about the fun stuff.''',
u'Tags': {u'Documentation': None, u'Work': None, u'Play': None},}

example_day3 = {
'text': '''\
=== Todo list ===
You can also use RedNotebook as a todo list. A big advantage is, that you never \
have to explicitly state the date when you added the todo item, you just add it \
on one day and it remains there until you delete it. 

Here is how it goes:
- On the right click on "New Entry"
- Fill "Todo" and "Remember the milk" in the fields and hit "OK"
- Select the categories cloud from the drop down menu on the left
- Now you can click on "todo" and see all your todo items


- To tick off a todo item you can strike it out by adding "--" around the item.
- To mark an item as important, add "**" around it.


So --Remember the milk-- becomes stricken and **Wash the dishes** becomes bold. 

You can see all your todo items at once by clicking "todo" in the category cloud \
on the left. There you can also \
group your todo items into important and finished items by hitting "Entry" \
at the top of the list.

It probably sometimes makes sense to add the todo items to the day you want to \
have completed them (deadline day).

Once you've finished an item, you could also change its category name from \
"Todo" to e.g. "Done".''',
u'Tags': {u'Documentation': None,},
u'Todo': {u'--Remember the milk--': None,
		u'Take a break': None},
u'Done': {u'--Check mail--': None,},
}

example_content = [welcome_day, example_day1, example_day2, example_day3]

helpText = '''\n
== Text ==
This text field is the container for your normal diary entries like this one: 

Today I went to a //pet shop// and bought a **tiger**. Then we went to the \
--pool-- park and had a nice time playing \
ultimate frisbee. Afterwards we watched "__Life of Brian__".

== Format ==
As you see you can format your text ""**""**bold**""**"", ""//""//italic//""//"", \
""--""--stricken--""--"" and ""__""__underlined__""__"".

% Formatting commands inside two pairs of "" are not interpreted

**Comments** can be inserted after percent signs (**%**). They will not be shown in the \
preview and the exports. The % has to be the first character on the line.

To see the results, just click on the "Preview" button. 
You can also see how \
this text was formatted by looking at its [source source.txt].

== Extra Content ==
On the right there is space for extra content, things that can easily be sorted into categories.
For example you could add the category Ideas and then add your ideas \
of that day to it:

- Ideas
  - Invent Anti-Hangover-Machine
  
  
The name "Categories" is a little bit confusing. It does not mean that a day is put into a category, 
but that there is additional content on the right, sorted into categories. "Topics" would probably be a better name.

Those topics have several items distributed over various days. \
I’ll give you an example: I like to maintain a list of cool things I have done. \
So if I did a cool thing on some day, I navigate to that day, add the category \
"Cool Stuff" and add an entry "Visit the pope" (Sadly I haven’t done that, yet ;-) ). \
When I have done more cool things on many days, they all have a category "Cool Stuff" \
and many different entries. Now it is possible to export only that category and \
get a list of the cool stuff that happened to me with the respective dates.

== Images, Files and Links ==
RedNotebook lets you insert images, files and links into your entries. To do so, select the \
appropriate option in the "Insert" pull-down menu above the main text field. The text will \
be inserted at the current cursor position.

== Templates ==
RedNotebook supports a template system. Click on the arrow next to the \
"Template" button to see the available options. You can have one template for every day \
of the week and unlimited arbitrarily named templates.

== Tags ==
Tagging an entry (e.g. with the tag "Work") is also easy: On the right, click on "Add Tag" and insert \
"Work" into the lower textbox. The result looks like:

- Tags
  - Work
  

You can see a tag cloud on the left by activating the "Clouds" tab and \
selecting "Tags". Get a list of all tags with a given name by clicking on that tag in the cloud.

== Search ==
On the left you find the fancy search field. You can search for text, display a \
category's content or show all days with a given tag. Double-clicking on a day takes you directly \
to it. 

== Clouds ==
Clicking on the "Clouds" tab on the left lets you view the most often used words in your journal.
You can select to view your category or tag clouds by clicking on the scroll-down menu.
If words appear in the cloud that you don't want to see there, you can exclude them. Just mark the \
words and right click on the selection. Then click on "Hide selected words".
Alternatively you can open the Preferences dialog and add the words to the cloud blocklist there.

== Options ==
Make sure you check out the customizable options in the Preferences dialog. You can
open this dialog by clicking on the entry in the "Edit" menu.

== Save ==
Everything you enter will be saved automatically at regular intervals and when you exit the program. \
If you want to double check you can save your contents by pressing "Strg-S" \
or using the menu entry under "File" in the top left corner. 
To avoid data loss you should also backup your content regularly. "Backup" in the "File" menu saves \
all your entered data in a zip file.

== Export ==
In the same menu you also find an "Export"-Button. Click on it and export your diary to Plain Text, HTML or Latex.

**Latex caveats**

Make sure to type all links with the full path including the protocol:

- http://www.wikipedia.org or http://wikipedia.org (--wikipedia.org--, --"""www.wikipedia.org"""--)
- file:///home/sam/myfile.txt (--/home/sam/myfile.txt--)


===Export to PDF===

Although you cannot export your journal directly to PDF, you can easily convert \
the exported latex (.tex) files to PDF. Here is how you do it:

**Linux**

For the conversion on Linux you need some extra packages: texlive-latex-base and \
texlive-latex-recommended. Maybe you also need texlive-latex-extra. Those contain \
the pdflatex program and are available in the repositories of most Linux distros. 

You can convert the .tex file by typing the following text in a command line: \

"""pdflatex your-rednotebook-export.tex"""

Alternatively you can install a Latex editor like Kile \
(http://kile.sourceforge.net/), open the .tex file with it and hit the export \
button.

However there are some pitfalls: Sometimes not all exported characters can be \
converted to pdf. 
E.g. problems occur when exporting \
the euro sign (€) or other "non-standard" characters to pdf.

If you run into any problems during the conversion, the easiest way to solve \
them is to install a latex editor and do the conversion with it. That way \
you can see the errors right away and get rid of them by editing the file. 

**Windows**

You can open an exported Latex file with Texniccenter and convert it to PDF \
with MikTex. Visit www.texniccenter.org/ and www.miktex.org \
for the programs and instructions. Basically you have to download both programs, \
open the .tex file with Texniccenter and select "Build Output" from the \
"Output" menu. The program will then create the beautifully looking PDF in the
same directory.

== Keyboard Shortcuts ==
||   Action          |   Shortcut             |
| Preview (On/Off)   | <Ctrl> + P             |
| Find               | <Ctrl> + F             |
| Go back one day    | <Ctrl> + PageDown      |
| Go forward one day | <Ctrl> + PageUp        |
| Insert link        | <Ctrl> + L             |
| Insert date/time   | <Ctrl> + D             |
| New entry          | <Ctrl> + N             |
| Add Tag            | <Ctrl> + T             |

You can find other shortcuts in the menus.

== Questions ==
If you have any questions or comments, feel free to post them in the forum or \
contact me directly.

== Bugs ==
There is no software without bugs, so if you encounter one please drop me a note.
This way RedNotebook can get better not only for you, but for all users.

Bug reports should go [here https://bugs.launchpad.net/rednotebook], but if you
don't know how to use that site, a simple mail is equally fine.
'''

desktop_file = '''\
[Desktop Entry]
Version=1.0
Name=RedNotebook
GenericName=Journal
Comment=Daily journal with calendar, templates and keyword searching
Exec=rednotebook
Icon=rednotebook
Terminal=false
Type=Application
Categories=Office;
StartupNotify=true
'''
