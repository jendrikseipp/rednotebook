import pytest

from rednotebook.util import utils


@pytest.mark.parametrize(
    "version, tup",
    [
        ("1.2.11", (1, 2, 11)),
        ("1.2", (1, 2, 0)),
        ("1", (1, 0, 0)),
        ("1.", (1, 0, 0)),
        (" 1.", (1, 0, 0)),
    ],
)
def test_version_tuple(version, tup):
    assert utils._get_version_tuple(version) == tup


@pytest.mark.parametrize(
    "v1, v2, v2_newer",
    [
        ("1.2.11", "1.2.13", True),
        ("1.2.11", "1.1.13", False),
        ("1.2.11", "0.15.7", False),
        ("1.2.11", "1.3.7", True),
        ("1.2.11", "2", True),
    ],
)
def test_version_comparison(v1, v2, v2_newer):
    assert (utils._get_version_tuple(v2) > utils._get_version_tuple(v1)) == v2_newer
