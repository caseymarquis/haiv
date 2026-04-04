"""Tests for recent_files gatherer — git status parsing with real repos."""

import subprocess
from pathlib import Path

import pytest

from haiv.helpers.tui.TuiModel import FileStatus
from haiv.helpers.tui.recent_files import _git_status, gather_recent_files


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo with one committed file."""
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test"],
        cwd=tmp_path,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=tmp_path,
        capture_output=True,
    )
    (tmp_path / "committed.txt").write_text("initial")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    return tmp_path


class TestGitStatusUntracked:

    def test_untracked_directory_lists_individual_files(self, git_repo: Path):
        """Untracked dirs should expand to individual files, not show as dirs."""
        subdir = git_repo / "newdir" / "nested"
        subdir.mkdir(parents=True)
        (subdir / "a.py").write_text("hello")
        (subdir / "b.py").write_text("world")

        entries = _git_status(git_repo)
        paths = [p for p, _ in entries]

        assert "newdir/nested/a.py" in paths
        assert "newdir/nested/b.py" in paths
        # Should NOT have the directory itself
        assert "newdir/" not in paths
        assert "newdir/nested/" not in paths

    def test_untracked_single_file(self, git_repo: Path):
        (git_repo / "new.txt").write_text("new")
        entries = _git_status(git_repo)
        paths = [p for p, _ in entries]
        assert "new.txt" in paths

    def test_modified_tracked_file(self, git_repo: Path):
        (git_repo / "committed.txt").write_text("changed")
        entries = _git_status(git_repo)
        assert ("committed.txt", FileStatus.MODIFIED) in entries

    def test_deleted_tracked_file(self, git_repo: Path):
        (git_repo / "committed.txt").unlink()
        entries = _git_status(git_repo)
        assert ("committed.txt", FileStatus.DELETED) in entries


class TestGatherRecentFiles:

    def test_untracked_dir_files_appear_individually(self, git_repo: Path):
        """End-to-end: untracked dir contents show as individual modified files."""
        # gather_recent_files expects a parent dir containing worktree dirs
        worktrees_dir = git_repo.parent
        # Rename repo dir to look like a worktree
        worktree = worktrees_dir / "test-wt"
        git_repo.rename(worktree)

        subdir = worktree / "somedir"
        subdir.mkdir()
        (subdir / "file.py").write_text("content")

        raw = gather_recent_files(worktrees_dir)
        mod_paths = [e.path for e in raw.modified]
        assert "somedir/file.py" in mod_paths
        assert "somedir/" not in mod_paths
