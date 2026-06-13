import datetime

import pytest

from rednotebook.data import Day, Month
from rednotebook.util import urls
from rednotebook.util.markup import _convert_paths, convert, get_markup_for_day
from rednotebook.util.pango_markup import convert_from_pango, convert_to_pango


@pytest.mark.parametrize(
    "markdown,pango",
    [
        ("**bold**", "<b>bold</b>"),
        ("*italic*", "<i>italic</i>"),
        ("~~struck~~", "<s>struck</s>"),
        ("`code`", "<tt>code</tt>"),
        ("<u>underlined</u>", "<u>underlined</u>"),
    ],
)
def test_pango(markdown, pango):
    assert convert_to_pango(markdown) == pango
    assert convert_from_pango(pango) == markdown


def test_pango_strips_links():
    assert convert_to_pango("[name](http://x.com)") == "name"


def test_relative_path_conversion(tmp_path):
    for name in ("rel.jpg", "rel.pdf", "rel.png"):
        (tmp_path / name).write_text("")  # Create empty file.

    def url(name):
        return urls.get_local_url(str(tmp_path / name))

    rel_paths = [
        ("![](rel.jpg)", f"![]({url('rel.jpg')})"),
        ("[doc](rel.pdf)", f"[doc]({url('rel.pdf')})"),
        ("![](rel.png?50)", f"![]({url('rel.png')}?50)"),
    ]
    for markup, expected in rel_paths:
        assert _convert_paths(markup, tmp_path) == expected


def test_absolute_path_conversion(tmp_path):
    abs_paths = [
        "![](file:///abs.jpg)",
        f"![]({tmp_path}/aha.jpg)",
        "[doc](file:///abs.pdf)",
        "[site](http://www.google.com)",
    ]
    for path in abs_paths:
        assert path == _convert_paths(path, tmp_path)


def test_entry_reference_fragment_untouched(tmp_path):
    assert _convert_paths("[2019-08-01](#2019-08-01)", tmp_path) == "[2019-08-01](#2019-08-01)"


class TestHtml:
    @staticmethod
    @pytest.fixture
    def process(tmp_path):
        def process(markup):
            return convert(markup, "html", tmp_path)

        return process

    def test_encoding(self, process):
        assert '<meta charset="utf-8">' in process("Content")

    def test_legacy_txt2tags_input(self, process):
        document = process("//italic// and --struck--")
        assert "<em>italic</em>" in document
        assert "<s>struck</s>" in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("#TAG", '<span style="color:red">#TAG</span>'),
            ("Numeric #3tag", '<span style="color:red">#3tag</span>'),
            ("Just #34 numbers", "#34"),
        ],
    )
    def test_hashtags(self, markup, expected, process):
        assert expected in process(markup)

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("{Sky|color:blue}", '<span style="color:blue">Sky</span>'),
            ("{Red|color:#FF0000} truck", '<span style="color:#FF0000">Red</span> truck'),
        ],
    )
    def test_colors(self, markup, expected, process):
        assert expected in process(markup)

    def test_image_resize(self, process):
        document = process("![](/image.png?50)")
        assert 'src="/image.png"' in document
        assert 'width="50"' in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("Simple [named reference 2019-08-01]", '<a href="#2019-08-01">named reference</a>'),
            ("An inline [2019-08-01] date", '<a href="#2019-08-01">2019-08-01</a>'),
        ],
    )
    def test_entry_reference_links(self, markup, expected, process):
        assert expected in process(markup)

    def test_day_fragment_anchor_element(self, process):
        date = datetime.date(2019, 10, 21)
        day = Day(Month(date.year, date.month), date.day)
        markup = get_markup_for_day(day, "html", date=date.strftime("%d-%m-%Y"))
        assert f'<span id="{date:%Y-%m-%d}"></span>' in process(markup)

    def test_mathjax_added(self, process):
        assert "MathJax" in process("$$x^3$$")

    def test_mathjax_absent(self, process):
        assert "MathJax" not in process("no formula")


class TestLatex:
    @staticmethod
    @pytest.fixture
    def process(tmp_path):
        def process(markup):
            return convert(markup, "tex", tmp_path)

        return process

    def test_preamble(self, process):
        document = process("Content")
        assert r"\documentclass" in document
        assert r"\begin{document}" in document

    def test_legacy_heading(self, process):
        assert r"\section{Title}" in process("= Title =")

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("#TAG", r"\textcolor{red}{\#TAG\index{TAG}}"),
            ("Numeric #3tag", r"\textcolor{red}{\#3tag\index{3tag}}"),
        ],
    )
    def test_hashtags(self, markup, expected, process):
        assert expected in process(markup)

    def test_color(self, process):
        assert r"\textcolor{blue}{Sky}" in process("{Sky|color:blue}")

    def test_entry_reference(self, process):
        assert "named reference (2019-08-01)" in process("A [named reference 2019-08-01]")


class TestPlainText:
    @staticmethod
    @pytest.fixture
    def process(tmp_path):
        def process(markup):
            return convert(markup, "txt", tmp_path)

        return process

    def test_color_stripped(self, process):
        document = process("{Sky|color:blue}")
        assert "Sky" in document
        assert "color" not in document

    def test_entry_reference(self, process):
        assert "named reference (2019-08-01)" in process("A [named reference 2019-08-01]")
