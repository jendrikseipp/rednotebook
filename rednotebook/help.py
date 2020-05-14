# -----------------------------------------------------------------------
# Copyright (c) 2009-2018  Jendrik Seipp
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

from rednotebook import info


commandline_help = info.get_commandline_parser().format_help()

tags = _("Tags")

greeting = _("Hello!")
intro = _(
    "Some example text has been added to help you start and "
    "you can erase it whenever you like."
)
# Translators: "Help" -> noun
help_par = _(
    "The example text and more documentation is available under "
    '"Help" -> "Contents".'
)

# Translators: noun
preview = _("Preview")
preview1 = _(
    "There are two modes in RedNotebook, the __edit__ mode and the " "__preview__ mode."
)
preview2 = _("Click on Edit above to see the difference.")
preview_par = " ".join([preview1, preview2])

tags1 = _("Tagging is easy.")
tags2 = _("Just use #hashtags like on twitter.")
tags_par = " ".join([tags1, tags2])

example_entry = _(
    "Today I went to the //pet shop// and bought a **tiger**. "
    "Then we went to the --pool-- park and had a nice time playing "
    'ultimate frisbee. Afterwards we watched "__Life of Brian__".'
)

templates = "Templates"
temp1 = "RedNotebook supports templates."
temp2 = 'Click on the arrow next to the "Template" button to see some options.'
temp3 = """You can have one template for every day
of the week and unlimited arbitrarily named templates."""
temp_par = " ".join([temp1, temp2, temp3])

# Translators: both are verbs
save = _("Save and Export")
save1 = _(
    "Everything you enter will be saved automatically at regular "
    "intervals and when you exit the program."
)
save2 = _("To avoid data loss you should backup your journal regularly.")
save3 = _('"Backup" in the "Journal" menu saves all your entered data in a zip file.')
save4 = _('In the "Journal" menu you also find the "Export" button.')
save5 = _('Click on "Export" and export your diary to Plain Text, PDF, HTML or Latex.')
save_par = " ".join([save1, save2, save3, save4, save5])

error1 = _("If you encounter any errors, please drop me a note so I can fix them.")
error2 = _("Any feedback is appreciated.")
error_par = " ".join([error1, error2])

goodbye_par = _("Have a nice day!")

complete_welcome_text = (
    """\
%(greeting)s %(intro)s %(help_par)s

=== %(preview)s ===
%(preview_par)s

=== %(tags)s ===
%(tags_par)s

=== %(save)s ===
%(save_par)s

%(error_par)s

%(goodbye_par)s"""
    % globals()
)


welcome_day = {"text": complete_welcome_text}

multiple_entries_text = _(
    """\
=== Multiple entries ===
You can add multiple entries to a single day by \
using different journals (one named "Work", the other "Family"), \
separating your entries with different titles (=== Work ===, === Family ===) \
and using horizontal separator lines (20 "="s)."""
)

multiple_entries_example = _(
    """\
=== Work ===
Here goes the first entry. It is about #work.

====================

=== Family ===
Here comes the entry about my #family."""
)

multiple_entries_day = {
    "text": multiple_entries_text
    + "\n\n"
    + 20 * "="
    + "\n\n"
    + multiple_entries_example
}

example_content = [welcome_day, multiple_entries_day]

help_text = (
    """
== Layout ==
%(preview1)s


== Text ==
The main text field is the container for your normal diary entries like this one:

%(example_entry)s


== Format ==

As you see, the text can be formatted **bold**, //italic//, --struck
through-- and __underlined__. As a convenience there is also the
"Format" button.

A blank line starts a new **paragraph**, two backslashes \\\\ result in
a **newline**.

To see the result, click on the "Preview" button. You can also see how
this text was formatted by looking at its [source source.txt].

**Lists** can be created by using the following syntax, if you use "+"
instead of "-" you can create a **numbered list**:

```
- First Item
  - Indented Item
- Do not forget two blank lines after a list


```


== Hashtags ==
%(tags_par)s


== Images, Files and Links ==

RedNotebook lets you insert images, files and links into your entries.
To do so, select the appropriate option in the "Insert" pull-down menu
above the main text field. The text will be inserted at the current
cursor position. Note that currently, the things you insert are only
linked to, but not copied into your journal directory.

With the insert button you cannot insert **links to directories** on
your computer. Those can be inserted manually however (``[Home
""file:///home/""]`` becomes [Home ""file:///home/""]).


== Entry references ==

You can reference days in your journal by simply writing the date in
[YYYY-MM-DD] format. A date like [2019-02-14] will be rendered as a clickable
link in preview mode.

Alternatively, you can name your references. For example,

  ``[Today 2019-02-14] was a good day.``

will be shown as

  [Today 2019-02-14] was a good day.


== %(templates)s ==

%(temp_par)s
The files 1.txt to 7.txt in the template directory correspond to the
templates for each day of the week. The current weekday's template will
be filled into the text area when you click on "Template". You can open
the template files from inside RedNotebook by opening the menu next to
the "Template" button.


== Search ==

On the left you find the search box. Double-clicking on a day in the
search results lets you jump to it.

You can search for text or dates (e.g. 2014, 2014-01, 2014-01-19).


== Clouds ==[clouds]

The most frequently used words will appear in the word cloud on the
left. Its contents are only refreshed when RedNotebook starts and when
the journal is saved.

If a word appears in the cloud that you don't want to see there,
right-click and select to hide it. Alternatively, you can open the
Preferences dialog and add the word to the cloud blacklist. Short words
with less than five letters can be white-listed there as well. [Regular
expressions http://docs.python.org/library/re.html] are allowed in the
lists. If you want to hide words with special characters, you can
escape them with a backslash: 3\\.50\\?

You can limit the number of displayed words by tweaking the 'Tags in cloud'
configuration option. If this option is set to 0, no tags are displayed.

You can **hide the word cloud** by adding the regular expression .* to
the blacklist. This will filter out all words.


== Spellcheck ==

RedNotebook supports spellchecking your entries. This feature needs the
pyenchant library (``python-enchant`` on Ubuntu). Spellchecking can be
turned on and off by toggling the menu item in the "Edit" menu.

You can select the spellchecking language by right-clicking on the main
text area (in edit mode) and choosing it from the submenu "Languages".

=== Adding custom dictionaries under Windows ===

You can add more aspell dictionary files to the directory <RedNotebook
Dir>\\lib\\aspell-0.60\\. If RedNotebook is running, you need to restart
it for new dictionaries to be recognized. You can find aspell
dictionaries at ftp://ftp.gnu.org/gnu/aspell/dict/0index.html. Please
read the README files included in the tarballs for information on how to
compile the necessary files.


== Options ==

Make sure you check out the customizable options in the preferences
dialog. You can open this dialog by clicking on the entry in the "Edit"
menu.


== Save ==

%(save1)s %(save2)s %(save3)s


== Export ==

%(save4)s %(save5)s

Since version 0.9.2 you can also directly export your journal to PDF.
If the option does not show up in the export assistant, you need to
install pywebkitgtk version 1.1.5 or later (the package is sometimes
called ``python-webkit``).

**Latex caveats**

Make sure to type all links with the full path including the protocol:

- http://www.wikipedia.org or http://wikipedia.org
  (--wikipedia.org--, --\"""www.wikipedia.org\"""--)
- file:///home/sam/myfile.txt (--/home/sam/myfile.txt--)


== Synchronize across multiple computers ==[sync]

Syncing RedNotebook with a remote server is easy. You can either use a
cloud service like Dropbox or save your journal to your own server.

=== Dropbox ===

If you have a [Dropbox https://www.dropbox.com] account, you can just
save your journal in a subdirectory of the Dropbox folder in your home
directory. Alternatives to Dropbox, which give you complete control over
your where your data is stored, include
[Syncthing https://syncthing.net].

=== Directly save to remote FTP or SSH server ===

With Linux you can have your journal directory on a remote server. To
use the feature you have to connect your computer to the remote server.
This is most easily done in Nautilus by clicking on "File" -> "Connect
to Server". Be sure to add a bookmark for the server. This way you can
see your server in Nautilus at all times on the left side. The next
time you open RedNotebook you will find your server in the "New",
"Open" and "Save As" dialogs. There you can select a new folder on the
server for your journal.

=== External sync with remote server ===

If you have your own server, you might want to try
[Conduit http://www.conduit-project.org] or
[Unison http://www.cis.upenn.edu/~bcpierce/unison]. To sync or backup
your journal you have to sync your journal folder (default is
"$HOME/.rednotebook/data/") with a folder on your server.

Obviously you have to be connected to the internet to use that feature.
Be sure to backup your data regularly if you plan to save your content
remotely. There are always more pitfalls when an internet connection is
involved.

=== Dual boot ===

Using RedNotebook from multiple operating systems on the same computer
is also possible. Save your journal with "Journal->Save As" in a
directory all systems can access. Then on the other systems you can
open the journal with "Journal->Open".

Optionally, you can also **share your settings** and templates. The
relevant setting is found in the file "rednotebook/files/default.cfg".
There you can set the value of ``userDir`` to the path where you want
to share your settings between the systems.


== Portable mode ==

RedNotebook can be run in portable mode. In this mode, the template
directory, the configuration and the log file are saved in the
application directory instead of in the home directory. Additionally,
the path to the last opened journal is remembered relatively to the
application directory.

To use RedNotebook on a flash drive on Windows, run the installer and
select a directory on your USB drive as the installation directory.
You probably don't need the "Start Menu Group" and Desktop icons in
portable mode.

To **activate portable mode**, change into the files/ directory and in
the default.cfg file set portable=1.


== Network drive ==

Unfortunately, you cannot add links to files on network shares directly
with the file selection dialog (this is due to a bug in GTK 2, it is
fixed in GTK 3, but RedNotebook still uses GTK 2 [bug on launchpad
""https://bugs.launchpad.net/ubuntu/+source/gtk+2.0/+bug/304345""]).
However, it is possible to enter links directly, for example ``[U:
""file:///U:/""]`` to reference the mapped drive letter [U
""file:///U:/""].


== Convert Latex output to PDF ==

In recent RedNotebook versions you can export your journal directly to
PDF, so this section may be obsolete. However, some people may prefer
to export their journal to Latex first and convert it to PDF later.
Here is how you do it:

=== Linux ===

For the conversion on Linux you need some extra packages:
texlive-latex-base and texlive-latex-recommended. Maybe you also need
texlive-latex-extra. Those contain the pdflatex program and are
available in the repositories of most Linux distros.

You can convert the .tex file to PDF by using the following commands:

```
pdflatex your-rednotebook-export.tex
makeindex your-rednotebook-export
pdflatex your-rednotebook-export.tex
```

If you omit the last two commands, your PDF won't have an index of tags.

If you run into any problems during the conversion, the easiest way to
solve them is to install a latex editor (e.g. [Kile
http://kile.sourceforge.net]) and do the conversion with it. That way
you can see the errors right away and get rid of them by editing the
file.

=== Windows ===

You can open an exported Latex file with Texniccenter and convert it to
PDF with MikTex. Visit www.texniccenter.org and www.miktex.org for the
programs and instructions. Basically, you have to download both
programs, open the .tex file with Texniccenter and select "Build
Output" from the "Output" menu. The program will then create the PDF in
the same directory.


== Keyboard shortcuts ==

|| General              |                        |
| Show help             | <Ctrl> + H             |
| Find                  | <Ctrl> + F             |
| Export                | <Ctrl> + E             |
| Spellcheck            | F7                     |
| Fullscreen            | F11                    |
|| Navigation           |                        |
| Go back one day       | <Ctrl> + PageUp        |
| Go forward one day    | <Ctrl> + PageDown      |
| Go to today           | <Alt> + Home (Pos1)    |
|| Insert               |                        |
| Insert link           | <Ctrl> + L             |
| Insert date/time      | <Ctrl> + D             |
|| Format               |                        |
| Bold                  | <Ctrl> + B             |
| Italic                | <Ctrl> + I             |
| Monospace             | <Ctrl> + M             |
| Underline             | <Ctrl> + I             |
| Strikethrough         | <Ctrl> + K             |
| Remove format         | <Ctrl> + R             |

You can find more shortcuts in the menus in the main menu bar.


== Encryption ==

You can use e.g. [TrueCrypt http://www.truecrypt.org] to encrypt your
journal. The general idea is to create and mount an encrypted folder
with TrueCrypt and put your journal files in there.

In many Linux distributions it has become pretty easy to encrypt your
entire home partition. I would recommend to do that to anyone who
wishes to protect her/his diary and all other personal files. This
method is especially useful for laptop users, because their computers
are more likely to be stolen. If you encrypt your home partition all
RedNotebook data will be encrypted, too.


== Appearance on Windows ==

You can use a GTK3 compatible theme to change the appearance of your
RedNotebook installation. Once you find a GTK3 compatible theme, copy
the theme into ``<RedNotebook Dir>\\share\\themes``, e.g.,
``C:\\Program Files (x86)\\RedNotebook\\share\\themes`` and then edit
``C:\\Program Files (x86)\\RedNotebook\\etc\\gtk-3.0\\settings.ini`` to
comment out the current theme setting and add your own.

For example, for using the [FlatStudio https://www.gnome-look.org/p/1013733/]
theme, download the ``*.tar.gz``
file and extract it. Out of the four themes -- FlatStudio,
FlatStudioDark, FlatStudioLight, FlatStudioGray -- pick one of the
folders (e.g., FlatStudioDark) and copy it into
``<RedNotebook Dir>\\share\\themes``. Then edit
``etc\\gtk-3.0\\settings.ini`` so it looks similar to this:

```
[Settings]
# gtk-theme-name=win32
gtk-theme-name=FlatStudioDark
```

Finally, relaunch RedNotebook.


== Tips ==
%(multiple_entries_text)s

=== Week numbers ===

If you'd like to see the week numbers in the calendar, you can set the
value of weekNumbers to 1 in the configuration file. This file normally
resides at $HOME/.rednotebook/configuration.cfg.

=== Language ===

If you want to change RedNotebook's language, setting the environment
variable LANG (Linux) or LANGUAGE (Windows) to a different language
code should be sufficient. Language codes have e.g. the format "de_DE"
or "de_DE.UTF-8" (German). To set the language to English you can also
set the code to "C". Before you change the language make sure you have
the required language packs installed. Otherwise an error will be
shown.

On **Linux**, start a terminal and call ``LANG=de_DE.utf8``. Then in the
same terminal, run ``rednotebook``. The language change will be gone
however once you close the terminal.

On **Windows**, set or create a LANGUAGE environment variable with the
desired code:

+ Right-click My Computer and click Properties.
+ In the System Properties window, click on the Advanced tab
  (Windows XP) or go to Advanced System Settings (Windows 7).
+ In the Advanced section, click the Environment Variables button.
+ Click the New button and insert LANGUAGE at the top and e.g. de or
  de_DE or de_DE.UTF-8 (use your [language code
  ""http://en.wikipedia.org/wiki/ISO_639-1""]).


=== Titles ===

You can insert titles into your post by adding "="s around your title
text. = My Title = is the biggest heading, ===== My Title ===== is
the smallest heading. A title line can only contain the title, nothing
else.

Numbered titles can be created by using "+" instead of "=". ""+ My
Title +"" produces a title like "1.", +++++ My Title +++++ produces a
title like 0.0.0.0.1

=== Insert HTML or Latex code ===

To insert custom code into your entries surround the code with single
quotes. Use 2 single quotes for inline insertions and 3 single quotes
if you want to insert a whole paragraph. For paragraphs be sure to put
the single quotes on their own line.

||   Text                  |   Output                              |
| ``''<font color="red">Red</font>''`` | ''<font color="red">Red</font>'' |
| ``''$a^2$''``            | ''$a^2$'' (''a<sup>2</sup>'' in Latex) |

This feature can be used to insert e.g. Latex formulas:

```
'''
$$\\sum_{i=1}^{n} i =\frac{ncdot (n+1)}{2}$$
'''
```

will produce a nice looking formula in the Latex export.

=== Verbatim text (Preserve format) ===

To insert preformatted text preserving newlines and spaces, you can
use the backquotes (`). Use 2 backquotes for inline insertions and 3
backquotes if you want to insert a whole paragraph.
For paragraphs be sure to put the backquotes on their own line.

Two examples (have a look at the [source source.txt] to see how it's
done):

To install rednotebook use ``sudo apt-get install rednotebook``.

```
class Robot:
    def greet(self):
        print 'Hello World'

robot = Robot()
robot.greet()
```

=== Unparsed text ===

Formatting commands inside two pairs of "" are not interpreted (""**not
bold**"").

=== Comments ===

Comments can be inserted after percent signs (**%%**). They will not be
shown in the preview and the exports. The %% has to be the first
character on the line.

=== List of all entries ===

To get a list of your entries search for "-". You can sort the
resulting list chronologically by pressing the "Date" button.


== Command line options ==

```
%(commandline_help)s
```


== Data format ==

The content of a RedNotebook journal is saved in a directory with many
files, not just one file. The directory name is used as a name for the
journal.

In the directory there are several files all conforming to the naming
scheme <year>-<month>.txt (e.g. 2010-05.txt). Obviously these files
correspond to months (e.g. May 2010).

Each month file contains plain text for the days of that month.
The text is actually [YAML www.yaml.org] markup. Without the
(unnecessary) python directives the files look like this:

```
24: {text: "This is a normal text entry."}
25:
  Ideas: {"Invent Anti-Hangover machine": null}
  text: "This is another text entry, shown in the main text area."
```

As you can see, the data format uses a dictionary (hashmap) for storing
the information. The outer dictionary has the day numbers as keys and
the day content as values. The day values consist of another
dictionary. It can have a key "text" whose value will be inserted in
the main content area. Additionally there can be multiple other keys
that stand for the categories that belong to that day. Each category
contains a dictionary mapping category entries to the null value.

In summary the data format is a hierarchy of dictionaries. This way the
format can be easily extended if the need for that arises.

All textual content can be formatted with http://txt2tags.org markup.


== Questions ==

If you have any questions or comments, feel free to post them on the
mailing list or contact me directly.


== Bugs ==

There is no software without bugs, so if you encounter one please drop
me a note. This way RedNotebook can get better, not only for you, but
for all users.

Bug reports should go [here https://bugs.launchpad.net/rednotebook],
but if you don't know how to use that site, a simple mail is equally
fine.

"""
    % globals()
)
