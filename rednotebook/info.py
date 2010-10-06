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

import os

# For testing
import __builtin__
if not hasattr(__builtin__, '_'):
    def _(string):
        return string

version =           '1.1.2'
author =            'Jendrik Seipp'
authorMail =        'jendrikseipp@web.de'
url =               'http://rednotebook.sourceforge.net'
forum_url =         'http://apps.sourceforge.net/phpbb/rednotebook/'
translation_url =   'https://translations.launchpad.net/rednotebook/'
bug_url =           'https://bugs.launchpad.net/rednotebook/+filebug'

developers =    ['Jendrik Seipp <jendrikseipp@web.de>',
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

license_text = '''\
Copyright (c) 2009,2010  Jendrik Seipp

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
u'Movies': {u"Monty Python's Life of Brian": None},
u'Tags': {u'Work': None, u'Documentation': None},
}

example_day1 = {
'text': '''\
=== Annotations in Categories ===
%(ann_par)s

- Ideas
  - Invent Anti-Hangover-Machine
- Movies
  - Monty Python and the Holy Grail


The name "Categories" is a little bit confusing. It does not mean that a day is \
put into a category, but that there is additional content on the right, \
sorted into categories. A category will contain several notes distributed over various days.

For example you could want to remember all the movies you watch. \
Each time you watch a new one, add the category "Movies" with the \
entry "Name of the movie" to the day.

I’ll give you another example: I like to maintain a list of cool things I have done. \
So if I did a cool thing on some day, I navigate to that day and add the category \
"Cool Stuff" with the entry "Visit the pope" (Sadly I haven’t done that, yet ;-) ). \
When I have done more cool things on many days, they all have a category "Cool Stuff" \
and many different entries. It is possible to export only that category and \
get a list of the cool stuff that happened to me with the respective dates.

Additionally you can select the "Cool Stuff" category in the word cloud window \
to get a list of all the cool things.

Maybe a good thing to know is the following: 
"Tags" is a category, the tagnames are entries in the category "Tags", \
distributed over various days. 
Similarly you can have a category "Movies" and add it together with \
the movie's name to every day on which you see a new film.

Category entries can have all of the formatting that the main text supports, \
so e.g. you can add bold text, links or images.''' % globals(),
u'Cool Stuff': {u'Went to see the pope': None},
u'Ideas': {u'Invent Anti-Hangover-Machine': None},
u'Movies': {u'Monty Python and the Holy Grail': None},
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


So --Remember the milk-- becomes struck through and **Wash the dishes** becomes bold.

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

multiple_entries_text = example_day2['text']
multiple_entries_text = multiple_entries_text.replace('=== Work ===', '**Work**\n')
multiple_entries_text = multiple_entries_text.replace('=== Play ===', '**Play**\n')

todo_help_text = example_day3['text']


help_text = '''
==== Text ====
The main text field is the container for your normal diary entries like this one:

%(example_entry)s

==== Format ====
As you see, the text can be formatted **bold**, \
//italic//, --struck through-- and __underlined__. As a convenience there \
is also the "Format" button, with which you can format the main text and nodes \
in the categories tree on the right.

A blank line starts a new **paragraph**, \\\\ results in a newline.

%% Formatting commands inside two pairs of "" are not interpreted (""**not bold**"")

**Comments** can be inserted after percent signs (**%%**). They will not be shown in the \
preview and the exports. The %% has to be the first character on the line.

To see the result, click on the "Preview" button.
You can also see how \
this text was formatted by looking at its [source source.txt].

%(ann_help_text)s

==== Images, Files and Links ====
RedNotebook lets you insert images, files and links into your entries. \
To do so, select the appropriate option in the "Insert" pull-down menu \
above the main text field. The text will be inserted at the current \
cursor position.

With the insert button you cannot insert **links to directories** on your computer. \
Those can be inserted manually however (""[Home ""file:///home/""]"").

==== %(templates)s ====
%(temp_par)s 
The files 1.txt to 7.txt in the template directory correspond to the templates \
for each day of the week. The current weekday's template will be filled \
into the text area when you click on "Template". You can open the template files \
from inside RedNotebook by opening the menu next to the "Template" button.

==== Tags ====
Tagging an entry (e.g. with the tag "Work") is also easy: \
On the right, click on "Add Tag" and insert \
"Work" into the lower textbox. The result looks like:

- Tags
  - Work


You can see a tag cloud on the left by activating the "Clouds" tab and \
selecting "Tags". Get a list of all tags with a given name by clicking \
on that tag in the cloud.

==== Search ====
On the left you find the search box. You can search for text, display a \
category's content or show all days with a given tag. \
Double-clicking on a day lets you jump to it.

==== Clouds ====
Clicking on the "Clouds" tab on the left lets you view the most often used words in your journal.
You can select to view your category or tag clouds by clicking on the scroll-down menu.
If words appear in the cloud that you don't want to see there, just right-click on them. \
Alternatively you can open the Preferences dialog and add the words to the cloud blacklist there.

==== Spellcheck ====
RedNotebook supports spellchecking your entries if you have \
python-gtkspell installed (Only available on Linux). \
To highlight all misspelled words in your entries, select the corresponding option in \
the preferences window.

Since gtkspell 2.0.15, you can select the spellchecking language by right-clicking on the \
main text area (in edit mode) and choosing it from the submenu "Languages".

==== Options ====
Make sure you check out the customizable options in the Preferences dialog. You can
open this dialog by clicking on the entry in the "Edit" menu.

==== Save ====
%(save1)s %(save2)s %(save3)s

==== Export ====
%(save4)s %(save5)s

Since version 0.9.2 you can also directly export your journal to PDF. If the \
option does not show up in the export assistant, you need to install \
pywebkitgtk version 1.1.5 or later (the package is sometime called \
python-webkit). 

**Latex caveats**

Make sure to type all links with the full path including the protocol:

- http://www.wikipedia.org or http://wikipedia.org (--wikipedia.org--, --"""www.wikipedia.org"""--)
- file:///home/sam/myfile.txt (--/home/sam/myfile.txt--)


==== Synchronize across multiple computers ====[sync]
Syncing RedNotebook with a remote server is easy. You can either use a \
cloud service like Ubuntu One or Dropbox or save your journal to your \
own server.

=== Ubuntu One and Dropbox ===
If you are registered for either [Ubuntu One ""http://one.ubuntu.com""] \
or [Dropbox http://www.dropbox.com], you can just save your journal in \
a subfolder of the respective synchronized folder in your home directory.

=== Directly save to remote FTP or SSH server ===
Since version 0.8.9 you can have your journal directory on a remote server. The feature is \
however only available on Linux machines. To use the feature you have to connect your computer \
to the remote server. This is most easily done in Nautilus by clicking on "File" -> \
"Connect to Server". Be sure to add a bookmark for the server. This way you can see your \
server in Nautilus at all times on the left side. The next time you open RedNotebook you \
will find your server in the "New", "Open" and "Save As" dialogs. There you can select \
a new folder on the server for your journal.

=== External sync with remote server ===
If you have your own server, you might want to try \
[Conduit http://www.conduit-project.org] or \
[Unison http://www.cis.upenn.edu/~bcpierce/unison] for example. \
To sync or backup your journal you have to sync your journal folder \
(default is "$HOME/.rednotebook/data/") with a folder on your server. \
It would be great if someone could write a tutorial about that.

Obviously you have to be connected to the internet to use that feature. Be sure to backup your \
data regularly if you plan to save your content remotely. There are always more pitfalls when \
an internet connection is involved.

=== Dual Boot ===
Using RedNotebook from multiple operating systems on the same computer is \
also possible. Save your Journal with "Journal->Save As" in a directory \
all systems can access. Then on the other systems you can open the \
journal with "Journal->Open".

Optionally you can also **share your settings** and templates. \
This is possible since version 0.9.4. The relevant setting is found in \
the file "rednotebook/files/default.cfg". There you can set the value of \
userDir to the path where you want to share your settings between the \
systems.

==== Portable mode ====
RedNotebook can be run in portable mode. In this mode, the \
template directory and the configuration and log file are saved \
in the application directory instead of in the home directory. \
Additionally the path to the last opened journal is remembered \
relatively to the application directory. 

To use RedNotebook on a flash drive on Windows, run the installer and \
select a directory on your USB drive as the installation directory. \
You probably don't need the "Start Menu Group" and Desktop icons in \
portable mode.

To **activate portable mode**, change into the files/ directory and in the \
default.cfg file set portable=1.

=== Convert Latex output to PDF ===

In recent RedNotebook versions you can export your journal directly to PDF, \
so this section may be obsolete. \
However, there may be some people who prefer to export their \
journal to Latex first and convert it to PDF later. Here is how you do it:

== Linux ==

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

== Windows ==

You can open an exported Latex file with Texniccenter and convert it to PDF \
with MikTex. Visit www.texniccenter.org/ and www.miktex.org \
for the programs and instructions. Basically you have to download both programs, \
open the .tex file with Texniccenter and select "Build Output" from the \
"Output" menu. The program will then create the beautifully looking PDF in the
same directory.

==== Keyboard Shortcuts ====
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

==== Encryption ====
You can use e.g. [TrueCrypt http://www.truecrypt.org] to encrypt your \
journal. Nick Bair has written a nice tutorial about \
[encrypting RedNotebook files \
http://sourceforge.net/apps/phpbb/rednotebook/viewtopic.php?f=3&t=14] \
on Windows. The procedure for other operating systems should be similar. \
The general idea is to create and mount an encrypted folder with \
TrueCrypt and put your journal files in there.

In recent Linux distributions is has become pretty easy to encrypt \
your entire home partition. I would recommend that to anyone who \
wishes to protect her/his diary and all other personal files. \
This method is especially useful for laptop users, because their \
computers are more likely to be stolen. If you encrypt your home \
partition all RedNotebook data will be encrypted, too.

==== Tips ====
%(multiple_entries_text)s

%(todo_help_text)s

=== Week Numbers ===
If you'd like to see the week numbers in the calendar, you can set the \
value of weekNumbers to 1 in the configuration file. This file \
normally resides at $HOME/.rednotebook/configuration.cfg

=== Language ===
If you want to change RedNotebook's language, setting the environment \
variable LANG to a different language code should be sufficient. \
Language codes have e.g. the format "de_DE" or "de_DE.UTF-8" (German). \
To set the language to English you can also set the code to "C".

On Linux, start a terminal and call ``LANG=de_DE.utf8``. Then in the \
same terminal, run ``rednotebook``. The language change will be gone \
however once you close the terminal.

On Windows, set or create a PATH environment variable with the desired \
code.

=== Insert HTML or Latex code ===
To insert custom code into your entries surround the code with single \
quotes. Use 2 single quotes for inline insertions and 3 single quotes \
if you want to insert a whole paragraph. For paragraphs be sure to put \
the single quotes on their own line. \
This feature requires you to use webkit for previews (Only available on Linux).

||   Text                  |   Output                              |
| ``''<font color="red">Red</font>''`` | ''<font color="red">Red</font>'' |
| ``''$a^2$''``            | ''$a^2$'' (''a<sup>2</sup>'' in Latex) |

This feature can be used to insert e.g. latex formulas:

```
\'''
$$\sum_{i=1}^{n} i = \\frac{n \cdot (n+1)}{2}$$
\'''
```

will produce a nice looking formula in the Latex export.

=== Insert verbatim text (Preserve format) ===
To insert preformatted text preserving newlines and spaces, you can \
use the backquotes (`). Use 2 backquotes for inline insertions and 3 \
backquotes if you want to insert a whole paragraph. \
For paragraphs be sure to put the backquotes on their own line. \
This feature requires you to use webkit for previews (Only available on Linux).

Two examples (have a look at the [source source.txt] to see how it's done):

To install rednotebook use ``sudo apt-get install rednotebook``.

```
class Robot(object):
    def greet(self):
        print 'Hello World'

robot = Robot()
robot.greet()
```

=== List of all Entries ===
To get a list of all entries, just search for " " (the space character). \
This character is most likely included in all entries. You can sort the \
resulting list chronologically by pressing the "Date" button.

==== Command line options ====
```
Usage: rednotebook [options] [journal-path]

RedNotebook %(version)s

The optional journal-path can be one of the following:
 - An absolute path (e.g. /home/username/myjournal)
 - A relative path (e.g. ../dir/myjournal)
 - The name of a directory under $HOME/.rednotebook/ (e.g. myjournal)

If the journal-path is omitted the last session's journal will be used.
At the first program start this defaults to "$HOME/.rednotebook/data".


Options:
  -h, --help        show this help message and exit

  -d, --debug       Output debugging messages (default: False)

  -m, --minimized   Start mimimized to system tray (default: False)
```

==== Data Format ====
In this paragraph I will explain shortly what the RedNotebook files \
consist of. Firstly it is important to understand that the content \
is saved in a directory with many files, not just one file. \
The directory name is used as a name for the journal.

In the directory there are several files all conforming to the naming \
scheme "2010-05.txt" (<year>-<month>.txt). Obviously these files \
correspond to months (May 2010). 

Each month file contains text for the days of that month. \
The text is actually [YAML www.yaml.org] markup. Without the \
(unnecessary) python directives the files look like this:

```
24: {text: "This is a normal text entry."}
25:
  Ideas: {"Invent Anti-Hangover machine": null}
  text: "This is another text entry, shown in the main text area."
```

As you can see the data format uses a dictionary (or hashmap structure) \
for storing the information. The outer dictionary has the daynumbers as \
keys and the day content as values. The day values consist of another \
dictionary. It can have a key "text" whose value will be inserted in \
the main content area. Additionally there can be multiple other keys \
that stand for the categories that belong to that day. Each category \
contains a dictionary with only one key, the category entry.

==== Questions ====
If you have any questions or comments, feel free to post them in the \
[forum http://apps.sourceforge.net/phpbb/rednotebook/] or \
contact me directly.

==== Bugs ====
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
    from rednotebook.util import filesystem
    from rednotebook.util import markup

    filesystem.write_file(os.path.join(dir, 'source.txt'), help_text)
    headers = [_('RedNotebook Documentation'), version, '']
    options = {'toc': 1,}
    html = markup.convert(help_text, 'xhtml', headers, options)
    filesystem.write_file(os.path.join(dir, 'help.html'), html)

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
