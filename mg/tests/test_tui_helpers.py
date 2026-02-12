"""Tests for mg.helpers.tui.helpers module."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mg.helpers.sessions import create_session, Session
from mg.helpers.tui.helpers import mind_launch


def _mock_terminal(*, active_mind: str | None = None, parked_minds: list[str] | None = None):
    """Create a mock TerminalManager with configurable pane state."""
    parked = set(parked_minds or [])
    terminal = MagicMock()
    terminal.is_mind_active.side_effect = lambda m: m == active_mind
    terminal.is_mind_parked.side_effect = lambda m: m in parked
    return terminal


def _mock_client():
    """Create a mock ModelClient."""
    return MagicMock()


class TestMindLaunchNoExistingPane:
    """When the mind has no pane (not active, not parked)."""

    def test_resolves_staged_session_and_launches(self, tmp_path):
        """Staged session is transitioned and a new pane is launched."""
        sessions_file = tmp_path / "sessions.toml"
        create_session(sessions_file, "staged task", "wren", status="staged")
        terminal = _mock_terminal()
        client = _mock_client()

        session = mind_launch(
            terminal, client, sessions_file, "wren", tmp_path,
        )

        assert session.status == "started"
        assert session.claude_session_id != ""
        terminal.launch_in_mind_pane.assert_called_once()
        args = terminal.launch_in_mind_pane.call_args
        assert args[0][0] == "wren"  # mind name

    def test_creates_session_with_task(self, tmp_path):
        """Creates a new session when task is provided and no session exists."""
        sessions_file = tmp_path / "sessions.toml"
        terminal = _mock_terminal()
        client = _mock_client()

        session = mind_launch(
            terminal, client, sessions_file, "wren", tmp_path,
            task="new task",
        )

        assert session.task == "new task"
        assert session.status == "started"
        terminal.launch_in_mind_pane.assert_called_once()

    def test_creates_session_without_task(self, tmp_path):
        """Creates session with empty task when no session and no task provided."""
        sessions_file = tmp_path / "sessions.toml"
        terminal = _mock_terminal()
        client = _mock_client()

        session = mind_launch(
            terminal, client, sessions_file, "wren", tmp_path,
        )

        assert session.task == ""
        assert session.status == "started"
        terminal.launch_in_mind_pane.assert_called_once()

    def test_sets_parent_on_new_session(self, tmp_path):
        """Parent is passed through to session creation."""
        sessions_file = tmp_path / "sessions.toml"
        terminal = _mock_terminal()
        client = _mock_client()

        session = mind_launch(
            terminal, client, sessions_file, "wren", tmp_path,
            task="child task", parent_id="parent-123",
        )

        assert session.parent_id == "parent-123"

    def test_env_vars_include_mind_and_session(self, tmp_path):
        """Environment variables contain MG_MIND, MG_SESSION, and MG_ROOT."""
        sessions_file = tmp_path / "sessions.toml"
        create_session(sessions_file, "task", "wren", status="staged")
        terminal = _mock_terminal()
        client = _mock_client()

        session = mind_launch(
            terminal, client, sessions_file, "wren", tmp_path,
        )

        env = terminal.launch_in_mind_pane.call_args[0][1]
        assert env["MG_MIND"] == "wren"
        assert env["MG_SESSION"] == session.id
        assert env["MG_ROOT"] == str(tmp_path)

    def test_claude_command_includes_become_and_session(self, tmp_path):
        """Claude command contains mg become and session id."""
        sessions_file = tmp_path / "sessions.toml"
        create_session(sessions_file, "task", "wren", status="staged")
        terminal = _mock_terminal()
        client = _mock_client()

        session = mind_launch(
            terminal, client, sessions_file, "wren", tmp_path,
        )

        commands = terminal.launch_in_mind_pane.call_args[0][2]
        assert len(commands) == 1
        assert "mg become wren" in commands[0]
        assert "--session-id" in commands[0]

    def test_refreshes_model(self, tmp_path):
        """TUI model is refreshed."""
        sessions_file = tmp_path / "sessions.toml"
        terminal = _mock_terminal()
        client = _mock_client()

        mind_launch(terminal, client, sessions_file, "wren", tmp_path)

        client.write.assert_called()


class TestMindLaunchParkedPane:
    """When the mind has a parked pane."""

    def test_switches_to_parked_pane(self, tmp_path):
        """Switches to parked pane instead of launching a new one."""
        sessions_file = tmp_path / "sessions.toml"
        create_session(sessions_file, "running task", "wren")
        terminal = _mock_terminal(parked_minds=["wren"])
        client = _mock_client()

        session = mind_launch(
            terminal, client, sessions_file, "wren", tmp_path,
        )

        terminal.switch_to_mind.assert_called_once_with("wren")
        terminal.launch_in_mind_pane.assert_not_called()
        assert session.task == "running task"

    def test_refreshes_model(self, tmp_path):
        """TUI model is refreshed even when just switching."""
        sessions_file = tmp_path / "sessions.toml"
        create_session(sessions_file, "task", "wren")
        terminal = _mock_terminal(parked_minds=["wren"])
        client = _mock_client()

        mind_launch(terminal, client, sessions_file, "wren", tmp_path)

        client.write.assert_called()


class TestMindLaunchActiveMind:
    """When the mind is already active in the hud."""

    def test_no_op_when_already_active(self, tmp_path):
        """Does not switch or launch when mind is already showing."""
        sessions_file = tmp_path / "sessions.toml"
        create_session(sessions_file, "active task", "wren")
        terminal = _mock_terminal(active_mind="wren")
        client = _mock_client()

        session = mind_launch(
            terminal, client, sessions_file, "wren", tmp_path,
        )

        terminal.switch_to_mind.assert_not_called()
        terminal.launch_in_mind_pane.assert_not_called()
        assert session.task == "active task"

    def test_refreshes_model(self, tmp_path):
        """TUI model is refreshed even when no-op."""
        sessions_file = tmp_path / "sessions.toml"
        create_session(sessions_file, "task", "wren")
        terminal = _mock_terminal(active_mind="wren")
        client = _mock_client()

        mind_launch(terminal, client, sessions_file, "wren", tmp_path)

        client.write.assert_called()
