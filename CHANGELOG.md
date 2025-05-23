# 2.39 (2025-03-25)
* Support GIRepository 3.0 (#817, #818, Jendrik Seipp).

# 2.38 (2025-02-23)
* Fix: include right-pane tags without subentries in search results (#794, @jendrikseipp).
* Upgrade to txt2tags 3.9 (@jendrikseipp).

# 2.37 (2024-12-18)
* Improve bidirectional text support in preview mode (#781, @metemaddar).

# 2.36 (2024-11-24)
* When searching for hashtags, show remainder of line after hashtag in search results (@jendrikseipp).
* When searching for a hashtag, scroll to hashtag and highlight it (@jendrikseipp).
* Add simple way for showing all entries: allow searching for whitespace (which should be part of all days) (@jendrikseipp).

# 2.35 (2024-09-22)
* Add option to auto-indent text in editor and activate it by default (#561, #562, Allen Benter, Varunjay Varma).

# 2.34 (2024-09-16)
* Copy/paste text into the correct text field (#677, @jendrikseipp).

# 2.33 (2024-05-05)
* Ignore image filenames and web links in word clouds (#537, #696, @laraconda).
* Add more pre-commit checks (#705, @laraconda).

# 2.32 (2024-02-17)
* Allow copying text in preview mode (#732, Jendrik Seipp).
* Allow hashtags that start with (but are longer than) hex colors and preprocessor directives (#738, Jendrik Seipp).
* Highlight hashtags and formatting within lists (#744, Jendrik Seipp).
* Improve Debian packaging (Phil Wyett).
* Test macOS 12 and 13 instead of 11 and 12 (Jendrik Seipp).

# 2.31 (2023-09-02)
* Add basic text replace functionality (#715, @curioussushiroll).

# 2.30 (2023-08-10)
* Modernize code (#689, @HighnessAtharva and @laraconda).
* Fix: Correctly color URLs with hashtags symbols in edit mode (#703, @laraconda).
* Add menu item to insert numbered lists (#526, @curioussushiroll).

# 2.29.6 (2023-04-28)
* Restore all keyboard shorts (#690, Jendrik Seipp).

# 2.29.5 (2023-04-13)
* Fix: Don't try to print WebKit2 version on Windows (#686, Jendrik Seipp).

# 2.29.4 (2023-04-11)
* Accept arbitrary WebKit2 version. Use 4.1 if available (#681, Jendrik Seipp).

# 2.29.3 (2023-01-16)
* Make all menu items translatable (Jendrik Seipp).
* Packaging: install translation files under <prefix>/share/locale again (#666, Jendrik Seipp).

# 2.29.2 (2023-01-13)
* Fix `setup.py` script: only build translation files when needed (Jendrik Seipp).
* Add continuous integration check to ensure that the basic Debian package builds correctly (Jendrik Seipp).

# 2.29.1 (2023-01-12)
* Remove bundled msgfmt.py module and use msgfmt binary from gettext suite instead. This fixes most of the translations on Windows (Jendrik Seipp).

# 2.29 (2022-12-31)
* Document alternatives for changing the GTK theme on Windows (Ankur A Sharma, #494).
* Fix en_GB translations (Jendrik Seipp, #659).

# 2.28.1 (2022-12-28)
* Require `setuptools` for Debian package (Jendrik Seipp).

# 2.28 (2022-12-28)
* Remove code that uses the deprecated `distutils` module (Jendrik Seipp, #655, #656).
* Fix checking for newer versions (Jendrik Seipp).
* Gracefully handle unsupported locale settings (Jendrik Seipp, #613).

# 2.27.2 (2022-12-01)
* Fix passing command line arguments (Jendrik Seipp).
* Update translation files (Jendrik Seipp).

# 2.27.1 (2022-11-18)
* Fix application ID for Flatpak (#650, Jendrik Seipp).

# 2.27 (2022-11-16)
* Upgrade to GTK 3.24 on Windows (Jendrik Seipp).
* Use external preview on Windows since embedding the preview is impossible with newer GTK versions (Jendrik Seipp).
* Use GtkApplication class and only allow running one RedNotebook instance at a time (Jendrik Seipp).
* Add support for GtkSourceView 4 (Jendrik Seipp).
* Raise minimum Python version to 3.6 (Jendrik Seipp).
* Add more languages to Windows installer (Jendrik Seipp).

# 2.26 (2022-09-28)
* Fix issue #632 by skipping obsolete Python function (Jendrik Seipp).
* Fix: only try to load CEF Python on Windows (Jendrik Seipp).
* Update Turkish translation (sabriunal).

# 2.25 (2022-05-16)
* Use icon names instead of GTK stock icons to support newer GTK versions (Jendrik Seipp).
* Handle several GTK deprecation warnings (Jendrik Seipp).

# 2.24 (2022-02-21)
* Revert to plain naming scheme for data files since reverse DNS naming causes problems (#611, Phil Wyett).

# 2.23 (2022-02-13)
* Check that a newly written month file is valid before deleting the old month file.
* Rename "autostart" file. Please re-enable autostart option in preferences if you want RedNotebook to run on system startup.
* Fix Python crash on program start (#583, Max Krummenacher).
* Prevent save failures on network and cloud drives (#593, Robert Little).
* Add script for importing entries (#571, Cary Gravel).
* Revamp packaging for Debian (#599, #600, Phil Wyett).
* Fix continuous integration tests.

# 2.22 (2021-04-25)
* Add a "Give Feedback" button (#551, Rahul Jha).
* Test code on macOS (#552, Rahul Jha).

# 2.21 (2020-12-07)
* Update MathJax to version 3 (#515, @dgcampea).
* Fix date references in CEF-based HtmlView (#544, Paweł Żukowski).

# 2.20 (2020-08-03)
* Fix drag and drop (#492, @dgcampea).
* Fix external previews (Eric Chazan).
* Document how to change the theme on Windows (#487, Ankur A. Sharma).
* Allow symlinking to `./run` script (#509).

# 2.19 (2020-05-04)
* Reload GTK theme colors when saving the journal (#485).
* Don't use dark mode for exported HTML files (#486).
* Use PNG version instead of SVG for RedNotebook icons to avoid problems on macOS.
* Use GitHub actions for continuous integration testing.

# 2.18 (2020-02-29)
* Use background and foreground colors from GTK theme for HTML preview.

# 2.17 (2020-02-23)
* Fix HTML colors for dark themes (#474).

# 2.16 (2020-01-23)
* Add menu items for adding titles (#464, Paweł Żukowski).
* Upgrade msgfmt.py to version 1.2 (#470).

# 2.15 (2019-12-04)
* Fix tray icon on Windows (#394).

# 2.14 (2019-11-17)
* Support entry reference links in exported HTML (#452, Paweł Żukowski).
* Add support for dark themes to cloud panel (#438).

# 2.13 (2019-11-07)
* Change unnamed date references from 2019-11-06 to [2019-11-06] (#458, #460, Paweł Żukowski).
* Add option for controlling number of displayed tags (#456, Paweł Żukowski).
* Fix setting maximum number of displayed tags (#461).

# 2.12 (2019-11-02)
* Allow linking between days with dates like 2019-02-14 and `[named links 2019-02-14]` (#176, #444, Paweł Żukowski).
* Allow opening statistics dialog multiple times in one session (#370, #457, Paweł Żukowski).
* Warn about outdated backups every week by default.
* Increase default width of left panel to ensure that the calendar is fully visible (#376).

# 2.11.1 (2019-04-07)
* Always initialize spell checking whenever we switch text buffers (fixes #435).

# 2.11 (2019-03-26)
* Revert to GTK 3.18 stack on Windows (fixes #429 and #430).

# 2.10 (2019-03-24)
* Automatically push newest version to flathub.

# 2.9.1 (2019-03-20)
* Disable internal preview on Windows again since it sometimes crashes the app.

# 2.9 (2019-03-17)
* Use Python 3.6 and GTK 3.22 on Windows.
* Build Windows installer with Appveyor.

# 2.8.1 (2019-03-17)
* Load the correct template for a given weekday (fixes #416).
* Clear text buffers when opening a new journal (fixes #421).
* Minor bug fixes.

# 2.8 (2018-11-15)
* Support internal previews on Windows again (#369).

# 2.7.1 (2018-11-13)
* Never let search phrases end up in the main text field (fixes #401).
* Fix spell checking (fixes #412).

# 2.7 (2018-11-06)
* Use GtkSourceView for editor to obtain better undo/redo functionality (thanks @takluyver).
* When saving, update the list of tags in the auto-complete list for the search.
* Fix opening RedNotebook homepage from About dialog (#411).

# 2.6.1 (2018-08-21)
* Fix bug preventing new installations from starting up.

# 2.6 (2018-08-20)
* Move date format option to preferences dialog.
* Use date format option for date in titlebar.
* Remember selected date format for exports between sessions.
* Check remote info.py file for latest version number.
* Check for latest version in separate thread.

# 2.5 (2018-06-08)
* Restore instant search (search as you type).
* Add option for disabling instant search to preferences dialog.
* Disable undo/redo buttons in preview mode (fixes #103).
* Remove option to show/hide right-side tags panel from GUI (still present in configuration file).

# 2.4 (2018-03-07)
* Make search significantly faster by indexing all days.
* Allow searching for multiple words.
* Add AppVersion to InnoSetup file.
* Homepage: Switch to HTTPS.

# 2.3 (2017-09-25)
* Compress backups.
* Use newer txt2tags version 2.6 and reapply changes to obtain a GPL-2+ version.
* Remove brittle PDF export. Please export to HTML and print to PDF with browser instead.
* Remove intro page from export wizard.
* Fix: image files were not found on Windows and Mac OS.
* Print peak memory usage on Linux when program exits.
* Hide tags panel completely by default instead of only minimizing it.
* Update Debian files (@kathenas).

# 2.2 (2017-09-08)
* Port RedNotebook 2 to Windows.
* Windows: uninstall old version before installing new version to remove old files.
* Windows: use Aspell for spell checking.
* Update Debian files (@kathenas).

# 2.1.5 (2017-08-09)
* Fix debian/control.

# 2.1.4 (2017-08-08)
* Use old names for appdata and desktop files.

# 2.1.3 (2017-08-06)
* Fix creating translation files.

# 2.1.2 (2017-08-03)
* Fix "Exec" field in .desktop file.

# 2.1.1 (2017-08-02)
* Reset package name to 'rednotebook'.

# 2.1 (2017-07-29)
* Make webkit optional (but highly recommended). If missing, show preview in external browser.
* Support inserting SVG images.
* Don't switch between edit and review mode automatically by default.

# 2.0 (2017-05-19)
* Port to Python 3 and GTK 3.
* Add index of tags to LaTeX export (#324, thanks Alex Schickedanz).
* Use new CDN link for MathJax.

# 1.15 (2017-02-11)
* Bundle pygtkspellcheck 4.0.5 since earlier versions contain a bug (lp:1615629).
* Fix toggling autostart (lp:1628497).
* Set system tray icon name (lp:1660129).

# 1.14 (2016-09-26)
* Use new pygtkspellcheck API (lp:1592727).
* Fix conversion from old single "Tags" category to new tags format.

# 1.13 (2016-06-17)
* When selecting a journal directory, show all journal directories by default (thanks Paul Jackson).
* Allow ampersands in e-mail addresses (lp:1570476, thanks pdofak).
* python-gtkspell has been renamed to python-gtkspellcheck. Update docs and debian/control accordingly.

# 1.12 (2016-03-28)
* Add option to hide right-hand tags pane (thanks Ron Brown, Jr.).
* Never overwrite externally changed month files (thanks Felix Zörgiebel).
* Remove support for Python 2.6.

# 1.11 (2015-11-08)
* Remind users to make new backup if last backup is older than a month.
* When inserting a link for a selected text passage, replace text passage.

# 1.10.4 (2015-10-19)
* Fix right-clicking cloud words to hide them.

# 1.10.3 (2015-10-15)
* Make #hashtags regular expression faster (up to 1000x).

# 1.10.2 (2015-08-24)
* Fix Chinese fonts in preview mode on Windows by using the fonts mingliu and MS Mincho (thanks Amos Ng).
* Fix instructions for running RedNotebook on Windows (thanks Amos Ng).
* Move repository from launchpad to github.

# 1.10.1 (2015-04-14)
* When undoing a formatting action, only remove formatting, not the text (lp:1326606).
* Fix searching with enter for text with non-ASCII characters (lp:1430697).
* Fix filtering exports by tags containing non-ASCII characters (lp:1267263).
* Don't remove whitespace from old-style tags in autocomplete box (lp:1414603).
* Don't try to change spellchecking language if spellchecker is not set up (lp:1443818).
* Don't try to access files with wrong encoding (lp:1443818).

# 1.10 (2015-04-12)
* Write data to temporary files first to prevent corrupted month files.
* Add format button for monospace font. Automatically add the correct format for code blocks.
* Show warning for dates before 1900 (not supported by Python's datetime module).
* Fix undo/redo.
* Don't add unneeded newlines around titles and code.

# 1.9.0 (2014-12-27)
* Add #tags to cloud ignore list to remove them from the tag cloud (thanks Przemysław Buczkowski).
* Remove option to start RedNotebook minimized.
* Do not remove menu bar in fullscreen mode (lp:1400356).
* Allow exiting fullscreen mode with ESC key.
* Only allow comment signs (#) at the beginning of a line in the config file.
* Fix reading configuration files.

# 1.8.1 (2014-08-03)
* Do not show new version dialog if latest version cannot be determined (lp:1324126).
* Fix date formatting for invalid locale encodings.
* Add necessary library files for spell-checking on Windows (lp:1331876).

# 1.8.0 (2013-12-12)
* Add font selection for edit mode (Philip Akesson).
* Allow changing preview and cloud font in preferences.
* Only allow opening RedNotebook minimized on Windows since other systems may lack a system tray.
* Fix: Display tags starting with "SEP" in preview (lp:1255582).
* Write scripts to cross-compile RedNotebook Windows exe and installer on Linux.

# 1.7.3 (2013-11-10)
* Jump to a specific date on startup with "--date 2013-10-31" on the commandline (Rob Norris).
* Display current date in the title bar (Rob Norris).
* Support inserting multiple pictures in one step.
* Add DejaVu Sans as font fallback for clouds and preview.
* Fix setting last image directory for insert dialog.
* Only allow exporting selected text if we are in edit mode (lp:1221792).

# 1.7.2 (2013-06-28)
* Show error if saving fails due to a directory not being created.
* Ignore hashtags starting with more than one #.
* Fix: Allow inserting files and pictures from the "recently used" section (lp:1195759).

# 1.7.1 (2013-03-01)
* Fix: Insert spellchecking correction in the correct position (LP:1137925).

# 1.7.0 (2013-02-28)
* Allow filtering exported days by tags (Alistair Marshall).
* Add option to export only the currently selected text (Alistair Marshall).
* Move spellcheck option from preferences to edit menu and add F7 shortcut (Alistair Marshall).
* Enable spellchecking on Windows. See help for adding custom dictionaries.
* Better error message for invalid markup.
* Show warning if no directory is selected before clicking the "Open" button when choosing a journal directory.
* Gracefully handle BadStatusLines when checking for new versions.
* Do not try to set file permissions on Windows where they are unavailable.
* Fix hide-from-cloud for words containing backslashes (LP:1131412).
* Fix relative file links on Windows.
* Code: Switch from optparse to argparse (Alistair Marshall).

# 1.6.6 (2013-01-21)
* Edit templates in RedNotebook directly. Preview and use the Insert and Format toolbar menus before inserting a template.
* Support relative image links like [""my_pic"".jpg].
* Add Ctrl+Return shortcut for adding manual linebreaks.
* Let all toolbar menus always open the menu before performing an action.
* Change Go-To-Today shortcut to Alt+Home (Ctrl+Home moves cursor to the start of the text).
* Do not allow choosing an empty name for templates.
* Do not parse #include as a hashtag.
* Add info about network drives to help text.
* Fix help text about links to local directories.
* Fix: Let categories pane use new infobar notifications (LP:1098625).

# 1.6.5 (2012-12-27)
* Add menu item for clearing the text format.
* Add toolbar menus "Insert" and "Format" to main menu for better accessibility and HUD integration.
* Only show keyboard shortcuts in main menu, not in toolbar menus.
* Use selected text as link name when a new link is inserted.
* When an image or file is inserted, use selected text as the name of the link.
* Format selected text as header when a header is inserted.
* Convert selected text to a list when a list is inserted.
* Select title after it has been inserted to allow for easy editing.
* Change file permissions so that journal files are only readable by the user.
* Windows: Restore slider positions after opening RedNotebook from the tray.
* Windows: Support non-ascii installation paths.

# 1.6.4 (2012-12-22)
* Never include previous RedNotebook backups in new backups.
* Add strikethrough shortcut Ctrl+K.
* By default don't switch between edit and preview mode automatically.
* Add experimental support for irc protocol.

# 1.6.3 (2012-12-06)
* Fix: Don't interpret URLs with non-empty paths as local links.

# 1.6.2 (2012-11-18)
* Add option for automatically switching between edit and preview mode to preferences.
* Since debian doesn't have a python2 symlink, try to run python2.7 and python2.6 in the run script.
* Use PNG image in about dialog (SVG support is broken in Windows version).

# 1.6.1 (2012-11-11)
* Allow specifying the width when inserting an image.
* Add relative links: Relative paths [myfile image.jpg] is automatically transformed to /path/to/journal/image.jpg.
* Use smarter regular expression for finding hashtags in the text.
* Give focus to link box when the link dialog opens.
* Hide tag panel by default.
* Adapt introductory and help texts for hashtags.
* Break search results at newlines.
* Fix: When searching for multiple tags, only add a single result for every hit.

# 1.6.0 (2012-10-31)
* Inline #hashtagging: Directly add hashtags like #Movies, #my_project in the main text.
* Highlight #hashtags in red.
* Include # for tags in tag cloud to be consistent with the hashtags.
* Change to edit/preview mode if text is missing/present automatically.
* Change to edit mode when double-clicked into preview.
* Detach model from combobox when updating the tags to make inserting a new tag faster.
* Fix searching for dates.
* Fix inserting and editing templates with unicode names.
* Fix opening and creating journals (lp:1068655).
* Use apport (If a crash occurs on Linux, an automatic bug report is prepared, but not submitted).
* Do not allow using $HOME as a journal directory.
* Do not let error notifications blink.
* For Journal->New and Journal->Save-As: Only allow using empty directories.
* For Journal->Open: Only allow using directories with at least one month file.
* Use InfoBars for nicer inline notifications about errors.
* Enable finishing link dialog with hitting ENTER.
* Disable insert (Ctrl+V) and cut (Ctrl+X) shortcuts in preview mode.
* Add more shortcuts in Journal menu: Export (Ctrl+E), Backup and Statistics (Alt+letter).
* Update translations.

# 1.5.0 (12-07-19)
* Use new logo redesigned by Ciaran.
* Remember possible undo/redo actions for each day separately.
* Turn all entries of old "Tags" categories into tags without entries at startup.
* Suggest last tag when a new tag is added.
* When suggesting to use the last tag, leave focus on the tag.
* Enable copy menu item in preview mode (LP:834473).
* Grey out cut and paste menu items in preview mode.
* Only allow hiding words from the cloud, not the tags.
* Add shortcut (Ctrl+Home) for "Go to Today"
* Fix undo for tags.
* Fix: Remove special characters in template names before displaying them.
* Exports: Make tag lists scrollable and sort the available tags alphabetically.
* Install .mo files (translations) in the standard directories under Linux.
* Drop support for Python 2.5. This means that we now support Python 2.6 and 2.7.
* Windows: Update libraries in installer to gtk+ 2.24 and python 2.7.
* Windows: Correctly show italics in preview.
* OSX: Make the _() function available even if gettext is not working.
* Update translations.

# 1.4.0 (12-04-01)
* Search: If a search contains a hashtag (e.g. #Work or #Movies), only days
  with all of those tags will be searched. This means you can e.g. search for
  "project-xyz" only in the days tagged with "Work" with the query
  "#Work project-xyz".
* Search for combinations of tags (e.g. #magazine #linux)
* Search: If the query only contains a single hashtag (e.g. #Movies), a list of
  all subtags (the names of the movies) is shown.
* Search: Automatically scroll to found text in edit mode
* Split tag and word clouds
* Show tag and word cloud only if there are any tags and words respectively
* Remove spaces from multi-word tags during search and in clouds
* Auto-complete tags in search
* Always include all tags regardless of their frequency in the cloud
* Exports: Correctly set the appropriate extension for each export type
* Exports: Always add a title for LaTeX exports
* Fix: Correctly parse configuration values containing ='s
* Fix: Paths returned from file and folder choosers must be converted to unicode
* Fix: Correctly redirect error output into the logfile on Windows

# 1.3.0 (12-01-24)
* Let tags be categories without entries. This greatly simplifies and in fact
  unifies tags and categories.
* Unify clouds and search -> Show the search bar above the clouds
  When a search is made, substitute the word cloud with the search results.
* Apply styling for thick horizontal lines
  - Thin line:  --------------------
  - Thick line: ====================
* Apply formatting only once if a format button is clicked multiple times
* Allow "Close to tray" only on Windows as most modern Linux distros don't have a tray anymore (lp:902228)
  If you still want the tray icon, set closeToTray=1 in the configuration file.
* Make journal saving more than twice as fast by using libyaml.
* Change Ctrl-PageUp(Down) directions to be more intuitive
* Update and revise help text
* Fix: utf-8 special chars not displayed correctly in html export for firefox (LP:910094)
* Fix: Do not abort if a wrong regex is entered
* Fix: Correctly highlight all picture formats in edit mode
* Fix: When the format button is clicked and a tag is selected, format it instead of the editor pane
* Write month only if changes are actually made (LP:871730)
* Call categories tags in more places
* Print PDF export path after export
* Do not warn if second instance is suspected (too many false-positives)
* Updated translations

# 1.2.0 (11-10-05)
* Let the "Back" and "Forward" button jump over empty days
* Allow wildcards (*,.,?) in cloud black/white lists ("altr." hides altro, altra, etc.)
* Add "Export currently visible day" option in export assistant
* By default select the time range from today to today in the export wizard (LP:834489)
* Show warning when second RedNotebook instance is started to prevent data loss (LP:771396)
* Add option to set the date format for exports. An empty field removes dates from exports.
* Remember scrollbar and cursor positions when changing between days and edit and preview mode
* Allow double backslashes (\\) in filenames (e.g. for UNC paths)
* Use Ubuntu font in editor, preview and cloud if it's available
* Remember last export and backup locations
* Show the most recent entries at the top of the search list by default
* Search in annotations as well
* Use auto-completion for all category entries
* Mention the name of the day in weekday templates
* Allow linebreaks (\\) only at the end of lines
* Do not write empty month files to disk
* Remove "Delete Entry" button (Use the context menu or the delete key instead)
* Add tooltips for category buttons
* Always keep categories sorted in search and annotations drop-down menus
* Allow markup for links in categories (--http://mypage.com--) (LP:782697)
* Escape regular expression syntax in searches (*, +, etc.)
* Use a better icon for Annotate (Edit)
* Add more markup examples to templates help text
* Fix: Txt2tags highlighting should not allow spaces between format markup and text
* Fix: Do not use str.capitalize() for fonts in txt2tags.py to support turkish locales (LP:841698)
* Fix on Windows: Correctly open local links with whitespace (LP:824420)
* Let "Get help online" point to RedNotebook's answers section at launchpad
* Code optimizations
  * Remove old cloud implementation
  * Remove external module htmltextview.py
  * Remove dead unicode code
  * Remove obsolete KeepNote source files
  * Remove unnecessary imports
* Updated translations

# 1.1.8 (11-08-08)
* Fix: Abort startup if yaml file cannot be read to avoid losing data
* Updated translations

# 1.1.7 (11-07-13)
* Fix: Chinese characters are not correctly rendered in preview (LP:731273)
* Fix: Screen position not correctly remembered when opened from system tray (LP:804792)
* Fix: Date is not inserted if default encoding can not be determined
* Fix: Windows executable has no icon on Windows 7
* Windows installer: Update to GTK+-2.16.6
* Code: Use smarter internationalization code from elib.intl
* Updated translations

# 1.1.6 (11-05-11)
* Fix date encoding (LP:775269)
* Some translations updated

# 1.1.5 (11-05-03)
* Remove "RedNotebook" title in exports
* Make templates translatable
* Fix: Inserted dates always shows the time 00:00h (LP:744624)
* Mention "--record installed-files" setup.py's option for remembering
  installed files in README

== 1.1.4 (11-03-26) ===
* Add "phone call" and "personal" templates
* Fix: Application crashes while resetting last position (LP:728466)
* Fix: Editing a category entry that contains a \\ removes the new line symbol (LP:719830)
* Fix: Introductory text is not translated
* Fix: Properly convert dates to unicode
* When a format (bold, etc.) is applied with no text selected, add whitespace,
  not descriptive text
* Add a tooltip for the edit button
* Improve introductory text
* Improve help text
* Do not refer to annotations as "nodes" but as "entries"
* Translate the word "Categories" in exports
* In statistics window use "Selected Day" instead of "Current Day"
* Cleanup GUI glade file
* Many translations updated

# 1.1.3 (11-03-02)
* Remember window position from last session
* Restore window position when returning from tray
* Let the sub-windows be displayed relative to the main screen
* After searching change to date with single click instead of double-click
* Add useWebkit flag in configuration file
  Can be set to 0 if webkit causes problems e.g. for Chinese fonts
* Fix: Special characters inflate cloud black-/whitelist
* Fix: Insertion of templates (LP:696205)
* Fix: Do not load backup files accidentally (LP:705260)
* Fix: Preferences window can't be opened (LP:696186)
* Windows: Fix opening linked files with umlauts or other special characters
* Code: Make pywebkitgtk an explicit requirement

# 1.1.2 (10-12-26)
* Add fullscreen mode (F11)
* Highlight all found occurrences of the searched word (LP:614353)
* Highlight mixed markups (**__Bold underline__**)
* Highlight structured headers (=Part=, ==Subpart==, ===Section===, ====Subsection====, =====Subsubsection=====)
* Document structured headers
* Highlight ``, "", ''
* Write documentation about ``, "", ''
* Let the preview and edit button have the same size
* Fix: Correctly highlight lists (LP:622456)
* Fix: Do not set maximized to True when sending RedNotebook to the tray (LP:657421)
* Fix: Add Ctrl-P shortcut for edit button (LP:685609)
* Fix: Add "\" to the list of ignored chars for word clouds
* Fix: Escape characters before adding results to the search list
* Fix: Local links with whitespace in latex
* Windows: Fix opening linked files
* Windows: Do not center window to prevent alignment issues
* Windows: Fix image preview (LP:663944)
* Internal: Replace tabs by whitespace in source code
* Many translations updated

# 1.1.1 (10-08-21)
* Let user delete category with 'DELETE' key (LP:608717)
* Sort categories alphabetically (LP:612859)
* Fix: After clicking "Change the text" on an annotation, directly edit it (LP:612861)
* Fix: Journal -> _Journal in menu
* Fix: Do not clear entry when category is changed in new-entry dialog
* Fix: restore left divider position
* Fix: Use rednotebook website for retrieving newest version information (LP:621975)
* Windows: Shrink installer size
* Windows: Update gtk libs
* Windows: New theme
* Windows: New icons
* New translations:
  * English (United Kingdom)
  * Norwegian Bokmal
* Many translations updated

# 1.1.0 (10-08-03)
* When searching for text, search in dates too (Search for 2010-05 displays all entries of May 2010)
* Improve checking for new version (Show version numbers)
* Save last selected tab (Search/Clouds) (LP:590483)
* Save journal files as readable unicode
* Save journal files without python directives
* Let the Preview and the Edit button always have the same size
* Get rid of warnings caused by older webkit versions
* Use webkit on Windows
* Use webkit by default if installed
* Get rid of CamelCase in sourcecode
* Open external files asynchronously with subprocess.Popen from preview
* Fix: Correctly highlight multiple links and images on one line
* Fix: Months that have been cleared of all text are now rewritten to disk
* Fix: Allow ampersands in annotation links (LP:612490)
* Rewrite export assistant code
* Much more code rewritten or restructured
* Bundle msvcr dll in windows installer (Fixes Error 14001)
* New translations:
  * Chinese (Traditional)
* Many translations updated

# 1.0.0 (10-06-23)
* Describe how to add latex math formulas and custom html tags in help
* Fix crash on windows when data and program live on different drives in portable mode (LP:581646)
* Fix display of italic text in edit mode
* Fix inserting templates on Windows
* New Translations:
  * Faroese

# 0.9.5 (10-05-11)
* Show week numbers in calendar (edit weekNumbers in config file)
* Sort items in configuration.cfg
* Automatically put cursor into search field, when search tab is opened
* Do not translate log
* Fix export error on Windows (LP:575999)
* Get rid of PangoWarnings on Windows
* Get rid of Statusbar deprecation message
* New recommended dependency: python-chardet

# 0.9.4 (10-04-29)
* Allow dragging of files and pictures into RedNotebook (Linux only)
* Save data dir relative to application dir in portable mode
* Remember if window was maximized
* Make webkit the default preview backend
* Improve documentation (Synchronization, Portable mode)
* Improve list markup highlighting
* Only add help content at first startup (Closes LP:550814)
* Live highlighting of searched words in text
* Scroll to found word at search
* Make user directory configurable in default.cfg
* Windows:
  * Fully translate Windows version
  * Add more languages to the Windows installer
  * Fix picture export on Windows
  * Hide PDF export button on windows (pywebkitgtk not available)
  * Portable mode has been improved
  * Let users insert templates again (Closes LP:538391)
* New translations:
  * Brazilian Portuguese
* Many translations updated

# 0.9.3 (10-02-23)
* Add graphical option to select webkit for previews
* If available use webkit for clouds
* Add context menu to the webkit clouds for hiding words
* Change "Stricken" to "Strikethrough"
* Add locale functions for complete translations
* Change xhtml extension to .html
* Improve documentation
* New translations:
  * Italian
* Many translations updated


# 0.9.2 (10-01-21)
* Use webkit for direct PDF export
* Remove pdflatex (texlive) package suggestion
* Improve menu layout
* Add "Report A Problem" button
* Add "Translate RedNotebook" button
* Add "Get Help Online" button
* Handle opening of links externally in webkit preview
* Fix spellchecking
* Fix linebreaks for XHTML
* Improve documentation
* New Translations:
  * Spanish
* Updated Translations:
  * German
  * Indonesian
  * Hebrew
  * Malay
  * Czech
  * Polish
  * Dutch
  * Chinese (Simplified)

# 0.9.1 (09-12-27)
* Make markup highlighting much faster
* Allow using webkit for previews (In the config file, set useWebkit to 1)
* Make pywebkitgtk (python-webkit) an optional, but highly recommended dependency
* Make welcome text translatable
* Add comments for translators
* Make help available online

# 0.9.0 (09-12-17)
* Markup Highlighting (a little WYSIWYG/RTF)
* New translations:
  * Indonesian
  * Asturian
  * Ukrainian
  * Danish
* Updated translations:
  * All (Yay, thanks!)

# 0.8.9 (09-10-04)
* Save your journal to a remote server (SSH, FTP and WebDAV support)
* Do not load backup files in data directory
* Fix "Save As"
* New translations:
  * Dutch
  * Polish

# 0.8.8 (09-10-23)
* Internationalization:
 * RedNotebook is now available in:
   * German
   * Czech
   * Hebrew
   * Malay
   * Romanian
   * Russian
   * Simplified Chinese
   * French
 * Translations are partly available for:
   * Brazilian Portuguese
   * Croatian
   * Italian
   * Dutch
   * Belarusian
 * New translations can be made at launchpad.net
* Add "Start minimized to tray" command line parameter
* Add cloud words white list for short words

# 0.8.7 (2009-09-27)
* Only save content and config when they have been changed
* Make the UI easier to understand
  * provide more tooltips
* Update help
  * explain how to use Categories as Todo items there
  * make help topic centric
  * cleanup template help
* Fix "Insert this Weekday's Template"

# 0.8.6.1 (2009-09-04)
* Fix duplicate naming bug (LP:424550)

# 0.8.6 (2009-09-04)
* Added an optional tray icon
  (Closing the window sends RedNotebook to the system tray)
* The menubar has been rewritten to support gtk+ 2.14
* Fix "add example content"
* Fix calendar issue (again)
* Fix crash on Hardy

# 0.8.5 (2009-08-29)
* Spell Checking (not for Windows)
  (Requires gtkspell for python. This is included in the python-gnome2-extras package)
* When a template is inserted, every occurrence of "$date$" is converted to the current date
  (Set date format in preferences)
* Open a specified journal from the command line
  (execute "rednotebook -h" for instructions)
* Autocomplete category entries
* Wrap lines in categories view
* When a category is selected on the right and you add a new category entry,
  set focus directly in entry field
* Fix: Allow underscores and whitespace in filenames for latex (LP:414588)
* Fix: Reset min gtk version to 2.14

# 0.8.4 (2009-08-13)
* Add Undu and Redo for Categories
  (Hit Ctrl-Z to restore a deleted category entry)
* Hide cloud words with simple right-click
* Open pictures by double-clicking them (in preview)
* Statistics: Show number of distinct words
* Category items can now be formatted bold, italic, underlined, stricken
  (Just put **, //, __ or -- around the entry text)
* Format category entries with the "Format" button
  (Select a node on the right and apply a format from the "Format" menu)
* Add "Stricken" format button
  (Useful e.g. for completed todo items)
* New Shortcuts:
  * Ctrl-N: Add a new entry to a category
  * Ctrl-T: Tag the current day
* You can now use TAB to navigate in the "New entry dialog"
* Switch from libglade to GtkBuilder (the python-glade dep can be dropped)
* Fix undo and redo for main text

# 0.8.3 (2009-08-07)
* New statistics dialog with daily word count. Shows number of words, lines, and chars
* Fill some days of the journal with solutions of common question at first startup
* Add option to restore that example content. It will be placed after the last edited day
* Add "Autostart RedNotebook" option
  * Linux: Option in Program
  * Win: Installer Option
* Format category entries in search window
* Finish a new category entry by hitting ENTER
* Put the initial focus in the text window for direct typing (LP:406450)
* Fix calendar warning
* Use glib.timeout_add_seconds for automatic saving for less energy consumption on laptops
* Highlight searched words in preview too

# 0.8.2 (2009-07-28)
* Blacklist for clouds in GUI
* Let the search function highlight found words
* Fix line breaks for exports
* Fix opening files on Mac
* Add little section about comments to Help text
* Fix size for insert icon by using a stock icon
* Do not use small toolbar icon sizes (LP:405991)

# 0.8.1 (2009-07-24)
* make font size configurable (under preferences)
* Add line breaks (under insert menu)
* Add a whitespace char between adjacent lines
* Fix: Win Version should use smaller insert-image icon (16x16)

# 0.8.0 (2009-07-22)
* Graphical preferences dialog (Under "Edit" menu)
* Make date/time format configurable in the preferences dialog
* Fix unicode bugs

# 0.7.6 (2009-07-15)
* Undu and redo for the main text
* Use libyaml for faster loading and dumping of files (Big journals now open ~10 times faster)
* Speed improvements for navigation between days
* Add information for Latex to PDF conversion
* Shortcut for turning on/off the preview: Ctrl+P
* New entry in Edit menu: "Find"
* Append error messages to the logfile
* Use new svn version of txt2tags
* Fix URL and file link insertion

# 0.7.5 (2009-06-30)
* Buttons for bold, italic, underlined text
* Fixed hardy bug: yaml 3.05 does not have __version__ attribute
* Removed shebangs from python modules (Closes LP:393602)

# 0.7.4 (2009-06-25)
* Create ~/.rednotebook dir before logging is initialized (Closes LP:392235)
* Set native theme for windows version

# 0.7.3 (2009-06-21)
* Only save months that have been visited for a faster exit
* Improve logging
* Automatically create a logfile for debugging
* Fix: Check if directory exists before opening it

# 0.7.2 (2009-05-25)
* Choose a folder for journal (Save-As)
* Have more than one journal (New Journal)
* Open existing journals (Open Journal)

# 0.7.1 (2009-05-21)
* Open and create template files from within RedNotebook
* Live update of template list
* Fix opening files for Win

# 0.7.0 (2009-05-19)
* Arbitrarily named templates
* Enable copy/paste in categories edit box
* Live update of clouds after categories have been edited

# 0.6.9 (2009-05-05)
* Re-enable stricken text
* Select individual categories to export
* Export only text, or only categories, or both
* Handle local file opening
  Double-clicks on links in the preview open the link with the preferred app
* Categories can be edited with right mouse clicks:
  Click on an existing category then right mouse click to add a new entry
* Link template files
* Make toolbars equally sized
* Delete GTKMozembed cruft
  * Delete mozembed.py module (originally taken from listen-project)
* Delete markup cruft

# 0.6.8 (2009-05-03)
* Drop GTKMozembed dependency
  * Add keepnote modules
  * remove numbered lists
* Minor Bugfixes

# 0.6.7 (2009-04-21)
* Make deb package Python 2.6 compatible
* Add yaml-parser error handling
* Fix inserting file links containing whitespace

# 0.6.6 (2009-04-07)
* Fix: A modified category and tag name is not modified in the category drop
  down list until you reload the application.
* Fix: Cloud words should have the same color as text words (LP:353738)

# 0.6.5 (2009-04-01)
* Ignore list for clouds (Mark word(s) in cloud, right-click and select "Hide")
* Keyboard shortcuts for inserting pictures, files, links and the date

# 0.6.4 (2009-03-29)
* Easier Tagging (Added tag button)
* New-Entry-Dialog: Show previous tags in drop-down menu when "Tags" is selected as category
* New-Entry-Dialog: Only make a new entry submittable, if text has been entered
* Shortcuts to navigate between days (<Ctrl> + PageUp, <Ctrl> + PageDown)
* Check xulrunner paths at startup
* Made Windows installer

# 0.6.3 (2009-03-21)
* Add an option to insert the current time and date
* Save divider positions and frame size
* Add new statistics
* Disable GTKMozembed automatically if RedNotebook crashes

# 0.6.2 (2009-03-17)
* Content is automatically saved every ten minutes
* Fix Debian/Jaunty Bug (LP:340101)

# 0.6.1 (2009-03-03)
* New types to insert: Bullet List, Numbered List, Title, Line

# 0.6.0 (2009-02-25)
* Allow linking of files
* Allow embedding images
* Links and mail addresses are recognized automatically
* Adding named links to websites is now possible
* Better documentation

# 0.5.6 (2009-02-23)
* Disable automatic update checking
* Add "Check for new version" menu entry
* Add config file and tips for packagers
* Add 'Disable GTKMozembed' option to config files
* Add copyright notice to source files
* Add LICENSE file

# 0.5.5 (2009-02-12)
* Make GTKMozembed optional
* Use preview in browser if GTKMozembed not installed
* Add browser navigation buttons to preview
* Remove gtkhtml2 dependency
* Add name of day to title in preview and export

# 0.5.4 (2009-02-02)
* RedNotebook now checks for new version when it is started
* The configuration is saved in a file when the program exits
* The Fedora gtkmozembed bug has been fixed (LP:320492)

# 0.5.3 (2009-01-30)
* Word, tag and category clouds
* Catch abnormal aborts and save content to disk

# 0.5.2 (2009-01-27)
* The Export Wizard is back again (Thanks Alexandre)
* It is now possible to search for text, categories and tags

# 0.5.1 (2009-01-21)
* Days can be tagged
* Formatting text is possible
* Bugfixes

# 0.5.0 (2009-01-19)
* The GUI has been ported to PyGTK
* Almost all of the features have been adapted to the new interface
* A Preview Tab for a day's content was added

# 0.4.1 (2009-01-15)
* Do not export empty days (Fixes Bug #314385)
* Fix search for single digit months (Fixes Bug #312988)

# 0.4.0 (2008-12-18)
* Export Functionality added: Text, HTML, Latex
* Use of Configuration Files

# 0.3.0 (2008-11-29)
* Template entries for each weekday
* Undo & Redo
  * Ubuntu Main Menu Entry
* Improved Documentation

# 0.2.0 (2008-11-07)
* Word Cloud
* Frame Icons in Multiple Resolutions
* After adding new category, directly add new entry
* Example Categories in Right Pane
* Case-insensitive search
* Statistics: Number of words, entries

# 0.1.0 (2008-09-23)
* Initial Release
* Available Features
  * Enter Day Content
  * Add Day Categories
  * (Live-) Search for Day Content
  * Automatic saving
  * Backup to zip archive
  * Mark edited days
  * Calendar Navigation
