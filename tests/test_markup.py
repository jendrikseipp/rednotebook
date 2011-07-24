from rednotebook.util.markup import convert_to_pango, convert_from_pango

def assert_equal(param, expected):
    assert param == expected

def test_pango():
    vals = ((r'--stricken--', '<s>stricken</s>'),
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
        yield assert_equal, pango, expected
        # Ampersand escaping is only needed in sourcecode, so we do not try to
        # preserve the encoding
        if not '&amp;' in t2t_markup:
            yield assert_equal, convert_from_pango(pango), t2t_markup
