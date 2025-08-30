# -----------------------------------------------------------------------
# Copyright (c) 2008-2024 Jendrik Seipp
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

import codecs
import locale
import logging
import os
import platform
import subprocess
import sys

import gi


ENCODING = sys.getfilesystemencoding() or locale.getlocale()[1] or "UTF-8"
LANGUAGE = locale.getdefaultlocale()[0]
REMOTE_PROTOCOLS = ["http", "ftp", "irc"]

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

LOCAL_FILE_PEFIX = "file:///" if IS_WIN else "file://"


try:
    gi.require_version("GIRepository", "3.0")
except ValueError:
    try:
        gi.require_version("GIRepository", "2.0")
    except ValueError:
        sys.exit("Please install GIRepository (package gir1.2-glib-* on Ubuntu).")
from gi.repository import GIRepository


repo = GIRepository.Repository()
logging.info(f"Available versions of the WebKit2 namespace: {repo.enumerate_versions('WebKit2')}")


def _is_nvidia_graphics_detected():
    """
    Detect if the system has Nvidia graphics drivers that might be affected
    by the WebKitGTK DMA-BUF renderer bug.

    Returns True if Nvidia graphics are detected, False otherwise.
    """
    # Fast path: check common file indicators and return immediately if any exist.
    if any(
        os.path.exists(p)
        for p in (
            "/proc/driver/nvidia/version",
            "/dev/nvidia0",
            "/dev/nvidiactl",
        )
    ):
        return True

    # Fallback: use lspci output (best effort, ignore errors/timeouts).
    try:
        result = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and "nvidia" in result.stdout.lower():
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return False


def _is_x11_forwarding_detected():
    """
    Detect if we're running in an X11 forwarding environment (e.g., SSH with X11 forwarding).
    """
    # Check for SSH connection indicators
    ssh_indicators = ["SSH_CLIENT", "SSH_CONNECTION", "SSH_TTY"]
    has_ssh = any(var in os.environ for var in ssh_indicators)

    # Check if DISPLAY is set to a remote display (contains a colon and number > 0)
    display = os.environ.get("DISPLAY", "")
    is_remote_display = False
    if display and ":" in display:
        try:
            # Extract display number (e.g., ":10.0" -> 10)
            display_num = int(display.split(":")[1].split(".")[0])
            # Local displays typically use :0, remote X11 forwarding uses higher numbers
            is_remote_display = display_num > 0
        except (IndexError, ValueError):
            pass

    return has_ssh and display and is_remote_display


def _apply_webkit_x11_forwarding_workaround():
    """
    Apply workarounds for WebKitGTK when running with X11 forwarding.

    X11 forwarding often lacks hardware acceleration and can cause WebKit2 to crash
    or fail to initialize. This function sets environment variables to disable
    problematic features.
    """
    if _is_x11_forwarding_detected():
        # Environment variables to set for better X11 forwarding compatibility.
        webkit_env_vars = {
            "WEBKIT_DISABLE_SANDBOX": "1",  # Disable sandboxing which may not work remotely
            "WEBKIT_DISABLE_DMABUF_RENDERER": "1",  # Disable DMA-BUF renderer
            "WEBKIT_DISABLE_COMPOSITING_MODE": "1",  # Disable compositing
        }

        # Only set variables that aren't already set by the user.
        set_vars = []
        for var, value in webkit_env_vars.items():
            if var not in os.environ:
                os.environ[var] = value
                set_vars.append(var)

        if set_vars:
            logging.info(
                f"X11 forwarding detected. Setting WebKit environment variables "
                f"for remote display compatibility: {', '.join(set_vars)}"
            )


def _apply_webkit_nvidia_workaround():
    """
    Apply workaround for WebKitGTK DMA-BUF renderer bug with Nvidia drivers.

    This sets WEBKIT_DISABLE_DMABUF_RENDERER=1 if Nvidia graphics are detected
    and the environment variable is not already set.
    """
    env_var = "WEBKIT_DISABLE_DMABUF_RENDERER"

    # Only apply if not already set by user
    if env_var not in os.environ:
        if _is_nvidia_graphics_detected():
            os.environ[env_var] = "1"
            logging.info(
                "Nvidia graphics detected. Setting WEBKIT_DISABLE_DMABUF_RENDERER=1 "
                "to work around WebKitGTK rendering issues."
            )


# Apply workarounds before importing WebKit2
if not IS_WIN:  # Only apply on Linux/Unix systems
    _apply_webkit_nvidia_workaround()
    _apply_webkit_x11_forwarding_workaround()


try:
    gi.require_version("WebKit2", "4.1")
except ValueError as err:
    logging.warning(
        f"WebKit2 4.1 not found. Trying to use arbitrary version. Error message: '{err}'"
    )

try:
    from gi.repository import WebKit2

    # Don't log the version as it leads to a warning about a failed assertion.
    # logging.info(
    #    f"Loaded version of the WebKit2 namespace: {repo.get_version('WebKit2')}"
    # )
except ImportError as err:
    logging.info("Failed to load the WebKit2 namespace")
    WebKit2 = None
    if not IS_WIN:
        logging.info(
            f"WebKit2Gtk not found. Please install"
            f" it if you want in-app previews."
            f" On Debian/Ubuntu you need the gir1.2-webkit2-4.1 package."
            f' Error message: "{err}"'
        )


def has_system_tray():
    return IS_WIN  # A smarter detection is needed here ;)


def main_is_frozen():
    return hasattr(sys, "frozen")


if main_is_frozen():
    app_dir = sys._MEIPASS  # os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if main_is_frozen():
    locale_dir = os.path.join(app_dir, "share", "locale")
else:
    locale_dir = os.path.join(sys.prefix, "share", "locale")

image_dir = os.path.join(app_dir, "images")
frame_icon_dir = os.path.join(image_dir, "rednotebook-icon")
files_dir = os.path.join(app_dir, "files")

user_home_dir = os.path.expanduser("~")


class Filenames(dict):
    """
    Dictionary for dirnames and filenames
    """

    def __init__(self, config):
        for key, value in globals().items():
            # Exclude "get_main_dir()"
            if key.lower().endswith("dir") and isinstance(value, str):
                value = os.path.abspath(value)
                self[key] = value
                setattr(self, key, value)

        self.portable = bool(config.read("portable"))

        self.journal_user_dir = self.get_user_dir(config)

        self.data_dir = self.default_data_dir

        # Assert that all dirs and files are in place so that logging can take start
        make_directories([self.journal_user_dir, self.data_dir, self.template_dir, self.temp_dir])
        make_files([(self.config_file, ""), (self.log_file, "")])

        self.last_pic_dir = self.user_home_dir
        self.last_file_dir = self.user_home_dir

        self.forbidden_dirs = [user_home_dir, self.journal_user_dir]

    def get_user_dir(self, config):
        if not (custom := config.read("userDir")):
            return (
                os.path.join(self.app_dir, "user")
                if self.portable
                else os.path.join(self.user_home_dir, ".rednotebook")
            )
        # If a custom user dir has been set,
        # construct the absolute path (if not absolute already)
        # and use it
        if not os.path.isabs(custom):
            custom = os.path.join(self.app_dir, custom)
        return custom

    def is_valid_journal_path(self, path):
        return os.path.isdir(path) and os.path.abspath(path) not in self.forbidden_dirs

    def __getattribute__(self, attr):
        user_paths = {
            "template_dir": "templates",
            "temp_dir": "tmp",
            "default_data_dir": "data",
            "config_file": "configuration.cfg",
            "log_file": "rednotebook.log",
        }

        if attr in user_paths:
            return os.path.join(self.journal_user_dir, user_paths.get(attr))

        return dict.__getattribute__(self, attr)


def read_file(filename):
    """Try to read a given file.

    Return empty string if an error is encountered.
    """
    try:
        with codecs.open(filename, "rb", encoding="utf-8", errors="replace") as file:
            return file.read()
    except ValueError as err:
        logging.info(err)
    except Exception as err:
        logging.error(err)
    return ""


def write_file(filename, content):
    assert os.path.isabs(filename)
    try:
        with codecs.open(filename, "wb", errors="replace", encoding="utf-8") as file:
            file.write(content)
    except OSError as e:
        logging.error(f'Error while writing to "{filename}": {e}')


def make_directory(dir):
    if not os.path.isdir(dir):
        os.makedirs(dir)


def make_directories(dirs):
    for dir in dirs:
        make_directory(dir)


def make_file(file, content=""):
    if not os.path.isfile(file):
        write_file(file, content)


def make_files(file_content_pairs):
    for file, content in file_content_pairs:
        make_file(file, content)


def make_file_with_dir(file, content):
    dir = os.path.dirname(file)
    make_directory(dir)
    make_file(file, content)


def get_relative_path(from_dir, to_dir):
    """
    Try getting the relative path from from_dir to to_dir
    """
    # If the data is saved on two different windows partitions,
    # return absolute path to to_dir.
    # drive1 and drive2 are always empty strings on Unix.
    drive1, _ = os.path.splitdrive(from_dir)
    drive2, _ = os.path.splitdrive(to_dir)
    if drive1.upper() != drive2.upper():
        return to_dir

    return os.path.relpath(to_dir, from_dir)


def get_journal_title(dir):
    """
    returns the last dirname in path
    """
    dir = os.path.abspath(dir)
    # Remove double slashes and last slash
    dir = os.path.normpath(dir)

    dirname, basename = os.path.split(dir)
    # Return "/" if journal is located at /
    return basename or dirname


def get_platform_info():
    import yaml
    from gi.repository import GObject, Gtk

    functions = [
        platform.machine,
        platform.platform,
        platform.processor,
        platform.python_version,
        platform.release,
        platform.system,
    ]
    names_values = [(func.__name__, func()) for func in functions]

    names_values.extend(
        [
            (
                "GTK",
                (
                    Gtk.get_major_version(),
                    Gtk.get_minor_version(),
                    Gtk.get_micro_version(),
                ),
            ),
            ("Glib", GObject.glib_version),
            ("PyGObject", GObject.pygobject_version),
            ("YAML", yaml.__version__),
        ]
    )
    if WebKit2:
        names_values.append(
            (
                "WebKit2",
                (
                    WebKit2.get_major_version(),
                    WebKit2.get_minor_version(),
                    WebKit2.get_micro_version(),
                ),
            )
        )

    vals = [f"{name}: {val}" for name, val in names_values]
    return "System info: " + ", ".join(vals)


def system_call(args):
    """
    Asynchronous system call

    subprocess.call runs synchronously
    """
    subprocess.Popen(args)


def get_peak_memory_in_kb():
    try:
        # This will only work on Linux systems.
        with open("/proc/self/status") as status_file:
            for line in status_file:
                parts = line.split()
                if parts[0] == "VmPeak:":
                    return int(parts[1])
    except OSError:
        pass
    raise Warning("warning: could not determine peak memory")
