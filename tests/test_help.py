"""The help text, the example entries and the templates use Markdown."""

import re

import pytest

from rednotebook import help
from rednotebook.util.markdownmarkup import render


TXT2TAGS = [
    re.compile(r"(?m)^(=+|\++) .* \1\s*(\[[\w-]*\])?$"),  # Titles
    re.compile(r"\[[^\]\n]+ (https?|ftp)://[^\]\s]+\]"),  # Named links
    re.compile(r'\[[^\]\n]* ?""[^"\n]+""(\.\w+)?\]'),  # Quoted links and images
    re.compile(r"(?m)^\+ "),  # Numbered lists
    re.compile(r"(?<![:/])//\w[^/\n]*\w//"),  # Italic
    re.compile(r"(?m)^={20,}$"),  # Horizontal rules
]


def texts():
    from rednotebook import templates

    yield "help", help.help_text
    yield "welcome", help.complete_welcome_text
    yield "multiple entries", help.multiple_entries_day["text"]
    for name in ["example_text", "meeting", "journey", "call", "personal"]:
        yield name, getattr(templates, name)


@pytest.mark.parametrize("name, text", list(texts()))
def test_texts_use_markdown(name, text):
    for pattern in TXT2TAGS:
        match = pattern.search(text)
        assert not match, f"{name} contains txt2tags markup: {match.group()!r}"


def test_help_renders_all_sections():
    html = render(help.help_text, "html", {"toc": 1})
    for section in [
        "format",
        "hashtags",
        "entry-references",
        "keyboard-shortcuts",
        "math-formulas",
    ]:
        assert f'href="#{section}"' in html
    # Placeholders like <RedNotebook Dir> must be visible.
    assert "&lt;RedNotebook Dir&gt;" in html
    assert "3\\.50\\?" in html
    assert "<table>" in html
