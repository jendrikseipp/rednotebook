# -----------------------------------------------------------------------
# Copyright (c) 2026 Simon Glass
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
# with this program.  If not, see <https://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------

"""Git-based cloud sync for RedNotebook journals.

Provides automatic synchronisation of journal data across multiple machines
using git as the transport and merge engine. Edits to different days within
the same month file are merged automatically by git. When the same day is
edited on two machines, both versions are kept by appending the remote text.

Usage:
    Enable sync in the configuration with syncEnabled=1 and set
    syncRemoteUrl to a git remote (e.g. a private GitHub/GitLab repo).
    The journal data directory becomes a git repository. On each save,
    changes are committed and pushed. On each open, remote changes are
    pulled and merged.
"""

import logging
import os
import re
import subprocess
import threading

import yaml


try:
    from yaml import CLoader as Loader
    from yaml import CSafeDumper as Dumper
except ImportError:
    from yaml import Dumper, Loader


# Merge marker for text appended from a remote machine
MERGE_MARKER = "--- synced from remote ---\n"

# Shown when the git binary is missing. Install hints are platform-specific
# so we keep the message short; callers follow it with a help URL.
GIT_NOT_INSTALLED = (
    "git is not installed or not on PATH. "
    "Install it from https://git-scm.com and restart RedNotebook."
)


class GitNotInstalledError(FileNotFoundError):
    """Raised when the 'git' binary cannot be found on PATH."""


class SyncResult:
    """Outcome of a sync/pull operation.

    Truthy on success so `if sync.sync(...)` and `assert sync.sync(...)`
    work. Carries:
      - conflicts: 'YYYY-MM-DD' strings for days whose content was
        modified on both sides during the merge
      - pulled_new_data: True when a pull brought in new commits so
        callers know when to reload data from disk
      - error: on failure, a short human-readable string (git stderr
        where available). Empty on success.
    """

    def __init__(self, success, conflicts=None, pulled_new_data=False, error=""):
        self.success = success
        self.conflicts = list(conflicts) if conflicts else []
        self.pulled_new_data = pulled_new_data
        self.error = error or ""

    def __bool__(self):
        return self.success

    def __repr__(self):
        return (
            f"SyncResult(success={self.success}, "
            f"conflicts={self.conflicts!r}, "
            f"pulled_new_data={self.pulled_new_data}, "
            f"error={self.error!r})"
        )


# On Windows, spawning a console-mode child (git.exe) from a GUI app
# briefly pops a black console window for every call. CREATE_NO_WINDOW
# suppresses that flicker; the flag is a no-op on non-Windows platforms
# because subprocess exposes it only on Windows.
_SUBPROCESS_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _run_git(data_dir, *args, check=True):
    """Run a git command in the data directory.

    Args:
        data_dir: Path to the journal data directory (the git working tree).
        *args: Git subcommand and arguments.
        check: If True, raise on non-zero exit.

    Returns:
        subprocess.CompletedProcess with stdout/stderr captured as text.
    """
    cmd = ["git", "-C", data_dir] + list(args)
    logging.debug("sync: running %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            creationflags=_SUBPROCESS_FLAGS,
        )
    except FileNotFoundError as exc:
        logging.error("sync: %s", GIT_NOT_INSTALLED)
        raise GitNotInstalledError(GIT_NOT_INSTALLED) from exc
    if check and result.returncode != 0:
        logging.error("sync: git command failed: %s\n%s", " ".join(cmd), result.stderr)
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd,
            result.stdout,
            result.stderr,
        )
    return result


def _is_git_repo(data_dir):
    """Check whether data_dir is itself a git repository.

    Note: this returns False when data_dir is *inside* another git repo's
    working tree but is not itself the repo root. This matters because
    RedNotebook's default data dir (~/.rednotebook/data) sometimes lives
    inside a stray ~/.rednotebook/.git created by earlier sync attempts
    or manual setup - and if we accepted that as our repo we would end
    up committing/pushing files from the parent directory instead of the
    journal data.

    Raises GitNotInstalledError when git is missing - callers that just
    want a status probe should catch it.
    """
    result = _run_git(data_dir, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        return False
    toplevel = result.stdout.strip()
    if not toplevel:
        return False
    try:
        return os.path.samefile(toplevel, data_dir)
    except OSError:
        return False


def _has_commits(data_dir):
    """Check whether the repo has at least one commit."""
    result = _run_git(data_dir, "rev-parse", "HEAD", check=False)
    return result.returncode == 0


def _has_remote(data_dir, name="origin"):
    """Check whether a remote with the given name exists."""
    result = _run_git(data_dir, "remote", "get-url", name, check=False)
    return result.returncode == 0


def _has_changes(data_dir):
    """Check whether there are uncommitted changes (staged or unstaged)."""
    result = _run_git(data_dir, "status", "--porcelain")
    return bool(result.stdout.strip())


def _get_conflicted_files(data_dir):
    """Return a list of files with merge conflicts."""
    result = _run_git(data_dir, "diff", "--name-only", "--diff-filter=U", check=False)
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().splitlines() if f]


def _is_month_file(filename):
    """Check whether a filename matches the YYYY-MM.txt pattern."""
    return bool(re.match(r"\d{4}-\d{2}\.txt$", os.path.basename(filename)))


def _merge_yaml_day_text(local_text, remote_text):
    """Merge two versions of a day's text.

    If the texts are identical, return one copy. Otherwise concatenate
    them with a marker so the user can reconcile later.
    """
    if local_text == remote_text:
        return local_text
    # Check if one already contains the other (previous merge)
    if remote_text in local_text:
        return local_text
    if local_text in remote_text:
        return remote_text
    return local_text + "\n\n" + MERGE_MARKER + remote_text


def _merge_yaml_content(local_content, remote_content):
    """Merge two YAML day-content dicts (text + categories).

    Categories from both sides are combined. Text is merged with
    _merge_yaml_day_text().
    """
    merged = dict(local_content)

    # Merge text
    local_text = local_content.get("text", "")
    remote_text = remote_content.get("text", "")
    merged["text"] = _merge_yaml_day_text(local_text, remote_text)

    # Merge categories: keep all keys from both sides
    for key, value in remote_content.items():
        if key == "text":
            continue
        if key not in merged:
            merged[key] = value
        elif isinstance(merged[key], dict) and isinstance(value, dict):
            # Merge sub-entries within a category
            merged[key] = {**merged[key], **value}

    return merged


def _resolve_month_file(data_dir, filename):
    """Resolve a merge conflict in a month YAML file.

    Reads the local (ours), remote (theirs), and base versions, then
    merges day-by-day. Days that exist only on one side are kept.
    Days that differ are merged with _merge_yaml_content().

    Returns (success, conflict_days) where conflict_days is the list of
    day numbers (ints) whose content was modified on both sides and had
    to be merged together (not just picked up from one side).
    """
    filepath = os.path.join(data_dir, filename)

    try:
        # Extract the three merge versions
        base_result = _run_git(data_dir, "show", f":1:{filename}", check=False)
        ours_result = _run_git(data_dir, "show", f":2:{filename}", check=False)
        theirs_result = _run_git(data_dir, "show", f":3:{filename}", check=False)

        base_data = (
            yaml.load(base_result.stdout, Loader=Loader) if base_result.returncode == 0 else {}
        )
        ours_data = (
            yaml.load(ours_result.stdout, Loader=Loader) if ours_result.returncode == 0 else {}
        )
        theirs_data = (
            yaml.load(theirs_result.stdout, Loader=Loader) if theirs_result.returncode == 0 else {}
        )

        base_data = base_data or {}
        ours_data = ours_data or {}
        theirs_data = theirs_data or {}
    except yaml.YAMLError as exc:
        logging.error("sync: failed to parse YAML during conflict resolution: %s", exc)
        return False, []

    # Merge day by day
    all_days = set(ours_data.keys()) | set(theirs_data.keys())
    merged = {}
    conflict_days = []

    for day in sorted(all_days):
        ours_day = ours_data.get(day)
        theirs_day = theirs_data.get(day)

        if ours_day and not theirs_day:
            merged[day] = ours_day
        elif theirs_day and not ours_day:
            merged[day] = theirs_day
        elif ours_day == theirs_day:
            merged[day] = ours_day
        else:
            # Both sides modified the same day - merge content
            merged[day] = _merge_yaml_content(ours_day, theirs_day)
            conflict_days.append(day)

    # Write the resolved file
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(merged, f, Dumper=Dumper, allow_unicode=True)
        _run_git(data_dir, "add", filename)
        return True, conflict_days
    except OSError as exc:
        logging.error("sync: failed to write resolved file %s: %s", filepath, exc)
        return False, []


def _write_gitignore(data_dir):
    """Ensure a .gitignore exists that excludes temporary/backup files."""
    gitignore_path = os.path.join(data_dir, ".gitignore")
    patterns = [
        "*.new.txt",
        "*.old.txt",
        "*.CONFLICT_BACKUP*.txt",
    ]
    existing = ""
    if os.path.exists(gitignore_path):
        with open(gitignore_path, encoding="utf-8") as f:
            existing = f.read()

    missing = [p for p in patterns if p not in existing]
    if missing:
        with open(gitignore_path, "a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            for p in missing:
                f.write(p + "\n")


def _ensure_identity(data_dir):
    """Set a local user.email/user.name if git has none configured.

    'git commit' refuses to run without an author identity. Users with a
    global ~/.gitconfig already have one; users on a fresh install (e.g.
    first run after installing Git for Windows) do not. Fall back to a
    RedNotebook-specific identity in the local repo config so sync just
    works out of the box.
    """
    result = _run_git(data_dir, "config", "user.email", check=False)
    if result.returncode != 0:
        _run_git(data_dir, "config", "user.email", "noreply@rednotebook.app")
    result = _run_git(data_dir, "config", "user.name", check=False)
    if result.returncode != 0:
        _run_git(data_dir, "config", "user.name", "RedNotebook")


def init_repo(data_dir):
    """Initialise the data directory as a git repository if needed.

    Creates the repo, adds a .gitignore, and makes an initial commit
    if one does not already exist.

    Returns True if the repo is ready, False on failure.
    """
    try:
        if not _is_git_repo(data_dir):
            _run_git(data_dir, "init")
            # Force the branch name so two machines sync against the same
            # branch regardless of their local git's default (which varies:
            # 'master' on older git, 'main' on git 2.28+ unless overridden,
            # 'main' on macOS's Xcode git). Use symbolic-ref instead of
            # 'init -b' so this works on git older than 2.28 too.
            _run_git(data_dir, "symbolic-ref", "HEAD", "refs/heads/master")
            logging.info("sync: initialised git repo in %s", data_dir)

        _write_gitignore(data_dir)
        _ensure_identity(data_dir)

        if not _has_commits(data_dir):
            _run_git(data_dir, "add", "-A")
            _run_git(data_dir, "commit", "-m", "Initial journal commit")
            logging.info("sync: created initial commit")

        return True
    except GitNotInstalledError:
        # Propagate so the outer sync() handler can produce the
        # 'git is not installed' SyncResult with its install URL.
        raise
    except (subprocess.CalledProcessError, OSError) as exc:
        logging.error("sync: failed to initialise repo: %s", exc)
        return False


def set_remote(data_dir, url, name="origin"):
    """Set or update the git remote URL.

    Returns True on success.
    """
    try:
        if _has_remote(data_dir, name):
            _run_git(data_dir, "remote", "set-url", name, url)
        else:
            _run_git(data_dir, "remote", "add", name, url)
        logging.info("sync: remote '%s' set to %s", name, url)
        return True
    except subprocess.CalledProcessError as exc:
        logging.error("sync: failed to set remote: %s", exc)
        return False


def commit_changes(data_dir, message=None):
    """Stage all changes and create a commit.

    Args:
        data_dir: Path to the journal data directory.
        message: Optional commit message. A default is generated if omitted.

    Returns True if a commit was created, False if there was nothing to
    commit or on error.
    """
    try:
        if not _has_changes(data_dir):
            logging.debug("sync: nothing to commit")
            return False

        _run_git(data_dir, "add", "-A")

        if not message:
            message = "Journal update"

        _run_git(data_dir, "commit", "-m", message)
        logging.info("sync: committed changes")
        return True
    except subprocess.CalledProcessError as exc:
        logging.error("sync: commit failed: %s", exc)
        return False


def is_auth_error(error_text):
    """Heuristic: does this git error look like an authentication failure?"""
    if not error_text:
        return False
    lowered = error_text.lower()
    patterns = [
        "permission denied (publickey)",
        "permission denied, please try again",
        "authentication failed",
        "could not read username",
        "could not read password",
        "invalid username or token",
        "password authentication is not supported",
        "public key denied",
        "git@github.com: permission denied",
        "repository not found",  # GitHub's message
    ]
    if any(p in lowered for p in patterns):
        return True
    # Git's own 'fatal: repository '...' not found' - checked separately
    # because the URL sits between the two words.
    if "repository" in lowered and "not found" in lowered:
        return True
    return False


def auth_help_text(error_text):
    """Return a short user-facing hint for an auth failure."""
    if not error_text:
        return ""
    lowered = error_text.lower()
    if "publickey" in lowered or "public key" in lowered:
        return (
            "The SSH key on this machine is not authorised for the remote. "
            "Add its public key to your GitHub/GitLab account, or switch to "
            "an HTTPS URL with a personal access token."
        )
    if (
        "password authentication is not supported" in lowered
        or "invalid username or token" in lowered
        or "authentication failed" in lowered
    ):
        return (
            "GitHub no longer accepts passwords over HTTPS. Use a personal "
            "access token, or switch to an SSH URL like "
            "git@github.com:user/repo.git."
        )
    if "could not read username" in lowered or "could not read password" in lowered:
        return (
            "No credentials are available for this remote. Configure a git "
            "credential helper, use an SSH URL with a set-up SSH key, or "
            "embed a personal access token in the URL."
        )
    if "repository" in lowered and "not found" in lowered:
        return (
            "The remote repository could not be found. Check the URL is "
            "correct, and that your credentials give you access to it."
        )
    return ""


def format_conflict_note(conflicts):
    """Return the note text to append to today's entry for a conflict list."""
    return f"[Sync: please review conflicts on {', '.join(conflicts)}]"


def append_conflict_note(existing_text, conflicts):
    """Return existing_text with a conflict note appended.

    Idempotent: if the same note is already present, returns
    existing_text unchanged. If conflicts is empty, returns
    existing_text unchanged.
    """
    if not conflicts:
        return existing_text
    note = format_conflict_note(conflicts)
    existing = existing_text or ""
    if note in existing:
        return existing
    separator = "\n\n" if existing.strip() else ""
    return existing + separator + note


def _month_from_filename(filename):
    """Return (year, month) parsed from 'YYYY-MM.txt'."""
    base = os.path.basename(filename)
    return base[:4], base[5:7]


def pull_and_merge(data_dir, remote="origin", branch=None):
    """Pull from the remote and merge, resolving conflicts in YAML files.

    Args:
        data_dir: Path to the journal data directory.
        remote: Remote name (default "origin").
        branch: Branch to pull. If None, uses the current branch.

    Returns a SyncResult. SyncResult.conflicts holds the list of days
    ('YYYY-MM-DD' strings) whose content was modified on both sides.
    """
    if not _has_remote(data_dir, remote):
        logging.debug("sync: no remote '%s' configured, skipping pull", remote)
        return SyncResult(True)

    try:
        # Fetch first so we can check if there is anything new
        _run_git(data_dir, "fetch", remote)
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or "").strip() or str(exc)
        logging.warning("sync: fetch failed (network unavailable?): %s", err)
        return SyncResult(False, error=f"fetch failed: {err}")

    # Determine the branch to merge
    if not branch:
        result = _run_git(data_dir, "rev-parse", "--abbrev-ref", "HEAD", check=False)
        branch = result.stdout.strip() if result.returncode == 0 else "main"

    # Check if there is anything to merge
    remote_ref = f"{remote}/{branch}"
    result = _run_git(data_dir, "rev-parse", remote_ref, check=False)
    if result.returncode != 0:
        logging.debug("sync: remote branch %s does not exist yet", remote_ref)
        return SyncResult(True)

    # Record HEAD before merging so we can tell whether the merge
    # actually brought in new commits. Callers use this to decide
    # whether to reload the journal data from disk.
    head_before = _run_git(data_dir, "rev-parse", "HEAD", check=False)
    head_before_sha = head_before.stdout.strip() if head_before.returncode == 0 else ""

    # Try the merge
    merge_result = _run_git(data_dir, "merge", remote_ref, check=False)

    # First-sync case: local and remote were both initialised
    # independently and share no ancestor. Retry with the flag that
    # tells git it is OK to merge two separate histories - that is
    # exactly what we want when combining machines for the first time.
    if merge_result.returncode != 0 and "unrelated histories" in merge_result.stderr:
        logging.info(
            "sync: local and remote have unrelated histories; "
            "retrying with --allow-unrelated-histories"
        )
        merge_result = _run_git(
            data_dir,
            "merge",
            "--allow-unrelated-histories",
            remote_ref,
            check=False,
        )

    def _pulled_new_data():
        head_after = _run_git(data_dir, "rev-parse", "HEAD", check=False)
        head_after_sha = head_after.stdout.strip() if head_after.returncode == 0 else ""
        return bool(head_after_sha) and head_after_sha != head_before_sha

    if merge_result.returncode == 0:
        pulled = _pulled_new_data()
        if pulled:
            logging.info("sync: pull and merge succeeded, new data pulled")
        else:
            logging.info("sync: pull and merge succeeded, already up to date")
        return SyncResult(True, pulled_new_data=pulled)

    # Handle conflicts
    conflicted = _get_conflicted_files(data_dir)
    if not conflicted:
        err = (merge_result.stderr or "").strip() or "unknown merge error"
        logging.error("sync: merge failed but no conflicts found:\n%s", err)
        _run_git(data_dir, "merge", "--abort", check=False)
        return SyncResult(False, error=f"merge failed: {err}")

    logging.info("sync: resolving %d conflicted file(s)", len(conflicted))

    all_resolved = True
    all_conflicts = []
    for filename in conflicted:
        if _is_month_file(filename):
            resolved, days = _resolve_month_file(data_dir, filename)
            if resolved:
                year, month = _month_from_filename(filename)
                for day in days:
                    all_conflicts.append(f"{year}-{month}-{int(day):02d}")
                logging.info(
                    "sync: resolved conflict in %s (days: %s)",
                    filename,
                    days or "none",
                )
            else:
                logging.error("sync: failed to resolve conflict in %s", filename)
                all_resolved = False
        else:
            # For non-month files (e.g. .gitignore), keep ours
            _run_git(data_dir, "checkout", "--ours", filename)
            _run_git(data_dir, "add", filename)
            logging.info("sync: kept local version of %s", filename)

    if all_resolved:
        _run_git(data_dir, "commit", "--no-edit")
        if all_conflicts:
            logging.warning(
                "sync: merged remote changes; days with content conflicts: %s",
                ", ".join(all_conflicts),
            )
        else:
            logging.info("sync: merge conflict resolution committed")
        # Reached here because a merge happened - HEAD definitely moved.
        return SyncResult(True, all_conflicts, pulled_new_data=True)
    else:
        _run_git(data_dir, "merge", "--abort", check=False)
        logging.error("sync: could not resolve all conflicts, merge aborted")
        return SyncResult(False, error="could not resolve all merge conflicts")


def push(data_dir, remote="origin", branch=None):
    """Push committed changes to the remote.

    Returns (success, error_message). error_message is empty on success
    and set to git's stderr text on failure so the caller can display
    it to the user (auth failures, non-fast-forward pushes, etc.).
    """
    if not _has_remote(data_dir, remote):
        logging.debug("sync: no remote '%s' configured, skipping push", remote)
        return True, ""

    # Always pass an explicit refspec: 'git push -u origin' fails on the
    # first push because git refuses to guess the branch. 'HEAD' resolves
    # to the current branch and works for subsequent pushes too.
    ref = branch or "HEAD"
    try:
        result = _run_git(data_dir, "push", "-u", remote, ref, check=False)
    except OSError as exc:
        logging.warning("sync: push failed: %s", exc)
        return False, str(exc)

    if result.returncode == 0:
        logging.info("sync: pushed to %s", remote)
        return True, ""

    err = result.stderr.strip() or result.stdout.strip() or "unknown error"
    logging.error("sync: push failed:\n%s", err)
    return False, err


def test_remote(url, timeout=60):
    """Test whether a git remote URL is reachable and authorised.

    Runs 'git ls-remote' against the URL without touching any local
    state. This validates the URL is well-formed, the network can
    reach it, and any required authentication succeeds.

    Args:
        url: Git remote URL to test.
        timeout: Seconds to wait before giving up.

    Returns:
        Tuple (success: bool, message: str). The message is either a
        summary of what was found (e.g. number of refs) on success, or
        the git error output on failure.
    """
    if not url:
        return False, "No URL provided"

    # Let git use its configured credential helpers so a Test on a
    # private HTTPS remote can trigger the usual auth flow (e.g. Git
    # Credential Manager opening a browser on Windows). The UI runs
    # test_remote on a background thread, so a slow interactive helper
    # does not freeze the dialog; subprocess.run's timeout still bounds
    # the wait.
    cmd = ["git", "ls-remote", "--heads", url]
    logging.debug("sync: testing remote with %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            creationflags=_SUBPROCESS_FLAGS,
        )
    except subprocess.TimeoutExpired:
        return False, f"Timed out after {timeout}s"
    except FileNotFoundError:
        return False, GIT_NOT_INSTALLED

    if result.returncode == 0:
        refs = [line for line in result.stdout.strip().splitlines() if line]
        if refs:
            return True, f"Reachable ({len(refs)} branch(es) on remote)"
        return True, "Reachable (empty repository)"

    err = result.stderr.strip() or result.stdout.strip() or "unknown error"
    return False, err


def sync(data_dir, remote_url=None, remote="origin", branch=None):
    """Perform a full sync cycle: commit, pull+merge, push.

    Args:
        data_dir: Path to the journal data directory.
        remote_url: If given, ensure the named git remote points at this
            URL before syncing.
        remote: Remote name.
        branch: Branch name. If None, uses the current branch.

    Returns a SyncResult. SyncResult.conflicts lists any days that had
    content merged from both sides during the pull step.
    """
    try:
        return _sync(data_dir, remote_url, remote, branch)
    except GitNotInstalledError as exc:
        return SyncResult(False, error=str(exc))


def _sync(data_dir, remote_url, remote, branch):
    logging.info("sync: starting sync cycle")

    if not _is_git_repo(data_dir):
        if not init_repo(data_dir):
            return SyncResult(False, error="could not initialise git repository")

    if remote_url:
        set_remote(data_dir, remote_url, remote)

    # A sync with no remote configured is a no-op that would silently
    # succeed. That is almost never what the user intends when they
    # explicitly ask for a sync, so surface it as an error.
    if not _has_remote(data_dir, remote):
        logging.error(
            "sync: no remote URL configured. Set 'Remote URL' in Preferences > Sync and click OK."
        )
        return SyncResult(False, error="no remote URL configured")

    # 1. Commit any local changes
    commit_changes(data_dir)

    # 2. Pull and merge remote changes
    pull_result = pull_and_merge(data_dir, remote, branch)
    if not pull_result:
        return pull_result

    # 3. Push our changes
    pushed, push_error = push(data_dir, remote, branch)
    if not pushed:
        return SyncResult(
            False,
            pull_result.conflicts,
            pulled_new_data=pull_result.pulled_new_data,
            error=f"push failed: {push_error}" if push_error else "push failed",
        )

    logging.info("sync: sync cycle complete")
    return SyncResult(
        True,
        pull_result.conflicts,
        pulled_new_data=pull_result.pulled_new_data,
    )


def pull_on_open(data_dir, remote_url=None, remote="origin", branch=None):
    """Pull remote changes before opening the journal.

    Similar to sync() but without committing or pushing - just fetch
    and merge so the user sees the latest data from other machines.

    Args:
        data_dir: Path to the journal data directory.
        remote_url: If given, ensure the named git remote points at
            this URL before pulling.
        remote: Remote name.
        branch: Branch to pull. If None, uses the current branch.

    Returns a SyncResult carrying any conflict day strings.
    """
    try:
        return _pull_on_open(data_dir, remote_url, remote, branch)
    except GitNotInstalledError as exc:
        return SyncResult(False, error=str(exc))


def _pull_on_open(data_dir, remote_url, remote, branch):
    if not _is_git_repo(data_dir):
        return SyncResult(True)  # Not a sync-enabled journal

    if remote_url:
        set_remote(data_dir, remote_url, remote)

    if not _has_remote(data_dir, remote):
        return SyncResult(True)

    logging.info("sync: pulling latest changes before opening journal")

    # Commit any uncommitted local changes first (e.g. from a crash)
    if _has_changes(data_dir):
        commit_changes(data_dir, "Auto-commit before pull (uncommitted changes found)")

    return pull_and_merge(data_dir, remote, branch)


class AsyncSyncer:
    """Run sync() on a background thread.

    A second request that arrives while a sync is running is dropped, not
    queued. Results are handed to 'dispatch', which must run its callback
    on the UI thread (the app passes GLib.idle_add), so on_done callbacks
    can safely touch the UI. Taking 'dispatch' as a parameter keeps this
    module free of GTK imports.
    """

    def __init__(self, dispatch):
        self._dispatch = dispatch
        self._lock = threading.Lock()
        self._running = False

    def is_running(self):
        with self._lock:
            return self._running

    def run(self, data_dir, remote_url=None, branch=None, on_done=None):
        """Start a sync on a background thread.

        on_done is dispatched with the SyncResult, or with None if the
        request was dropped because a sync was already in flight, so
        callers can tell 'skipped' from 'ran'.
        """
        with self._lock:
            if self._running:
                logging.debug("sync: another sync is already running, skipping")
                if on_done:
                    self._dispatch(on_done, None)
                return
            self._running = True

        def worker():
            try:
                result = sync(data_dir, remote_url=remote_url, branch=branch)
            except Exception:
                logging.exception("sync: unexpected error in background sync")
                result = SyncResult(False)
            finally:
                with self._lock:
                    self._running = False
            if on_done:
                self._dispatch(on_done, result)

        threading.Thread(target=worker, daemon=True, name="sync-worker").start()
