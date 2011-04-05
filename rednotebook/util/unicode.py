# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2009  Jendrik Seipp
#
# RedNotebook is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# RedNotebook is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with RedNotebook; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# -----------------------------------------------------------------------

import htmlentitydefs


def make_transdict():
    '''
    returns a dict that maps unicode chars to corresponding
    chars without tildes etc.
    '''
    cp2n = htmlentitydefs.codepoint2name
    #suffixes = 'acute crave circ uml slash tilde cedil'.split()
    suffixes = htmlentitydefs.name2codepoint.keys()
    td = {}
    for x in range(128, 256):
        if x not in cp2n: continue
        n = cp2n[x]
        for s in suffixes:
            if n.endswith(s):
                td[x] = unicode(n[-len(s)])
                break
    return td


def coll(us, td=make_transdict()):
    '''
    Unicode sort function

    Usage:
    unicode_strings = [u'\xe9cole', u'ecole', u'las', u'laß', u'lax',
                        u'ueber', u'über', u'zer']
    unicode_strings.sort(key=coll)
    '''
    if type(us) is not unicode:
        us = unicode(us, errors='replace')
    return us.translate(td)


def test_unicode_sorting():
    l = [u'\xe9cole', u'ecole', u'las', u'laß', u'lax',
         u'ueber', u'über', u'zer']
    l = [u'z', u'äpfel', u'apfel', u'fohlen', u'école', u'e',
         u'sonne', u'ßonne', u'somnia']
    print sorted(l, key=coll)

    from unicodedata import normalize
    norm = map(lambda u: normalize('NFD', u.lower()), l)
    print sorted(norm)

    from locale import strxfrm
    bin = map(lambda u: u.encode('utf-8'), l)
    print sorted(bin, key=strxfrm)

if __name__ == '__main__':
    test_unicode_sorting()
