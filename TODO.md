# Roadmap

If you have any suggestions or comments, feel free to start a
[discussion](https://github.com/jendrikseipp/rednotebook/discussions). Before
starting to work on a feature, please check back with me briefly about its
status.

## Important features

- [ ] Support Markdown.
- [ ] Use separate file for storing CSS to allow users to override styles more easily.
- [ ] Make default CSS prettier.
- [ ] Allow searching for days that contain *multiple* words or tags.
- [ ] Add simple way to show all entries: allow searching for whitespace (i.e., don't strip whitespace from search string).
- [ ] Copy files and pictures into data subdirectory (#163, #469).
- [ ] Require minimum width for calendar panel to avoid hiding it by accident.

- [ ] Data safety:
  - [ ] Make sure that RedNotebook contents are saved under Windows when system is shut down.
  - [ ] Make sure there is no race condition between automatic and manual saving that could cause data corruption.

- [ ] Windows:
  - [ ] Make sure we use libyaml and not yaml on Windows.
  - [ ] Check that images work on Windows in LaTeX exports.

### Remove right-side tags panel (disabled by default)

- [X] When searching for a hashtag (see #498): if hashtag starts the line: show text after hashtag.
- [ ] When searching for a hashtag, scroll to hashtag and highlight it.
- [-] Optional: enable right-side tags panel by default, if journal has right-side tags.
- [ ] Transform existing right-side tags foo:bar to "#foo bar" when loading a journal.
- [ ] Remove code for right-side tags panel.

## Optional features

- [ ] Auto-completion for hashtags.
- [ ] Add macro system that takes a macro like `{weather}` and renders it for the preview, e.g., an HTML snippet that displays that day's weather symbol.
- [ ] Live preview of selected font in editor pane.
- [ ] Allow exporting the entries of a search result.
- [ ] Translate help page.
- [ ] Allow hashtags with non-alphanumeric characters, e.g., `#c++`.
- [ ] Add menus to forward and backward buttons to navigate to recently visited days.
- [ ] Make deleting templates easier.
- [ ] Translate templates.

## Implementation changes

- [ ] Enable faulthandler module (<https://docs.python.org/3/library/faulthandler.html>, added in Python 3.3).

## Deferred features

After switching to Markdown, add the following features:

- [X] Insert Latex formulas
  - [X] Preview Latex formulas
  - [X] Highlight formulas in edit mode
  - [X] Support formulas in all export formats
  - [ ] Add menu item for inserting formulas
- [X] Tables
  - [X] Highlight tables in edit mode
- [X] Numbered lists
- [X] Add quotes by indenting them with a tab

## Unwanted features

- verbatim / raw ( """/"" - supported, undocumented) (too confusing / poorly behaving)
- remote pictures (pictures would have to be downloaded and saved in a folder for exports)
- Copy/Paste category entries (Too complicated)
- Add --portable command line parameter (The default config file is better)
- word wrapping while editing category entries (too complicated, would involve writing C code)
- Language selection for spell checking (is already implemented in new versions of gtkspell)
- Todo tab next to clouds (KISS)
- Automatic Backups (KISS, intruding, gentle messages are better)
- Rethink linebreaks? (Changing paragraphs in txt2tags will probably crash
  everything, Current behaviour should be fine)
- allow opening config file from within RedNotebook
  (Probably no good idea as some options might be unavailable or confusing)
- Make the Format button remember its last action -> No, current behaviour good enough.
- Tabs for different notebooks (KISS)
- Add option for time interval between automatic savings? (KISS)
- Let user select the language for RedNotebook in Windows installer (Users probably want their default language)
- Get proper file layout with one script not part of module (Everything works without name clashes)
- Use threads for file loading and link opening (Probably a bad idea since threads are a source of errors)
- List recently opened journals under "Journal" -> "Recently Used" (KISS, config option needed)
- Drag and Drop for Windows (gtk inter application dnd isn't implemented on win32)
- Use configobj for config files (KISS, Never change A running system ;)
- Search for multiple words at the same time (KISS)
- For each journal to have its own templates (KISS)
- Let the Search type selection remember the selection between sessions (KISS)
- Let the Annotate and Tag window box remember their positions between sessions (KISS)
- Select template file when clicking the button instead of adding weekday's file
- Use categories for number data and present it graphically (KMs, Cash, Calories) (KISS)
- Check for duplicates in cloud blacklists (Does not make much sense since each word
  can only be right-clicked once in the cloud)
- Right-click on word in main text area to add it to cloud whitelist
  (Functionality will be difficult to find, would have to be implemented for
  preview as well)
- Image resizing with PIL (The width parameter is more useful)
- Use attributes for formatting glade strings for easier translation
  (requires GTK 2.16 and does not make much sense now that all strings have been translated)
- Move the "update application" command into the help menu (central place for the checking is better)
- Use a custom config.t2t per diary
  (This will be overkill for most users and having a data subdirectory for images etc. will suffice)
- Open the exported file after the export? (No other program does that)
- Monitor clipboard and add all copied stuff into RedNotebook in "clip mode" (unintuitive, KISS)
- Generalize tags to "hierarchical tags" (This is the job of outliners)
- Add additional one-click menu (like the one with Search and Tags Cloud) that
  contains quick links to other journals (KISS)
- Syntaxhighlighting support (pygments) (KISS, can probably be done with javascript)
- Support for 'inline files': read content from file upon preview of page and
  add the contents of the file inline (which allows for 'dynamic' content) (KISS)
- Field or shortcut to enter a date and takes you there (One navigation suffices)
- Disable cache for preview to support previewing externally changed files (Rarely used, might slowdown app)
- Use new markup for images: {/home/user/pic.png?50} (Too disruptive)
- Support %!include, %!preprocess, etc. (very txt2tags specific)
- Encryption (there are dedicated tools for encrypting files)
- Highlight the current day in the calendar (#466, Gtk.Calendar supports only one highlight style)
