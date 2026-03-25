"""Gather recent commits across all worktrees with file stats.

Called from a background worker thread. Runs git log in each worktree
and returns commits with denormalized file lists.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from haiv.helpers.tui.TuiModel import CommitEntry, CommitFileEntry, RecentCommitsRaw


def gather_recent_commits(
    worktrees_dir: Path,
    *,
    max_commits_per_worktree: int = 10,
) -> RecentCommitsRaw:
    """Gather recent commits across all worktrees.

    Returns commits sorted by timestamp descending (newest first).
    """
    if not worktrees_dir.is_dir():
        return RecentCommitsRaw()

    all_commits: list[CommitEntry] = []

    for wt_dir in worktrees_dir.iterdir():
        if not wt_dir.is_dir() or wt_dir.name.startswith("."):
            continue
        worktree = wt_dir.name

        commits = _git_log_with_files(wt_dir, max_commits_per_worktree)
        for c in commits:
            c.worktree = worktree
        all_commits.extend(commits)

    all_commits.sort(key=lambda c: c.timestamp, reverse=True)
    return RecentCommitsRaw(commits=all_commits)


def _git_log_with_files(worktree: Path, count: int) -> list[CommitEntry]:
    """Get commits with metadata and file stats in a single git call.

    Uses a null-byte prefix in the format string as a commit separator.
    The output pattern per commit is:
        \\x00HASH\\x00SHORT\\x00SUBJECT\\x00AUTHOR\\x00TIMESTAMP
        (blank line)
        numstat lines...
    """
    try:
        result = subprocess.run(
            ["git", "log", f"-{count}", "--numstat", "--format=%x00%H%x00%h%x00%s%x00%an%x00%at"],
            cwd=worktree,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, OSError):
        return []

    return parse_git_log_numstat(result.stdout)


def parse_git_log_numstat(output: str) -> list[CommitEntry]:
    """Parse combined git log --numstat output into CommitEntry objects.

    Exported for testing. The format string uses \\x00 as field separator
    and commit delimiter (each commit's format line starts with \\x00).
    """
    if not output.strip():
        return []

    # Split on \x00 — first element is empty (leading \x00), rest alternate
    # between commit headers and gaps
    chunks = output.split("\x00")

    commits: list[CommitEntry] = []
    for chunk in chunks:
        if not chunk:
            continue

        lines = chunk.splitlines()
        if not lines:
            continue

        # First line is: HASH\x00SHORT\x00... but we already split on \x00,
        # so we need to collect the next 4 chunks as fields.
        # Actually — let me rethink. The format is:
        #   \x00HASH\x00SHORT\x00SUBJECT\x00AUTHOR\x00TIMESTAMP
        # Split on \x00 gives: ["", "HASH", "SHORT", "SUBJECT", "AUTHOR", "TIMESTAMP\n\nfiles..."]
        # So every 5 chunks after the first empty = one commit's fields.
        pass

    # Re-approach: split on \x00 gives us alternating fields.
    # Fields 1-5 = first commit, field 5 contains timestamp + \n\n + numstat.
    # Fields 6-10 = second commit, etc.
    parts = output.split("\x00")
    # Drop leading empty from initial \x00
    if parts and parts[0] == "":
        parts = parts[1:]
    elif parts and not parts[0].strip():
        parts = parts[1:]

    commits = []
    i = 0
    while i + 4 < len(parts):
        full_hash = parts[i]
        short_hash = parts[i + 1]
        subject = parts[i + 2]
        author = parts[i + 3]
        tail = parts[i + 4]  # "TIMESTAMP\n\nnumstat_lines...\n"
        i += 5

        # Parse timestamp from first line of tail, rest is numstat
        tail_lines = tail.splitlines()
        try:
            timestamp = float(tail_lines[0]) if tail_lines else 0.0
        except ValueError:
            timestamp = 0.0

        # Numstat lines start after the blank line following the timestamp
        files: list[CommitFileEntry] = []
        for line in tail_lines[1:]:
            if not line:
                continue
            tab_parts = line.split("\t", 2)
            if len(tab_parts) == 3:
                try:
                    adds = int(tab_parts[0]) if tab_parts[0] != "-" else 0
                    dels = int(tab_parts[1]) if tab_parts[1] != "-" else 0
                except ValueError:
                    continue
                files.append(CommitFileEntry(
                    path=tab_parts[2],
                    additions=adds,
                    deletions=dels,
                ))

        commits.append(CommitEntry(
            hash=full_hash,
            short_hash=short_hash,
            subject=subject,
            author=author,
            timestamp=timestamp,
            files=files,
        ))

    return commits
