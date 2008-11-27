from rednotebook.util import filesystem

version = '0.3.0'
author = 'Jendrik Seipp'
authorMail = 'jendrikseipp@web.de'
url = "http://rednotebook.sourceforge.net"
developers = [author]

welcomeText = """\
Hello, 
this is the RedNotebook, a simple diary. This program helps you to keep track of your activities and thoughts. \
Thank you very much for giving it a try.
The text field in which you are reading this text, is the container for your normal diary entries like this one: 

Today I went to a pet shop and bought a tiger. Then we went to the park and had a nice time playing \
ultimate frisbee. Afterwards we watched the Flying Circus.

The usual stuff.
On the right there is space for extra content, things that can easily be sorted into categories. Those entries \
are shown in a tree. For example you could add the category Ideas and then add an entry which reminds you of \
what your idea was about:

> Ideas
  Found a way to end all wars. (More on that tomorrow.)
  
In addition you could add

> Cool Stuff
  Went to see the pope
  
for the really cool things you did that day. On the right panel you control everything with right-clicks. Click either \
on the white space or on existing categories.

Since Version 0.3.0 RedNotebook supports a template system: In the directory """ \
        + filesystem.templateDir + """ you find seven text files. One for each day of the week. You can edit those files \
with your favourite text editor and the text will appear whenever you navigate to an empty day in RedNotebook.
    
Everything you enter will be saved automatically when you exit the program. If you want to double check you can save \
pressing "Strg-S" or using the menu entry under "File" in the top left corner. "Backup" saves all your entered data in a \
zip file. After pressing the button you can select a location for that.

There are many features I have planned to add in the future so stay tuned.
I hope you enjoy the program!
            """
            
welcomeHelpText = '''\
Hello, 
this is the RedNotebook, a simple diary. This program helps you to keep track of your activities and thoughts. \
Thank you very much for giving it a try.
'''

dayEntryHelpText1 = '''\
The text field in the middle is the container for your normal diary entries like this one: 

'''

dayEntryHelpText2 = '''\
Today I went to a pet shop and bought a tiger. 
Then we went to the park and had a nice time playing ultimate frisbee. 
Afterwards we watched the Flying Circus.'''

dayEntryHelpText = dayEntryHelpText1 + dayEntryHelpText2

categoriesHelpText1 = '''\
On the right there is space for extra content, things that can easily be sorted into categories. \
Those entries are shown in a tree. For example you could add the category Ideas and then add an \
entry which reminds you of what your idea was about:'''

categoriesHelpText2 = '''\
> Ideas
  Found a way to end all wars. (More on that tomorrow.)
  
In addition you could add

> Cool Stuff
  Went to see the pope'''

categoriesHelpText3 = '''
for the really cool things you did that day. On the right panel you control everything with right-clicks. Click either \
on the white space or on existing categories.'''

categoriesHelpText = categoriesHelpText1 + '\n\n' + categoriesHelpText2 + '\n' + categoriesHelpText3

templateHelpText = '''\
RedNotebook supports a template system: In the directory "''' \
        + filesystem.templateDir + '''" you find seven text files. One for each day of the week. You can edit those files \
with your favourite text editor and the text for a given weekday will be inserted when you press the button \
"Insert Template".'''

automaticSavingHelpText = '''\
Everything you enter will be saved automatically when you exit the program. If you want to double check you can save \
pressing "Strg-S" or using the menu entry under "File" in the top left corner. "Backup" saves all your entered data in a \
zip file. After pressing the button you can select a location for that.'''

goodbyeHelpText = '''\
Now you can erase this help text and enter what you have done today. To read the instructions again, press "F1" or \
go to "Help -> Show Help" in the menu bar.

There are many features I have planned to add in the future so stay tuned.
I hope you enjoy the program!'''

completeWelcomeText = welcomeHelpText + '\n' + dayEntryHelpText + '\n\n' + categoriesHelpText + '\n\n' + templateHelpText + \
                        '\n\n' + automaticSavingHelpText + '\n\n' + goodbyeHelpText

htmlHelp = '''\
<html>

<body bgcolor="#ababab">
<h4>Table of Contents</h4>

<ul>
<li><a href="#dayEntries">Day Entries</a></li>
<li><a href="#categories">Category Entries</a></li>
<li><a href="#templates">Templates</a></li>
<li><a href="#saving">Automatic Saving</a></li>
</ul>

<p>
<a name="dayEntries">
<h6>Day Entries</h6>''' + dayEntryHelpText1 + '''<pre>''' + dayEntryHelpText2 + '''</pre>''' + '''\
</a>
</p>

<p>
<a name="categories">
<h6>Category Entries</h6>''' + categoriesHelpText1 + \
'''<pre>''' + categoriesHelpText2 + '''</pre>'''+ categoriesHelpText3 + '''\
</a>
</p>

<p>
<a name="templates">
<h6>Templates</h6>''' + templateHelpText + '''\
</a>
</p>

<p>
<a name="saving">
<h6>Automatic Saving</h6>''' + automaticSavingHelpText + '''\
</a>
</p>

</body>
</html>
'''