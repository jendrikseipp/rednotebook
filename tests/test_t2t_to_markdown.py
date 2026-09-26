import pytest

from rednotebook.util.markdownmarkup import render
from rednotebook.util.t2t_to_markdown import convert_to_markdown as c


class TestHeadings:
    def test_levels(self):
        assert c("= Title =") == "# Title"
        assert c("== Title ==") == "## Title"
        assert c("===== Title =====") == "##### Title"

    def test_heading_with_anchor(self):
        assert c("== Clouds ==[clouds]") == "## Clouds"

    def test_markdown_heading_untouched(self):
        assert c("# Already Markdown") == "# Already Markdown"

    def test_heading_with_inline_markup(self):
        assert c("== My //special// day ==") == "## My *special* day"


class TestInlineFormatting:
    def test_italic(self):
        assert c("//italic//") == "*italic*"

    def test_bold_unchanged(self):
        assert c("**bold**") == "**bold**"

    def test_underline(self):
        assert c("__underlined__") == "<u>underlined</u>"

    def test_strikethrough(self):
        assert c("--struck--") == "~~struck~~"

    def test_monospace(self):
        assert c("``code``") == "`code`"

    def test_combination(self):
        assert c("a //b// and **c** and --d--") == "a *b* and **c** and ~~d~~"

    def test_italic_does_not_touch_urls(self):
        assert c("see http://example.com now") == "see http://example.com now"


class TestHorizontalRule:
    def test_long_equals(self):
        assert c("====================") == "---"

    def test_long_dashes(self):
        assert c("--------------------") == "---"

    def test_short_dashes_untouched(self):
        # Three dashes is already a Markdown rule and must survive.
        assert c("---") == "---"

    def test_rule_after_text_gets_blank_line(self):
        # Without the blank line, "---" would turn "text" into a heading.
        assert c("text\n====================") == "text\n\n---"


class TestLists:
    def test_bullet_unchanged(self):
        assert c("- item") == "- item"

    def test_numbered(self):
        assert c("+ item") == "1. item"

    def test_indented_numbered(self):
        assert c("  + item") == "  1. item"

    def test_numbered_with_inline_markup(self):
        assert c("+ visit //grandma//") == "1. visit *grandma*"


class TestLinks:
    def test_named_web_link(self):
        assert c("[heise http://heise.de]") == "[heise](http://heise.de)"

    def test_quoted_link(self):
        assert c('[my file ""file:///home/me/f.txt""]') == "[my file](file:///home/me/f.txt)"

    def test_bare_url_unchanged(self):
        assert c("http://example.com") == "http://example.com"


class TestImages:
    def test_simple_image(self):
        assert c('[""/home/pic"".png]') == "![](/home/pic.png)"

    def test_image_with_width(self):
        assert c('[""/home/pic"".png?50]') == "![](/home/pic.png?50)"

    def test_named_image(self):
        assert c('[alt ""/home/pic"".jpg]') == "![alt](/home/pic.jpg)"


class TestLineBreak:
    def test_trailing_backslashes(self):
        assert c("First\\\\\nSecond") == "First  \nSecond"

    def test_backslashes_midline_unchanged(self):
        assert c("First\\\\Second") == "First\\\\Second"


class TestFencedCodeIsPreserved:
    def test_no_inline_conversion_in_fence(self):
        text = "```\n//not italic//\n+ not numbered\n```"
        assert c(text) == text

    def test_entry_reference_passthrough(self):
        # Entry references are handled later in the pipeline, not here.
        assert c("[2019-08-01]") == "[2019-08-01]"


def body(text):
    return render(c(text), "html").split("<body>\n", 1)[1].split("</body>", 1)[0]


@pytest.mark.parametrize(
    "text",
    [
        "`__init__ //literal// --literal--`",
        "``code ` __init__``",
        "`multiline\n__init__`",
        "~~~python\n__init__\n% literal comment\n~~~",
        "````\n```\n__init__\n```\n````",
        "    __init__\n    //literal//",
        "> ~~~\n> __init__\n> ~~~",
        "[label](https://example.org/__path__)",
        "[label](https://example.org/a(__path__))",
        '[label](https://example.org "__title__")',
        "[label]: https://example.org/__path__",
        "https://example.org/__path__",
        "$x__i__$ and \\(x__i__\\)",
        "$$\nx__i__\n$$",
        r"\__literal__",
    ],
)
def test_preserves_literal_markdown_contexts(text):
    assert c(text) == text


def test_legacy_inline_code_keeps_literal_content():
    assert "<code>__init__</code>" in body("``__init__``")


def test_legacy_comments_are_not_exported():
    result = body("% private note\nvisible\n%%%\nprivate block\n%%%\nafter")
    assert "private" not in result
    assert "visible" in result and "after" in result


@pytest.mark.parametrize(
    "source, expected",
    [
        ('[""/my photos/pic (1)"".png]', "![](/my%20photos/pic%20%281%29.png)"),
        ('[file ""/my files/a(1).txt""]', "[file](/my%20files/a%281%29.txt)"),
        ('[""/photos/__name__"".png]', "![](/photos/__name__.png)"),
        ("[image.png]", "![](image.png)"),
    ],
)
def test_legacy_attachments(source, expected):
    assert c(source) == expected


def test_legacy_named_www_link_has_a_scheme():
    assert '<a href="http://www.example.org">site</a>' in body("[site www.example.org]")


def test_legacy_table_has_header_and_cells():
    result = body("|| Name | Value |\n| //first// | **second** |")
    assert "<th>Name</th>" in result
    assert "<td><em>first</em></td>" in result
    assert "<td><strong>second</strong></td>" in result


def test_modern_table_is_unchanged():
    text = "| Name | Value |\n| --- | --- |\n| first | second |"
    assert c(text) == text


def test_legacy_numbered_heading_is_not_a_list():
    result = body("+ First +\n\n++ Nested ++\n\n+ Second +")
    assert "<h1>1. First</h1>" in result
    assert "<h2>1.1. Nested</h2>" in result
    assert "<h1>2. Second</h1>" in result


def test_legacy_unparsed_text_preserves_markup():
    result = body('""**not bold** and __not underlined__""')
    assert "**not bold** and __not underlined__" in result
    assert "<strong>" not in result and "<u>" not in result


def test_legacy_unparsed_text_keeps_code_math_and_html_literal():
    result = body('""`code` $x$ <u>text</u> http://example.org""')
    assert "`code` $x$ &lt;u&gt;text&lt;/u&gt; http://example.org" in result
    assert "<code>" not in result and "<a " not in result


def test_legacy_image_with_backticks_in_path():
    assert c('[""/photos/`test`"".png]') == "![](/photos/%60test%60.png)"


def test_empty_legacy_numbered_item():
    assert "<ol>" in body("+\n+ filled")
    assert "<ul>" not in body("+\n+ filled")


def test_nested_numbered_lists_keep_their_hierarchy():
    result = body("+ parent\n  + child\n    + grandchild\n  + sibling\n+ next")
    assert result.count("<ol>") == 3
    assert "<li>parent\n<ol>" in result
    assert "<li>child\n<ol>" in result


def test_numbered_list_continuation_stays_in_its_item():
    result = body("+ parent\n  continuation\n  - child\n+ next")
    assert "<li>parent\ncontinuation\n<ul>" in result


@pytest.mark.parametrize("first_line", ["+ parent\n  ```", "+ ```"])
def test_numbered_list_code_block_keeps_its_indentation(first_line):
    result = body(first_line + "\n  __init__\n  ```\n  + child")
    assert result.count("<ol>") == 2
    assert "<code>__init__" in result
    assert result.startswith("<ol>")
    assert result.index("<pre>") < result.index("</li>")


@pytest.mark.parametrize("target", ["html", "tex", "txt"])
def test_legacy_raw_block_preserves_target_markup(target):
    source = "'''\n<b>raw __text__</b>\n\\textbf{raw}\n'''"
    result = render(c(source), target)
    assert "<b>raw __text__</b>" in result
    assert r"\textbf{raw}" in result
    assert "'''" not in result


def test_legacy_raw_block_uses_a_longer_fence_than_its_contents():
    source = "'''\n```\n__literal__\n```\n'''"
    converted = c(source)
    assert "````rednotebook-raw\n```\n__literal__\n```\n````" in converted
    assert "__literal__" in body(source)


@pytest.mark.parametrize("target", ["html", "tex", "txt"])
def test_legacy_unparsed_block_preserves_all_its_text(target):
    source = '"""\n**not bold**\n% literal comment\n<u>literal</u>\n"""'
    result = render(c(source), target)
    assert "**not bold**" in result
    assert "literal comment" in result
    assert '"""' not in result and "&quot;&quot;&quot;" not in result
    if target == "html":
        assert "&lt;u&gt;literal&lt;/u&gt;" in result


@pytest.mark.parametrize("marker", ["'''", '"""'])
def test_legacy_quote_blocks_inside_code_are_unchanged(marker):
    source = f"```\n{marker}\n__literal__\n{marker}\n```"
    assert c(source) == source


def test_legacy_raw_block_inside_comments_is_not_exported():
    source = "%%%\n'''\nprivate\n'''\n%%%\nvisible"
    assert "private" not in body(source)
    assert "visible" in body(source)


@pytest.mark.parametrize(
    "source",
    ["|| Header ||\n| one | two |", "|| Header |\n| one | two |"],
)
def test_legacy_table_wider_rows_keep_all_cells(source):
    result = body(source)
    assert "<table>" in result
    assert "<th>Header</th>" in result
    assert "<td>one</td>" in result and "<td>two</td>" in result


def test_legacy_table_body_spans_preserve_following_columns():
    result = body("|| first | second | third |\n| one || three |")
    assert "<td>one</td>\n<td></td>\n<td>three</td>" in result


@pytest.mark.parametrize("text", ["% progress", "= title =", "+ item", "|| a | b |"])
def test_inline_mode_preserves_block_markers(text):
    assert c(text + " //italic//", inline=True) == text + " *italic*"


def test_inline_mode_preserves_code_and_link_destinations():
    text = "`__init__` [link](https://example.org/__path__)"
    assert c(text, inline=True) == text
