import datetime
import os
import sys

import pytest

from rednotebook.data import Day, Month
from rednotebook.util import filesystem
from rednotebook.util.markup import _convert_paths, convert, get_markup_for_day
from rednotebook.util.pango_markup import convert_from_pango, convert_to_pango


@pytest.mark.parametrize(
    "t2t_markup,expected",
    [
        (r"--stricken--", "<s>stricken</s>"),
        (r"//italic//", "<i>italic</i>"),
        (r"--www.test.com--", "<s>www.test.com</s>"),
        # Linebreaks only on line ends
        (r"First\\Second", r"First\\Second"),
        (r"First\\", "First\n"),
        (r"a&b", "a&amp;b"),
        (r"a&amp;b", "a&amp;b"),
        (r"http://site/s.php?q&c", "http://site/s.php?q&amp;c"),
        (r"http://site/s.php?q&amp;c", "http://site/s.php?q&amp;c"),
    ],
)
def test_pango(t2t_markup, expected):
    pango = convert_to_pango(t2t_markup)
    assert pango == expected
    # Ampersand escaping is only needed in sourcecode, so we do not try to
    # preserve the encoding
    if "&amp;" not in t2t_markup:
        assert convert_from_pango(pango) == t2t_markup


def test_relative_path_conversion(tmp_path):
    for path in [tmp_path / f for f in ("rel.jpg", "rel.pdf")]:
        path.write_text("")  # Create empty file.
    tmp_path_uri = filesystem.LOCAL_FILE_PEFIX + str(tmp_path) + os.sep + "rel"

    rel_paths = [
        ('[""file://rel"".jpg]', f'[""{tmp_path_uri}"".jpg]'),
        ('[""rel"".jpg]', f'[""{tmp_path_uri}"".jpg]'),
        (
            '[rel.pdf ""file://rel.pdf""]',
            f'[rel.pdf ""{tmp_path_uri}.pdf""]',
        ),
        ('[rel.pdf ""rel.pdf""]', f'[rel.pdf ""{tmp_path_uri}.pdf""]'),
    ]

    for markup, expected in rel_paths:
        assert expected == _convert_paths(markup, tmp_path)


def test_absolute_path_conversion(tmp_path):
    abs_paths = [
        '[""file:///abs"".jpg]',
        f'[""{tmp_path}/aha 1"".jpg]',
        '[abs.pdf ""file:///abs.pdf""]',
        f'[abs.pdf ""{tmp_path}/abs.pdf""]',
        "www.google.com",
        "www.google.com/page.php",
    ]

    for path in abs_paths:
        assert path == _convert_paths(path, tmp_path)


class TestGetHtmlExportConfig:
    @staticmethod
    @pytest.fixture
    def process(tmp_path):
        def process(markup):
            html_document = convert(markup, "html", tmp_path)
            return html_document.split("\n")

        return process

    def test_encoding(self, process):
        document = process("Content")
        assert '<meta charset="utf-8">' in document

    def test_toc(self, process):
        document = process("Content")
        assert '<div class="toc">' not in document

    def test_css_sugar(self, process):
        document = process("Content")
        assert '<div class="body">' in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("content \\\\ ", "content <br />"),
            ("content\\\\", "content<br />"),
            ("content\\\\ ", "content<br />"),
        ],
    )
    def test_line_break_escaping(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("#TAG", r'<span style="color:red">#TAG</span>'),
            ("Numeric #3tag", r'Numeric <span style="color:red">#3tag</span>'),
            ("Just #34 numbers", r"Just #34 numbers"),
        ],
    )
    def test_hashtags(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("{Sky|color:blue}", r'<span style="color:blue">Sky</span>'),
            (
                "{Red|color:#FF0000} firetruck",
                r'<span style="color:#FF0000">Red</span> firetruck',
            ),
        ],
    )
    def test_colors(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            (
                '[""/image"".png?50]',
                '<img class="center" width="50" src="/image.png" alt="">',
            ),
            (
                '[""/image"".jpg?50]',
                '<img class="center" width="50" src="/image.jpg" alt="">',
            ),
            (
                '[""/image"".jpeg?50]',
                '<img class="center" width="50" src="/image.jpeg" alt="">',
            ),
            (
                '[""/image"".gif?50]',
                '<img class="center" width="50" src="/image.gif" alt="">',
            ),
            (
                '[""/image"".eps?50]',
                '<img class="center" width="50" src="/image.eps" alt="">',
            ),
            (
                '[""/image"".bmp?50]',
                '<img class="center" width="50" src="/image.bmp" alt="">',
            ),
            (
                '[""/image"".svg?50]',
                '<img class="center" width="50" src="/image.svg" alt="">',
            ),
        ],
    )
    def test_images_resize_allowed_extensions(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            (
                '[""/image"".png?50]',
                '<img class="center" width="50" src="/image.png" alt="">',
            ),
            (
                '[""/image"".jpg]',
                '<img class="center" src="/image.jpg" alt="">',
            ),
            (
                '[""file:///image"".png?10]',
                '<img class="center" width="10" src="file:///image.png" alt="">',
            ),
            (
                '[""file:///image"".jpg]',
                '<img class="center" src="file:///image.jpg" alt="">',
            ),
        ],
    )
    def test_images_width_resize(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            (
                "Simple [named reference 2019-08-01]",
                'Simple <a href="#2019-08-01">named reference</a>',
            ),
            (
                "An inline [2019-08-01] date",
                'An inline <a href="#2019-08-01">2019-08-01</a> date',
            ),
            ("[2019-10-20] is first", '<a href="#2019-10-20">2019-10-20</a> is first'),
        ],
    )
    def test_entry_reference_links(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    def test_day_fragment_anchor_element(self, process):
        date = datetime.date(2019, 10, 21)
        day = Day(Month(date.year, date.month), date.day)

        markup = get_markup_for_day(day, "html", date=date.strftime("%d-%m-%Y"))
        document = process(markup)

        assert rf'<span id="{date:%Y-%m-%d}"></span>' in document

    def test_mathjax(self, process):
        document = process("$$x^3$$")
        assert r"<!--MathJax included-->" in document


class TestGetTexExportConfig:
    @staticmethod
    @pytest.fixture
    def process(tmp_path):
        def process(markup):
            html_document = convert(markup, "tex", tmp_path)
            return html_document.split("\n")

        return process

    def test_encoding(self, process):
        document = process("Content")
        assert r"\usepackage[utf8]{inputenc}  % char encoding" in document

    def test_euro_replacement(self, process):
        document = process("€")
        assert "Euro" in document

    @pytest.mark.parametrize(
        "markup,expected",
        [(r'[""file/path"".png]', r'\includegraphics{"file/path".png}')],
    )
    def test_path_escape(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific")
    def test_image_scheme_fix_win32(self, process):
        document = process('[""file:///image"".png]')
        assert r'\includegraphics{"image".png}' in document

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX-specific")
    def test_image_scheme_fix_posix(self, process):
        document = process('[""file://image"".png]')
        assert r'\includegraphics{"image".png}' in document

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific")
    def test_file_scheme_fix_win32(self, process):
        document = process("[file.txt file:///path/to/text/file.txt]")
        assert r"\htmladdnormallink{file.txt}{run:path/to/text/file.txt}" in document

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX-specific")
    def test_file_scheme_fix_posix(self, process):
        document = process("[file.txt file://path/to/text/file.txt]")
        assert r"\htmladdnormallink{file.txt}{run:path/to/text/file.txt}" in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("content \\\\ ", "content \\\\"),
            ("content\\\\", "content\\\\"),
            ("content\\\\ ", "content\\\\"),
        ],
    )
    def test_line_break_escaping(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("#TAG", r"\textcolor{red}{\#TAG\index{TAG}}"),
            ("Numeric #3tag", r"Numeric \textcolor{red}{\#3tag\index{3tag}}"),
            ("Just #34 numbers", r"Just \#34 numbers"),
            ("#include <iostream>", r"\#include $<$iostream$>$"),
            # TODO: ('#define FOO BAR', r'\#define FOO BAR'),
            ("Blue: #0000FF", r"Blue: \#0000FF"),
        ],
    )
    def test_hashtags(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ('[""image"".png?50]', '\\includegraphics[width=50px]{"image".png}'),
            ('[""image"".jpg]', '\\includegraphics{"image".jpg}'),
        ],
    )
    def test_images_width_resize(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize(
        "markup,expected",
        [(r"\[f(x) = x^2\]", "$$f(x) = x^2$$"), (r"$$f(x) = x^2$$", "$$f(x) = x^2$$")],
    )
    def test_latex_equation_escape_display_mode(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize("markup,expected", [(r"\(f(x) = x^2\)", "$f(x) = x^2$")])
    def test_latex_equation_escape_inline_mode(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize(
        "markup,expected", [(r"„content”", '"content"'), (r"”content“", '"content"')]
    )
    def test_quotation_mark_replacement(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("{Sky|color:blue}", r"\textcolor{blue}{Sky}"),
            ("{Red|color:#FF0000} firetruck", r"\textcolor{\#FF0000}{Red} firetruck"),
        ],
    )
    def test_colors(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    def test_index_generation(self, process):
        document = process("content")
        assert r"\usepackage{makeidx}  % user defined" in document
        assert r"\makeindex" in document
        assert r"\printindex" in document

    def test_tags_are_collected_for_index_generation(self, process):
        document = process("#tag")
        assert r"\index{tag}" in "".join(document)

    @pytest.mark.parametrize(
        "markup,expected",
        [
            (
                "This is a [named reference 2019-08-01]",
                "This is a named reference (2019-08-01)",
            ),
            (
                "Today is 2019-08-01 - a wonderful day",
                "Today is 2019-08-01 - a wonderful day",
            ),
        ],
    )
    def test_entry_reference_links(self, markup, expected, process):
        document = process(markup)
        assert expected in document


class TestGetPlainTextExportConfig:
    @staticmethod
    @pytest.fixture
    def process(tmp_path):
        def process(markup):
            html_document = convert(markup, "txt", tmp_path)
            return html_document.split("\n")

        return process

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("content \\\\ ", "content "),
            ("content\\\\", "content"),
            ("content\\\\ ", "content"),
        ],
    )
    def test_line_break_escaping(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            ("{Sky|color:blue}", r"Sky"),
            ("{Red|color:#FF0000} firetruck", r"Red firetruck"),
        ],
    )
    def test_colors(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize(
        "markup,expected",
        [("[image.png?50]", "[image.png?50]"), ("[image.jpg]", "[image.jpg]")],
    )
    def test_images_width_resize(self, markup, expected, process):
        document = process(markup)
        assert expected in document

    @pytest.mark.parametrize(
        "markup,expected",
        [
            (
                "This is a [named reference 2019-08-01]",
                "This is a named reference (2019-08-01)",
            ),
            (
                "Today is 2019-08-01 - a wonderful day",
                "Today is 2019-08-01 - a wonderful day",
            ),
        ],
    )
    def test_entry_reference_links(self, markup, expected, process):
        document = process(markup)
        assert expected in document
