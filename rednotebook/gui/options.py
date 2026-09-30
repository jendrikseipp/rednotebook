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
# with this program.  If not, see <https://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------

import logging
import os
import platform

from gi.repository import Gtk

from rednotebook import info, sync
from rednotebook.configuration import Config
from rednotebook.gui import editor
from rednotebook.gui.customwidgets import ActionButton, CustomComboBoxEntry, UrlButton
from rednotebook.util import dates, filesystem, utils


class Option(Gtk.HBox):
    def __init__(self, text, option_name, tooltip=""):
        Gtk.HBox.__init__(self)

        self.text = text
        self.option_name = option_name

        self.set_spacing(5)

        self.label = Gtk.Label(label=self.text)
        self.pack_start(self.label, False, False, 0)

        if tooltip:
            self.set_tooltip_text(tooltip)

    def get_value(self):
        raise NotImplementedError


class TickOption(Option):
    def __init__(self, text, name, value=None, tooltip=""):
        Option.__init__(self, "", name, tooltip=tooltip)

        self.check_button = Gtk.CheckButton(text)
        if value is None:
            self.check_button.set_active(Option.config.read(name) == 1)
        else:
            self.check_button.set_active(value)
        self.check_button.connect("clicked", self.on_check_button_clicked)
        self.pack_start(self.check_button, False, False, 0)

    def on_check_button_clicked(self, widget):
        pass
        # TODO: Apply corresponding actions.

    def get_value(self):
        """
        We use 0 and 1 internally for bool options
        """
        return int(self.check_button.get_active())


class AutostartOption(TickOption):
    def __init__(self):
        self.autostart_file = os.path.expanduser("~/.config/autostart/rednotebook.desktop")
        autostart_file_exists = os.path.exists(self.autostart_file)
        TickOption.__init__(
            self, _("Load RedNotebook at startup"), None, value=autostart_file_exists
        )

    def get_value(self):
        return self.check_button.get_active()

    def set(self):
        """Apply the current setting"""
        if self.get_value():
            # Add autostart file if it is not present
            filesystem.make_file_with_dir(self.autostart_file, info.desktop_file)
        elif os.path.exists(self.autostart_file):
            os.remove(self.autostart_file)


class TextOption(Option):
    def __init__(self, text, option_name, default="", **kwargs):
        Option.__init__(self, text, option_name, **kwargs)

        # directly read the string, not the list
        value = Option.config.read(option_name, default)

        # Ensure that we have a string here
        value = str(value)

        self.entry = Gtk.Entry()
        self.entry.set_text(value)

        self.pack_start(self.entry, True, True, 0)

    def get_value(self):
        return self.entry.get_text()


class IntegerOption(Option):
    def __init__(
        self,
        text,
        option_name,
        default=0,
        min_value=0,
        max_value=1000,
        increment=1,
        **kwargs,
    ):
        Option.__init__(self, text, option_name, **kwargs)

        value = Option.config.read(option_name, default=default)
        value = int(value)

        self.spin_button = Gtk.SpinButton()
        adjustment = Gtk.Adjustment(value, min_value, max_value, increment, 10, 0)
        self.spin_button.set_adjustment(adjustment)
        self.spin_button.set_value(value)
        self.spin_button.set_numeric(True)
        self.spin_button.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)

        self.pack_start(self.spin_button, True, True, 0)

    def get_value(self):
        return self.spin_button.get_value_as_int()


class ComboBoxOption(Option):
    def __init__(self, text, name, entries, tooltip=""):
        Option.__init__(self, text, name, tooltip=tooltip)

        self.combo = CustomComboBoxEntry(Gtk.ComboBox.new_with_entry())
        self.combo.set_entries(entries)

        self.pack_start(self.combo.combo_box, False, False, 0)

    def get_value(self):
        return self.combo.get_active_text()


class DateFormatOption(ComboBoxOption):
    def __init__(self, text, name, tooltip):
        date_formats = [
            "%A, %x %X",
            _("%A, %x, Day %j"),
            "%H:%M",
            _("Week %W of Year %Y"),
            "%y-%m-%d",
            _("Day %j"),
            "%A",
            "%B",
        ]

        ComboBoxOption.__init__(self, text, name, date_formats, tooltip=tooltip)

        date_url = "http://docs.python.org/library/time.html#time.strftime"
        date_format_help_button = UrlButton(_("Help"), date_url)

        self.preview = Gtk.Label()
        self.pack_start(self.preview, False, False, 0)

        self.pack_end(date_format_help_button, False, False, 0)

        # Set default format if not present
        format = Option.config.read(name, "%A, %x %X")
        format = str(format)
        self.combo.set_active_text(format)

        self.combo.combo_box.connect("changed", self.on_format_changed)

        # Update the preview
        self.on_format_changed(None)

    def on_format_changed(self, widget):
        format_string = self.get_value()
        date_string = dates.format_date(format_string)
        # Translators: Noun
        label_text = f"{_('Preview:')} {date_string}"
        self.preview.set_text(label_text)


class FontOption(Option):
    def __init__(self, text, name):
        Option.__init__(self, text, name, "")

        self.dialog = None

        self.font_name = Option.config.read(name, editor.DEFAULT_FONT)

        self.label = Gtk.Label()
        self.label.set_text(self.font_name)

        self.button = Gtk.Button(_("Choose font ..."))
        self.button.connect("clicked", self.on_button_clicked)

        self.pack_start(self.label, False, False, 0)
        self.pack_start(self.button, False, False, 0)

    def on_button_clicked(self, widget):
        if not self.dialog:
            self.dialog = Gtk.FontSelectionDialog(_("Choose font"))

            self.dialog.set_font_name(self.font_name)
            self.dialog.set_modal(True)
            self.dialog.set_transient_for(Option.main_window.options_manager.dialog.dialog)
            self.dialog.connect("destroy", self.dialog_destroyed)
            self.dialog.get_ok_button().connect("clicked", self.font_selection_ok)
            self.dialog.get_cancel_button().connect_object(
                "clicked", lambda window: window.destroy(), self.dialog
            )

        self.dialog.show()

    def dialog_destroyed(self, widget):
        self.dialog = None

    def font_selection_ok(self, widget):
        self.font_name = self.dialog.get_font_name()
        self.label.set_text(self.font_name)
        Option.main_window.set_font(self.font_name)
        self.dialog.destroy()

    def get_value(self):
        return self.font_name


class SyncStatusOption(Option):
    """Displays the current sync status and provides a manual sync button.

    The 'Save and sync now' button acts on the values currently typed
    into the sync fields in this dialog - not on whatever was last
    saved to config - so it always does what the user just typed even
    if they have not clicked OK yet.
    """

    def __init__(self, journal, get_current_settings):
        Option.__init__(self, "", None)
        self.journal = journal
        self.data_dir = journal.dirs.data_dir
        # Callback that returns (enabled, url, branch) from the current
        # dialog field values, not from the saved config.
        self.get_current_settings = get_current_settings

        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0)
        self._update_status()
        self.pack_start(self.status_label, True, True, 0)

        sync_now_button = Gtk.Button(_("Save and sync now"))
        sync_now_button.set_tooltip_text(_("Save the settings above and run a sync immediately"))
        sync_now_button.connect("clicked", self._on_sync_now)
        self.pack_start(sync_now_button, False, False, 0)

    def _update_status(self):
        if not sync._is_git_repo(self.data_dir):
            self.status_label.set_text(_("Not initialised"))
        elif not sync._has_remote(self.data_dir):
            self.status_label.set_text(_("No remote configured"))
        else:
            result = sync._run_git(
                self.data_dir,
                "remote",
                "get-url",
                "origin",
                check=False,
            )
            url = result.stdout.strip() if result.returncode == 0 else "?"
            self.status_label.set_text(_("Remote: %s") % url)

    def _on_sync_now(self, widget):
        enabled, url, branch = self.get_current_settings()

        # Persist the values from the dialog so the next auto-sync sees
        # them, and so cancelling the dialog does not discard them.
        config = self.journal.config
        config["syncEnabled"] = int(bool(enabled))
        config["syncRemoteUrl"] = url or ""
        config["syncBranch"] = branch or ""
        config.save_to_disk()

        if not enabled:
            self.status_label.set_text(_("Sync is not enabled"))
            return
        if not url:
            self.status_label.set_text(_("No Remote URL set"))
            return

        result = sync.sync(
            self.data_dir,
            remote_url=url,
            branch=(branch or None),
        )
        if not result:
            self.status_label.set_text(_("Sync failed - check the log"))
            return

        if result.conflicts:
            self.journal._record_sync_conflicts(result.conflicts)
            self.status_label.set_text(
                _("Sync completed with %d day conflict(s): %s")
                % (len(result.conflicts), ", ".join(result.conflicts))
            )
        elif result.pulled_new_data:
            self.status_label.set_text(_("Sync completed - new entries pulled"))
        else:
            self.status_label.set_text(_("Sync completed"))
            self._update_status()  # Refresh remote line

        if result.pulled_new_data:
            self.journal._reload_after_sync()

    def get_value(self):
        return None


class OptionsDialog:
    def __init__(self, dialog):
        self.dialog = dialog
        self.categories = {}

    def __getattr__(self, attr):
        """Wrap the dialog"""
        return getattr(self.dialog, attr)

    def add_option(self, category, option):
        self.categories[category].pack_start(option, False, False, 0)
        option.show_all()

    def add_category(self, name, vbox):
        self.categories[name] = vbox

    def clear(self):
        for vbox in self.categories.values():
            for option in vbox.get_children():
                vbox.remove(option)


class OptionsManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.builder = main_window.builder
        self.journal = main_window.journal
        self.config = self.journal.config

        self.dialog = OptionsDialog(self.builder.get_object("options_dialog"))
        self.dialog.set_transient_for(self.main_window.main_frame)
        self.dialog.set_default_size(600, 300)
        self.dialog.add_category("general", self.builder.get_object("general_vbox"))
        self.dialog.add_category("sync", self.builder.get_object("sync_vbox"))

    def on_options_dialog(self):
        self.dialog.clear()

        # Make the config globally available
        Option.config = self.config
        Option.main_window = self.main_window

        self.options = []

        if platform.system() == "Linux" and os.path.exists("/usr/bin/rednotebook"):
            logging.debug("Running on Linux. Is installed. Adding autostart option")
            self.options.insert(0, AutostartOption())

        # Most modern Linux distributions do not have a systray anymore.
        # If this option is activated on a system without a systray, the
        # application keeps on running in the background after it has been
        # closed. The option can still be activated in the configuration file.
        if filesystem.has_system_tray():
            self.options.append(
                TickOption(
                    _("Close to system tray"),
                    "closeToTray",
                    tooltip=_("Closing the window will send RedNotebook to the tray"),
                )
            )

        # Automatic switching between preview and edit mode.
        self.options.append(
            TickOption(
                _("Switch between edit and preview mode automatically"),
                "autoSwitchMode",
            )
        )

        # Check for new version
        check_version_option = TickOption(
            _("Check for new version at startup"), "checkForNewVersion"
        )

        self.options.append(TickOption(_("Search as you type"), "instantSearch"))

        self.options.append(TickOption(_("Auto indent"), "autoIndent"))

        def check_version_action(widget):
            utils.check_new_version(self.main_window.journal, info.version, startup=False)
            # Apply changes from dialog to options window
            check = bool(self.journal.config.read("checkForNewVersion"))
            check_version_option.check_button.set_active(check)

        check_version_button = ActionButton(_("Check now"), check_version_action)
        check_version_option.pack_start(check_version_button, False, False, 0)
        self.options.append(check_version_option)

        self.options.extend(
            [
                # Use separate fonts since the preview often doesn't support the edit font.
                FontOption(_("Edit font:"), "mainFont"),
                TextOption(
                    _("Preview font:"),
                    "previewFont",
                    default=Config.defaults["previewFont"],
                    tooltip=_("Comma-separated font names"),
                ),
                DateFormatOption(
                    _("Date/Time format"),
                    "dateTimeString",
                    tooltip=_("Used by Date/Time button and $date$ template macro."),
                ),
                DateFormatOption(
                    _("Date format"),
                    "exportDateFormat",
                    tooltip=_("Used for dates in titlebar and exports."),
                ),
                IntegerOption(
                    _("Tags in cloud"),
                    "cloudMaxTags",
                    tooltip=_("Maximum number of tags displayed in the cloud"),
                ),
                TextOption(
                    _("Exclude from cloud"),
                    "cloudIgnoreList",
                    tooltip=_("Do not show these comma separated words and #tags in the clouds"),
                ),
                TextOption(
                    _("Include small words in cloud"),
                    "cloudIncludeList",
                    tooltip=_("Allow these words with 4 letters or less"),
                ),
            ]
        )

        # Sync options
        self.sync_options = []

        self.sync_enabled_option = TickOption(
            _("Enable sync"),
            "syncEnabled",
            tooltip=_(
                "Synchronise journal data across machines using git. Requires git to be installed."
            ),
        )
        self.sync_options.append(self.sync_enabled_option)

        self.sync_url_option = TextOption(
            _("Remote URL:"),
            "syncRemoteUrl",
            tooltip=_(
                "Git remote URL. SSH is recommended for sync "
                "(no password prompts, no token expiry): "
                "e.g. git@github.com:user/journal.git. "
                "HTTPS also works but needs a cached personal access "
                "token or credential helper: "
                "e.g. https://github.com/user/journal.git."
            ),
        )
        test_button = Gtk.Button(_("Test"))
        test_button.set_tooltip_text(_("Check the URL is reachable without modifying anything"))
        test_button.connect("clicked", self._on_test_remote)
        self.sync_url_option.pack_start(test_button, False, False, 0)
        self.sync_options.append(self.sync_url_option)

        self.sync_branch_option = TextOption(
            _("Branch:"),
            "syncBranch",
            tooltip=_("Git branch to sync against. Defaults to 'master'."),
        )
        self.sync_options.append(self.sync_branch_option)

        self.sync_options.append(
            TickOption(
                _("Sync automatically on save"),
                "syncAuto",
                tooltip=_("Commit and push after every save, pull on open"),
            )
        )

        def get_current_sync_settings():
            return (
                self.sync_enabled_option.get_value(),
                self.sync_url_option.get_value().strip(),
                self.sync_branch_option.get_value().strip(),
            )

        self.sync_options.append(SyncStatusOption(self.journal, get_current_sync_settings))

        self.add_all_options()

        response = self.dialog.run()

        if response == Gtk.ResponseType.OK:
            self.save_options()

            # Apply some options
            self.main_window.cloud.update_lists()
            self.main_window.cloud.update(force_update=True)
            self.main_window.set_auto_indent()

            visible = self.config.read("closeToTray") == 1
            # The tray icon is now only instantiated on Windows.
            if self.main_window.tray_icon:
                self.main_window.tray_icon.set_visible(visible)
        else:
            # Reset some options
            self.main_window.set_font(self.config.read("mainFont", editor.DEFAULT_FONT))

        self.dialog.hide()

    def add_all_options(self):
        for option in self.options:
            self.dialog.add_option("general", option)
        for option in self.sync_options:
            self.dialog.add_option("sync", option)

    def save_options(self):
        logging.debug("Saving Options")
        for option in self.options + self.sync_options:
            value = option.get_value()
            if option.option_name is not None:
                logging.debug(f"Setting {option.option_name} = {repr(value)}")
                self.config[option.option_name] = value
            elif hasattr(option, "set"):
                # We don't save the autostart setting in the config file
                option.set()

        self._apply_sync_settings()

    def _on_test_remote(self, widget):
        """Test the URL currently in the sync URL field."""
        url = self.sync_url_option.get_value().strip()
        ok, message = sync.test_remote(url)

        dialog = Gtk.MessageDialog(
            transient_for=self.dialog.dialog,
            modal=True,
            message_type=Gtk.MessageType.INFO if ok else Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=_("Remote reachable") if ok else _("Remote test failed"),
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def _apply_sync_settings(self):
        """Initialise the git sync repo and run a sync now."""
        if not self.config.read("syncEnabled"):
            return

        data_dir = self.journal.dirs.data_dir

        if not sync.init_repo(data_dir):
            self.journal.show_message(
                _("Sync setup failed - could not initialise git repository"),
                error=True,
            )
            return

        remote_url = self.config.read("syncRemoteUrl", "")
        if not remote_url:
            self.journal.show_message(
                _(
                    "Sync is enabled but no remote URL is set. "
                    "Nothing will be pushed until you add one."
                ),
                error=True,
            )
            return

        # Run a full sync now so the user does not have to save + reopen
        # preferences to trigger the first push. sync() will (re)set the
        # remote from the URL before pulling/pushing.
        branch = self.config.read("syncBranch") or None
        result = sync.sync(data_dir, remote_url=remote_url, branch=branch)
        if not result:
            self.journal.show_message(
                _("Sync failed - check the log for details"),
                error=True,
            )
            return

        if result.conflicts:
            self.journal._record_sync_conflicts(result.conflicts)
            self.journal.show_message(
                _("Sync completed. Days with conflicts (please review): %s")
                % ", ".join(result.conflicts),
                error=False,
            )
        elif result.pulled_new_data:
            self.journal.show_message(
                _("Sync completed - new entries pulled from remote"),
                error=False,
            )
        else:
            self.journal.show_message(
                _("Sync completed - journal pushed to %s") % remote_url,
                error=False,
            )

        if result.pulled_new_data:
            self.journal._reload_after_sync()
