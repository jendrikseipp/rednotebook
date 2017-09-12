from rednotebook.util import utils


def test_ngrams():
    for text, ngrams in [
            ('foo', ['f', 'o', 'o', 'fo', 'oo', 'foo']),
            ('foo fo', ['f', 'o', 'o', 'fo', 'oo', 'foo']),
            ('foo of', ['f', 'o', 'o', 'fo', 'oo', 'foo', 'of']),
            ]:
        assert utils.compute_ngrams(text) == set(ngrams)
