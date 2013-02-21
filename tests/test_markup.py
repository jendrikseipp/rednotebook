import os
import re
import tempfile

from rednotebook.util.markup import convert_to_pango, convert_from_pango, \
                                    convert, _convert_paths
from rednotebook.util import filesystem

def touch(path):
    with open(path, 'w') as f:
        pass


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
        html = convert(markup, 'xhtml', '/tmp')
        location = re.search(r'(<img.*?>)', html).group(1)
        assert location == expected


def test_images_latex():
    vals = [('[""/image"".png?50]', '\includegraphics[width=50px]{"/image".png}'),
            ('[""/image"".jpg]', '\includegraphics{"/image".jpg}'),
            ('[""file:///image"".png?10]', '\includegraphics[width=10px]{"/image".png}'),
            ('[""file:///image"".jpg]', '\includegraphics{"/image".jpg}'),
           ]
    for markup, expected in vals:
        latex = convert(markup, 'tex', '/tmp')
        assert expected in latex

def test_path_conversion():
    tmpdir = tempfile.gettempdir()
    for path in [os.path.join(tmpdir, f) for f in ('rel.jpg', 'rel.pdf')]:
        touch(path)
    tmpdir_uri = 'file://' + tmpdir

    rel_paths = [('[""file://rel"".jpg]', '[""%s/rel"".jpg]' % tmpdir_uri),
                 ('[""rel"".jpg]', '[""%s/rel"".jpg]' % tmpdir_uri),
                 ('[rel.pdf ""file://rel.pdf""]', '[rel.pdf ""%s/rel.pdf""]' % tmpdir_uri),
                 ('[rel.pdf ""rel.pdf""]', '[rel.pdf ""%s/rel.pdf""]' % tmpdir_uri)]

    abs_paths = ['[""file:///abs"".jpg]', '[""/tmp/aha 1"".jpg]',
                 '[abs.pdf ""file:///abs.pdf""]', '[abs.pdf ""/tmp/abs.pdf""]',
                 'www.google.com', 'www.google.com/page.php'
                ]

    for old, new in rel_paths:
        assert new == _convert_paths(old, tmpdir)

    for path in abs_paths:
        assert path == _convert_paths(path, tmpdir)
