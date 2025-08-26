import os

from rednotebook.util.filesystem import get_journal_title, is_kde_environment


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


def test_is_kde_environment():
    """Test KDE environment detection function."""
    # Save original environment
    original_env = {}
    for key in ["DESKTOP_SESSION", "KDE_SESSION_VERSION", "XDG_CURRENT_DESKTOP"]:
        original_env[key] = os.environ.get(key)

    try:
        # Test case 1: No KDE environment variables
        for key in ["DESKTOP_SESSION", "KDE_SESSION_VERSION", "XDG_CURRENT_DESKTOP"]:
            os.environ.pop(key, None)
        assert not is_kde_environment()

        # Test case 2: DESKTOP_SESSION contains "kde"
        os.environ["DESKTOP_SESSION"] = "kde"
        assert is_kde_environment()

        # Test case 3: DESKTOP_SESSION contains "plasma"
        os.environ["DESKTOP_SESSION"] = "plasma-x11"
        assert is_kde_environment()

        # Test case 4: KDE_SESSION_VERSION is set
        os.environ["DESKTOP_SESSION"] = "gnome"
        os.environ["KDE_SESSION_VERSION"] = "5"
        assert is_kde_environment()

        # Test case 5: XDG_CURRENT_DESKTOP contains "kde"
        os.environ.pop("KDE_SESSION_VERSION", None)
        os.environ["XDG_CURRENT_DESKTOP"] = "X-Cinnamon:KDE"
        assert is_kde_environment()

        # Test case 6: XDG_CURRENT_DESKTOP contains "plasma"
        os.environ["XDG_CURRENT_DESKTOP"] = "plasma:KDE"
        assert is_kde_environment()

        # Test case 7: Non-KDE environment
        os.environ["DESKTOP_SESSION"] = "gnome"
        os.environ["XDG_CURRENT_DESKTOP"] = "GNOME"
        assert not is_kde_environment()

    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
