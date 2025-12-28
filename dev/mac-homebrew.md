# Installing RedNotebook from source on macOS

After installing [Homebrew](https://docs.brew.sh/Installation), run:

```sh
brew install adwaita-icon-theme enchant gobject-introspection gsettings-desktop-schemas gtk+3 gtk-mac-integration gtksourceview4 git pipx
pipx install git+https://github.com/jendrikseipp/rednotebook#egg=rednotebook[spellcheck]
pipx ensurepath
rednotebook
```

To create a shortcut to the application, in Automator (run as a shell script):

```sh
export LC_ALL=en_US.UTF-8  # change to a different language if needed
/Users/$(whoami)/.local/bin/rednotebook
```

To upgrade to the latest version, it is `pipx upgrade rednotebook`.

(Thanks to Peter Green for documenting these steps at
https://gist.github.com/pmgreen/a1bf2c7015cb2a70d73e5e66bb84885e based on
https://jarrousse.org/installing-rednotebook-from-source-on-mac-os-x/)
