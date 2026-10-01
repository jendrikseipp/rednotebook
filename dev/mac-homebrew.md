# Installing RedNotebook from source on macOS

RedNotebook does not have a notarised `.app` or `.dmg` yet, so macOS
users install from source. The recommended workflow uses
[Homebrew](https://brew.sh) for the GTK stack and
[pipx](https://pipx.pypa.io/) for the Python app itself.

Thanks to Peter Green for the original recipe
(<https://gist.github.com/pmgreen/a1bf2c7015cb2a70d73e5e66bb84885e>)
based on <https://jarrousse.org/installing-rednotebook-from-source-on-mac-os-x/>.


## 1. Install Homebrew

If you do not have Homebrew yet, follow <https://brew.sh>. On a fresh
Mac this takes a few minutes and will prompt for your login password
to install into `/usr/local` (Intel Macs) or `/opt/homebrew`
(Apple Silicon).


## 2. Install the GTK stack and tooling

```sh
brew install adwaita-icon-theme enchant gobject-introspection \
    gsettings-desktop-schemas gtk+3 gtk-mac-integration gtksourceview4 \
    git pipx
```

What each one is for:

| Package | Purpose |
|---|---|
| adwaita-icon-theme | Default icon set for GTK |
| enchant | Spell-check backend (optional) |
| gobject-introspection | Python <-> GObject bridge |
| gsettings-desktop-schemas | GTK settings schemas |
| gtk+3 | GUI toolkit |
| gtk-mac-integration | Native macOS menu bar / dock integration |
| gtksourceview4 | Rich text editor widget |
| git | Required if you want cloud sync; omit if already installed |
| pipx | Installs the Python app in an isolated venv |

First time, expect 20-40 minutes while Homebrew builds or fetches
bottles. Subsequent `brew` runs are fast.


## 3. Install RedNotebook

To install the released version from GitHub:

```sh
pipx install 'git+https://github.com/jendrikseipp/rednotebook#egg=rednotebook[spellcheck]'
pipx ensurepath
```

To install a specific branch or fork (e.g. for testing a PR):

```sh
pipx install 'git+https://github.com/<user>/rednotebook@<branch>#egg=rednotebook[spellcheck]'
```

To install from a local checkout:

```sh
pipx install '/path/to/rednotebook[spellcheck]'
```


## 4. Run it

Open a new terminal (so `pipx ensurepath` is in effect) and run:

```sh
rednotebook
```


## 5. Add a Dock / Spotlight shortcut

In **Automator**, create a new **Application**, add a **Run Shell
Script** action, and paste:

```sh
export LC_ALL=en_US.UTF-8  # or the locale you prefer
/Users/$(whoami)/.local/bin/rednotebook
```

Save the Automator app to `/Applications`. It will then appear in
Spotlight, Launchpad and can be dragged to the Dock.


## Upgrading

```sh
pipx upgrade rednotebook
```

To upgrade the GTK stack:

```sh
brew upgrade
```


## Cloud sync on macOS

RedNotebook's cloud sync feature (Preferences > Sync) uses `git`. The
`brew install` above includes `git`; if you already had git from the
Xcode command-line tools, that works too. See the
[Cloud sync](../README.md#cloud-sync) section of the README for setup.


## Troubleshooting

**"rednotebook: command not found"**: `pipx ensurepath` only takes
effect in new terminal sessions. Open a fresh terminal or run
`source ~/.zprofile` (or your shell's equivalent).

**"Namespace Gtk not available"**: the GTK stack is not on PyGObject's
search path. Make sure PKG_CONFIG_PATH points at Homebrew's lib dir:

```sh
export PKG_CONFIG_PATH="$(brew --prefix)/lib/pkgconfig:$PKG_CONFIG_PATH"
```

Add that line to your `~/.zprofile` to make it persistent, then
reinstall with `pipx reinstall rednotebook`.

**Icon missing in the dock**: this is a limitation of running GTK
apps outside a `.app` bundle. The Automator shortcut above gives it a
proper macOS icon slot.

**App looks blurry on a Retina display**: GTK3 on macOS does not fully
support HiDPI. The Retina issue is a known upstream limitation; see
<https://gitlab.gnome.org/GNOME/gtk/-/issues/4780>.
