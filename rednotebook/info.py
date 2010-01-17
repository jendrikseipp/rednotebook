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

# For testing
import __builtin__
if not hasattr(__builtin__, '_'):
	def _(string):
		return string

version = '0.9.2'
author = 'Jendrik Seipp'
authorMail = 'jendrikseipp@web.de'
url = 'http://rednotebook.sourceforge.net'
forum_url = 'http://apps.sourceforge.net/phpbb/rednotebook/'
translation_url = 'https://translations.launchpad.net/rednotebook/'
bug_url = 'https://bugs.launchpad.net/rednotebook/+filebug'
developers = 	['Jendrik Seipp <jendrikseipp@web.de>',
				'',
				'Contributors:',
				'Alexandre Cucumel <superkiouk@gmail.com>',
				]
comments = '''\
RedNotebook is a graphical journal to keep track of notes and \
thoughts. It includes a calendar navigation, customizable \
templates, export functionality and word clouds. You can also \
format, tag and search your entries.\
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

command_line_help = '''\
RedNotebook %s

The optional journal-path can be one of the following:
 - An absolute path (e.g. /home/username/myjournal)
 - A relative path (e.g. ../dir/myjournal)
 - The name of a directory under $HOME/.rednotebook/ (e.g. myjournal)

If the journal-path is omitted the last session's journal will be used.
At the first program start this defaults to "$HOME/.rednotebook/data".
''' % version

greeting = _('''Hello,
this is RedNotebook, a desktop journal. Thank you very much for giving it a try.''')
overview1 = _('The interface is divided into three parts:')
### Translators: The location "left"
overview21 = _('Left')
overview22 = _('Navigation with the calendar')
### Translators: The location "center"
overview31 = _('Center')
overview32 = _('Text for a day')
### Translators: The location "right"
overview41 = _('Right')
overview42 = _('Annotations to a day')

text_entry = _('Text entries')
text_entry_par = _('An entry could look like this:')
example_entry = _('''Today I went to the //pet shop// and bought a **tiger**. Then we went to the \
--pool-- park and had a nice time playing \
ultimate frisbee. Afterwards we watched "__Life of Brian__".''')

annotations = _('Annotations')
ann1 = _('On the right there is space for annotations to a day.')
ann2 = _('Annotations are notes that can easily be sorted into categories.')
ann3 = _('''For example you could create the category "Ideas" \
and then add today's ideas to it.''')
ann_par = ' '.join([ann1, ann2, ann3])

templates = ('Templates')
temp1 = ('RedNotebook supports templates.')
temp2 = ('Click on the arrow next to the "Template" button to see some options.')
temp3 = ('''You can have one template for every day \
of the week and unlimited arbitrarily named templates.''')
temp_par = ' '.join([temp1, temp2, temp3])

### Translators: both are verbs
save = _('Save and Export')
save1 = _('''Everything you enter will be saved automatically at \
regular intervals and when you exit the program.''')
save2 = _('To avoid data loss you should backup your journal regularly.')
save3 = _('"Backup" in the "Journal" menu saves all your entered data in a zip file.')
save4 = _('In the "Journal" menu you also find the "Export" button.')
save5 = _('Click on "Export" and export your diary to Plain Text, HTML or Latex.')
save_par = ' '.join([save1, save2, save3, save4, save5])

### Translators: noun
help = _('Help')
### Translators: "Help" -> noun
help3 = _('You can find more documentation under "Help" -> "Help".')
help_par = ' '.join([help3])

error1 = _('If you encounter any errors, please drop me a note so I can fix them.')
error2 = _('Any feedback is appreciated.')
error_par = ' '.join([error1, error2])

goodbye_par = _('Have a nice day!')


completeWelcomeText = '''\
%(greeting)s
%(overview1)s

- **%(overview21)s**: %(overview22)s
- **%(overview31)s**: %(overview32)s
- **%(overview41)s**: %(overview42)s


=== %(text_entry)s ===
%(text_entry_par)s

%(example_entry)s

=== %(annotations)s ===
%(ann_par)s

=== %(save)s ===
%(save_par)s

=== %(help)s ===
%(help_par)s

%(error_par)s

%(goodbye_par)s''' % globals()

welcome_day = {'text': completeWelcomeText,
u'Cool Stuff': {u'Ate **two** cans of spam': None},
_(u'Ideas'): {_(u'Use a cool journal app'): None},
u'Tags': {u'Work': None, u'Documentation': None},
}

example_day1 = {
'text': '''\
=== %(annotations)s ===
%(ann_par)s

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
to get a list of all the cool things.''' % globals(),
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

Here is how it works:
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
"Todo" to "Done".''',
u'Tags': {u'Documentation': None,},
u'Todo': {u'--Remember the milk--': None,
		u'Take a break': None},
u'Done': {u'--Check mail--': None,},
}

example_content = [welcome_day, example_day1, example_day2, example_day3]

ann_help_text = example_day1['text'].replace('===', '==')

multiple_entries_text = example_day2['text']#.replace('=== Multiple Entries ===', '== Multiple Entries ==')
multiple_entries_text = multiple_entries_text.replace('=== Work ===', '**Work**\n')
multiple_entries_text = multiple_entries_text.replace('=== Play ===', '**Play**\n')

todo_help_text = example_day3['text']#.replace('=== Todo list ===', '== Todo list ==')


helpText = '''
== Text ==
The main text field is the container for your normal diary entries like this one:

%(example_entry)s

== Format ==
As you see, the text can be formatted **bold**, \
//italic//, --stricken-- and __underlined__. As a convenience there \
is also the "Format" button, with which you can format the main text and nodes \
in the categories tree on the right.

A blank line starts a new **paragraph**, \\ results in a newline.

%% Formatting commands inside two pairs of "" are not interpreted (""**not bold**"")

**Comments** can be inserted after percent signs (**%%**). They will not be shown in the \
preview and the exports. The %% has to be the first character on the line.

To see the result, click on the "Preview" button.
You can also see how \
this text was formatted by looking at its [source source.txt].

%(ann_help_text)s

== Images, Files and Links ==
RedNotebook lets you insert images, files and links into your entries. To do so, select the \
appropriate option in the "Insert" pull-down menu above the main text field. The text will \
be inserted at the current cursor position.

== %(templates)s ==
%(temp_par)s 
The files 1.txt to 7.txt in the template directory correspond to the templates \
for each day of the week. The current weekday's template will be filled \
into the text area when you click on "Template". You can open the template files \
from inside RedNotebook by opening the menu next to the "Template" button.

== Tags ==
Tagging an entry (e.g. with the tag "Work") is also easy: On the right, click on "Add Tag" and insert \
"Work" into the lower textbox. The result looks like:

- Tags
  - Work


You can see a tag cloud on the left by activating the "Clouds" tab and \
selecting "Tags". Get a list of all tags with a given name by clicking on that tag in the cloud.

== Search ==
On the left you find the search box. You can search for text, display a \
category's content or show all days with a given tag. \
Double-clicking on a day lets you jump to it.

== Clouds ==
Clicking on the "Clouds" tab on the left lets you view the most often used words in your journal.
You can select to view your category or tag clouds by clicking on the scroll-down menu.
If words appear in the cloud that you don't want to see there, just right-click on them. \
Alternatively you can open the Preferences dialog and add the words to the cloud blocklist there.

== Options ==
Make sure you check out the customizable options in the Preferences dialog. You can
open this dialog by clicking on the entry in the "Edit" menu.

== Save ==
%(save1)s %(save2)s %(save3)s

=== Save to remote FTP or SSH server ===
Since version 0.8.9 you can have your journal directory on a remote server. The feature is \
however only available on Linux machines. To use the feature you have to connect your computer \
to the remote server. This is most easily done in Nautilus by clicking on "File" -> \
"Connect to Server". Be sure to add a bookmark for the server. This way you can see your \
server in Nautilus at all times on the left side. The next time you open RedNotebook you \
will find your server in the "New", "Open" and "Save As" dialogs. There you can select \
a new folder on the server for your journal.

Obviously you have to be connected to the internet to use that feature. Be sure to backup your \
data regularly if you plan to save your content remotely. There are always more pitfalls when \
an internet connection is involved.

== Export ==
%(save4)s %(save5)s

**Latex caveats**

Make sure to type all links with the full path including the protocol:

- http://www.wikipedia.org or http://wikipedia.org (--wikipedia.org--, --"""www.wikipedia.org"""--)
- file:///home/sam/myfile.txt (--/home/sam/myfile.txt--)


===Convert Latex output to PDF===

Since version 0.9.2 you can export your journal directly to PDF, so this section \
may be obsolete. However, there may be some people who prefer to export their \
journal to Latex first and convert it to PDF later. Here is how you do it:

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
| New category entry | <Ctrl> + N             |
| Add Tag            | <Ctrl> + T             |

You can find other shortcuts in the menus.

== Tips ==
%(multiple_entries_text)s

%(todo_help_text)s

== Questions ==
If you have any questions or comments, feel free to post them in the \
[forum http://apps.sourceforge.net/phpbb/rednotebook/] or \
contact me directly.

== Bugs ==
There is no software without bugs, so if you encounter one please drop me a note.
This way RedNotebook can get better not only for you, but for all users.

Bug reports should go [here https://bugs.launchpad.net/rednotebook], but if you
don't know how to use that site, a simple mail is equally fine.
''' % globals()

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

def write_documentation(dir):
	'''
	Write the documenation as html to a directory
	Include the original markup as "source.txt"
	'''
	from rednotebook.util import utils
	from rednotebook.util import markup

	utils.write_file(helpText, os.path.join(dir, 'source.txt'))
	headers = [_('RedNotebook Documentation'), version, '']
	options = {'toc': 1,}
	html = markup.convert(helpText, 'xhtml', headers, options)
	utils.write_file(html, os.path.join(dir, 'help.html'))

if __name__ == '__main__':
	import sys
	sys.path.insert(0, os.path.abspath("./../"))

	print completeWelcomeText
	print '*'*80
	print helpText

	doc_dir = '../doc'
	doc_dir = os.path.abspath(doc_dir)

	write_documentation(doc_dir)

	#logging.getLogger('').setLevel(logging.DEBUG)
