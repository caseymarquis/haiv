"""Tests for mg pop command."""

from unittest.mock import patch

import pytest

from mg import test
from mg.errors import CommandError
from mg.helpers.sessions import create_session, load_sessions
from mg.test import Sandbox
from mg.wrappers.git import Git


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sandbox():
    """Sandbox with git repo on mg-state, main in a worktree (mirrors real setup)."""
    sb = test.create_sandbox()
    root = sb.ctx.paths.root
    git = Git(root, quiet=True)

    git.run("init -b main")
    git.run("config user.email test@test.com")
    git.run("config user.name Test")

    (root / "README.md").write_text("# Test\n")
    git.run("add .")
    git.run("commit -m 'Initial commit'")

    # Switch root to mg-state so main can live in a worktree
    git.run("checkout -b mg-state")
    main_worktree = root / "worktrees" / "main"
    git.run(f"worktree add {main_worktree} main")

    return sb


def _create_session_with_branch(sandbox, *, mind="echo", branch="echo", base_branch="main"):
    """Create a session with branch metadata and return it."""
    return create_session(
        sandbox.ctx.paths.user.sessions_file,
        "test task",
        mind,
        branch=branch,
        base_branch=base_branch,
    )


# =============================================================================
# Command Routing Tests
# =============================================================================


class TestRouting:
    """Test command routes correctly."""

    def test_routes_to_pop(self):
        """mg pop routes to correct file."""
        match = test.require_routes_to("pop")
        assert match.file.name == "pop.py"


# =============================================================================
# Checklist Tests
# =============================================================================


class TestChecklist:
    """Test default checklist output."""

    def test_prints_checklist(self, sandbox: Sandbox, capsys):
        """Prints the wind-down checklist when no flags given."""
        sandbox.run("pop")
        output = capsys.readouterr().out

        assert "TODOs" in output
        assert "gaps in completion" in output
        assert "small improvements" in output
        assert "Discuss" in output
        assert "test coverage" in output
        assert "Commit" in output
        assert "mg pop --merge" in output
        assert "mg pop --session" in output


# =============================================================================
# Merge Tests
# =============================================================================


class TestMerge:
    """Test --merge flag behavior."""

    def test_merges_branch_into_base(self, sandbox: Sandbox):
        """Merges the mind's branch into the base branch."""
        root = sandbox.ctx.paths.root
        git = Git(root, quiet=True)

        # Create a worktree branch with a commit
        echo_worktree = root / "worktrees" / "echo"
        git.run(f"worktree add -b echo {echo_worktree} main")
        echo_git = Git(echo_worktree, quiet=True)
        (echo_worktree / "feature.txt").write_text("new feature\n")
        echo_git.run("add .")
        echo_git.run("commit -m 'Add feature'")

        session = _create_session_with_branch(sandbox)

        with patch.dict("os.environ", {"MG_SESSION": session.id}):
            sandbox.run("pop --merge")

        # Branch should be merged — feature.txt should exist in main
        main_worktree = root / "worktrees" / "main"
        assert (main_worktree / "feature.txt").is_file()

    def test_removes_worktree_and_branch(self, sandbox: Sandbox):
        """Removes worktree directory and deletes branch after merge."""
        root = sandbox.ctx.paths.root
        git = Git(root, quiet=True)

        echo_worktree = root / "worktrees" / "echo"
        git.run(f"worktree add -b echo {echo_worktree} main")

        session = _create_session_with_branch(sandbox)

        with patch.dict("os.environ", {"MG_SESSION": session.id}):
            sandbox.run("pop --merge")

        assert not echo_worktree.exists()

    def test_errors_without_mg_session(self, sandbox: Sandbox):
        """Raises error when MG_SESSION is not set."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(CommandError, match="MG_SESSION"):
                sandbox.run("pop --merge")

    def test_skips_merge_when_branch_has_no_new_commits(self, sandbox: Sandbox, capsys):
        """Skips merge and still cleans up when branch has nothing to merge."""
        root = sandbox.ctx.paths.root
        git = Git(root, quiet=True)

        # Create a worktree branch with NO new commits (identical to main)
        echo_worktree = root / "worktrees" / "echo"
        git.run(f"worktree add -b echo {echo_worktree} main")

        session = _create_session_with_branch(sandbox)

        with patch.dict("os.environ", {"MG_SESSION": session.id}):
            sandbox.run("pop --merge")

        # Worktree and branch should still be cleaned up
        assert not echo_worktree.exists()

        # Should mention skipping
        output = capsys.readouterr().out
        assert "no new commits" in output.lower()

    def test_errors_when_session_missing_branch(self, sandbox: Sandbox):
        """Raises error when session has no branch metadata."""
        session = create_session(
            sandbox.ctx.paths.user.sessions_file,
            "test task",
            "echo",
        )

        with patch.dict("os.environ", {"MG_SESSION": session.id}):
            with pytest.raises(CommandError, match="missing branch"):
                sandbox.run("pop --merge")


# =============================================================================
# Session Removal Tests
# =============================================================================


class TestSession:
    """Test --session flag behavior."""

    def test_removes_session(self, sandbox: Sandbox):
        """Removes the current session."""
        session = _create_session_with_branch(sandbox)

        with patch.dict("os.environ", {"MG_SESSION": session.id}):
            sandbox.run("pop --session")

        sessions = load_sessions(sandbox.ctx.paths.user.sessions_file)
        assert len(sessions) == 0

    def test_errors_without_mg_session(self, sandbox: Sandbox):
        """Raises error when MG_SESSION is not set."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(CommandError, match="MG_SESSION"):
                sandbox.run("pop --session")
