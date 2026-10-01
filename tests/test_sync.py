"""Tests for the git-based sync module."""

import os
import subprocess
import tempfile
import threading

import pytest
import yaml

from rednotebook import sync


def _git(repo, *args):
    """Helper to run git commands in a test repo."""
    subprocess.run(
        ["git", "-C", repo] + list(args),
        capture_output=True,
        text=True,
        check=True,
    )


def _write_month(data_dir, filename, data):
    """Write a YAML month file."""
    with open(os.path.join(data_dir, filename), "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)


def _read_month(data_dir, filename):
    """Read a YAML month file."""
    with open(os.path.join(data_dir, filename), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _make_repo(path):
    """Create a git repo with an initial commit.

    Force the branch to 'master' so tests run the same way on git versions
    that default to 'main' (git 2.28+, macOS Xcode git).
    """
    os.makedirs(path, exist_ok=True)
    _git(path, "init", "-b", "master")
    _git(path, "config", "user.email", "test@test.com")
    _git(path, "config", "user.name", "Test")
    # Create an initial file so we have a commit
    with open(os.path.join(path, ".gitignore"), "w") as f:
        f.write("*.new.txt\n*.old.txt\n")
    _git(path, "add", "-A")
    _git(path, "commit", "-m", "init")


class TestMissingGit:
    """When git is missing from PATH, sync surfaces a clear error."""

    def _without_git(self, monkeypatch):
        # Point PATH at an empty directory so 'git' cannot be found
        empty = tempfile.mkdtemp()
        monkeypatch.setenv("PATH", empty)

    def test_sync_without_git_reports_error(self, monkeypatch, tmp_path):
        self._without_git(monkeypatch)
        data = tmp_path / "data"
        data.mkdir()
        result = sync.sync(str(data))
        assert not result
        assert "git is not installed" in result.error.lower()
        assert "git-scm.com" in result.error

    def test_pull_on_open_without_git_reports_error(self, monkeypatch, tmp_path):
        self._without_git(monkeypatch)
        data = tmp_path / "data"
        data.mkdir()
        # pull_on_open calls _is_git_repo first which fails cleanly
        result = sync.pull_on_open(str(data))
        assert not result
        assert "git is not installed" in result.error.lower()

    def test_test_remote_without_git(self, monkeypatch):
        self._without_git(monkeypatch)
        ok, message = sync.test_remote("git@example.com:x/y.git")
        assert not ok
        assert "git is not installed" in message.lower()

    def test_is_git_repo_raises_without_git(self, monkeypatch, tmp_path):
        self._without_git(monkeypatch)
        with pytest.raises(sync.GitNotInstalledError):
            sync._is_git_repo(str(tmp_path))


class TestSyncResult:
    def test_truthy_on_success(self):
        assert sync.SyncResult(True)
        assert not sync.SyncResult(False)


class TestHelpers:
    def test_is_month_file(self):
        assert sync._is_month_file("2024-03.txt")
        assert sync._is_month_file("1999-12.txt")
        assert not sync._is_month_file("notes.txt")
        assert not sync._is_month_file("2024-03.new.txt")
        assert not sync._is_month_file(".gitignore")

    def test_merge_yaml_day_text_identical(self):
        text = "Hello world"
        assert sync._merge_yaml_day_text(text, text) == text

    def test_merge_yaml_day_text_different(self):
        result = sync._merge_yaml_day_text("Local text", "Remote text")
        assert "Local text" in result
        assert "Remote text" in result
        assert sync.MERGE_MARKER in result

    def test_merge_yaml_day_text_subset(self):
        # If one contains the other, return the larger one
        short = "Hello"
        long = "Hello\n\nMore text"
        assert sync._merge_yaml_day_text(long, short) == long
        assert sync._merge_yaml_day_text(short, long) == long

    def test_merge_yaml_content_text_only(self):
        local = {"text": "Local entry"}
        remote = {"text": "Remote entry"}
        merged = sync._merge_yaml_content(local, remote)
        assert "Local entry" in merged["text"]
        assert "Remote entry" in merged["text"]

    def test_merge_yaml_content_categories(self):
        local = {"text": "Same", "tags": {"work": None}}
        remote = {"text": "Same", "tags": {"personal": None}, "mood": {"happy": None}}
        merged = sync._merge_yaml_content(local, remote)
        assert merged["text"] == "Same"
        assert "work" in merged["tags"]
        assert "personal" in merged["tags"]
        assert "happy" in merged["mood"]


class TestInitRepo:
    def test_init_new_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "data")
            os.makedirs(data_dir)
            _write_month(data_dir, "2024-03.txt", {1: {"text": "Hello"}})

            assert sync.init_repo(data_dir)
            assert sync._is_git_repo(data_dir)
            assert sync._has_commits(data_dir)

    def test_init_existing_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "data")
            _make_repo(data_dir)

            # Should succeed without error
            assert sync.init_repo(data_dir)

    def test_gitignore_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "data")
            os.makedirs(data_dir)
            sync.init_repo(data_dir)

            gitignore = os.path.join(data_dir, ".gitignore")
            assert os.path.exists(gitignore)
            with open(gitignore) as f:
                content = f.read()
            assert "*.new.txt" in content
            assert "*.old.txt" in content
            assert "*.CONFLICT_BACKUP*.txt" in content


class TestCommitChanges:
    def test_commit_new_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "data")
            _make_repo(data_dir)
            _write_month(data_dir, "2024-03.txt", {1: {"text": "Hello"}})

            assert sync.commit_changes(data_dir, "Test commit")

    def test_nothing_to_commit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "data")
            _make_repo(data_dir)

            assert not sync.commit_changes(data_dir)

    def test_commit_default_message(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "data")
            _make_repo(data_dir)
            _write_month(data_dir, "2024-03.txt", {1: {"text": "Hello"}})

            assert sync.commit_changes(data_dir)

            # Verify commit message
            result = subprocess.run(
                ["git", "-C", data_dir, "log", "-1", "--format=%s"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert result.stdout.strip() == "Journal update"


class TestSetRemote:
    def test_add_remote(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "data")
            _make_repo(data_dir)

            assert sync.set_remote(data_dir, "/tmp/fake-remote.git")
            assert sync._has_remote(data_dir)

    def test_update_remote(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "data")
            _make_repo(data_dir)

            sync.set_remote(data_dir, "/tmp/old-remote.git")
            assert sync.set_remote(data_dir, "/tmp/new-remote.git")

            result = subprocess.run(
                ["git", "-C", data_dir, "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert result.stdout.strip() == "/tmp/new-remote.git"


class TestPullAndMerge:
    def _make_pair(self, tmpdir):
        """Create a 'remote' bare repo and a 'local' clone."""
        remote_dir = os.path.join(tmpdir, "remote.git")
        local_dir = os.path.join(tmpdir, "local")

        # Create the bare remote
        os.makedirs(remote_dir)
        _git(remote_dir, "init", "--bare", "-b", "master")

        # Create local repo and push to remote
        _make_repo(local_dir)
        _git(local_dir, "remote", "add", "origin", remote_dir)
        _write_month(local_dir, "2024-03.txt", {1: {"text": "Day 1 entry"}})
        _git(local_dir, "add", "-A")
        _git(local_dir, "commit", "-m", "Add March data")
        _git(local_dir, "push", "-u", "origin", "master")

        return remote_dir, local_dir

    def test_pull_no_remote(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "data")
            _make_repo(data_dir)
            # No remote configured - should succeed silently
            assert sync.pull_and_merge(data_dir)

    def test_pull_no_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_dir, local_dir = self._make_pair(tmpdir)
            assert sync.pull_and_merge(local_dir)

    def test_pull_new_remote_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_dir, local_dir = self._make_pair(tmpdir)

            # Simulate another machine pushing changes via a second clone
            other_dir = os.path.join(tmpdir, "other")
            _git(tmpdir, "clone", remote_dir, "other")
            _git(other_dir, "config", "user.email", "test@test.com")
            _git(other_dir, "config", "user.name", "Test")
            _write_month(
                other_dir,
                "2024-03.txt",
                {
                    1: {"text": "Day 1 entry"},
                    5: {"text": "Day 5 from other machine"},
                },
            )
            _git(other_dir, "add", "-A")
            _git(other_dir, "commit", "-m", "Add day 5")
            _git(other_dir, "push")

            # Now pull into local
            assert sync.pull_and_merge(local_dir)

            # Verify day 5 is present
            data = _read_month(local_dir, "2024-03.txt")
            assert 5 in data
            assert "Day 5 from other machine" in data[5]["text"]

    def test_pull_conflict_different_days(self):
        """Edits to different days in the same month should auto-merge."""
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_dir, local_dir = self._make_pair(tmpdir)

            # Other machine adds day 10
            other_dir = os.path.join(tmpdir, "other")
            _git(tmpdir, "clone", remote_dir, "other")
            _git(other_dir, "config", "user.email", "test@test.com")
            _git(other_dir, "config", "user.name", "Test")
            _write_month(
                other_dir,
                "2024-03.txt",
                {
                    1: {"text": "Day 1 entry"},
                    10: {"text": "Day 10 from other"},
                },
            )
            _git(other_dir, "add", "-A")
            _git(other_dir, "commit", "-m", "Add day 10")
            _git(other_dir, "push")

            # Local adds day 15
            _write_month(
                local_dir,
                "2024-03.txt",
                {
                    1: {"text": "Day 1 entry"},
                    15: {"text": "Day 15 from local"},
                },
            )
            _git(local_dir, "add", "-A")
            _git(local_dir, "commit", "-m", "Add day 15")

            # Pull should merge cleanly (different days)
            assert sync.pull_and_merge(local_dir)

            data = _read_month(local_dir, "2024-03.txt")
            assert 1 in data
            assert 10 in data
            assert 15 in data

    def test_pull_conflict_same_day(self):
        """Edits to the same day should be resolved by appending."""
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_dir, local_dir = self._make_pair(tmpdir)

            # Other machine modifies day 1
            other_dir = os.path.join(tmpdir, "other")
            _git(tmpdir, "clone", remote_dir, "other")
            _git(other_dir, "config", "user.email", "test@test.com")
            _git(other_dir, "config", "user.name", "Test")
            _write_month(
                other_dir,
                "2024-03.txt",
                {
                    1: {"text": "Day 1 edited on other machine"},
                },
            )
            _git(other_dir, "add", "-A")
            _git(other_dir, "commit", "-m", "Edit day 1")
            _git(other_dir, "push")

            # Local also modifies day 1
            _write_month(
                local_dir,
                "2024-03.txt",
                {
                    1: {"text": "Day 1 edited locally"},
                },
            )
            _git(local_dir, "add", "-A")
            _git(local_dir, "commit", "-m", "Edit day 1 locally")

            # Pull should resolve conflict
            assert sync.pull_and_merge(local_dir)

            data = _read_month(local_dir, "2024-03.txt")
            # Both versions should be present
            assert "edited locally" in data[1]["text"]
            assert "edited on other machine" in data[1]["text"]


class TestAppendConflictNote:
    """The helper that adds a to-do note to today's entry."""

    def test_empty_conflicts_returns_text_unchanged(self):
        assert sync.append_conflict_note("hello", []) == "hello"
        assert sync.append_conflict_note("", []) == ""
        assert sync.append_conflict_note(None, []) is None

    def test_appended_to_empty(self):
        result = sync.append_conflict_note("", ["2024-03-01"])
        assert "2024-03-01" in result
        assert not result.startswith("\n")

    def test_appended_to_none(self):
        result = sync.append_conflict_note(None, ["2024-03-01"])
        assert "2024-03-01" in result

    def test_separator_added_after_existing_content(self):
        result = sync.append_conflict_note("Today I wrote", ["2024-03-01"])
        assert result.startswith("Today I wrote\n\n[Sync:")

    def test_multiple_conflicts_listed(self):
        result = sync.append_conflict_note("", ["2024-03-01", "2024-05-20"])
        assert "2024-03-01" in result
        assert "2024-05-20" in result

    def test_idempotent_same_note(self):
        first = sync.append_conflict_note("hi", ["2024-03-01"])
        second = sync.append_conflict_note(first, ["2024-03-01"])
        assert first == second

    def test_different_conflicts_appended_separately(self):
        first = sync.append_conflict_note("", ["2024-03-01"])
        second = sync.append_conflict_note(first, ["2024-05-20"])
        assert "2024-03-01" in second
        assert "2024-05-20" in second
        # Two separate notes
        assert second.count("[Sync:") == 2


class TestConflictReporting:
    """sync() must report which days had genuine content conflicts."""

    def _setup(self, tmpdir):
        remote_dir = os.path.join(tmpdir, "remote.git")
        os.makedirs(remote_dir)
        _git(remote_dir, "init", "--bare", "-b", "master")

        a_dir = os.path.join(tmpdir, "a")
        _make_repo(a_dir)
        _git(a_dir, "remote", "add", "origin", remote_dir)
        _write_month(
            a_dir,
            "2024-03.txt",
            {
                1: {"text": "baseline"},
                5: {"text": "baseline day 5"},
            },
        )
        _write_month(
            a_dir,
            "2024-04.txt",
            {
                2: {"text": "baseline april"},
            },
        )
        _git(a_dir, "add", "-A")
        _git(a_dir, "commit", "-m", "baseline")
        _git(a_dir, "push", "-u", "origin", "master")

        b_dir = os.path.join(tmpdir, "b")
        _git(tmpdir, "clone", remote_dir, "b")
        _git(b_dir, "config", "user.email", "test@test.com")
        _git(b_dir, "config", "user.name", "Test")
        return a_dir, b_dir

    def test_no_conflicts_reported_for_clean_sync(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a_dir, b_dir = self._setup(tmpdir)
            data = _read_month(b_dir, "2024-03.txt")
            data[10] = {"text": "new day, no conflict"}
            _write_month(b_dir, "2024-03.txt", data)
            result = sync.sync(b_dir)
            assert result
            assert result.conflicts == []

    def test_single_conflict_reported(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a_dir, b_dir = self._setup(tmpdir)

            data = _read_month(a_dir, "2024-03.txt")
            data[1] = {"text": "A's version of day 1"}
            _write_month(a_dir, "2024-03.txt", data)
            assert sync.sync(a_dir)

            data = _read_month(b_dir, "2024-03.txt")
            data[1] = {"text": "B's version of day 1"}
            _write_month(b_dir, "2024-03.txt", data)
            result = sync.sync(b_dir)
            assert result
            assert result.conflicts == ["2024-03-01"]

    def test_multiple_conflicts_across_files_reported(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a_dir, b_dir = self._setup(tmpdir)

            # A modifies days 1 and 5 in March, and day 2 in April
            data = _read_month(a_dir, "2024-03.txt")
            data[1] = {"text": "A day 1"}
            data[5] = {"text": "A day 5"}
            _write_month(a_dir, "2024-03.txt", data)
            data = _read_month(a_dir, "2024-04.txt")
            data[2] = {"text": "A april"}
            _write_month(a_dir, "2024-04.txt", data)
            assert sync.sync(a_dir)

            # B independently modifies the same three days differently
            data = _read_month(b_dir, "2024-03.txt")
            data[1] = {"text": "B day 1"}
            data[5] = {"text": "B day 5"}
            _write_month(b_dir, "2024-03.txt", data)
            data = _read_month(b_dir, "2024-04.txt")
            data[2] = {"text": "B april"}
            _write_month(b_dir, "2024-04.txt", data)

            result = sync.sync(b_dir)
            assert result
            assert sorted(result.conflicts) == [
                "2024-03-01",
                "2024-03-05",
                "2024-04-02",
            ]

    def test_disjoint_edits_are_not_conflicts(self):
        """Edits to different days on each side do not count as conflicts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            a_dir, b_dir = self._setup(tmpdir)

            data = _read_month(a_dir, "2024-03.txt")
            data[10] = {"text": "A only"}
            _write_month(a_dir, "2024-03.txt", data)
            assert sync.sync(a_dir)

            data = _read_month(b_dir, "2024-03.txt")
            data[20] = {"text": "B only"}
            _write_month(b_dir, "2024-03.txt", data)
            result = sync.sync(b_dir)
            assert result
            # Same file was touched on both sides but no day overlaps
            assert result.conflicts == []

    def test_pull_on_open_returns_conflicts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a_dir, b_dir = self._setup(tmpdir)

            data = _read_month(a_dir, "2024-03.txt")
            data[1] = {"text": "A"}
            _write_month(a_dir, "2024-03.txt", data)
            assert sync.sync(a_dir)

            # B has a competing local commit but hasn't pushed
            data = _read_month(b_dir, "2024-03.txt")
            data[1] = {"text": "B"}
            _write_month(b_dir, "2024-03.txt", data)
            _git(b_dir, "add", "-A")
            _git(b_dir, "commit", "-m", "b day 1")

            result = sync.pull_on_open(b_dir)
            assert result
            assert result.conflicts == ["2024-03-01"]


class TestConflictScenarios:
    """End-to-end conflict scenarios that mirror real two-machine use.

    Each test simulates two machines editing the same journal via two
    clones of a bare remote, then verifies exactly what ends up in the
    merged YAML.
    """

    def _three_repos(self, tmpdir):
        """Create bare remote + two clones ('a' and 'b')."""
        remote_dir = os.path.join(tmpdir, "remote.git")
        os.makedirs(remote_dir)
        _git(remote_dir, "init", "--bare", "-b", "master")

        a_dir = os.path.join(tmpdir, "a")
        _make_repo(a_dir)
        _git(a_dir, "remote", "add", "origin", remote_dir)
        _write_month(
            a_dir,
            "2024-03.txt",
            {
                1: {"text": "Baseline day 1"},
                2: {"text": "Baseline day 2"},
            },
        )
        _git(a_dir, "add", "-A")
        _git(a_dir, "commit", "-m", "baseline")
        _git(a_dir, "push", "-u", "origin", "master")

        b_dir = os.path.join(tmpdir, "b")
        _git(tmpdir, "clone", remote_dir, "b")
        _git(b_dir, "config", "user.email", "test@test.com")
        _git(b_dir, "config", "user.name", "Test")

        return remote_dir, a_dir, b_dir

    def test_disjoint_days_merge_cleanly(self):
        """A edits day 5, B edits day 10. Both entries survive verbatim."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, a_dir, b_dir = self._three_repos(tmpdir)

            data = _read_month(a_dir, "2024-03.txt")
            data[5] = {"text": "New from A"}
            _write_month(a_dir, "2024-03.txt", data)
            assert sync.sync(a_dir)

            data = _read_month(b_dir, "2024-03.txt")
            data[10] = {"text": "New from B"}
            _write_month(b_dir, "2024-03.txt", data)
            assert sync.sync(b_dir)

            # A pulls what B pushed
            assert sync.sync(a_dir)

            result = _read_month(a_dir, "2024-03.txt")
            assert result[1]["text"] == "Baseline day 1"
            assert result[2]["text"] == "Baseline day 2"
            assert result[5]["text"] == "New from A"
            assert result[10]["text"] == "New from B"

    def test_same_day_both_texts_kept(self):
        """A and B both rewrite day 1. Both texts land, with the marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, a_dir, b_dir = self._three_repos(tmpdir)

            data = _read_month(a_dir, "2024-03.txt")
            data[1] = {"text": "Rewritten by A"}
            _write_month(a_dir, "2024-03.txt", data)
            assert sync.sync(a_dir)

            data = _read_month(b_dir, "2024-03.txt")
            data[1] = {"text": "Rewritten by B"}
            _write_month(b_dir, "2024-03.txt", data)
            # B must pull first (A pushed), which triggers the conflict
            assert sync.sync(b_dir)

            result = _read_month(b_dir, "2024-03.txt")
            merged = result[1]["text"]
            assert "Rewritten by A" in merged
            assert "Rewritten by B" in merged
            assert sync.MERGE_MARKER in merged
            # Other days are untouched
            assert result[2]["text"] == "Baseline day 2"

    def test_same_day_identical_text_deduplicated(self):
        """If A and B independently type the same text, no marker appears."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, a_dir, b_dir = self._three_repos(tmpdir)

            same = "Both machines wrote this identical text"
            data = _read_month(a_dir, "2024-03.txt")
            data[1] = {"text": same}
            _write_month(a_dir, "2024-03.txt", data)
            assert sync.sync(a_dir)

            data = _read_month(b_dir, "2024-03.txt")
            data[1] = {"text": same}
            _write_month(b_dir, "2024-03.txt", data)
            assert sync.sync(b_dir)

            result = _read_month(b_dir, "2024-03.txt")
            assert result[1]["text"] == same
            assert sync.MERGE_MARKER not in result[1]["text"]

    def test_same_day_one_is_extension_of_other(self):
        """If one side just appended, the longer text is kept without marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, a_dir, b_dir = self._three_repos(tmpdir)

            # A keeps day 1 as baseline. B extends it.
            data = _read_month(b_dir, "2024-03.txt")
            data[1] = {"text": "Baseline day 1\n\nExtra thought from B"}
            _write_month(b_dir, "2024-03.txt", data)
            assert sync.sync(b_dir)

            # A adds day 3, doesn't touch day 1
            data = _read_month(a_dir, "2024-03.txt")
            data[3] = {"text": "Something on day 3 from A"}
            _write_month(a_dir, "2024-03.txt", data)
            assert sync.sync(a_dir)

            result = _read_month(a_dir, "2024-03.txt")
            assert result[1]["text"] == "Baseline day 1\n\nExtra thought from B"
            assert sync.MERGE_MARKER not in result[1]["text"]
            assert result[3]["text"] == "Something on day 3 from A"

    def test_categories_from_both_sides_kept(self):
        """Same day, different tag categories — union of both is kept."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, a_dir, b_dir = self._three_repos(tmpdir)

            data = _read_month(a_dir, "2024-03.txt")
            data[1] = {"text": "Day 1 with A tags", "tags": {"work": None}}
            _write_month(a_dir, "2024-03.txt", data)
            assert sync.sync(a_dir)

            data = _read_month(b_dir, "2024-03.txt")
            data[1] = {
                "text": "Day 1 with B tags",
                "tags": {"personal": None},
                "mood": {"happy": None},
            }
            _write_month(b_dir, "2024-03.txt", data)
            assert sync.sync(b_dir)

            result = _read_month(b_dir, "2024-03.txt")
            assert "work" in result[1]["tags"]
            assert "personal" in result[1]["tags"]
            assert "happy" in result[1]["mood"]

    def test_new_month_files_from_each_side(self):
        """A creates April, B creates May — both files land on both."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, a_dir, b_dir = self._three_repos(tmpdir)

            _write_month(a_dir, "2024-04.txt", {1: {"text": "April from A"}})
            assert sync.sync(a_dir)

            _write_month(b_dir, "2024-05.txt", {1: {"text": "May from B"}})
            assert sync.sync(b_dir)
            assert sync.sync(a_dir)

            assert _read_month(a_dir, "2024-04.txt")[1]["text"] == "April from A"
            assert _read_month(a_dir, "2024-05.txt")[1]["text"] == "May from B"

    def test_three_way_pingpong(self):
        """A -> B -> A -> B, each side adding one day each round."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, a_dir, b_dir = self._three_repos(tmpdir)

            for day, machine, label in [
                (5, a_dir, "A round 1"),
                (6, b_dir, "B round 1"),
                (7, a_dir, "A round 2"),
                (8, b_dir, "B round 2"),
            ]:
                data = _read_month(machine, "2024-03.txt")
                data[day] = {"text": label}
                _write_month(machine, "2024-03.txt", data)
                assert sync.sync(machine)

            # Final sync so A gets B's round 2 push
            assert sync.sync(a_dir)

            result = _read_month(a_dir, "2024-03.txt")
            for day, expected in [
                (5, "A round 1"),
                (6, "B round 1"),
                (7, "A round 2"),
                (8, "B round 2"),
            ]:
                assert result[day]["text"] == expected, f"day {day}: got {result.get(day)}"


class TestSync:
    def test_full_sync_no_remote_fails(self):
        """Sync without a remote configured must fail loudly, not silently.

        Regression: previously sync() with no origin returned success
        after skipping pull and push, leaving the user with an empty
        remote repository and no clear error.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "data")
            os.makedirs(data_dir)
            _write_month(data_dir, "2024-03.txt", {1: {"text": "Hello"}})

            sync.init_repo(data_dir)
            _git(data_dir, "config", "user.email", "test@test.com")
            _git(data_dir, "config", "user.name", "Test")

            result = sync.sync(data_dir)
            assert not result

    def test_full_sync_with_remote(self):
        """Full sync cycle with a remote repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_dir = os.path.join(tmpdir, "remote.git")
            local_dir = os.path.join(tmpdir, "local")

            os.makedirs(remote_dir)
            _git(remote_dir, "init", "--bare", "-b", "master")

            # Set up local
            _make_repo(local_dir)
            _git(local_dir, "remote", "add", "origin", remote_dir)
            _write_month(local_dir, "2024-03.txt", {1: {"text": "Hello"}})
            _git(local_dir, "add", "-A")
            _git(local_dir, "commit", "-m", "initial data")
            _git(local_dir, "push", "-u", "origin", "master")

            # Make a local change
            _write_month(
                local_dir,
                "2024-03.txt",
                {
                    1: {"text": "Hello"},
                    2: {"text": "New day"},
                },
            )

            assert sync.sync(local_dir)

            # Verify pushed - clone and check
            verify_dir = os.path.join(tmpdir, "verify")
            _git(tmpdir, "clone", remote_dir, "verify")
            data = _read_month(verify_dir, "2024-03.txt")
            assert 2 in data
            assert data[2]["text"] == "New day"


class TestSyncSetsRemote:
    """Regression: sync() must configure the remote from the URL argument.

    Previously the sync() call sites (menu, save_to_disk) didn't set the
    remote before running the sync cycle, so pull/push silently skipped
    when the git repo had no origin configured yet.
    """

    def test_sync_adds_missing_remote(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_dir = os.path.join(tmpdir, "remote.git")
            local_dir = os.path.join(tmpdir, "local")

            os.makedirs(remote_dir)
            _git(remote_dir, "init", "--bare", "-b", "master")

            os.makedirs(local_dir)
            _write_month(local_dir, "2024-03.txt", {1: {"text": "hi"}})
            assert sync.init_repo(local_dir)
            _git(local_dir, "config", "user.email", "test@test.com")
            _git(local_dir, "config", "user.name", "Test")

            # Repo has no remote yet - sync must add it from the URL
            assert not sync._has_remote(local_dir)
            assert sync.sync(local_dir, remote_url=remote_dir)
            assert sync._has_remote(local_dir)

            # And the push actually happened
            result = subprocess.run(
                ["git", "-C", remote_dir, "log", "--oneline"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert result.stdout.strip()


class TestAuthErrorDetection:
    def test_ssh_publickey_denied(self):
        assert sync.is_auth_error("git@github.com: Permission denied (publickey).")
        hint = sync.auth_help_text("Permission denied (publickey).")
        assert "SSH key" in hint

    def test_https_password_deprecated(self):
        err = "remote: Password authentication is not supported for Git operations."
        assert sync.is_auth_error(err)
        hint = sync.auth_help_text(err)
        assert "personal access token" in hint.lower() or "token" in hint.lower()

    def test_no_credentials(self):
        err = "fatal: could not read Username for 'https://github.com': No such device"
        assert sync.is_auth_error(err)
        hint = sync.auth_help_text(err)
        assert "credential" in hint.lower() or "token" in hint.lower()

    def test_repository_not_found(self):
        err = "fatal: repository 'https://github.com/x/y.git' not found"
        assert sync.is_auth_error(err)
        hint = sync.auth_help_text(err)
        assert "url" in hint.lower() or "credentials" in hint.lower()

    def test_authentication_failed(self):
        err = "remote: Authentication failed"
        assert sync.is_auth_error(err)
        assert sync.auth_help_text(err)

    def test_not_an_auth_error(self):
        assert not sync.is_auth_error("")
        assert not sync.is_auth_error("fatal: refusing to merge unrelated histories")
        assert not sync.is_auth_error(
            "Updates were rejected because the tip of your current branch is behind"
        )
        assert not sync.is_auth_error(None)

    def test_hint_empty_for_generic_error(self):
        assert sync.auth_help_text("some random error") == ""


class TestErrorReporting:
    """SyncResult.error must contain a useful message on failure."""

    def test_no_remote_reports_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "data")
            os.makedirs(data_dir)
            _write_month(data_dir, "2024-03.txt", {1: {"text": "hi"}})
            assert sync.init_repo(data_dir)
            _git(data_dir, "config", "user.email", "test@test.com")
            _git(data_dir, "config", "user.name", "Test")

            result = sync.sync(data_dir)
            assert not result
            assert "no remote" in result.error.lower()

    def test_push_failure_reports_git_stderr(self):
        """A push to a nonexistent remote should surface the git error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "data")
            os.makedirs(data_dir)
            _write_month(data_dir, "2024-03.txt", {1: {"text": "hi"}})
            assert sync.init_repo(data_dir)
            _git(data_dir, "config", "user.email", "test@test.com")
            _git(data_dir, "config", "user.name", "Test")

            # Point origin at a nonexistent local path so push fails
            fake_remote = os.path.join(tmpdir, "does-not-exist.git")
            sync.set_remote(data_dir, fake_remote)

            result = sync.sync(data_dir, remote_url=fake_remote)
            assert not result
            assert result.error  # not empty
            # Git will complain about the remote in some way
            assert any(
                word in result.error.lower()
                for word in ("does not appear", "not a git", "fetch failed", "unable")
            ), f"unexpected error: {result.error!r}"

    def test_successful_sync_has_empty_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_dir = os.path.join(tmpdir, "remote.git")
            local_dir = os.path.join(tmpdir, "local")
            os.makedirs(remote_dir)
            _git(remote_dir, "init", "--bare", "-b", "master")

            os.makedirs(local_dir)
            _write_month(local_dir, "2024-03.txt", {1: {"text": "hi"}})
            assert sync.init_repo(local_dir)
            _git(local_dir, "config", "user.email", "test@test.com")
            _git(local_dir, "config", "user.name", "Test")

            result = sync.sync(local_dir, remote_url=remote_dir)
            assert result
            assert result.error == ""


class TestPulledNewData:
    """sync() must report whether the pull actually brought new commits."""

    def _pair(self, tmpdir):
        remote_dir = os.path.join(tmpdir, "remote.git")
        os.makedirs(remote_dir)
        _git(remote_dir, "init", "--bare", "-b", "master")

        a_dir = os.path.join(tmpdir, "a")
        _make_repo(a_dir)
        _git(a_dir, "remote", "add", "origin", remote_dir)
        _write_month(a_dir, "2024-03.txt", {1: {"text": "seed"}})
        _git(a_dir, "add", "-A")
        _git(a_dir, "commit", "-m", "seed")
        _git(a_dir, "push", "-u", "origin", "master")

        b_dir = os.path.join(tmpdir, "b")
        _git(tmpdir, "clone", remote_dir, "b")
        _git(b_dir, "config", "user.email", "test@test.com")
        _git(b_dir, "config", "user.name", "Test")
        return a_dir, b_dir

    def test_already_up_to_date_reports_no_new_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a_dir, b_dir = self._pair(tmpdir)
            result = sync.sync(b_dir)
            assert result
            assert not result.pulled_new_data

    def test_fast_forward_pull_reports_new_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a_dir, b_dir = self._pair(tmpdir)

            # A adds a new file and pushes
            _write_month(a_dir, "2024-04.txt", {1: {"text": "new"}})
            _git(a_dir, "add", "-A")
            _git(a_dir, "commit", "-m", "add april")
            _git(a_dir, "push")

            # B pulls -- should report new data
            result = sync.sync(b_dir)
            assert result
            assert result.pulled_new_data
            # And the file lands on B's disk
            assert os.path.exists(os.path.join(b_dir, "2024-04.txt"))

    def test_conflict_merge_reports_new_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a_dir, b_dir = self._pair(tmpdir)

            data = _read_month(a_dir, "2024-03.txt")
            data[1] = {"text": "A version"}
            _write_month(a_dir, "2024-03.txt", data)
            assert sync.sync(a_dir)

            data = _read_month(b_dir, "2024-03.txt")
            data[1] = {"text": "B version"}
            _write_month(b_dir, "2024-03.txt", data)
            result = sync.sync(b_dir)
            assert result
            assert result.pulled_new_data
            assert result.conflicts == ["2024-03-01"]

    def test_only_pushing_reports_no_new_data(self):
        """If B only pushes local changes and doesn't pull anything new."""
        with tempfile.TemporaryDirectory() as tmpdir:
            a_dir, b_dir = self._pair(tmpdir)
            data = _read_month(b_dir, "2024-03.txt")
            data[15] = {"text": "B local"}
            _write_month(b_dir, "2024-03.txt", data)
            result = sync.sync(b_dir)
            assert result
            assert not result.pulled_new_data


class TestAsyncSyncer:
    """The real sync.AsyncSyncer, dispatching inline instead of via GLib."""

    @staticmethod
    def _inline(fn, *args):
        fn(*args)

    def test_result_is_dispatched(self, monkeypatch):
        monkeypatch.setattr(sync, "sync", lambda *args, **kwargs: sync.SyncResult(True))
        done = threading.Event()
        results = []

        def on_done(result):
            results.append(result)
            done.set()

        sync.AsyncSyncer(self._inline).run("/tmp/x", on_done=on_done)
        assert done.wait(5)
        assert len(results) == 1 and results[0]

    def test_second_call_while_running_is_dropped(self, monkeypatch):
        started = threading.Event()
        release = threading.Event()

        def blocking_sync(*args, **kwargs):
            started.set()
            release.wait(5)
            return sync.SyncResult(True)

        monkeypatch.setattr(sync, "sync", blocking_sync)
        syncer = sync.AsyncSyncer(self._inline)
        first_done = threading.Event()
        results = []

        def on_first(result):
            results.append(("first", result))
            first_done.set()

        syncer.run("/tmp/x", on_done=on_first)
        assert started.wait(5)
        assert syncer.is_running()

        # The second request is dropped and reported straight away
        syncer.run("/tmp/x", on_done=lambda result: results.append(("second", result)))
        assert results == [("second", None)]

        release.set()
        assert first_done.wait(5)
        assert not syncer.is_running()
        assert results[1][0] == "first" and results[1][1]

    def test_exception_in_sync_reports_failure(self, monkeypatch):
        def failing_sync(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(sync, "sync", failing_sync)
        done = threading.Event()
        results = []

        def on_done(result):
            results.append(result)
            done.set()

        syncer = sync.AsyncSyncer(self._inline)
        syncer.run("/tmp/x", on_done=on_done)
        assert done.wait(5)
        assert not results[0]
        assert not syncer.is_running()


class TestNestedRepo:
    """Regression: _is_git_repo must not accept a parent git repo.

    If ~/.rednotebook/ was set up as a git repo by a previous manual
    sync attempt, ~/.rednotebook/data/ is inside that repo's working
    tree. Old code treated data/ as 'already a git repo' and every
    sync operated on the parent, silently pushing the wrong files.
    """

    def test_child_dir_not_treated_as_parent_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            parent = os.path.join(tmpdir, "parent")
            child = os.path.join(parent, "data")
            os.makedirs(child)
            _git(parent, "init")

            # Sanity: git considers child to be inside the parent repo
            result = subprocess.run(
                ["git", "-C", child, "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert result.stdout.strip() == "true"

            # But our check must say child is not itself a repo
            assert not sync._is_git_repo(child)
            # And parent should be recognised as a repo
            assert sync._is_git_repo(parent)

    def test_init_repo_creates_child_repo_inside_parent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            parent = os.path.join(tmpdir, "parent")
            child = os.path.join(parent, "data")
            os.makedirs(child)
            _git(parent, "init")
            _write_month(child, "2024-03.txt", {1: {"text": "hi"}})

            assert sync.init_repo(child)
            # child now has its own .git and is its own repo
            assert os.path.isdir(os.path.join(child, ".git"))
            assert sync._is_git_repo(child)

            # And its git top-level is child, not parent
            result = subprocess.run(
                ["git", "-C", child, "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert os.path.realpath(result.stdout.strip()) == os.path.realpath(child)


class TestUnrelatedHistories:
    """First sync from a new machine: local and remote share no ancestor."""

    def test_pull_with_unrelated_histories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Remote: bare repo with its own initial commit
            remote_dir = os.path.join(tmpdir, "remote.git")
            os.makedirs(remote_dir)
            _git(remote_dir, "init", "--bare", "-b", "master")

            seed_dir = os.path.join(tmpdir, "seed")
            _make_repo(seed_dir)
            _git(seed_dir, "remote", "add", "origin", remote_dir)
            _write_month(seed_dir, "2024-01.txt", {1: {"text": "Seed from other machine"}})
            _git(seed_dir, "add", "-A")
            _git(seed_dir, "commit", "-m", "seed")
            _git(seed_dir, "push", "-u", "origin", "master")

            # Local: independently initialised, with its own history
            local_dir = os.path.join(tmpdir, "local")
            os.makedirs(local_dir)
            _write_month(local_dir, "2024-03.txt", {1: {"text": "Local existing entry"}})
            assert sync.init_repo(local_dir)
            _git(local_dir, "config", "user.email", "test@test.com")
            _git(local_dir, "config", "user.name", "Test")

            # First sync: merge two unrelated histories
            assert sync.sync(local_dir, remote_url=remote_dir)

            # Both files should now be present locally
            data_jan = _read_month(local_dir, "2024-01.txt")
            assert data_jan[1]["text"] == "Seed from other machine"
            data_mar = _read_month(local_dir, "2024-03.txt")
            assert data_mar[1]["text"] == "Local existing entry"

            # And the remote should have both files after push
            result = subprocess.run(
                ["git", "-C", remote_dir, "ls-tree", "-r", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert "2024-01.txt" in result.stdout
            assert "2024-03.txt" in result.stdout


class TestFirstPush:
    """Regression: first push to a fresh empty remote must succeed."""

    def test_first_push_to_empty_remote(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_dir = os.path.join(tmpdir, "remote.git")
            local_dir = os.path.join(tmpdir, "local")

            os.makedirs(remote_dir)
            _git(remote_dir, "init", "--bare", "-b", "master")

            os.makedirs(local_dir)
            _write_month(local_dir, "2024-03.txt", {1: {"text": "hi"}})

            assert sync.init_repo(local_dir)
            _git(local_dir, "config", "user.email", "test@test.com")
            _git(local_dir, "config", "user.name", "Test")
            assert sync.set_remote(local_dir, remote_dir)
            assert sync.sync(local_dir)

            # Verify the remote has the commit and the journal file
            result = subprocess.run(
                ["git", "-C", remote_dir, "log", "--oneline"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert result.stdout.strip(), "remote has no commits after first push"

            result = subprocess.run(
                ["git", "-C", remote_dir, "ls-tree", "-r", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert "2024-03.txt" in result.stdout


class TestTestRemote:
    def test_empty_url(self):
        ok, message = sync.test_remote("")
        assert not ok
        assert "No URL" in message

    def test_local_bare_repo(self):
        """Test against a real (local) bare repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_dir = os.path.join(tmpdir, "remote.git")
            os.makedirs(remote_dir)
            _git(remote_dir, "init", "--bare", "-b", "master")

            ok, message = sync.test_remote(remote_dir)
            assert ok
            assert "empty" in message.lower() or "branch" in message.lower()

    def test_local_repo_with_branches(self):
        """A repo with branches reports the branch count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_dir = os.path.join(tmpdir, "remote.git")
            local_dir = os.path.join(tmpdir, "local")

            os.makedirs(remote_dir)
            _git(remote_dir, "init", "--bare", "-b", "master")

            _make_repo(local_dir)
            _git(local_dir, "remote", "add", "origin", remote_dir)
            _write_month(local_dir, "2024-03.txt", {1: {"text": "hi"}})
            _git(local_dir, "add", "-A")
            _git(local_dir, "commit", "-m", "data")
            _git(local_dir, "push", "-u", "origin", "master")

            ok, message = sync.test_remote(remote_dir)
            assert ok
            assert "1" in message  # 1 branch

    def test_nonexistent_url(self):
        ok, message = sync.test_remote("/nonexistent/path/to/repo.git")
        assert not ok
        assert message  # Should have an error message


class TestPullOnOpen:
    def test_not_a_git_repo(self):
        """Should return True for non-git directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert sync.pull_on_open(tmpdir)

    def test_no_remote(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_repo(tmpdir)
            assert sync.pull_on_open(tmpdir)

    def test_pulls_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_dir = os.path.join(tmpdir, "remote.git")
            local_dir = os.path.join(tmpdir, "local")

            os.makedirs(remote_dir)
            _git(remote_dir, "init", "--bare", "-b", "master")

            _make_repo(local_dir)
            _git(local_dir, "remote", "add", "origin", remote_dir)
            _write_month(local_dir, "2024-03.txt", {1: {"text": "Hello"}})
            _git(local_dir, "add", "-A")
            _git(local_dir, "commit", "-m", "initial")
            _git(local_dir, "push", "-u", "origin", "master")

            # Simulate remote change
            other_dir = os.path.join(tmpdir, "other")
            _git(tmpdir, "clone", remote_dir, "other")
            _git(other_dir, "config", "user.email", "test@test.com")
            _git(other_dir, "config", "user.name", "Test")
            _write_month(
                other_dir,
                "2024-03.txt",
                {
                    1: {"text": "Hello"},
                    3: {"text": "From other"},
                },
            )
            _git(other_dir, "add", "-A")
            _git(other_dir, "commit", "-m", "day 3")
            _git(other_dir, "push")

            assert sync.pull_on_open(local_dir)
            data = _read_month(local_dir, "2024-03.txt")
            assert 3 in data
