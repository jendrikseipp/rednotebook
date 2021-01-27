from rednotebook.util.filesystem import get_journal_title


def test_journal_title():
    dirs = [
        ("/home/my journal", "my journal"),
        ("/my journal/", "my journal"),
        ("/home/name/Journal", "Journal"),
        ("/home/name/jörnal", "jörnal"),
        ("/", "/"),
    ]
    for path, title in dirs:
        assert get_journal_title(path) == title
