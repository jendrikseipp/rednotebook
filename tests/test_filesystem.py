import os

from rednotebook.util.filesystem import get_journal_title


def test_journal_title():
    root = os.path.abspath(os.sep)
    dirs = [
        ("/home/my journal", "my journal"),
        ("/my journal/", "my journal"),
        ("/home/name/Journal", "Journal"),
        ("/home/name/jörnal", "jörnal"),
        (root, root),
    ]
    for path, title in dirs:
        assert get_journal_title(path) == title
