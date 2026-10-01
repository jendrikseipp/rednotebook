"""Preserve category source while rendering Markdown for the tag tree."""

from unittest.mock import Mock, patch

import gi
import pytest


gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from rednotebook.gui.categories import CategoriesTreeView
from rednotebook.util.pango_markup import convert_to_pango


@pytest.fixture
def categories():
    # The real TreeStore exercises persistence without requiring a display.
    with patch.multiple(
        "rednotebook.gui.categories.Gtk",
        Label=Mock(),
        TreeViewColumn=Mock(),
        CellRendererText=Mock(),
    ):
        with patch.object(CategoriesTreeView, "_get_context_menu", return_value=Mock()):
            return CategoriesTreeView(Mock(), Mock())


@pytest.mark.parametrize(
    "source",
    [
        'A "quoted" category',
        r"\*literal stars\*",
        r"\`literal backticks\`",
        "[reference](https://example.com)",
        "**bold** and *italic*",
        "<u>underlined</u>",
        "//legacy italic//",
        "&quot;entity spelling&quot;",
    ],
)
def test_category_source_survives_repeated_load_and_save(categories, source):
    content = {source: {r"\*literal entry\*": None, 'An "entry"': None}}
    for _ in range(3):
        categories.add_element(None, content)
        assert categories.get_day_content() == content
        category_iter = categories._get_category_iter(source)
        assert category_iter is not None
        assert categories.tree_store[category_iter][0] == convert_to_pango(source)
        categories.clear()


def test_adding_entries_reuses_original_category_name(categories):
    category = 'A "quoted" category'
    categories.add_entry(category, r"\*first\*")
    categories.add_entry(category, "[second](https://example.com)")
    assert categories.get_day_content() == {
        category: {r"\*first\*": None, "[second](https://example.com)": None}
    }
    assert categories.tree_store.iter_n_children(None) == 1


def test_category_editor_uses_original_source(categories):
    source = r'\*literal\* and "quoted"'
    categories.add_element(None, {source: None})
    category_iter = categories.tree_store.get_iter_first()
    editable = Mock()
    categories.on_editing_started(None, editable, categories.tree_store.get_path(category_iter))
    editable.set_text.assert_called_once_with(source)


def test_editing_updates_source_and_display(categories):
    categories.add_element(None, {"old": None})
    category_iter = categories.tree_store.get_iter_first()
    source = r'\*new\* and "quoted"'
    categories.edited_cb(
        None, categories.tree_store.get_path(category_iter), source, categories.tree_store
    )
    assert categories.get_day_content() == {source: None}
    assert categories.tree_store[category_iter][0] == convert_to_pango(source)


def test_formatting_updates_source_and_display(categories):
    categories.add_element(None, {"old": None})
    category_iter = categories.tree_store.get_iter_first()
    source = r"**\*literal\***"
    categories.set_iter_value(category_iter, source)
    assert categories.get_day_content() == {source: None}
    assert categories.tree_store[category_iter][0] == convert_to_pango(source)


def test_category_labels_do_not_use_diary_block_syntax():
    for source in ("% progress", "+ item", "= title =", "|| a | b |"):
        assert convert_to_pango(source) == source
