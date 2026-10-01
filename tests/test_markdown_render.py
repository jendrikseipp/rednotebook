"""Tests for the Markdown rendering pipeline (HTML, LaTeX and plain text)."""

import pytest

from rednotebook.util.markdownmarkup import render


def html(markup, **options):
    return render(markup, "html", options)


def tex(markup, **options):
    return render(markup, "tex", options)


def txt(markup, **options):
    return render(markup, "txt", options)


class TestHtmlBasics:
    def test_document_skeleton(self):
        doc = html("Content")
        assert "<!DOCTYPE html>" in doc
        assert '<meta charset="utf-8">' in doc
        assert '<p dir="auto">Content</p>' in doc

    def test_emphasis(self):
        doc = html("**b** and *i* and ~~s~~ and `c`")
        assert "<strong>b</strong>" in doc
        assert "<em>i</em>" in doc
        assert "<s>s</s>" in doc
        assert "<code>c</code>" in doc

    def test_heading(self):
        assert "<h2>Title</h2>" in html("## Title")

    def test_bullet_list(self):
        doc = html("- a\n- b")
        assert "<ul>" in doc and "<li>a</li>" in doc

    def test_link(self):
        assert '<a href="http://x.com">name</a>' in html("[name](http://x.com)")

    def test_autolink_bare_url(self):
        assert '<a href="http://x.com">http://x.com</a>' in html("see http://x.com")


class TestHtmlRedNotebookFeatures:
    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("#TAG", '<span style="color:red">#TAG</span>'),
            ("Numeric #3tag", '<span style="color:red">#3tag</span>'),
            ("Just #34 numbers", "#34"),
        ],
    )
    def test_hashtags(self, markup, expected):
        assert expected in html(markup)

    def test_hashtag_not_in_code(self):
        assert '<span style="color:red">' not in html("`#TAG`")

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("{Sky|color:blue}", '<span style="color:blue">Sky</span>'),
            ("{Red|color:#FF0000} truck", '<span style="color:#FF0000">Red</span> truck'),
        ],
    )
    def test_colors(self, markup, expected):
        assert expected in html(markup)

    def test_image_width(self):
        doc = html("![](/image.png?50)")
        assert 'src="/image.png"' in doc
        assert 'width="50"' in doc

    def test_image_no_width(self):
        doc = html("![](/image.jpg)")
        assert 'src="/image.jpg"' in doc
        assert "width=" not in doc

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("[named ref](#2019-08-01)", '<a href="#2019-08-01">named ref</a>'),
        ],
    )
    def test_entry_reference_links(self, markup, expected):
        assert expected in html(markup)

    def test_mathjax_added_when_formula_present(self):
        doc = html("$$x^3$$")
        assert "MathJax" in doc

    def test_mathjax_absent_without_formula(self):
        assert "MathJax" not in html("no math here")

    def test_inline_display_math(self):
        doc = html("around $$x^2$$ text")
        assert "$$x^2$$" in doc
        assert "MathJax" in doc

    def test_linebreak(self):
        assert "<br" in html("first  \nsecond")

    def test_toc(self):
        doc = html("# One\n\ntext\n\n## Two", toc=1)
        assert '<a href="#one">One</a>' in doc
        assert '<a href="#two">Two</a>' in doc
        assert '<h1 id="one">One</h1>' in doc
        assert '<h2 id="two">Two</h2>' in doc

    def test_no_toc_by_default(self):
        assert "toc" not in html("# One\n\ntext")


class TestLatex:
    def test_preamble(self):
        doc = tex("Content")
        assert r"\documentclass" in doc
        assert r"\begin{document}" in doc
        assert r"\end{document}" in doc

    def test_emphasis(self):
        doc = tex("**b** and *i*")
        assert r"\textbf{b}" in doc
        assert r"\textit{i}" in doc

    def test_heading(self):
        assert r"\section{Title}" in tex("# Title")

    def test_hashtag_with_index(self):
        doc = tex("#TAG")
        assert r"\textcolor{red}{\#TAG\index{TAG}}" in doc

    def test_color(self):
        assert r"\textcolor{blue}{Sky}" in tex("{Sky|color:blue}")

    def test_special_chars_escaped(self):
        assert r"100\%" in tex("100%")

    def test_inline_display_math(self):
        assert "$$x^2$$" in tex("around $$x^2$$ text")

    def test_table(self):
        doc = tex("| a | b |\n|---|---|\n| 1 | 2 |")
        assert "\\begin{tabular}{ll}" in doc
        assert "a & b \\\\" in doc
        assert "\\hline" in doc
        assert "1 & 2 \\\\" in doc
        assert "\\end{tabular}" in doc

    def test_underline(self):
        assert r"\uline{text}" in tex("a <u>text</u> b")

    def test_unbalanced_underline_braces(self):
        doc = tex("a <u>text b")
        assert doc.count("{") == doc.count("}")


class TestPlainText:
    def test_plain_text(self):
        assert "Content" in txt("Content")

    def test_strips_emphasis(self):
        out = txt("**bold** and *italic*")
        assert "bold" in out and "*" not in out

    def test_color_stripped(self):
        assert "Sky" in txt("{Sky|color:blue}")
        assert "color" not in txt("{Sky|color:blue}")

    def test_bullet_list(self):
        out = txt("- a\n- b")
        assert "a" in out and "b" in out

    def test_inline_display_math(self):
        assert "x^2" in txt("around $$x^2$$ text")

    def test_table(self):
        out = txt("| a | b |\n|---|---|\n| 1 | 2 |")
        assert "a | b\n" in out
        assert "1 | 2\n" in out


class TestMath:
    @pytest.mark.parametrize("markup", ["It costs $5 and $10 today", "$x$ stays text", "a $ b $ c"])
    def test_single_dollar_signs_are_text(self, markup):
        assert f'<p dir="auto">{markup}</p>' in html(markup)
        assert "MathJax" not in html(markup)

    @pytest.mark.parametrize(
        "markup, expected",
        [
            ("a \\(x^2\\) b", "a \\(x^2\\) b"),
            ("a $$x^2$$ b", "a $$x^2$$ b"),
            ("a \\[x^2\\] b", "a $$x^2$$ b"),
            ("a $$x < y$$ b", "a $$x &lt; y$$ b"),
        ],
    )
    def test_inline_math(self, markup, expected):
        assert f'<p dir="auto">{expected}</p>' in html(markup)

    @pytest.mark.parametrize(
        "markup", ["$$\nx\n$$", "\\[\nx\n\\]", "$$x$$", "$$\nx = 1\n\ny = 2\n$$"]
    )
    def test_display_math(self, markup):
        doc = html(markup)
        assert "<p" not in doc.split("<body>")[1]
        assert "MathJax" in doc

    def test_display_math_after_text_stops_at_blank_lines(self):
        doc = html("$$ money\n\nlater $$")
        assert '<p dir="auto">$$ money</p>' in doc and "MathJax" not in doc

    def test_text_after_math_is_kept(self):
        assert "$$x$$ (eq1)" in html("$$x$$ (eq1)")

    def test_escaped_dollars(self):
        assert '<p dir="auto">$$x$$</p>' in html("\\$$x\\$$")
        assert "MathJax" not in html("\\$$x\\$$")

    def test_latex(self):
        doc = tex("Inline \\(x\\) and $$y$$\n\n$$\nz\n$$\n\nPrice $5")
        assert "Inline $x$ and $$y$$" in doc
        assert "$$\nz\n$$" in doc
        assert r"Price \$5" in doc

    def test_plain_text(self):
        assert txt("Inline \\(x\\) and $5") == "Inline x and $5\n"


class TestRedNotebookSyntax:
    @pytest.mark.parametrize(
        "target, expected",
        [
            (
                "html",
                '<span style="color:blue"><strong>bold</strong> <a href="http://x.com">x</a></span>',
            ),
            ("tex", r"\textcolor{blue}{\textbf{bold} \href{http://x.com}{x}}"),
            ("txt", "bold x (http://x.com)\n"),
        ],
    )
    def test_colored_text_is_formatted(self, target, expected):
        assert expected in render("{**bold** [x](http://x.com)|color:blue}", target)

    def test_fullwidth_hashtag(self):
        doc = html("text ＃tag and ＃２ and a＃b")
        assert '<span style="color:red">＃tag</span>' in doc
        assert "＃２" in doc and "a＃b" in doc
        assert doc.count('style="color:red"') == 1

    @pytest.mark.parametrize(
        "markup, expected",
        [
            ("[Foo \\* bar 2019-01-01]", '<a href="#2019-01-01">Foo * bar</a>'),
            ("{a \\* b|color:red}", '<span style="color:red">a * b</span>'),
            ("![a \\] b](x.png)", 'alt="a ] b"'),
        ],
    )
    def test_escapes_in_nested_text(self, markup, expected):
        # Newer markdown-it versions produce "text_special" tokens here.
        assert expected in html(markup)

    @pytest.mark.parametrize("target", ["tex", "txt"])
    def test_escapes_in_entry_references(self, target):
        assert "Foo * bar (2019-01-01)" in render("[Foo \\* bar 2019-01-01]", target)


class TestTables:
    TABLE = "|  |  |\n| --- | --- |\n| a | b |"

    def test_empty_header_is_hidden(self):
        doc = html(self.TABLE)
        assert "<thead>" not in doc and "<th>" not in doc
        assert "<td>a</td>" in doc

    def test_empty_header_in_latex(self):
        doc = tex(self.TABLE)
        assert "\\begin{tabular}{ll}" in doc
        assert "\\hline" not in doc
        assert "a & b \\\\" in doc

    def test_empty_header_in_plain_text(self):
        assert txt(self.TABLE) == "a | b\n"


class TestLatexConstructs:
    def test_lists(self):
        doc = tex("- a\n  - b\n\n1. c\n2. d")
        assert "\\begin{itemize}\n\\item a\\begin{itemize}\n\\item b" in doc
        assert "\\begin{enumerate}\n\\item c\n\\item d\n\\end{enumerate}" in doc

    def test_blockquote(self):
        assert "\\begin{quote}\nquoted\n\n\\end{quote}" in tex("> quoted")

    def test_horizontal_rule(self):
        assert "\\rule{\\linewidth}{0.4pt}" in tex("a\n\n---\n\nb")

    def test_strikethrough_and_code(self):
        doc = tex("~~gone~~ and `a_b # %`")
        assert r"\sout{gone}" in doc
        assert r"\texttt{a\_b \# \%}" in doc

    def test_code_block(self):
        assert "\\begin{verbatim}\n$ # % {}\n\\end{verbatim}" in tex("```\n$ # % {}\n```")

    def test_hashtag_index_is_escaped(self):
        assert r"\textcolor{red}{\#my\_tag\index{my\_tag}}" in tex("#my_tag")

    @pytest.mark.parametrize(
        "markup", ["**[x](http://e.com/a%20b#c)**", "# [x](http://e.com/a%20b#c)"]
    )
    def test_link_targets_are_escaped(self, markup):
        assert r"\href{http://e.com/a\%20b\#c}{x}" in tex(markup)

    @pytest.mark.parametrize(
        "markup, expected",
        [
            ("<strong>b</strong>", r"\textbf{b}"),
            ("<em>i</em>", r"\textit{i}"),
            ("<s>s</s>", r"\sout{s}"),
            ("<b>b</b> <i>i</i> <del>d</del>", r"\textbf{b} \textit{i} \sout{d}"),
            ("<strong>a <em>b</strong> c</em>", r"\textbf{a \textit{b}} c"),
        ],
    )
    def test_html_formatting_tags(self, markup, expected):
        doc = tex(markup)
        assert expected in doc
        assert doc.count("{") == doc.count("}")

    def test_entry_reference(self):
        assert "Visit (2019-01-01)" in tex("[Visit 2019-01-01]")


class TestPlainTextConstructs:
    def test_headings_and_rules(self):
        assert (
            txt("# Title\n\ntext\n\n---\n\nmore")
            == "Title\n\ntext\n\n\n====================\n\nmore\n"
        )

    def test_images_and_links(self):
        assert txt("![](pic.png) [x](http://e.com) http://e.com") == (
            "[pic.png] x (http://e.com) http://e.com\n"
        )


class TestToc:
    def test_duplicate_headings_get_unique_anchors(self):
        doc = html("# Notes\n\n# Notes\n\n## Sub", toc=1)
        assert '<h1 id="notes">' in doc and '<h1 id="notes-2">' in doc
        assert doc.count("<ul>") == 2

    def test_heading_without_text(self):
        assert '<h1 id="section">' in html("# !!!", toc=1)


def test_paragraph_direction_follows_the_text():
    doc = html("مرحبا بالعالم\n\nHello\n\n- tight list item")
    assert '<p dir="auto">مرحبا بالعالم</p>' in doc
    assert '<p dir="auto">Hello</p>' in doc
    assert "<li>tight list item</li>" in doc
