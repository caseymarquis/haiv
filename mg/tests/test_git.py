"""Tests for mg.wrappers.git module."""

import pytest

from mg.wrappers.git import Git, GitError


@pytest.fixture
def git_repo(tmp_path):
    """A minimal git repo with one commit."""
    git = Git(tmp_path, quiet=True)
    git.run("init -b main")
    git.run("config user.email test@test.com")
    git.run("config user.name Test")
    (tmp_path / "README.md").write_text("# Test\n")
    git.run("add .")
    git.run("commit -m 'Initial commit'")
    return git


class TestAtPath:
    """Tests for Git.at_path()."""

    def test_returns_git_at_path(self, git_repo):
        """Returns a Git instance rooted at the given path."""
        subdir = git_repo.path / "subdir"
        subdir.mkdir()

        result = git_repo.at_path(subdir)

        assert result.path == subdir

    def test_resolves_relative_paths(self, git_repo):
        """Relative paths resolve against the parent instance's path."""
        subdir = git_repo.path / "subdir"
        subdir.mkdir()

        result = git_repo.at_path("subdir")

        assert result.path == subdir

    def test_absolute_paths_used_directly(self, tmp_path, git_repo):
        """Absolute paths are not joined with the parent path."""
        result = git_repo.at_path(tmp_path)

        assert result.path == tmp_path

    def test_inherits_quiet(self, git_repo):
        """New instance inherits the quiet setting."""
        assert git_repo.quiet is True
        result = git_repo.at_path(".")
        assert result.quiet is True


class TestWorktreePathForBranch:
    """Tests for Git.worktree_path_for_branch()."""

    def test_finds_main_worktree(self, git_repo):
        """Finds the worktree for the main branch."""
        result = git_repo.worktree_path_for_branch("main")

        assert result == git_repo.path

    def test_finds_added_worktree(self, git_repo):
        """Finds a worktree added with git worktree add."""
        worktree_path = git_repo.path / "worktrees" / "feature"
        git_repo.run(f"worktree add -b feature {worktree_path}")

        result = git_repo.worktree_path_for_branch("feature")

        assert result == worktree_path

    def test_returns_none_for_unknown_branch(self, git_repo):
        """Returns None when branch has no worktree."""
        result = git_repo.worktree_path_for_branch("nonexistent")

        assert result is None


class TestAtWorktree:
    """Tests for Git.at_worktree()."""

    def test_returns_git_at_worktree(self, git_repo):
        """Returns a Git instance for the branch's worktree."""
        result = git_repo.at_worktree("main")

        assert result.path == git_repo.path

    def test_raises_for_unknown_branch(self, git_repo):
        """Raises GitError when branch has no worktree."""
        with pytest.raises(GitError, match="No worktree found"):
            git_repo.at_worktree("nonexistent")
