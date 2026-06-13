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
        assert "<p>Content</p>" in doc

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

    def test_linebreak(self):
        assert "<br" in html("first  \nsecond")


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
