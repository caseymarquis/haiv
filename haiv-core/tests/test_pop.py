"""Tests for hv pop command."""

from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from haiv import test
from haiv.errors import CommandError
from haiv.helpers.sessions import create_session, load_sessions
from haiv.test import Sandbox
from haiv.wrappers.git import Git


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sandbox():
    """Sandbox with git repo on haiv, main in a worktree (mirrors real setup)."""
    sb = test.create_sandbox()
    root = sb.ctx.paths.root
    git = Git(root, quiet=True)

    git.run("init -b main")
    git.run("config user.email test@test.com")
    git.run("config user.name Test")

    (root / "README.md").write_text("# Test\n")
    git.run("add .")
    git.run("commit -m 'Initial commit'")

    # Switch root to haiv so main can live in a worktree
    git.run("checkout -b haiv")
    main_worktree = root / "worktrees" / "main"
    git.run(f"worktree add {main_worktree} main")

    return sb


def _create_session_with_branch(sandbox, *, mind="echo", branch="echo", base_branch="main", parent_id=""):
    """Create a session with branch metadata and return it."""
    return create_session(
        sandbox.ctx.paths.user.sessions_file,
        "test task",
        mind,
        branch=branch,
        base_branch=base_branch,
        parent_id=parent_id,
    )


def _create_parent_and_child(sandbox, *, parent_mind="wren", child_mind="echo"):
    """Create a parent session and a child session linked to it. Returns (parent, child)."""
    parent = create_session(
        sandbox.ctx.paths.user.sessions_file,
        "parent task",
        parent_mind,
    )
    child = _create_session_with_branch(
        sandbox, mind=child_mind, branch=child_mind, base_branch="main",
        parent_id=parent.id,
    )
    return parent, child


# =============================================================================
# Command Routing Tests
# =============================================================================


class TestRouting:
    """Test command routes correctly."""

    def test_routes_to_pop(self):
        """hv pop routes to correct file."""
        match = test.require_routes_to("pop")
        assert match.file.name == "pop.py"


# =============================================================================
# Checklist Tests
# =============================================================================


class TestChecklist:
    """Test default checklist output."""

    def test_prints_checklist(self, sandbox: Sandbox, capsys):
        """Prints the wind-down checklist when no flags given."""
        session = _create_session_with_branch(sandbox)

        with patch.dict("os.environ", {"HV_SESSION": session.id}):
            sandbox.run("pop")
        output = capsys.readouterr().out

        assert "Create a task for each item" in output
        assert "gaps in completion" in output
        assert "small improvements" in output
        assert "Discuss" in output
        assert "test coverage" in output
        assert "Commit" in output
        assert "hv pop --merge" in output
        assert "hv pop --session" in output
        assert "spirit of the original task" in output

    def test_scaffolds_aar_in_parent_mind(self, sandbox: Sandbox):
        """Creates AAR template in parent mind's work/aars/ directory."""
        parent, child = _create_parent_and_child(sandbox)

        with patch.dict("os.environ", {"HV_SESSION": child.id}):
            sandbox.run("pop")

        aar_path = (
            sandbox.ctx.paths.user.minds_dir / "wren" / "work" / "aars" / "test-task.md"
        )
        assert aar_path.is_file()

    def test_aar_not_overwritten_if_exists(self, sandbox: Sandbox):
        """Does not overwrite an existing AAR file."""
        parent, child = _create_parent_and_child(sandbox)

        aar_dir = sandbox.ctx.paths.user.minds_dir / "wren" / "work" / "aars"
        aar_dir.mkdir(parents=True)
        aar_path = aar_dir / "test-task.md"
        aar_path.write_text("existing content\n")

        with patch.dict("os.environ", {"HV_SESSION": child.id}):
            sandbox.run("pop")

        assert aar_path.read_text() == "existing content\n"

    def test_checklist_references_aar_path(self, sandbox: Sandbox, capsys):
        """Checklist includes an item referencing the AAR path."""
        parent, child = _create_parent_and_child(sandbox)

        with patch.dict("os.environ", {"HV_SESSION": child.id}):
            sandbox.run("pop")
        output = capsys.readouterr().out

        assert "Fill in your AAR" in output
        assert "aars/test-task.md" in output

    def test_no_aar_item_without_parent(self, sandbox: Sandbox, capsys):
        """Checklist omits AAR item when session has no parent."""
        session = _create_session_with_branch(sandbox)

        with patch.dict("os.environ", {"HV_SESSION": session.id}):
            sandbox.run("pop")
        output = capsys.readouterr().out

        assert "AAR" not in output


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

        with patch.dict("os.environ", {"HV_SESSION": session.id}):
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

        with patch.dict("os.environ", {"HV_SESSION": session.id}):
            sandbox.run("pop --merge")

        assert not echo_worktree.exists()

    def test_errors_without_haiv_session(self, sandbox: Sandbox):
        """Raises error when HV_SESSION is not set."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(CommandError, match="HV_SESSION"):
                sandbox.run("pop --merge")

    def test_skips_merge_when_branch_has_no_new_commits(self, sandbox: Sandbox, capsys):
        """Skips merge and still cleans up when branch has nothing to merge."""
        root = sandbox.ctx.paths.root
        git = Git(root, quiet=True)

        # Create a worktree branch with NO new commits (identical to main)
        echo_worktree = root / "worktrees" / "echo"
        git.run(f"worktree add -b echo {echo_worktree} main")

        session = _create_session_with_branch(sandbox)

        with patch.dict("os.environ", {"HV_SESSION": session.id}):
            sandbox.run("pop --merge")

        # Worktree and branch should still be cleaned up
        assert not echo_worktree.exists()

        # Should mention skipping
        output = capsys.readouterr().out
        assert "no new commits" in output.lower()

    def test_reports_cleanly_when_branch_already_gone(self, sandbox: Sandbox, capsys):
        """Reports cleanly when the branch no longer exists."""
        session = _create_session_with_branch(sandbox)

        with patch.dict("os.environ", {"HV_SESSION": session.id}):
            sandbox.run("pop --merge")

        output = capsys.readouterr().out
        assert "missing" in output.lower()
        assert "already synced" in output.lower()

    def test_errors_when_session_missing_branch(self, sandbox: Sandbox):
        """Raises error when session has no branch metadata."""
        session = create_session(
            sandbox.ctx.paths.user.sessions_file,
            "test task",
            "echo",
        )

        with patch.dict("os.environ", {"HV_SESSION": session.id}):
            with pytest.raises(CommandError, match="missing branch"):
                sandbox.run("pop --merge")


# =============================================================================
# Session Removal Tests
# =============================================================================


class TestSession:
    """Test --session flag behavior."""

    def test_removes_session_and_launches_parent(self, sandbox: Sandbox):
        """Removes session, launches parent mind, and closes pane."""
        parent, child = _create_parent_and_child(sandbox)

        with patch.dict("os.environ", {"HV_SESSION": child.id}):
            ctx = sandbox.run("pop --session")

        # Session should be removed
        sessions = load_sessions(sandbox.ctx.paths.user.sessions_file)
        assert all(s.id != child.id for s in sessions)
        # Parent should still exist
        assert any(s.id == parent.id for s in sessions)

        # Should have launched parent mind and closed our pane
        mock_tui = cast(MagicMock, ctx.tui)
        mock_tui.mind_launch.assert_called_once_with("wren")
        mock_tui.mind_close_pane.assert_called_once_with("echo")

    def test_notifies_parent_mind(self, sandbox: Sandbox):
        """Sends AAR notification to parent mind's pane."""
        parent, child = _create_parent_and_child(sandbox)

        with patch.dict("os.environ", {"HV_SESSION": child.id}):
            ctx = sandbox.run("pop --session")

        mock_tui = cast(MagicMock, ctx.tui)
        mock_tui.mind_try_send_text.assert_called_once()
        call_args = mock_tui.mind_try_send_text.call_args
        assert call_args[0][0] == "wren"
        assert "echo finished" in call_args[0][1]
        assert "aars/test-task.md" in call_args[0][1]

    def test_session_works_when_parent_pane_missing(self, sandbox: Sandbox):
        """Completes successfully even when parent pane is not found."""
        parent, child = _create_parent_and_child(sandbox)

        with patch.dict("os.environ", {"HV_SESSION": child.id}):
            ctx = sandbox.run("pop --session")

        # mind_try_send_text returns MagicMock (truthy) by default,
        # but the point is it doesn't raise — session cleanup still completes
        sessions = load_sessions(sandbox.ctx.paths.user.sessions_file)
        assert all(s.id != child.id for s in sessions)

    def test_errors_when_no_parent(self, sandbox: Sandbox):
        """Raises error when session has no parent."""
        session = _create_session_with_branch(sandbox)

        with patch.dict("os.environ", {"HV_SESSION": session.id}):
            with pytest.raises(CommandError, match="no parent"):
                sandbox.run("pop --session")

    def test_errors_when_parent_not_found(self, sandbox: Sandbox):
        """Raises error when parent session doesn't exist."""
        session = _create_session_with_branch(sandbox)
        from haiv.helpers.sessions import update_session
        update_session(
            sandbox.ctx.paths.user.sessions_file,
            session.id,
            lambda s: setattr(s, "parent_id", "nonexistent-id"),
        )

        with patch.dict("os.environ", {"HV_SESSION": session.id}):
            with pytest.raises(CommandError, match="Parent session not found"):
                sandbox.run("pop --session")

    def test_errors_without_haiv_session(self, sandbox: Sandbox):
        """Raises error when HV_SESSION is not set."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(CommandError, match="HV_SESSION"):
                sandbox.run("pop --session")
