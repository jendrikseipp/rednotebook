# RedNotebook

RedNotebook is a modern desktop journal. It lets you format, tag and
search your entries. You can also add pictures, links and customizable
templates, spell check your notes, and export to plain text, HTML,
Latex or PDF.


**Installers for Linux and Windows**:
[rednotebook.app/downloads.html](https://www.rednotebook.app/downloads.html)


## Requirements

Needed for running RedNotebook:

  * GTK (3.24): https://www.gtk.org
  * GtkSourceView (3.0+): https://wiki.gnome.org/Projects/GtkSourceView
  * Python (3.8+): https://www.python.org
  * PyYAML (3.10+): https://pyyaml.org
  * WebKitGTK (2.16+): https://webkitgtk.org (only on Linux and macOS)
  * PyEnchant for spell checking (1.6+): https://pypi.org/project/pyenchant/ (optional)

Needed for installing RedNotebook:

  * GNU gettext: https://www.gnu.org/software/gettext
  * Setuptools (60.0+): https://pypi.org/project/setuptools


## Run from source

Install all dependencies:

  * Linux/macOS: [run-tests.yml](.github/workflows/run-tests.yml)
  * Windows: [build-windows.yml](.github/workflows/build-windows.yml)

Start RedNotebook:

  * Linux/macOS: `python3 rednotebook/journal.py`
  * Windows: `py rednotebook/journal.py`


## Cloud sync

RedNotebook can synchronise your journal across multiple machines using
git. Each machine commits, pushes and pulls automatically so that
entries from all machines are merged together.

### Requirements

  * Git must be installed and available on your `PATH`.
  * A remote git repository that all machines can access (e.g. a
    private repo on GitHub, GitLab, or a self-hosted server).

### Quick setup

1. Create a **private** remote repository (e.g. on GitHub).
2. Open **Edit > Preferences** and switch to the **Sync** tab.
3. Tick **Enable sync**.
4. Paste the remote URL into **Remote URL**. **SSH is recommended**
   (e.g. `git@github.com:you/journal.git`): one-time key setup, no
   password prompts or token expiry. HTTPS also works but needs a
   cached personal access token or credential helper.
5. Click **Test** to verify the URL is reachable and authentication
   works. This does not modify anything.
6. Leave **Branch** empty to use the default branch, or enter a branch
   name.
7. Leave **Sync automatically on save** ticked (recommended).
8. Click **OK**. RedNotebook will initialise the local git repo, set
   the remote and perform the first sync immediately.

RedNotebook will initialise a git repository inside your journal data
directory, configure the remote and start syncing.

### Setting up a second machine

Repeat the same steps on the second machine. On the first sync,
RedNotebook will pull the existing journal from the remote and merge it
with any local entries.

### How conflicts are resolved

  * Edits to **different days** within the same month are merged
    automatically by git.
  * If the **same day** is edited on two machines before a sync, both
    versions are kept: the remote text is appended below a
    `--- synced from remote ---` marker so nothing is lost. You can
    then tidy up the entry at your leisure.
  * Categories and tags from both sides are combined.

### Manual sync

If you prefer not to sync on every save, untick **Sync automatically
on save** and use the **Sync now** button in the Sync preferences tab
whenever you want to push/pull.

### Command-line setup (alternative)

You can also enable sync without the GUI by editing
`~/.rednotebook/configuration.cfg`:

```
syncEnabled=1
syncRemoteUrl=git@github.com:you/journal.git
syncBranch=
syncAuto=1
```

### Tips

  * Use SSH keys (or a credential helper) so that git does not prompt
    for a password on every sync.
  * The data directory must not be inside another git repository.
  * If something goes wrong, check `~/.rednotebook/rednotebook.log`
    for sync messages (all prefixed with `sync:`).


## Set up pre-commit hooks

Install [pre-commit](https://pre-commit.com/), then run `pre-commit install`.


## Run tests

Install [tox](https://tox.wiki), then run `tox`.


## Thanks to

  * The authors of the libraries listed under 'Requirements'.
  * Ciaran for creating the RedNotebook icon.
  * The [txt2tags](https://txt2tags.org) team for their markup conversion tool.
  * Dieter Verfaillie for his [elib.intl](https://github.com/dieterv/elib.intl) module.
  * Maximilian Köhl for his [pygtkspellcheck](https://github.com/koehlma/pygtkspellcheck) project.
  * The Weblate team for hosting [translations for RedNotebook](https://hosted.weblate.org/engage/rednotebook/).


## License notes

RedNotebook is published under the GPLv2+. Since it bundles code
released under the LGPLv3+, the resulting work is licensed under the
GPLv3+. See `debian/copyright` for detailed license information.


Enjoy!
