"""Exercise editor actions without opening GTK windows."""

import html
from html.parser import HTMLParser
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import unquote, urlsplit

import gi
import pytest
from markdown_it import MarkdownIt


gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from rednotebook.gui.insert_menu import InsertMenu
from rednotebook.util import markup, urls


@pytest.fixture
def editor_class(monkeypatch):
    # Querying the desktop theme can connect to a display during import.
    monkeypatch.setattr(Gtk.Settings, "get_default", lambda: None)
    from rednotebook.gui.editor import Editor

    return Editor


def inline_tokens(text):
    parser = MarkdownIt()
    # Check the inserted syntax independently of RedNotebook's URI policy.
    parser.validateLink = lambda url: True
    return [child for token in parser.parse(text) for child in (token.children or [])]


def inserted_target(text, token_type, attribute):
    tokens = [token for token in inline_tokens(text) if token.type == token_type]
    assert len(tokens) == 1, text
    return tokens[0].attrGet(attribute)


def rendered_element(text, tag):
    elements = []
    parser = HTMLParser()
    parser.handle_starttag = lambda name, attrs: elements.append((name, dict(attrs)))
    parser.feed(markup.convert(text, "html", "/tmp"))
    matches = [attrs for name, attrs in elements if name == tag]
    assert len(matches) == 1
    return matches[0]


def menu_with_widgets(widgets, selection=""):
    editor = Mock()
    editor.get_selected_text.return_value = selection
    builder = Mock()
    builder.get_object.side_effect = widgets.__getitem__
    return SimpleNamespace(
        main_window=SimpleNamespace(
            day_text_field=editor,
            builder=builder,
            journal=SimpleNamespace(
                dirs=SimpleNamespace(last_pic_dir="", last_file_dir=""),
            ),
        )
    )


@pytest.mark.parametrize(
    "filename", ["my report.txt", "report).txt", "report[1].txt", "report#1?.txt", "report%20.txt"]
)
def test_insert_file_escapes_filename(filename):
    chooser = Mock()
    chooser.run.return_value = Gtk.ResponseType.OK
    chooser.get_current_folder.return_value = None
    chooser.get_filename.return_value = "/tmp/" + filename
    menu = menu_with_widgets({"file_chooser": chooser})

    text = InsertMenu.on_insert_file.__wrapped__(menu, "")

    target = urlsplit(inserted_target(text, "link_open", "href"))
    assert rendered_element(text, "a")["href"] == inserted_target(text, "link_open", "href")
    assert unquote(target.path).endswith("/tmp/" + filename)
    assert not target.query
    assert not target.fragment
    assert (
        "".join(token.content for token in inline_tokens(text) if token.type == "text") == filename
    )


def test_insert_image_escapes_destination_and_label(monkeypatch):
    for name in ("FileFilter", "Box", "Label"):
        monkeypatch.setattr(Gtk, name, Mock())
    width_entry = Mock()
    width_entry.get_text.return_value = "80"
    monkeypatch.setattr(Gtk, "Entry", Mock(return_value=width_entry))
    chooser = Mock()
    chooser.run.return_value = Gtk.ResponseType.OK
    chooser.get_current_folder.return_value = None
    chooser.get_filenames.return_value = ["/tmp/my photo).jpg"]
    label = r"a ] caption \ ending"
    menu = menu_with_widgets({"picture_chooser": chooser}, label)

    text = InsertMenu.on_insert_pic.__wrapped__(menu, label)

    expected = urls.get_local_url("/tmp/my photo).jpg") + "?80"
    assert inserted_target(text, "image", "src") == expected
    assert inline_tokens(text)[0].children[0].content == label
    assert rendered_element(text, "img")["src"] == expected.rsplit("?", 1)[0]


def test_insert_link_escapes_destination_and_label():
    dialog, location, name = Mock(), Mock(), Mock()
    dialog.run.return_value = Gtk.ResponseType.OK
    location.get_text.return_value = "https://example.org/a path)?q=%20&x=1#part"
    label = r"a ] link \ ending"
    name.get_text.return_value = label
    menu = menu_with_widgets(
        {"link_creator": dialog, "link_location_entry": location, "link_name_entry": name},
        label,
    )

    text = InsertMenu.on_insert_link.__wrapped__(menu, label)

    assert inserted_target(text, "link_open", "href") == (
        "https://example.org/a%20path%29?q=%20&x=1#part"
    )
    assert "".join(token.content for token in inline_tokens(text) if token.type == "text") == label


@pytest.mark.parametrize(
    "directory,name",
    [("/tmp/", "my%20file)"), ("/C:/Users/Sam/", "my%23file%3F"), ("/tmp/", "my%2520file")],
)
@pytest.mark.parametrize(
    "extension,token_type,attribute", [("jpg", "image", "src"), ("pdf", "link_open", "href")]
)
def test_drop_escapes_decoded_uri(editor_class, extension, token_type, attribute, directory, name):
    editor = Mock()
    editor.day_text_view.get_iter_at_location.return_value = (True, None)
    selection = Mock()
    selection.get_text.return_value = f"file://{directory}{name}.{extension}"

    editor_class.on_drag_data_received(editor, None, Mock(), 0, 0, selection, None, 0)

    text = editor.insert.call_args.args[0]
    expected = f"file://{directory}{name.replace(')', '%29')}.{extension}"
    assert inserted_target(text, token_type, attribute) == expected
    assert rendered_element(text, "img" if token_type == "image" else "a")[attribute] == expected


@pytest.mark.parametrize("whole_selection", [False, True])
@pytest.mark.parametrize(
    "initial,format_,expected",
    [
        ("**word**", "italic", "***word***"),
        ("*word*", "bold", "***word***"),
        ("***word***", "italic", "***word***"),
        ("***word***", "bold", "***word***"),
    ],
)
def test_combine_emphasis(editor_class, initial, format_, expected, whole_selection):
    start = 0 if whole_selection else initial.index("word")
    end = len(initial) if whole_selection else start + 4
    editor = Mock()
    editor.get_selected_text.return_value = initial[start:end]
    editor.get_text_left_of_selection.side_effect = lambda n: initial[max(0, start - n) : start]
    editor.get_text_right_of_selection.side_effect = lambda n: initial[end : end + n]
    editor._get_markups.side_effect = lambda kind, text: editor_class._get_markups(
        editor, kind, text
    )

    editor_class.apply_format(editor, format_)

    replacement = "".join(editor.replace_selection_and_highlight.call_args.args)
    assert initial[:start] + replacement + initial[end:] == expected
    assert "<em><strong>word</strong></em>" in markup.convert(expected, "html", "/tmp")


@pytest.mark.parametrize(
    "selection",
    ["one `two` three", "a `b`", "`a` and b", "before\n```\ninside\n```\nafter"],
)
def test_monospace_preserves_selected_backticks(editor_class, selection):
    editor = Mock()
    editor.get_selected_text.return_value = selection
    editor.get_text_left_of_selection.return_value = ""
    editor.get_text_right_of_selection.return_value = ""
    editor._get_markups.side_effect = lambda kind, text: editor_class._get_markups(
        editor, kind, text
    )

    editor_class.apply_format(editor, "monospace")

    replacement = "".join(editor.replace_selection_and_highlight.call_args.args)
    result = markup.convert(replacement, "html", "/tmp")
    expected = html.escape(selection, quote=False)
    if "\n" in selection:
        expected += "\n"
    assert f"<code>{expected}</code>" in result


@pytest.mark.parametrize("selection", ["`word`", "``a `word` here``"])
def test_monospace_keeps_complete_code_span(editor_class, selection):
    editor = Mock()
    editor.get_selected_text.return_value = selection
    editor.get_text_left_of_selection.return_value = ""
    editor.get_text_right_of_selection.return_value = ""
    editor._get_markups.side_effect = lambda kind, text: editor_class._get_markups(
        editor, kind, text
    )

    editor_class.apply_format(editor, "monospace")

    assert "".join(editor.replace_selection_and_highlight.call_args.args) == selection


def test_windows_local_url_uses_uri_separators(monkeypatch):
    monkeypatch.setattr(urls, "IS_WIN", True)
    monkeypatch.setattr(urls, "LOCAL_FILE_PEFIX", "file:///")
    assert urls.get_local_url(r"C:\Users\Sam\my photo.jpg") == "file:///C:/Users/Sam/my%20photo.jpg"


def test_local_url_preserves_filename_characters():
    assert urls.get_local_url("/tmp/report#1?%20.txt").endswith("/tmp/report%231%3F%2520.txt")
    encoded = "file:///tmp/report%231%3F%2520.txt"
    assert urls.get_local_url(encoded) == encoded


def test_open_windows_file_url_decodes_percent_escapes_once(monkeypatch):
    monkeypatch.setattr(urls, "IS_WIN", True)
    monkeypatch.setattr(urls, "LOCAL_FILE_PEFIX", "file:///")
    startfile = Mock()
    monkeypatch.setattr(urls.os, "startfile", startfile, raising=False)

    urls.open_url("file:///C:/report%2520.txt")

    startfile.assert_called_once_with("file:///C:/report%2520.txt")


def test_markdown_destination_preserves_uri_delimiters():
    from rednotebook.util.markdownlinks import escape_destination

    assert escape_destination("https://[::1]/a b(c)<d>\\e?x=%20&y=1#part") == (
        "https://[::1]/a%20b%28c%29%3Cd%3E%5Ce?x=%20&y=1#part"
    )
