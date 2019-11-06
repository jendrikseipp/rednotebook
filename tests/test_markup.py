import re

import pytest

from rednotebook.util.markup import convert_to_pango, convert_from_pango, \
    convert, _convert_paths


def touch(path):
    with open(path, 'w') as f:
        # Silence pyflakes.
        assert f


@pytest.mark.parametrize("t2t_markup,expected", [
    (r'--stricken--', '<s>stricken</s>'),
    (r'//italic//', '<i>italic</i>'),
    (r'--www.test.com--', '<s>www.test.com</s>'),
    # Linebreaks only on line ends
    (r'First\\Second', r'First\\Second'),
    (r'First\\', 'First\n'),
    (r'a&b', 'a&amp;b'),
    (r'a&amp;b', 'a&amp;b'),
    (r'http://site/s.php?q&c', 'http://site/s.php?q&amp;c'),
    (r'http://site/s.php?q&amp;c', 'http://site/s.php?q&amp;c'),
])
def test_pango(t2t_markup, expected):
    pango = convert_to_pango(t2t_markup)
    assert pango == expected
    # Ampersand escaping is only needed in sourcecode, so we do not try to
    # preserve the encoding
    if '&amp;' not in t2t_markup:
        assert convert_from_pango(pango) == t2t_markup


@pytest.mark.parametrize("markup,expected", [
    ('[""/image"".png?50]',
     '<img align="middle" width="50" src="/image.png" border="0" alt=""/>'),
    ('[""/image"".jpg]',
     '<img align="middle" src="/image.jpg" border="0" alt=""/>'),
    ('[""file:///image"".png?10]',
     '<img align="middle" width="10" src="file:///image.png" border="0" alt=""/>'),
    ('[""file:///image"".jpg]', '<img align="middle" '
                                'src="file:///image.jpg" border="0" '
                                'alt=""/>'),
])
def test_images(markup, expected, tmp_path):
    html = convert(markup, 'xhtml', tmp_path)
    location = re.search(r'(<img.*?>)', html).group(1)
    assert location == expected


@pytest.mark.parametrize("markup,expected_xhtml", [
    ('Simple [named reference 2019-08-01]', 'Simple <a href="#2019-08-01">named reference</a>'),
    ('An inline [2019-08-01] date', 'An inline <a href="#2019-08-01">2019-08-01</a> date'),
    ('[2019-10-20] is first', '<a href="#2019-10-20">2019-10-20</a> is first'),
    ('Spaces [ 2019-10-20  ] are fine too', 'Spaces <a href="#2019-10-20">2019-10-20</a> are fine too')
])
def test_reference_links_in_xhtml(markup, expected_xhtml, tmp_path):
    document = convert(markup, 'xhtml', tmp_path)
    assert expected_xhtml in document


@pytest.mark.parametrize("markup,expected_tex", [
    ('This is a [named reference 2019-08-01]', 'This is a named reference (2019-08-01)'),
    ('Today is 2019-08-01 - a wonderful day', 'Today is 2019-08-01 - a wonderful day'),
])
def test_reference_links_in_tex(markup, expected_tex, tmp_path):
    document = convert(markup, 'tex', tmp_path)
    assert expected_tex in document


@pytest.mark.parametrize("markup,expected", [
    ('[""/image"".png?50]', '\\includegraphics[width=50px]{"/image".png}'),
    ('[""/image"".jpg]', '\\includegraphics{"/image".jpg}'),
    ('[""file:///image"".png?10]', '\\includegraphics[width=10px]{"/image".png}'),
    ('[""file:///image"".jpg]', '\\includegraphics{"/image".jpg}'),
])
def test_images_latex(markup, expected, tmp_path):
    latex = convert(markup, 'tex', tmp_path)
    assert expected in latex


def test_relative_path_conversion(tmp_path):
    for path in [tmp_path / f for f in ('rel.jpg', 'rel.pdf')]:
        touch(path)
    tmp_path_uri = 'file://' + str(tmp_path)

    rel_paths = [
        ('[""file://rel"".jpg]', '[""%s/rel"".jpg]' % tmp_path_uri),
        ('[""rel"".jpg]', '[""%s/rel"".jpg]' % tmp_path_uri),
        ('[rel.pdf ""file://rel.pdf""]', '[rel.pdf ""%s/rel.pdf""]' % tmp_path_uri),
        ('[rel.pdf ""rel.pdf""]', '[rel.pdf ""%s/rel.pdf""]' % tmp_path_uri)
    ]

    for markup, expected in rel_paths:
        assert expected == _convert_paths(markup, tmp_path)


def test_absolute_path_conversion(tmp_path):
    abs_paths = [
        '[""file:///abs"".jpg]', '[""%s/aha 1"".jpg]' % tmp_path,
        '[abs.pdf ""file:///abs.pdf""]', '[abs.pdf ""%s/abs.pdf""]' % tmp_path,
        'www.google.com', 'www.google.com/page.php']

    for path in abs_paths:
        assert path == _convert_paths(path, tmp_path)
