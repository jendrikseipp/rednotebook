import re

from rednotebook.util.markup import convert_to_pango, convert_from_pango, \
                                    convert


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
        assert pango == expected
        # Ampersand escaping is only needed in sourcecode, so we do not try to
        # preserve the encoding
        if not '&amp;' in t2t_markup:
            assert convert_from_pango(pango) == t2t_markup


def test_images():
    vals = [('[""/image"".png?50]',
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
        html = convert(markup, 'xhtml')
        location = re.search(r'(<img.*?>)', html).group(1)
        assert location == expected


def test_images_latex():
    vals = [('[""/image"".png?50]', '\includegraphics[width=50px]{"/image".png}'),
            ('[""/image"".jpg]', '\includegraphics{"/image".jpg}'),
            ('[""file:///image"".png?10]', '\includegraphics[width=10px]{"/image".png}'),
            ('[""file:///image"".jpg]', '\includegraphics{"/image".jpg}'),
           ]
    for markup, expected in vals:
        latex = convert(markup, 'tex')
        assert expected in latex


def test_formula_latex():
    vals = [('$abc$', '$abc$'), ('$ abc$', '$abc$'),
            ('$abc $', '$abc$'), ('$ abc $', '$abc$'),
            ('$\sum$', '$\sum$'),
            ('$\sum_{i=1}$', '$\sum_{i=1}$'),
            ('$\sum_{i=1}^n i = \\frac{n \\cdot (n+1)}{2}$',) * 2,
            #('$$abc$$', '$$abc$$')
            ]
    for formula, expected in vals:
        latex = convert(formula, 'tex')
        latex = latex[latex.find('\\clearpage') + 13:latex.find('% LaTeX2e code') - 3]
        assert expected == latex
