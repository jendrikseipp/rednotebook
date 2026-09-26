"""Regression tests through the same conversion entry point as preview/export."""

from html import escape
from html.parser import HTMLParser

import pytest

from rednotebook.util.markup import convert


@pytest.mark.parametrize("target", ["html", "tex", "txt"])
def test_local_attachments(tmp_path, target):
    image = tmp_path / "photo.png"
    document = tmp_path / "notes.txt"
    image.touch()
    document.touch()
    source = f"![photo]({image.as_uri()}?50)\n\n[notes]({document.as_uri()})"
    output = convert(source, target, tmp_path)
    if target == "html":
        assert f'src="{image.as_uri()}"' in output
        assert 'width="50"' in output
        assert f'href="{document.as_uri()}"' in output
    elif target == "tex":
        assert f'\\includegraphics[width=50px]{{"{image.as_posix()}"}}' in output
        assert f"\\href{{run:{document.as_posix()}}}{{notes}}" in output
    else:
        assert f"[{image.as_uri()}?50]" in output
        assert f"notes ({document.as_uri()})" in output


@pytest.mark.parametrize(
    "source,filename,attribute",
    [
        ('![photo](photo.png "caption")', "photo.png", "src"),
        ("![photo][pic]\n\n[pic]: photo.png", "photo.png", "src"),
        ("![photo](<my photo.png>)", "my photo.png", "src"),
        ("![photo](my%20photo.png)", "my photo.png", "src"),
        ("![photo](photo(1).png)", "photo(1).png", "src"),
        ('[notes](notes.txt "caption")', "notes.txt", "href"),
        ("[notes][doc]\n\n[doc]: notes.txt", "notes.txt", "href"),
        ("![photo](file://photo.png)", "photo.png", "src"),
    ],
)
def test_relative_attachment_syntax(tmp_path, source, filename, attribute):
    attachment = tmp_path / filename
    attachment.touch()
    output = convert(source, "html", tmp_path)
    assert f'{attribute}="{attachment.as_uri()}"' in output


@pytest.mark.parametrize(
    "source,expected",
    [
        ("[2026-09-26](https://example.org)", '<a href="https://example.org">2026-09-26</a>'),
        (
            "![trip 2026-09-26](https://example.org/photo.png)",
            '<img src="https://example.org/photo.png" alt="trip 2026-09-26">',
        ),
        (
            "[2026-09-26][report]\n\n[report]: https://example.org",
            '<a href="https://example.org">2026-09-26</a>',
        ),
        (
            "[site](https://example.org) and [meeting 2026-09-26]",
            '<a href="https://example.org">site</a> and <a href="#2026-09-26">meeting</a>',
        ),
        (
            "[[2026-09-26]](https://example.org)",
            '<a href="https://example.org">[2026-09-26]</a>',
        ),
    ],
)
def test_entry_references_do_not_rewrite_markdown_links(tmp_path, source, expected):
    assert expected in convert(source, "html", tmp_path)


@pytest.mark.parametrize("wrapper", ["`{}`", "```\n{}\n```", "~~~\n{}\n~~~", "    {}"])
@pytest.mark.parametrize("literal", ["[2026-09-26]", r"\(x\)", "[notes](notes.txt)"])
def test_preprocessing_preserves_literal_code(tmp_path, wrapper, literal):
    (tmp_path / "notes.txt").touch()
    source = wrapper.format(literal)
    output = convert(source, "html", tmp_path)
    newline = "" if wrapper == "`{}`" else "\n"
    assert f"<code>{escape(literal)}{newline}</code>" in output
    assert "MathJax included" not in output
    assert "<a href=" not in output


@pytest.mark.parametrize("delimiter", [("$", "$"), ("$$", "$$"), (r"\(", r"\)"), (r"\[", r"\]")])
def test_math_is_html_text(tmp_path, delimiter):
    class FormulaParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.data = []

        def handle_data(self, data):
            self.data.append(data)

    formula = "x<y>z & w"
    output = convert(delimiter[0] + formula + delimiter[1], "html", tmp_path)
    parser = FormulaParser()
    parser.feed(output)
    assert formula in "".join(parser.data)
    assert "MathJax included" in output


@pytest.mark.parametrize(
    "source", ["[Example](https://example.com)", "[Example https://example.com]"]
)
def test_plain_export_keeps_named_link_destinations(tmp_path, source):
    assert convert(source, "txt", tmp_path) == "Example (https://example.com)\n"


@pytest.mark.parametrize("source", ["https://example.com", "<https://example.com>"])
def test_plain_export_does_not_repeat_autolink(tmp_path, source):
    assert convert(source, "txt", tmp_path) == "https://example.com\n"


@pytest.mark.parametrize(
    "scheme", ["javascript:alert(1)", "vbscript:msgbox(1)", "data:text/html,hello"]
)
def test_allowing_local_files_does_not_allow_executable_urls(tmp_path, scheme):
    assert "<a href=" not in convert(f"[link]({scheme})", "html", tmp_path)


@pytest.mark.parametrize("target", ["html", "tex", "txt"])
def test_formatted_entry_reference(tmp_path, target):
    output = convert("[**meeting** 2026-09-26]", target, tmp_path)
    if target == "html":
        assert '<a href="#2026-09-26"><strong>meeting</strong></a>' in output
    elif target == "tex":
        assert r"\textbf{meeting} (2026-09-26)" in output
    else:
        assert output == "meeting (2026-09-26)\n"


@pytest.mark.parametrize("target", ["html", "tex", "txt"])
def test_display_math_with_blank_lines(tmp_path, target):
    output = convert("\\[\nx < y\n\nz\n\\]", target, tmp_path)
    if target == "html":
        assert "MathJax included" in output
        assert "x &lt; y\n\nz" in output
    elif target == "tex":
        assert "$$\nx < y\n\nz\n$$" in output
    else:
        assert output == "x < y\n\nz\n"


@pytest.mark.parametrize("target", ["tex", "txt"])
def test_code_exports_preserve_blank_lines(tmp_path, target):
    output = convert("```\na\n\n\nb\n```", target, tmp_path)
    assert "a\n\n\nb" in output


def test_image_label_and_title_survive_escaping(tmp_path):
    output = convert(
        r'![a \] caption **bold** and `code`](https://example.org/photo.png "my title")',
        "html",
        tmp_path,
    )
    assert 'alt="a ] caption bold and code"' in output
    assert 'title="my title"' in output


def test_html_document_title_is_escaped(tmp_path):
    output = convert("entry", "html", tmp_path, {"title": "a < b & c"})
    assert "<title>a &lt; b &amp; c</title>" in output
