import re

from rednotebook.data import HASHTAG_PATTERN


def test_hashtags():
    vals = [
        ("test #hashtag", ["hashtag"]),
        ("text #hash0tag", ["hash0tag"]),
        ("text #1tag", ["1tag"]),
        ("text #hash_tag", ["hash_tag"]),
        ("text #1234", []),
        ("text #12é34", ["12é34"]),
        ("text#hashtag", []),
        ("texté#hashtag", []),
        ("text #hashtag1 #hashtag2", ["hashtag1", "hashtag2"]),
        ("text.#hashtag", ["hashtag"]),
        ("&#nbsp;", []),
        ("text #hashtag!", ["hashtag"]),
        ("text #dodge/#answer", ["dodge", "answer"]),
        ("text #dodge/answer", ["dodge"]),
        ("text dodge/#answer", ["answer"]),
        ("text #hashtagの", ["hashtagの"]),
        ("text #hashtag\u306e", ["hashtag\u306e"]),
        ("text　#hashtag", ["hashtag"]),
        ("#hashtag　text", ["hashtag"]),
        # (u"＃hashtag", [u'hashtag']),
        ("#éhashtag", ["éhashtag"]),
        ("#hashtagé", ["hashtagé"]),
        ("#hashétag", ["hashétag"]),
        ("test #hashtag école", ["hashtag"]),
        ("hex #11ff22", []),
        ('<font color="#40e0d0">', []),
        ("test &#hashtag", []),
        ("test ##hashtag", []),
        ("test #!/usr/bin/env", []),
        ("#include", []),
    ]
    for text, tags in vals:
        print(repr(text))
        results = re.findall(HASHTAG_PATTERN, text, flags=re.I | re.U)
        results = [hashtag for _, _hash, hashtag in results]
        assert results == tags
