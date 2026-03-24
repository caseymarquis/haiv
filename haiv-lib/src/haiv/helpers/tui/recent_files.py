"""Gather recently modified files across all worktrees with git diff stats.

Called from a file watcher callback (worker thread). Scans the filesystem
for recently modified files, runs git diff --numstat for each affected
worktree, and pushes results into the TUI model.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from haiv.helpers.tui.TuiModel import RecentFileEntry, RecentFilesRaw


def gather_recent_files(
    worktrees_dir: Path,
    *,
    max_files: int = 30,
) -> RecentFilesRaw:
    """Scan worktrees for recently modified files with git diff stats.

    Returns files sorted by mtime descending (newest first), capped at max_files.
    """
    if not worktrees_dir.is_dir():
        return RecentFilesRaw()

    entries: list[RecentFileEntry] = []
    diff_cache: dict[str, dict[str, tuple[int, int]]] = {}

    for wt_dir in worktrees_dir.iterdir():
        if not wt_dir.is_dir() or wt_dir.name.startswith("."):
            continue
        worktree = wt_dir.name

        for path, mtime in _tracked_files_by_mtime(wt_dir):
            rel = str(path.relative_to(wt_dir))

            if worktree not in diff_cache:
                diff_cache[worktree] = _git_diff_numstat(wt_dir)

            stats = diff_cache[worktree].get(rel, (0, 0))
            entries.append(RecentFileEntry(
                path=rel,
                worktree=worktree,
                mtime=mtime,
                additions=stats[0],
                deletions=stats[1],
            ))

    entries.sort(key=lambda e: e.mtime, reverse=True)
    return RecentFilesRaw(files=entries[:max_files])


def _tracked_files_by_mtime(directory: Path) -> list[tuple[Path, float]]:
    """List git-tracked files with their mtime. Respects .gitignore."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, OSError):
        return []

    results = []
    for rel in result.stdout.strip().splitlines():
        path = directory / rel
        try:
            results.append((path, path.stat().st_mtime))
        except OSError:
            continue
    return results


def _git_diff_numstat(worktree: Path) -> dict[str, tuple[int, int]]:
    """Run git diff --numstat in a worktree, return {file: (additions, deletions)}."""
    try:
        result = subprocess.run(
            ["git", "diff", "--numstat"],
            cwd=worktree,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return {}

        stats: dict[str, tuple[int, int]] = {}
        for line in result.stdout.strip().splitlines():
            parts = line.split("\t", 2)
            if len(parts) == 3:
                adds = int(parts[0]) if parts[0] != "-" else 0
                dels = int(parts[1]) if parts[1] != "-" else 0
                stats[parts[2]] = (adds, dels)
        return stats
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return {}
