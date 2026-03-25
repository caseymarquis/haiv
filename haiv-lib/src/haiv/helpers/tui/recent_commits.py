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

        metadata = _git_log_metadata(wt_dir, max_commits_per_worktree)
        file_stats = _git_log_numstat(wt_dir, max_commits_per_worktree)

        for i, meta in enumerate(metadata):
            files = file_stats[i] if i < len(file_stats) else []
            meta.worktree = worktree
            meta.files = files
            all_commits.append(meta)

    all_commits.sort(key=lambda c: c.timestamp, reverse=True)
    return RecentCommitsRaw(commits=all_commits)


def _git_log_metadata(worktree: Path, count: int) -> list[CommitEntry]:
    """Get commit metadata: hash, short_hash, subject, author, timestamp."""
    try:
        result = subprocess.run(
            ["git", "log", f"-{count}", "--format=%H%x00%h%x00%s%x00%an%x00%at"],
            cwd=worktree,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, OSError):
        return []

    commits = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\x00", 4)
        if len(parts) != 5:
            continue
        try:
            timestamp = float(parts[4])
        except ValueError:
            timestamp = 0.0
        commits.append(CommitEntry(
            hash=parts[0],
            short_hash=parts[1],
            subject=parts[2],
            author=parts[3],
            timestamp=timestamp,
        ))
    return commits


def _git_log_numstat(worktree: Path, count: int) -> list[list[CommitFileEntry]]:
    """Get per-commit file stats via git log --numstat.

    Returns a list of file lists, one per commit in log order.
    Commits are separated by blank lines in the output.
    """
    try:
        result = subprocess.run(
            ["git", "log", f"-{count}", "--numstat", "--format="],
            cwd=worktree,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, OSError):
        return []

    # --format="" produces a blank line per commit, then numstat lines.
    # Split on double-newline to get per-commit groups.
    # The output starts with a blank line for each commit.
    commits_files: list[list[CommitFileEntry]] = []
    current: list[CommitFileEntry] = []

    for line in result.stdout.splitlines():
        if line == "":
            commits_files.append(current)
            current = []
            continue
        parts = line.split("\t", 2)
        if len(parts) == 3:
            adds = int(parts[0]) if parts[0] != "-" else 0
            dels = int(parts[1]) if parts[1] != "-" else 0
            current.append(CommitFileEntry(
                path=parts[2],
                additions=adds,
                deletions=dels,
            ))

    # Flush last group
    if current:
        commits_files.append(current)

    # The first entry may be empty (leading blank line from --format="")
    # Filter empties that don't correspond to real commits
    # Actually, --format="" produces one blank line per commit BEFORE its numstat.
    # So the pattern is: blank, [files...], blank, [files...], ...
    # Our split logic creates an empty first element, then alternating.
    # Let's just filter: keep non-empty groups, up to count.
    return [f for f in commits_files if f][:count]
