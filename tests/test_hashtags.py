# -*- coding: utf-8 -*-

import re

from rednotebook.data import HASHTAG_PATTERN

def test_hashtags():
    vals = [('test #hashtag', ['hashtag']),
            ("text #hash0tag", ['hash0tag']),
            ("text #1tag", ['1tag']),
            ("text #hash_tag", ['hash_tag']),
            ("text #1234", []),
            (u"text #12é34", [u'12é34']),
            ("text#hashtag", []),
            (u"texté#hashtag", []),
            ("text #hashtag1 #hashtag2", ['hashtag1', 'hashtag2']),
            ("text.#hashtag", ['hashtag']),
            ("&#nbsp;", []),
            ("text #hashtag!", ['hashtag']),
            ("text #dodge/#answer", ['dodge', 'answer']),
            ("text #dodge/answer", ['dodge']),
            ("text dodge/#answer", ['answer']),
            (u"text #hashtagの", [u'hashtagの']),
            (u"text #hashtag\u306e", [u'hashtag\u306e']),
            ("text　#hashtag", ['hashtag']),
            (u"#hashtag　text", ['hashtag']),
            #(u"＃hashtag", [u'hashtag']),
            (u"#éhashtag", [u'éhashtag']),
            (u"#hashtagé", [u'hashtagé']),
            (u"#hashétag", [u'hashétag']),
            (u'test #hashtag école', ['hashtag']),
            ('hex #11ff22', []),
            ('<font color="#40e0d0">', []),
            ('test &#hashtag', []),
            ('test ##hashtag', []),
            ('test #!/usr/bin/env', []),
            ('#include', []),
    ]
    for text, tags in vals:
        print repr(text)
        results = re.findall(HASHTAG_PATTERN, text, flags=re.I | re.U)
        results = [hashtag for _, _hash, hashtag in results]
        assert results == tags
