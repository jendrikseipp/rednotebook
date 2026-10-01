"""Verify that the editor's syntax-highlighting patterns match Markdown and
RedNotebook constructs.

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
        ("atx-header", "#"),
        ("atx-header", "   ## Indented heading"),
    ],
)
def test_pattern_matches(context_id, text):
    assert _search(context_id, text), f"{context_id} should match {text!r}"


@pytest.mark.parametrize(
    "context_id,text",
    [
        # A plain hashtag-less number is not a hashtag.
        ("hashtag", "issue 1234 done"),
        # A hashtag at the start of a line is not a heading.
        ("atx-header", "#work was fine"),
        ("atx-header", "####### Too many"),
    ],
)
def test_pattern_rejects(context_id, text):
    assert not _search(context_id, text), f"{context_id} should not match {text!r}"


def test_expected_contexts_present():
    for cid in ["atx-header", "strikethrough", "hashtag", "color", "entry-reference"]:
        assert cid in PATTERNS


def test_no_txt2tags_contexts():
    assert not [cid for cid in PATTERNS if cid.startswith("t2t")]


def test_fenced_code_end_matches_its_start():
    # The end pattern refers back to the opening fence, e.g. "````" or "~~~".
    context = next(
        c for c in ET.parse(LANG_FILE).iter("context") if c.get("id") == "3-backticks-code-span"
    )
    assert re.match(context.find("start").text, "````python")
    assert re.match(context.find("start").text, "~~~")
    assert "\\%{1@start}" in context.find("end").text
