====== RedNotebook ======

===== REQUIREMENTS =====
  - Python (2.5) (www.python.org)
  - PyYaml (3.05) (www.yaml.org)
  - PyGTK (2.13) (www.pygtk.org)
  - python-gtkhtml2 (2.19.1)
  - python-gtkmozembed (in package python-gnome2-extras)
  
    === Ubuntu ===
    On Ubuntu you type 'sudo apt-get install python-yaml python-gtk2 python-gtkhtml2 python-gnome2-extras'

    === Fedora ===
    yum -y install python-devel PyYAML gnome-python2-gtkmozembed 


===== INSTALL =====

as root run 'python setup.py install'
(install into path-to-python/site-packages/)

or run 'python setup.py install --root=testDir'
(install into current-directory/testDir/path-to-python/site-packages/)


===== RUN =====

If you installed the program into "site-packages" you can now run the command "rednotebook"
in any shell.

Otherwise navigate to the "rednotebook" directory and run "python redNotebook.py".


===== THANKS =====
  - The authors of the programs listed under 'requirements'. Remember that
           without them, RedNotebook would not be possible
  - Everaldo Coelho (www.everaldo.com) for the excellent icon
  - The txt2tags team (http://txt2tags.sf.net) for their super cool markup-tool
  - Gustavo J. A. M. Carneiro for his htmltextview.py module



Enjoy!
