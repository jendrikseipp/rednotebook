"""The txt2tags converter must produce Markdown that renders like txt2tags did."""

import pytest

from rednotebook.data import HASHTAG
from rednotebook.util.markdownmarkup import render
from rednotebook.util.t2t_to_markdown import convert_inline
from rednotebook.util.t2t_to_markdown import convert_to_markdown as c


def body(text):
    html = render(c(text), "html")
    return html.split("<body>\n", 1)[1].split("</body>", 1)[0]


class TestHeadings:
    @pytest.mark.parametrize(
        "source, expected",
        [
            ("= Title =", "# Title"),
            ("== Title ==", "## Title"),
            ("===== Five =====", "##### Five"),
            ("==Title==", "## Title"),
            ("  == Indented ==", "## Indented"),
            ("== Clouds ==[clouds]", "## Clouds"),
            ("== a = b ==", "## a = b"),
        ],
    )
    def test_titles(self, source, expected):
        assert c(source) == expected

    def test_unbalanced_title_is_text(self):
        assert c("== a =") == "== a ="

    def test_title_text_is_not_formatted(self):
        # txt2tags doesn't apply inline markup in titles.
        assert c("== My //special// day ==") == "## My //special// day"

    def test_numbered_titles(self):
        assert c("+ First +\n++ Nested ++\n+ Second +") == (
            "# 1. First\n\n## 1.1. Nested\n\n# 2. Second"
        )

    def test_trailing_hash_is_not_a_closing_sequence(self):
        assert c("== Issue # ==") == "## Issue \\#"
        assert "<h2>Issue #</h2>" in body("== Issue # ==")


class TestInlineFormatting:
    def test_all_formats(self):
        assert c("**bold** //italic// __underlined__ --struck-- ``mono``") == (
            "**bold** *italic* <u>underlined</u> ~~struck~~ `mono`"
        )

    def test_nested_formats(self):
        assert "<em><strong>both</strong></em>" in body("**//both//**")

    def test_intraword_bold(self):
        assert c("a**b**c") == "a**b**c"

    @pytest.mark.parametrize(
        "source, expected",
        [
            # Markdown wouldn't recognize "**" before "a" as closing delimiter.
            ("**(x)**a", "<strong>(x)</strong>a"),
            # "***" would be ambiguous.
            ("**a**//b//", "**a**<em>b</em>"),
        ],
    )
    def test_html_tags_where_markdown_delimiters_fail(self, source, expected):
        assert c(source) == expected

    def test_monospace_with_backtick(self):
        assert c("``code with `backtick``") == "``code with `backtick``"
        assert "<code>code with `backtick</code>" in body("``code with `backtick``")

    def test_raw_text_is_literal(self):
        assert c('""**not bold**""') == r"\*\*not bold\*\*"

    def test_tagged_text_is_html(self):
        assert c("''<font color=\"red\">Red</font>''") == '<font color="red">Red</font>'

    def test_double_dashes_with_spaces_are_text(self):
        assert c("a -- b --c-- d") == "a -- b ~~c~~ d"

    def test_formatting_does_not_span_lines(self):
        assert "<strong>" not in body("**a\nb**")


class TestEscaping:
    """Text that txt2tags showed literally must not become Markdown syntax."""

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("*sigh* and _grin_", r"\*sigh\* and \_grin\_"),
            ("5 * 3 = 15", "5 * 3 = 15"),
            ("snake_case_name", "snake_case_name"),
            ("a `b` c", r"a \`b\` c"),
            ("~~not struck~~", r"\~\~not struck\~\~"),
            ("[text](url) and ![alt](pic.png)", r"[text\](url) and ![alt\](pic.png)"),
            ("<Ctrl> + H and <b>tag</b>", r"\<Ctrl> + H and \<b>tag\</b>"),
            ("&amp; &copy; & AT&T", r"\&amp; \&copy; & AT&T"),
            ("C:\\Users\\me and 3\\.50\\?", "C:\\Users\\me and 3\\\\.50\\\\?"),
            ("It costs $5 and $10", "It costs $5 and $10"),
            ("#hashtag at start", "#hashtag at start"),
        ],
    )
    def test_inline(self, source, expected):
        assert c(source) == expected

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("# not a heading", r"\# not a heading"),
            ("> not a quote", r"\> not a quote"),
            ("* not a list", r"\* not a list"),
            ("1. not a list\n2. second", "1\\. not a list\n2\\. second"),
            ("2019. What a year", r"2019\. What a year"),
            ("text\n===", "text\n\\==="),
            ("text\n---", "text\n\\---"),
            ("---", r"\---"),
            ("***", r"\***"),
            ("~~~", r"\~~~"),
            ("[ref]: http://example.com", "&#91;ref]: http://example.com"),
        ],
    )
    def test_block_starts(self, source, expected):
        assert c(source) == expected

    @pytest.mark.parametrize(
        "source",
        [
            "*sigh*",
            "a `b` c",
            "<Ctrl>",
            "&copy;",
            "3\\.50\\?",
            "\\\\server\\share",
            "a \\\\ b",
            "[2019-02-14 ]",
            "# not a heading",
            "1. not a list",
        ],
    )
    def test_escaped_text_renders_unchanged(self, source):
        html = body(source)
        assert html.startswith("<p>") and html.count("<") == 2
        assert source.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") in html


class TestLinks:
    @pytest.mark.parametrize(
        "source, expected",
        [
            ("[heise http://heise.de]", "[heise](http://heise.de)"),
            (
                '[my file ""file:///home/me/my file.txt""]',
                "[my file](file:///home/me/my%20file.txt)",
            ),
            ("[site www.example.org]", "[site](http://www.example.org)"),
            ("[file ftp.example.org]", "[file](ftp://ftp.example.org)"),
            ("[mail me@example.com]", "[mail](mailto:me@example.com)"),
            ("[notes notes.txt]", "[notes](notes.txt)"),
            ("[photos /home/me/photos/]", "[photos](/home/me/photos/)"),
            # txt2tags doesn't format link labels.
            ("[**bold** http://example.com]", r"[\*\*bold\*\*](http://example.com)"),
        ],
    )
    def test_named_links(self, source, expected):
        assert c(source) == expected

    def test_bracketed_remarks_stay_text(self):
        # txt2tags turned this into a link "not" to a file called "sure".
        assert c("I am [not sure] about it") == "I am [not sure] about it"

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("see http://example.com/page.", "see http://example.com/page."),
            ("visit www.example.org today", "visit www.example.org today"),
            ("(see http://example.com/a)", "(see http://example.com/a)"),
            ("write to me@example.com", "write to me@example.com"),
            # Markdown might parse these URLs, so use autolinks.
            ("http://example.com/_a_/", "<http://example.com/_a_/>"),
            ("http://x.com/#frag", "<http://x.com/#frag>"),
        ],
    )
    def test_bare_links(self, source, expected):
        assert c(source) == expected

    def test_bare_link_ends_where_txt2tags_ended_it(self):
        assert '<a href="http://e.com/page">http://e.com/page</a>.#' in body("http://e.com/page.#")


class TestImages:
    @pytest.mark.parametrize(
        "source, expected",
        [
            ("[picture.png]", "![](picture.png)"),
            ("[picture.png?300]", "![](picture.png?300)"),
            ('[""/home/me/my pic"".jpg]', "![](/home/me/my%20pic.jpg)"),
            ('[""/home/me/pic"".png?50]', "![](/home/me/pic.png?50)"),
            ("[[thumb.png] http://example.com]", "[![](thumb.png)](http://example.com)"),
            # txt2tags creates a link for a quoted image with a label.
            ('[alt ""/p/pic"".png]', "[alt](/p/pic.png)"),
        ],
    )
    def test_images(self, source, expected):
        assert c(source) == expected

    def test_image_width(self):
        assert 'width="50"' in body('[""/home/me/pic"".png?50]')


class TestRedNotebookSyntax:
    @pytest.mark.parametrize(
        "source, expected",
        [
            ("[2019-02-14]", "[2019-02-14]"),
            ("[Today 2019-02-14] was good", "[Today 2019-02-14] was good"),
            ("[2019-02-14](note)", "[2019-02-14]&#40;note)"),
            ("[2019-02-14]: done", "[2019-02-14]&#58; done"),
            # txt2tags didn't link dates with extra spaces.
            ("[2019-02-14 ]", "&#91;2019-02-14 ]"),
        ],
    )
    def test_entry_references(self, source, expected):
        assert c(source) == expected

    def test_entry_reference_followed_by_parentheses(self):
        assert '<a href="#2019-02-14">2019-02-14</a>(note)' in body("[2019-02-14](note)")

    def test_colored_text_keeps_formatting(self):
        source = "{**bold** [x http://e.com]|color:blue}"
        assert c(source) == "{**bold** [x](http://e.com)|color:blue}"
        assert '<span style="color:blue"><strong>bold</strong> <a href="http://e.com">x</a>' in (
            body(source)
        )

    def test_line_break(self):
        assert c("line one\\\\\nline two") == "line one  \nline two"
        assert "line one<br />" in body("line one\\\\\nline two")


class TestHashtags:
    """RedNotebook indexes hashtags in the text, so the conversion must keep them."""

    @pytest.mark.parametrize(
        "source",
        [
            "__x__#tag",
            '""x""#tag',
            "#__init__",
            "me@example.com#tag",
            "__#tag__",
            "**#tag**",
            "text #tag, (#tag2) a#b &#c",
            "[#tag http://example.com]",
            "{#tag|color:blue}",
            "- #tag in a list\n\t#tag in a quote\n| #cell | #tag |",
            "== #title ==",
        ],
    )
    def test_hashtags_are_preserved(self, source):
        def tags(text):
            return sorted(match.group(3).lower() for match in HASHTAG.finditer(text))

        assert tags(c(source)) == tags(source)

    def test_hashtag_text_is_not_formatted(self):
        assert c("#__init__") == "#__init__"


class TestLists:
    @pytest.mark.parametrize(
        "source, expected",
        [
            ("- a\n- b", "- a\n- b"),
            ("+ a\n+ b", "1. a\n1. b"),
            ("- a\n  - b\n    - c", "- a\n  - b\n    - c"),
            # txt2tags nests on any additional indentation.
            ("- a\n - b\n  - c", "- a\n  - b\n    - c"),
            ("+ a\n  + b", "1. a\n   1. b"),
            ("- a\ncontinued", "- a\n  continued"),
            # A single blank line doesn't end txt2tags lists.
            ("- a\n\nsame item", "- a\n\n  same item"),
            ("- a\n\n\nnew paragraph", "- a\n\nnew paragraph"),
            # An empty item closes the list.
            ("- a\n-\nafter", "- a\n\nafter"),
            ("- a\n  - b\n  -\n  back in a", "- a\n  - b\n\n  back in a"),
            ("- - x", r"- \- x"),
            ("- # x", r"- \# x"),
            ("text\n- item", "text\n\n- item"),
            ("- a\n```\ncode\n```\n- b", "- a\n  ```\n  code\n  ```\n- b"),
        ],
    )
    def test_lists(self, source, expected):
        assert c(source) == expected

    @pytest.mark.parametrize(
        "source",
        ["- a\n\n\n- b", "+ a\n\n\n+ b", "  - indented\n- outer", "- a\n-\n- b"],
    )
    def test_separate_lists_stay_separate(self, source):
        html = body(source)
        assert html.count("<ul>") + html.count("<ol>") == 2

    def test_numbered_lists_restart(self):
        assert "<ol>" in body("+ a\n\n\n+ b").split("</ol>", 1)[1]

    def test_definition_list_becomes_bullet_list(self):
        assert c(": term\ndefinition") == "- term\n  definition"

    def test_table_closes_list(self):
        html = body("- a\n| x | y |")
        assert html.index("</ul>") < html.index("<table>")


class TestQuotes:
    @pytest.mark.parametrize(
        "source, expected",
        [
            ("\tquote", "> quote"),
            ("\tq1\n\t\tq2\n\tq1b", "> q1\n> > q2\n>\n> q1b"),
            ("para\n\tquote", "para\n\n> quote"),
            ("\tquote\ntext", "> quote\n\ntext"),
            ("\t> x", r"> \> x"),
        ],
    )
    def test_quotes(self, source, expected):
        assert c(source) == expected

    def test_space_indented_text_is_a_paragraph(self):
        assert body("    four spaces") == "<p>four spaces</p>\n"


class TestTables:
    def test_table_without_header(self):
        assert c("| a | b |\n| c | d |") == "|  |  |\n| --- | --- |\n| a | b |\n| c | d |"
        html = body("| a | b |\n| c | d |")
        assert "<thead>" not in html and "<td>a</td>" in html

    def test_table_with_header(self):
        assert c("|| h1 | h2 |\n| c | d |") == "| h1 | h2 |\n| --- | --- |\n| c | d |"

    def test_later_header_rows_are_bold(self):
        assert c("|| h1 | h2 |\n| c | d |\n|| h3 | h4 |").endswith("| **h3** | **h4** |")

    def test_spanned_cells_keep_columns(self):
        assert c("| a | b | c |\n| d || e |").endswith("| d |  | e |")

    def test_cells_are_split_at_spaced_pipes(self):
        assert c("|  center  |  right|left  |") == (
            "|  |  |\n| :---: | :---: |\n| center | right\\|left |"
        )

    def test_pipes_in_cell_content_are_escaped(self):
        assert c("| {red|color:red} | ``a|b`` |").endswith("| {red\\|color:red} | `a\\|b` |")
        html = body("| {red|color:red} | ``a|b`` | $$x|y$$ |")
        assert '<span style="color:red">red</span>' in html
        assert "<code>a|b</code>" in html
        assert "$$x|y$$" in html

    def test_pipes_without_spaces_are_no_table(self):
        assert c("|a|b|") == "|a|b|"


class TestBlocks:
    @pytest.mark.parametrize(
        "source, expected",
        [
            ("```\ncode **x**\n% not a comment\n```", "```\ncode **x**\n% not a comment\n```"),
            ("```\nunclosed", "```\nunclosed\n```"),
            ("``` one line", "```\none line\n```"),
            ("````\n```\n````", "\\`\\`\\`\\`\n\n`````\n````\n`````"),
            ('"""\n**raw**\n"""', r"\*\*raw\*\*"),
            ('""" raw line', "raw line"),
            ("'''\n<b>tagged</b>\n'''", "```rednotebook-raw\n<b>tagged</b>\n```"),
            ("''' <b>one line</b>", "```rednotebook-raw\n<b>one line</b>\n```"),
        ],
    )
    def test_blocks(self, source, expected):
        assert c(source) == expected

    @pytest.mark.parametrize("target", ["html", "tex", "txt"])
    def test_tagged_block_is_passed_through(self, target):
        source = "'''\n<b>raw __text__</b>\n\\textbf{raw}\n'''"
        result = render(c(source), target)
        assert "<b>raw __text__</b>" in result
        assert r"\textbf{raw}" in result

    def test_horizontal_rule_after_text(self):
        assert c("text\n====================") == "text\n\n---"


class TestComments:
    @pytest.mark.parametrize(
        "source, expected",
        [
            ("% comment\ntext", "<!-- comment -->\n\ntext"),
            # Comments don't interrupt txt2tags paragraphs.
            ("line1\n% c\nline2", "line1\nline2\n\n<!-- c -->"),
            ("%%%\nblock\ncomment\n%%%\ntext", "<!--\nblock\ncomment\n-->\n\ntext"),
            ("- a\n% c\n- b", "- a\n  <!-- c -->\n- b"),
            ("%!target: html\ntext", "<!-- !target: html -->\n\ntext"),
            ("% a --> b", "<!-- a -- > b -->"),
        ],
    )
    def test_comments_are_kept_hidden(self, source, expected):
        assert c(source) == expected

    @pytest.mark.parametrize("target", ["html", "tex", "txt"])
    def test_comments_are_not_exported(self, target):
        result = render(c("% private note\nvisible\n%%%\nprivate block\n%%%\nafter"), target)
        assert "visible" in result and "after" in result
        if target != "html":
            assert "private" not in result

    def test_comment_keeps_paragraph(self):
        assert body("line1\n% c\nline2").startswith("<p>line1\nline2</p>")


class TestMath:
    @pytest.mark.parametrize(
        "source",
        [
            "\\(x^2\\) and $$y$$ and \\[z\\]",
            "$$\nx = 1\n$$",
            "\\[\nx\n\\]",
            "\\(a_1 * b_2\\)",
            "$$a //b// c$$",
        ],
    )
    def test_math_is_kept_verbatim(self, source):
        assert c(source) == source

    def test_multi_line_math_does_not_include_comments(self):
        assert c("\\[ C3PO\n% c \\]") == "\\\\[ C3PO\n\n<!-- c \\] -->"

    def test_unclosed_display_math_stays_text(self):
        assert c("$$\nunclosed\n\nlater") == "\\$$\nunclosed\n\nlater"
        assert "MathJax" not in render(c("$$\nunclosed\n\nlater"), "html")


class TestInlineConversion:
    def test_tag_names(self):
        assert convert_inline("//italic// category") == "*italic* category"
        assert convert_inline("Work") == "Work"

    def test_line_break_is_dropped(self):
        assert convert_inline("a\\\\") == "a"


def test_legacy_journal_entry():
    source = """\
=== Holidays ===
We went to the //beach// and swam **a lot**. #vacation

+ Pack the bags
+ Buy [tickets http://example.com/tickets]
  - Train
  - Bus


[""/home/me/Pictures/beach day"".jpg?400]

% Remember to call grandma.
|| Day | Weather |
| Monday | sunny |
"""
    expected = """\
### Holidays

We went to the *beach* and swam **a lot**. #vacation

1. Pack the bags
1. Buy [tickets](http://example.com/tickets)
   - Train
   - Bus

![](/home/me/Pictures/beach%20day.jpg?400)

<!-- Remember to call grandma. -->

| Day | Weather |
| --- | --- |
| Monday | sunny |"""
    assert c(source) == expected
