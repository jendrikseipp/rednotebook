import re

from rednotebook.util.markup import convert_to_pango, convert_from_pango, \
    convert, _convert_paths


def touch(path):
    with open(path, 'w') as f:
        # Silence pyflakes.
        assert(f)


def test_pango():
    vals = (
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
    )
    for t2t_markup, expected in vals:
        pango = convert_to_pango(t2t_markup)
        assert pango == expected
        # Ampersand escaping is only needed in sourcecode, so we do not try to
        # preserve the encoding
        if '&amp;' not in t2t_markup:
            assert convert_from_pango(pango) == t2t_markup


def test_images(tmp_path):
    vals = [
        ('[""/image"".png?50]',
         '<img align="middle" width="50" src="/image.png" border="0" alt=""/>'),
        ('[""/image"".jpg]',
         '<img align="middle" src="/image.jpg" border="0" alt=""/>'),
        ('[""file:///image"".png?10]',
         '<img align="middle" width="10" src="file:///image.png" border="0" alt=""/>'),
        ('[""file:///image"".jpg]', '<img align="middle" '
                                    'src="file:///image.jpg" border="0" '
                                    'alt=""/>'),
    ]
    for markup, expected in vals:
        html = convert(markup, 'xhtml', tmp_path)
        location = re.search(r'(<img.*?>)', html).group(1)
        assert location == expected


def test_reference_links_in_xhtml(tmp_path):
    test_cases = (
        ('[Named reference 2019-08-01]', '<a href="notebook:2019-08-01">Named reference</a>'),
        ('An inline 2019-08-01 date', 'An inline <a href="notebook:2019-08-01">2019-08-01</a> date'),
    )

    for markup, expected_xhtml in test_cases:
        document = convert(markup, 'xhtml', tmp_path)
        assert expected_xhtml in document


def test_reference_links_in_tex(tmp_path):
    test_cases = (
        ('This is a [named reference 2019-08-01]', 'This is a named reference (2019-08-01)'),
        ('Today is 2019-08-01 - a wonderful day', 'Today is 2019-08-01 - a wonderful day'),
    )

    for markup, expected_tex in test_cases:
        document = convert(markup, 'tex', tmp_path)
        assert expected_tex in document


def test_images_latex(tmp_path):
    vals = [
        ('[""/image"".png?50]', '\\includegraphics[width=50px]{"/image".png}'),
        ('[""/image"".jpg]', '\\includegraphics{"/image".jpg}'),
        ('[""file:///image"".png?10]', '\\includegraphics[width=10px]{"/image".png}'),
        ('[""file:///image"".jpg]', '\\includegraphics{"/image".jpg}'),
    ]
    for markup, expected in vals:
        latex = convert(markup, 'tex', tmp_path)
        assert expected in latex


def test_path_conversion(tmp_path):
    for path in [tmp_path / f for f in ('rel.jpg', 'rel.pdf')]:
        touch(path)
    tmp_path_uri = 'file://' + str(tmp_path)

    rel_paths = [
        ('[""file://rel"".jpg]', '[""%s/rel"".jpg]' % tmp_path_uri),
        ('[""rel"".jpg]', '[""%s/rel"".jpg]' % tmp_path_uri),
        ('[rel.pdf ""file://rel.pdf""]', '[rel.pdf ""%s/rel.pdf""]' % tmp_path_uri),
        ('[rel.pdf ""rel.pdf""]', '[rel.pdf ""%s/rel.pdf""]' % tmp_path_uri)
    ]

    abs_paths = [
        '[""file:///abs"".jpg]', '[""%s/aha 1"".jpg]' % tmp_path,
        '[abs.pdf ""file:///abs.pdf""]', '[abs.pdf ""%s/abs.pdf""]' % tmp_path,
        'www.google.com', 'www.google.com/page.php']

    for old, new in rel_paths:
        assert new == _convert_paths(old, tmp_path)

    for path in abs_paths:
        assert path == _convert_paths(path, tmp_path)
