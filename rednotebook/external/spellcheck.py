# -*- coding:utf-8 -*-
#
# Copyright (C) 2012, Maximilian Köhl <linuxmaxi@googlemail.com>
# Copyright (C) 2012, Carlos Jenkins <carlos@jenkins.co.cr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
RedNotebook bundles its own copy of pygtkspellcheck, because pygtkspellcheck
versions < 4.0 don't decode UTF-8 from GTK widgets. The earliest Ubuntu version
with a fixed pygtkspellcheck (4.0.5) is 17.04 (see also
https://bugs.launchpad.net/rednotebook/+bug/1615629). This bug probably only
affects Python 2, so we may be able to remove our copy of pygtkspellcheck again.

A simple but quite powerful spellchecking library written in pure Python for Gtk
based on Enchant. It supports both GTK 3 and 4 via PyGObject with Python 3. For
automatic translation of the user interface it can use Gedit's translation files.
"""

import enchant
import gettext
import logging
import re
import sys
from collections import UserList

from gi.repository import Gio, GLib, GObject

# find any loaded gtk binding
if "gi.repository.Gtk" in sys.modules:
    Gtk = sys.modules["gi.repository.Gtk"]
else:
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk  # noqa: N813

_IS_GTK3 = Gtk.MAJOR_VERSION < 4

# public objects
__all__ = ["SpellChecker", "NoDictionariesFound"]

# logger
logger = logging.getLogger("")  # JS: was '__name__'


class NoDictionariesFound(Exception):
    """
    There aren't any dictionaries installed on the current system so
    spellchecking could not work in any way.
    """


# map between Gedit's translation and PyGtkSpellcheck's
_GEDIT_MAP = {
    "Languages": "Languages",
    "Ignore All": "Ignore _All",
    "Suggestions": "Suggestions",
    "(no suggestions)": "(no suggested words)",
    "Add to Dictionary": "Add w_ord",
    "Unknown": "Unknown",
}

_BATCHING_THRESHOLD_CHARS = 1500
_BATCH_SIZE_CHARS = 1000

# translation
if gettext.find("gedit"):
    _gedit = gettext.translation("gedit", fallback=True).gettext

    def _(message):
        return _gedit(_GEDIT_MAP[message]).replace("_", "")

else:
    locale_name = "py{}gtkspellcheck".format(sys.version_info.major)
    _ = gettext.translation(locale_name, fallback=True).gettext


def code_to_name(code, separator="_"):
    # Escape underscores for GTK menuitems.
    return code.replace(separator, separator * 2)


class SpellChecker(GObject.Object):
    """
    Main spellchecking class, everything important happens here.

    :param view: GtkTextView the SpellChecker should be attached to.
    :param language: The language which should be used for spellchecking.
        Use a combination of two letter lower-case ISO 639 language code with a
        two letter upper-case ISO 3166 country code, for example en_US or de_DE.
    :param prefix: A prefix for some internal GtkTextMarks.
    :param collapse: Enclose suggestions in its own menu.
    :param params: Dictionary with Enchant broker parameters that should be set
      e.g. `enchant.myspell.dictionary.path`.

    .. attribute:: languages

        A list of supported languages.

        .. function:: exists(language)

            Checks if a language exists.

            :param language: language to check
    """

    FILTER_WORD = "word"
    FILTER_LINE = "line"
    FILTER_TEXT = "text"

    DEFAULT_FILTERS = {
        FILTER_WORD: [r"[0-9.,]+"],
        FILTER_LINE: [
            (r"(https?|ftp|file):((//)|(\\\\))+[\w\d:" r"#@%/;$()~_?+-=\\.&]+"),
            r"[\w\d]+@[\w\d.]+",
        ],
        FILTER_TEXT: [],
    }

    DEFAULT_EXTRA_CHARS = "'"

    class _LanguageList(UserList):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.mapping = dict(self)

        @classmethod
        def from_broker(cls, broker):
            return cls(
                sorted(
                    [
                        (language, code_to_name(language))
                        for language in broker.list_languages()
                    ],
                    key=lambda language: language[1],
                )
            )

        def exists(self, language):
            return language in self.mapping

    class _Mark:
        def __init__(self, buffer, name, start, iter_worker):
            self._buffer = buffer
            self._name = name
            self._mark = self._buffer.create_mark(self._name, start, True)
            self._iter_worker = iter_worker

        @property
        def iter(self):
            return self._buffer.get_iter_at_mark(self._mark)

        @property
        def inside_word(self):
            return self._iter_worker.inside_word(self.iter)

        @property
        def word(self):
            start = self.iter
            if not self._iter_worker.starts_word(start):
                self._iter_worker.backward_word_start(start)
            end = self.iter
            if self._iter_worker.inside_word(end):
                self._iter_worker.forward_word_end(end)
            return start, end

        def move(self, location):
            self._buffer.move_mark(self._mark, location)

    class _IterWorker:
        def __init__(self, extra_word_chars):
            self._extra_word_chars = extra_word_chars

        def is_extra_word_char(self, loc):
            # Language extra chararacters should also be processed once Enchant's
            # enchant_dict_get_extra_word_characters is exposed in PyEnchant

            char = loc.get_char()
            return char != "" and char in self._extra_word_chars

        def inside_word(self, loc):
            if loc.inside_word():
                return True
            elif self.starts_word(loc):
                return True
            elif loc.ends_word() and not self.ends_word(loc):
                return True
            else:
                return False

        def starts_word(self, loc):
            if loc.starts_word():
                if loc.is_start():
                    return True
                else:
                    tmp = loc.copy()
                    tmp.backward_char()
                    return not self.is_extra_word_char(tmp)
            else:
                return False

        def ends_word(self, loc):
            if loc.ends_word():
                if loc.is_end():
                    return True
                else:
                    tmp = loc.copy()
                    tmp.forward_char()
                    return not self.is_extra_word_char(tmp)
            else:
                return False

        def forward_word_end(self, loc):
            def move_through_extra_chars():
                moved = False
                while self.is_extra_word_char(loc):
                    if not loc.forward_char():
                        break
                    moved = True
                return moved

            tmp = loc.copy()
            tmp.backward_char()
            loc.forward_word_end()
            while move_through_extra_chars():
                if loc.is_end() or not loc.inside_word() or not loc.forward_word_end():
                    break

        def backward_word_start(self, loc):
            def move_through_extra_chars():
                tmp = loc.copy()
                tmp.backward_char()
                moved = False
                while self.is_extra_word_char(tmp):
                    moved = True
                    loc.assign(tmp)
                    if not tmp.backward_char():
                        break
                return moved

            loc.backward_word_start()
            while move_through_extra_chars():
                tmp = loc.copy()
                tmp.backward_char()
                if (
                    loc.is_start()
                    or not tmp.inside_word()
                    or not loc.backward_word_start()
                ):
                    break

        def sync_extra_chars(self, obj, value):
            self._extra_word_chars = obj.extra_chars

    def __init__(
        self, view, language="en", prefix="gtkspellchecker", collapse=True, params=None
    ):
        super().__init__()
        self._view = view
        self.collapse = collapse
        # GTK 3-only signals. GTK 4 uses actions, below.
        if _IS_GTK3:
            # JS: Connect to signals only after successful initialization.
            # Otherwise, functions might be called on uninitialized object.
            pass
        self._prefix = prefix
        self._broker = enchant.Broker()
        if params is not None:
            for param, value in params.items():
                self._broker.set_param(param, value)
        self.languages = SpellChecker._LanguageList.from_broker(self._broker)
        if self.languages.exists(language):
            self._language = language
        elif self.languages.exists("en"):
            logger.warning(
                (
                    'no installed dictionary for language "{}", '
                    "fallback to english".format(language)
                )
            )
            self._language = "en"
        else:
            if self.languages:
                self._language = self.languages[0][0]
                logger.warning(
                    (
                        'no installed dictionary for language "{}" '
                        "and english, fallback to first language in"
                        'language list ("{}")'
                    ).format(language, self._language)
                )
            else:
                logger.critical("no dictionaries found")
                raise NoDictionariesFound()
        self._dictionary = self._broker.request_dict(self._language)
        self._deferred_check = False
        self._filters = dict(SpellChecker.DEFAULT_FILTERS)
        self._regexes = {
            SpellChecker.FILTER_WORD: re.compile(
                "|".join(self._filters[SpellChecker.FILTER_WORD])
            ),
            SpellChecker.FILTER_LINE: re.compile(
                "|".join(self._filters[SpellChecker.FILTER_LINE])
            ),
            SpellChecker.FILTER_TEXT: re.compile(
                "|".join(self._filters[SpellChecker.FILTER_TEXT]), re.MULTILINE
            ),
        }

        self._extra_chars = SpellChecker.DEFAULT_EXTRA_CHARS
        self._iter_worker = SpellChecker._IterWorker(self._extra_chars)
        self.connect("notify::extra-chars", self._iter_worker.sync_extra_chars)

        self._batched_rechecking = False

        self._languages_menu = None
        # GTK 4-only extra menu population, gesture creation and action setup. GTK 3
        # uses signals, above.
        if not _IS_GTK3:
            extra_menu = self._view.get_extra_menu()
            if extra_menu is None:
                extra_menu = Gio.Menu()
                self._view.set_extra_menu(extra_menu)
            self._spelling_menu = Gio.Menu()
            extra_menu.append_section(None, self._spelling_menu)

            controller = Gtk.GestureClick()
            controller.set_button(0)
            controller.connect("pressed", self._gtk4_on_textview_click)
            self._view.add_controller(controller)

            self._gtk4_setup_actions()

        # JS: Connect to signals only after successful initialization.
        # Otherwise, functions might be called on uninitialized object.
        if _IS_GTK3:
            self._view.connect(
                "populate-popup", lambda entry, menu: self.populate_menu(menu)
            )
            self._view.connect("popup-menu", self._click_move_popup)
            self._view.connect("button-press-event", self._click_move_button)

        self._enabled = True
        self.buffer_initialize()

    @GObject.Property(type=str, default="")
    def language(self):
        """
        The language used for spellchecking.
        """
        return self._language

    @language.setter
    def language(self, language):
        if language != self._language and self.languages.exists(language):
            self._language = language
            self._dictionary = self._broker.request_dict(language)
            self.recheck()

    @GObject.Property(type=bool, default=False)
    def enabled(self):
        """
        Enable or disable spellchecking.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        if enabled and not self._enabled:
            self.enable()
        elif not enabled and self._enabled:
            self.disable()

    @GObject.Property(type=bool, default=False)
    def batched_rechecking(self):
        """
        Whether to enable batched rechecking of large buffers.
        """
        return self._batched_rechecking

    @batched_rechecking.setter
    def batched_rechecking(self, val):
        self._batched_rechecking = val

    @GObject.Property(type=str, default=",")
    def extra_chars(self):
        """
        Fetch the list of extra characters beyond which words are extended.
        """
        return self._extra_chars

    @extra_chars.setter
    def extra_chars(self, chars):
        """
        Set the list of extra characters beyond which words are extended.

        :param val: String containing list of characters
        """
        self._extra_chars = chars

    def buffer_initialize(self):
        """
        Initialize the GtkTextBuffer associated with the GtkTextView. If you
        have associated a new GtkTextBuffer with the GtkTextView call this
        method.
        """
        self._buffer = self._view.get_buffer()
        self._buffer.connect("insert-text", self._before_text_insert)
        self._buffer.connect_after("insert-text", self._after_text_insert)
        self._buffer.connect_after("delete-range", self._range_delete)
        self._buffer.connect_after("mark-set", self._mark_set)
        start = self._buffer.get_bounds()[0]
        self._marks = {
            "insert-start": SpellChecker._Mark(
                self._buffer,
                "{}-insert-start".format(self._prefix),
                start,
                self._iter_worker,
            ),
            "insert-end": SpellChecker._Mark(
                self._buffer,
                "{}-insert-end".format(self._prefix),
                start,
                self._iter_worker,
            ),
            "click": SpellChecker._Mark(
                self._buffer, "{}-click".format(self._prefix), start, self._iter_worker
            ),
        }
        self._table = self._buffer.get_tag_table()

        # JS: Don't add "misspelled" tag if it's already present.
        misspelled_tag_name = "{}-misspelled".format(self._prefix)
        self._misspelled = self._table.lookup(misspelled_tag_name)
        if not self._misspelled:
            self._misspelled = Gtk.TextTag.new(misspelled_tag_name)
            self._misspelled.set_property("underline", 4)
            self._table.add(self._misspelled)

        self.ignored_tags = []

        def tag_added(tag, *args):
            if hasattr(tag, "spell_check") and not tag.spell_check:
                self.ignored_tags.append(tag)

        def tag_removed(tag, *args):
            if tag in self.ignored_tags:
                self.ignored_tags.remove(tag)

        self._table.connect("tag-added", tag_added)
        self._table.connect("tag-removed", tag_removed)
        self._table.foreach(tag_added, None)
        self.no_spell_check = self._table.lookup("no-spell-check")
        if not self.no_spell_check:
            self.no_spell_check = Gtk.TextTag.new("no-spell-check")
            self._table.add(self.no_spell_check)
        self.recheck()

    def recheck(self):
        """
        Rechecks the spelling of the whole text.
        """
        start, end = self._buffer.get_bounds()

        if self._batched_rechecking and end.get_offset() > _BATCHING_THRESHOLD_CHARS:
            start_mark = self._buffer.create_mark(None, start)
            self._continue_batched_recheck(start_mark)
        else:
            self.check_range(start, end, True)

    def disable(self):
        """
        Disable spellchecking.
        """
        self._enabled = False
        start, end = self._buffer.get_bounds()
        self._buffer.remove_tag(self._misspelled, start, end)

    def enable(self):
        """
        Enable spellchecking.
        """
        self._enabled = True
        self.recheck()

    def append_filter(self, regex, filter_type):
        """
        Append a new filter to the filter list. Filters are useful to ignore
        some misspelled words based on regular expressions.

        :param regex: The regex used for filtering.
        :param filter_type: The type of the filter.

        Filter Types:

        :const:`SpellChecker.FILTER_WORD`: The regex must match the whole word
            you want to filter. The word separation is done by Pango's word
            separation algorithm so, for example, urls won't work here because
            they are split in many words.

        :const:`SpellChecker.FILTER_LINE`: If the expression you want to match
            is a single line expression use this type. It should not be an open
            end expression because then the rest of the line with the text you
            want to filter will become correct.

        :const:`SpellChecker.FILTER_TEXT`: Use this if you want to filter
           multiline expressions. The regex will be compiled with the
           `re.MULTILINE` flag. Same with open end expressions apply here.
        """
        self._filters[filter_type].append(regex)
        if filter_type == SpellChecker.FILTER_TEXT:
            self._regexes[filter_type] = re.compile(
                "|".join(self._filters[filter_type]), re.MULTILINE
            )
        else:
            self._regexes[filter_type] = re.compile(
                "|".join(self._filters[filter_type])
            )

    def remove_filter(self, regex, filter_type):
        """
        Remove a filter from the filter list.

        :param regex: The regex which used for filtering.
        :param filter_type: The type of the filter.
        """
        self._filters[filter_type].remove(regex)
        if filter_type == SpellChecker.FILTER_TEXT:
            self._regexes[filter_type] = re.compile(
                "|".join(self._filters[filter_type]), re.MULTILINE
            )
        else:
            self._regexes[filter_type] = re.compile(
                "|".join(self._filters[filter_type])
            )

    def append_ignore_tag(self, tag):
        """
        Appends a tag to the list of ignored tags. A string will be automatic
        resolved into a tag object.

        :param tag: Tag object or tag name.
        """
        if isinstance(tag, str):
            tag = self._table.lookup(tag)
        self.ignored_tags.append(tag)

    def remove_ignore_tag(self, tag):
        """
        Removes a tag from the list of ignored tags. A string will be automatic
        resolved into a tag object.

        :param tag: Tag object or tag name.
        """
        if isinstance(tag, str):
            tag = self._table.lookup(tag)
        self.ignored_tags.remove(tag)

    def add_to_dictionary(self, word):
        """
        Adds a word to user's dictionary.

        :param word: The word to add.
        """
        self._dictionary.add_to_pwl(word)
        self.recheck()

    def ignore_all(self, word):
        """
        Ignores a word for the current session.

        :param word: The word to ignore.
        """
        self._dictionary.add_to_session(word)
        self.recheck()

    def check_range(self, start, end, force_all=False):
        """
        Checks a specified range between two GtkTextIters.

        :param start: Start iter - checking starts here.
        :param end: End iter - checking ends here.
        """
        logger.debug(
            "Check range called with range %d:%d to %d:%d and force all set to %s.",
            start.get_line(),
            start.get_line_offset(),
            end.get_line(),
            end.get_line_offset(),
            force_all,
        )
        if not self._enabled:
            return
        start = start.copy()
        end = end.copy()
        if self._iter_worker.inside_word(end):
            self._iter_worker.forward_word_end(end)
        if self._iter_worker.inside_word(start) or self._iter_worker.ends_word(start):
            self._iter_worker.backward_word_start(start)
        if not self._iter_worker.starts_word(start):
            self._iter_worker.forward_word_end(start)
            self._iter_worker.backward_word_start(start)
        self._buffer.remove_tag(self._misspelled, start, end)
        cursor = self._buffer.get_iter_at_mark(self._buffer.get_insert())
        precursor = cursor.copy()
        precursor.backward_char()
        highlight = cursor.has_tag(self._misspelled) or precursor.has_tag(
            self._misspelled
        )
        word_start = start.copy()
        while word_start.compare(end) < 0:
            word_end = word_start.copy()
            self._iter_worker.forward_word_end(word_end)
            in_word = (word_start.compare(cursor) < 0) and (
                cursor.compare(word_end) <= 0
            )
            if in_word and not force_all:
                if highlight:
                    self._check_word(word_start, word_end)
                else:
                    self._deferred_check = True
            else:
                self._check_word(word_start, word_end)
                self._deferred_check = False
            self._iter_worker.forward_word_end(word_end)
            self._iter_worker.backward_word_start(word_end)
            if word_start.equal(word_end):
                break
            word_start = word_end.copy()

    def populate_menu(self, menu):
        """
        Populate the provided menu with spelling items.

        :param menu: The menu to populate.
        """
        # In GTK 4 our existing menu needs to be cleared, providing for disabling
        if not _IS_GTK3:
            menu.remove_all()

        if not self._enabled:
            return

        if _IS_GTK3:
            separator = Gtk.SeparatorMenuItem.new()
            separator.show()
            menu.prepend(separator)
            languages = Gtk.MenuItem.new_with_label(_("Languages"))
            languages.set_submenu(self._get_languages_menu())
            languages.show_all()
            menu.prepend(languages)
        else:
            menu.append_item(self._get_languages_menu())

        if self._marks["click"].inside_word:
            start, end = self._marks["click"].word
            if start.has_tag(self._misspelled):
                word = self._buffer.get_text(start, end, False)
                items = self._suggestion_menu(word)
                if self.collapse:
                    menu_label = _("Suggestions")
                    if _IS_GTK3:
                        suggestions = Gtk.MenuItem.new_with_label(menu_label)
                        submenu = Gtk.Menu.new()
                    else:
                        suggestions = Gio.MenuItem.new(menu_label, None)
                        submenu = Gio.Menu.new()
                    for item in items:
                        if _IS_GTK3:
                            submenu.append(item)
                        else:
                            submenu.append_item(item)
                    suggestions.set_submenu(submenu)
                    if _IS_GTK3:
                        suggestions.show_all()
                        menu.prepend(suggestions)
                    else:
                        menu.prepend_item(suggestions)
                else:
                    items.reverse()
                    for item in items:
                        if _IS_GTK3:
                            menu.prepend(item)
                            menu.show_all()
                        else:
                            menu.prepend_item(item)

    def move_click_mark(self, iter):
        """
        Move the "click" mark, used to determine the word being checked.

        :param iter: TextIter for the new location
        """
        self._marks["click"].move(iter)

    def _gtk4_setup_actions(self) -> None:
        action_group = Gio.SimpleActionGroup.new()

        action = Gio.SimpleAction.new("ignore-all", GLib.VariantType("s"))
        action.connect(
            "activate", lambda _action, word: self.ignore_all(word.get_string())
        )
        action_group.add_action(action)

        action = Gio.SimpleAction.new("add-to-dictionary", GLib.VariantType("s"))
        action.connect(
            "activate", lambda _action, word: self.add_to_dictionary(word.get_string())
        )
        action_group.add_action(action)

        action = Gio.SimpleAction.new("replace-word", GLib.VariantType("s"))
        action.connect(
            "activate",
            lambda _action, suggestion: self._replace_word(suggestion.get_string()),
        )
        action_group.add_action(action)

        language = Gio.PropertyAction.new("language", self, "language")
        action_group.add_action(language)

        self._view.insert_action_group("spelling", action_group)

    def _get_languages_menu(self):
        if _IS_GTK3:
            return self._build_languages_menu()
        else:
            if self._languages_menu is None:
                self._languages_menu = self._build_languages_menu()
            return self._languages_menu

    def _build_languages_menu(self):
        if _IS_GTK3:

            def _set_language(item, code):
                self.language = code

            menu = Gtk.Menu.new()
            group = []
            connect = []
        else:
            menu = Gio.Menu.new()

        for code, name in self.languages:
            if _IS_GTK3:
                item = Gtk.RadioMenuItem.new_with_label(group, name)
                group.append(item)
                if code == self.language:
                    item.set_active(True)
                connect.append((item, code))
                menu.append(item)
            else:
                item = Gio.MenuItem.new(name, None)
                item.set_action_and_target_value(
                    "spelling.language", GLib.Variant.new_string(code)
                )
                menu.append_item(item)
        if _IS_GTK3:
            for item, code in connect:
                item.connect("activate", _set_language, code)
            return menu
        else:
            return Gio.MenuItem.new_submenu(_("Languages"), menu)

    def _suggestion_menu(self, word):
        menu = []
        suggestions = self._dictionary.suggest(word)
        if not suggestions:
            # Show GTK 3 no suggestions item (removed for GTK 4)
            if _IS_GTK3:
                item = Gtk.MenuItem.new()
                label = Gtk.Label.new("")
                try:
                    label.set_halign(Gtk.Align.LEFT)
                except AttributeError:
                    label.set_alignment(0.0, 0.5)
                label.set_markup("<i>{text}</i>".format(text=_("(no suggestions)")))
                item.add(label)
                menu.append(item)
        else:
            for suggestion in suggestions:
                if _IS_GTK3:
                    item = Gtk.MenuItem.new()
                    label = Gtk.Label.new("")
                    label.set_markup("<b>{text}</b>".format(text=suggestion))
                    try:
                        label.set_halign(Gtk.Align.LEFT)
                    except AttributeError:
                        label.set_alignment(0.0, 0.5)
                    item.add(label)

                    def _make_on_activate(word):
                        return lambda *args: self._replace_word(word)

                    item.connect("activate", _make_on_activate(suggestion))
                else:
                    escaped = suggestion.replace("'", "\\'")
                    item = Gio.MenuItem.new(
                        suggestion, f"spelling.replace-word('{escaped}')"
                    )
                menu.append(item)
        add_to_dict_menu_label = _("Add to Dictionary")
        word_escaped = word.replace("'", "\\'")
        if _IS_GTK3:
            menu.append(Gtk.SeparatorMenuItem.new())
            item = Gtk.MenuItem.new_with_label(add_to_dict_menu_label)
            item.connect("activate", lambda *args: self.add_to_dictionary(word))
        else:
            item = Gio.MenuItem.new(
                add_to_dict_menu_label, f"spelling.add-to-dictionary('{word_escaped}')"
            )
        menu.append(item)
        ignore_menu_label = _("Ignore All")
        if _IS_GTK3:
            item = Gtk.MenuItem.new_with_label(ignore_menu_label)
            item.connect("activate", lambda *args: self.ignore_all(word))
        else:
            item = Gio.MenuItem.new(
                ignore_menu_label, f"spelling.ignore-all('{word_escaped}')"
            )
        menu.append(item)
        return menu

    def _click_move_popup(self, *args):
        self.move_click_mark(self._buffer.get_iter_at_mark(self._buffer.get_insert()))
        return False

    def _click_move_button(self, widget, event):
        if event.button == 3:
            self._move_mark_for_input(event.x, event.y)
        return False

    def _move_mark_for_input(self, input_x, input_y):
        if self._deferred_check:
            self._check_deferred_range(True)
        x, y = self._view.window_to_buffer_coords(2, int(input_x), int(input_y))
        iter = self._view.get_iter_at_location(x, y)
        if isinstance(iter, tuple):
            iter = iter[1]
        self.move_click_mark(iter)

    def _gtk4_on_textview_click(self, click, n_press, x, y) -> None:
        if n_press != 1 or click.get_current_button() != 3:
            return

        self._move_mark_for_input(x, y)
        self.populate_menu(self._spelling_menu)

    def _before_text_insert(self, textbuffer, location, text, length):
        self._marks["insert-start"].move(location)

    def _after_text_insert(self, textbuffer, location, text, length):
        start = self._marks["insert-start"].iter
        self.check_range(start, location)
        self._marks["insert-end"].move(location)

    def _range_delete(self, textbuffer, start, end):
        self.check_range(start, end)

    def _mark_set(self, textbuffer, location, mark):
        if mark == self._buffer.get_insert() and self._deferred_check:
            self._check_deferred_range(False)

    def _replace_word(self, new_word):
        start, end = self._marks["click"].word
        old_word = start.get_text(end)
        offset = start.get_offset()
        self._buffer.begin_user_action()
        self._buffer.delete(start, end)
        self._buffer.insert(self._buffer.get_iter_at_offset(offset), new_word)
        self._buffer.end_user_action()
        self._dictionary.store_replacement(old_word, new_word)

    def _check_deferred_range(self, force_all):
        start = self._marks["insert-start"].iter
        end = self._marks["insert-end"].iter
        self.check_range(start, end, force_all)

    def _check_word(self, start, end):
        if start.has_tag(self.no_spell_check):
            return
        for tag in self.ignored_tags:
            if start.has_tag(tag):
                return
        word = self._buffer.get_text(start, end, False).strip()
        logger.debug(
            "Checking word %s in range %d:%d to %d:%d.",
            word,
            start.get_line(),
            start.get_line_offset(),
            end.get_line(),
            end.get_line_offset(),
        )
        if not word:
            return
        if len(self._filters[SpellChecker.FILTER_WORD]):
            if self._regexes[SpellChecker.FILTER_WORD].match(word):
                return
        if len(self._filters[SpellChecker.FILTER_LINE]):
            if _IS_GTK3:
                line_start = self._buffer.get_iter_at_line(start.get_line())
            else:
                _success, line_start = self._buffer.get_iter_at_line(start.get_line())
            line_end = end.copy()
            line_end.forward_to_line_end()
            line = self._buffer.get_text(line_start, line_end, False)
            for match in self._regexes[SpellChecker.FILTER_LINE].finditer(line):
                if match.start() <= start.get_line_offset() <= match.end():
                    if _IS_GTK3:
                        start = self._buffer.get_iter_at_line_offset(
                            start.get_line(), match.start()
                        )
                        end = self._buffer.get_iter_at_line_offset(
                            start.get_line(), match.end()
                        )
                    else:
                        # Success is not verified here as the locations come directly
                        # from the buffer
                        _success, start = self._buffer.get_iter_at_line_offset(
                            start.get_line(), match.start()
                        )
                        _success, end = self._buffer.get_iter_at_line_offset(
                            start.get_line(), match.end()
                        )
                    self._buffer.remove_tag(self._misspelled, start, end)
                    return
        if len(self._filters[SpellChecker.FILTER_TEXT]):
            text_start, text_end = self._buffer.get_bounds()
            text = self._buffer.get_text(text_start, text_end, False)
            for match in self._regexes[SpellChecker.FILTER_TEXT].finditer(text):
                if match.start() <= start.get_offset() <= match.end():
                    start = self._buffer.get_iter_at_offset(match.start())
                    end = self._buffer.get_iter_at_offset(match.end())
                    self._buffer.remove_tag(self._misspelled, start, end)
                    return
        if not self._dictionary.check(word):
            self._buffer.apply_tag(self._misspelled, start, end)

    def _continue_batched_recheck(self, start_mark):
        if start_mark.get_buffer() != self._buffer:
            return
        start = self._buffer.get_iter_at_mark(start_mark)
        self._buffer.delete_mark(start_mark)

        if not self._enabled:
            return

        end = start.copy()
        end.forward_chars(_BATCH_SIZE_CHARS)
        self._iter_worker.forward_word_end(end)

        self.check_range(start, end, True)

        if not end.is_end():
            end.forward_char()
            start_mark = self._buffer.create_mark(None, end)
            GLib.idle_add(self._continue_batched_recheck, start_mark)