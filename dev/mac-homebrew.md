# Installing RedNotebook from source on macOS

After installing [Git](https://git-scm.com/download/mac) and [Homebrew](https://docs.brew.sh/Installation), run:

    brew install adwaita-icon-theme enchant gobject-introspection gsettings-desktop-schemas gtk+3 gtk-mac-integration gtksourceview4
    python3 -m pip install pyenchant pygobject pyyaml
    export LANG=en_US.UTF-8
    export LC_ALL=en_US.UTF-8
    git clone https://github.com/jendrikseipp/rednotebook
    cd rednotebook
    python3 -m pip install --user .

In Automator (run as Bash shell script):

    export PATH=/usr/local/bin:$PATH
    export LANG=en_US.UTF-8
    export LC_ALL=en_US.UTF-8
    /Users/me/path/to/rednotebook

(Thanks to Peter Green for documenting these steps at
https://gist.github.com/pmgreen/a1bf2c7015cb2a70d73e5e66bb84885e based on
https://jarrousse.org/installing-rednotebook-from-source-on-mac-os-x/)
