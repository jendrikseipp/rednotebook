"""Verify that the editor's syntax-highlighting patterns match both Markdown
and legacy txt2tags constructs.

GtkSourceView applies these regexes (in GRegex/PCRE syntax) line by line. We
cannot easily exercise the highlighter headlessly, but we can read the patterns
straight from ``markdown.lang`` and check that they match the constructs they
are meant to highlight (and reject look-alikes). This guards against the
patterns silently breaking.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


LANG_FILE = Path(__file__).parent.parent / "rednotebook" / "files" / "markdown.lang"


def _patterns():
    """Map each context id to the regex string of its direct <match> element.

    Patterns are kept as strings (not compiled) because some Markdown contexts
    use variable-width look-behinds that GRegex accepts but Python's ``re``
    rejects. Only the patterns we actually test are compiled, on demand.
    """
    tree = ET.parse(LANG_FILE)
    patterns = {}
    for context in tree.iter("context"):
        cid = context.get("id")
        match = context.find("match")
        if cid and match is not None and match.text:
            # ElementTree already decodes &lt; etc. for us.
            flags = re.VERBOSE if match.get("extended") == "true" else 0
            patterns[cid] = (match.text.strip(), flags)
    return patterns


PATTERNS = _patterns()


def _search(context_id, text):
    pattern, flags = PATTERNS[context_id]
    return re.search(pattern, text, flags)


@pytest.mark.parametrize(
    "context_id,text",
    [
        # Markdown.
        ("atx-header", "# Heading"),
        ("atx-header", "### Smaller heading"),
        ("asterisks-strong-emphasis", "a **bold** b"),
        ("asterisks-emphasis", "a *italic* b"),
        ("underscores-strong-emphasis", "a __bold__ b"),
        ("strikethrough", "a ~~gone~~ b"),
        ("inline-link", "see [text](http://x.com)"),
        ("inline-image", "![alt](pic.png)"),
        ("list", "- item"),
        ("list", "1. item"),
        # RedNotebook constructs.
        ("hashtag", "a #work tag"),
        ("color", "{important|color:red}"),
        ("entry-reference", "[2019-02-14]"),
        ("named-entry-reference", "[my day 2019-02-14]"),
        # txt2tags constructs.
        ("t2t-italic", "a //italic// b"),
        ("t2t-strikethrough", "a --gone-- b"),
        ("t2t-heading", "= Title ="),
        ("t2t-heading", "=== Sub ==="),
        ("t2t-heading", "== Clouds ==[anchor]"),
        ("t2t-image", "[foo.png]"),
        ("t2t-image-quoted", '[""/path to/foo"".png?50]'),
        ("t2t-link", "[heise http://heise.de]"),
        ("t2t-link-quoted", '[my file ""file:///home/me/f.txt""]'),
    ],
)
def test_pattern_matches(context_id, text):
    assert _search(context_id, text), f"{context_id} should match {text!r}"


@pytest.mark.parametrize(
    "context_id,text",
    [
        # A bare URL must not be mistaken for //italic//.
        ("t2t-italic", "visit http://example.com today"),
        # A horizontal rule must not be mistaken for --strikethrough--.
        ("t2t-strikethrough", "--------------------"),
        # A plain hashtag-less number is not a hashtag.
        ("hashtag", "issue 1234 done"),
        # A Markdown heading is not a txt2tags heading.
        ("t2t-heading", "# Markdown heading"),
    ],
)
def test_pattern_rejects(context_id, text):
    assert not _search(context_id, text), f"{context_id} should not match {text!r}"


def test_expected_contexts_present():
    # Both Markdown and txt2tags contexts must exist.
    for cid in [
        "atx-header",
        "strikethrough",
        "hashtag",
        "color",
        "entry-reference",
        "t2t-italic",
        "t2t-strikethrough",
        "t2t-heading",
        "t2t-link",
        "t2t-link-quoted",
        "t2t-image",
        "t2t-image-quoted",
    ]:
        assert cid in PATTERNS
