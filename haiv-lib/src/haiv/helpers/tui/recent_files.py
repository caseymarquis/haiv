"""Gather pending file changes across all worktrees.

Called from a file watcher callback (worker thread). Uses git status to find
files with uncommitted changes, git diff for stats, and classifies them as
modified, deleted, or conflicted.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from haiv.helpers.tui.TuiModel import FileStatus, RecentFileEntry, RecentFilesRaw


def file_sort_key(e: RecentFileEntry) -> tuple[str, str, str]:
    """Sort key: worktree, then leaf filename, then full path as tiebreaker.

    Case-insensitive, underscores ignored. Uses forward-slash split only —
    paths must be git's forward-slash format (not Windows backslashes).
    """
    leaf = e.path.rsplit("/", 1)[-1].lower().replace("_", "")
    return (e.worktree.lower(), leaf, e.path.lower())


def gather_recent_files(
    worktrees_dir: Path,
    *,
    max_files: int = 50,
) -> RecentFilesRaw:
    """Scan worktrees for files with pending changes.

    Returns files classified into modified, deleted, and conflicted lists.
    Modified files are sorted alphabetically. Deleted and conflicted are
    sorted alphabetically.
    """
    if not worktrees_dir.is_dir():
        return RecentFilesRaw()

    modified: list[RecentFileEntry] = []
    deleted: list[RecentFileEntry] = []
    conflicted: list[RecentFileEntry] = []

    for wt_dir in worktrees_dir.iterdir():
        if not wt_dir.is_dir() or wt_dir.name.startswith("."):
            continue
        worktree = wt_dir.name

        status_entries = _git_status(wt_dir)
        if not status_entries:
            continue

        diff_stats = _git_diff_numstat(wt_dir)

        for path, file_status in status_entries:
            stats = diff_stats.get(path, (0, 0))
            mtime = 0.0

            if file_status != FileStatus.DELETED:
                try:
                    mtime = (wt_dir / path).stat().st_mtime
                except OSError:
                    pass

            if file_status == FileStatus.MODIFIED and stats == (0, 0):
                # Untracked file — count lines as additions
                stats = (_count_lines(wt_dir / path), 0)

            entry = RecentFileEntry(
                path=path,
                worktree=worktree,
                mtime=mtime,
                additions=stats[0],
                deletions=stats[1],
                status=file_status,
            )

            if file_status == FileStatus.CONFLICTED:
                conflicted.append(entry)
            elif file_status == FileStatus.DELETED:
                deleted.append(entry)
            else:
                modified.append(entry)

    modified.sort(key=file_sort_key)
    deleted.sort(key=file_sort_key)
    conflicted.sort(key=file_sort_key)

    return RecentFilesRaw(
        modified=modified[:max_files],
        deleted=deleted[:max_files],
        conflicted=conflicted[:max_files],
    )


def _git_status(worktree: Path) -> list[tuple[str, FileStatus]]:
    """Parse git status --porcelain to get changed files with status.

    Returns (path, FileStatus) tuples. Paths are git's forward-slash format.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "-uall"],
            cwd=worktree,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, OSError):
        return []

    entries: list[tuple[str, FileStatus]] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue

        xy = line[:2]
        path = line[3:]

        # Renames: "R  old -> new" — take the new path
        if " -> " in path:
            path = path.split(" -> ", 1)[1]

        if "U" in xy or (xy[0] == "D" and xy[1] == "D") or (xy[0] == "A" and xy[1] == "A"):
            entries.append((path, FileStatus.CONFLICTED))
        elif xy[1] == "D" or (xy[0] == "D" and xy[1] == " "):
            entries.append((path, FileStatus.DELETED))
        else:
            entries.append((path, FileStatus.MODIFIED))

    return entries


def _git_diff_numstat(worktree: Path) -> dict[str, tuple[int, int]]:
    """Run git diff HEAD --numstat in a worktree.

    Returns {path: (additions, deletions)} covering both staged and unstaged
    changes. Falls back to unstaged-only diff if HEAD doesn't exist.
    """
    for cmd in (
        ["git", "diff", "HEAD", "--numstat"],
        ["git", "diff", "--numstat"],
    ):
        try:
            result = subprocess.run(
                cmd,
                cwd=worktree,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                continue

            stats: dict[str, tuple[int, int]] = {}
            for line in result.stdout.strip().splitlines():
                parts = line.split("\t", 2)
                if len(parts) == 3:
                    adds = int(parts[0]) if parts[0] != "-" else 0
                    dels = int(parts[1]) if parts[1] != "-" else 0
                    stats[parts[2]] = (adds, dels)
            return stats
        except (subprocess.TimeoutExpired, OSError, ValueError):
            continue
    return {}


def _count_lines(path: Path) -> int:
    """Count lines in a file. Returns 0 for large or unreadable files."""
    try:
        size = path.stat().st_size
        if size > 1_000_000 or size == 0:
            return 0
        return len(path.read_bytes().split(b"\n"))
    except OSError:
        return 0
