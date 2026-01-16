"""Tests for mg sessions commands."""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import Mock

from mg import test
from mg._infrastructure.args import ResolveRequest
from mg.helpers.sessions import Session, save_session


class TestSessionsRouting:
    """Test that 'sessions' routes correctly."""

    def test_routes_to_sessions_index(self):
        """'sessions' routes to sessions/_index_.py."""
        match = test.require_routes_to("sessions")
        assert match.file.name == "_index_.py"
        assert "sessions" in str(match.file)

    def test_sessions_id_remove_routes_correctly(self):
        """'sessions 3 remove' routes to sessions/_session_/remove.py."""
        match = test.require_routes_to("sessions 3 remove")
        assert match.file.name == "remove.py"
        assert "_session_" in str(match.file)

    def test_captures_session_param(self):
        """Session identifier is captured as param."""
        match = test.require_routes_to("sessions abc123 remove")
        assert "session" in match.params
        assert match.params["session"].value == "abc123"
        assert match.params["session"].resolver == "session"


class TestSessionsListExecution:
    """Test sessions list command execution."""

    def test_shows_no_sessions_message(self, capsys):
        """Shows message when no sessions exist."""
        def setup(ctx):
            # Ensure state dir exists but no sessions file
            ctx.paths.user.state_dir.mkdir(parents=True, exist_ok=True)

        test.execute("sessions", setup=setup)

        captured = capsys.readouterr()
        assert "No active sessions" in captured.out

    def test_lists_sessions(self, capsys):
        """Lists sessions with short_id, mind, and task."""
        def setup(ctx):
            ctx.paths.user.state_dir.mkdir(parents=True, exist_ok=True)
            session = Session(
                id="abc123-def456",
                task="Implement feature X",
                started=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
                mind="wren",
                short_id=3,
            )
            save_session(ctx.paths.user.sessions_file, session)

        test.execute("sessions", setup=setup)

        captured = capsys.readouterr()
        assert "[3]" in captured.out
        assert "wren" in captured.out
        assert "Implement feature X" in captured.out

    def test_lists_multiple_sessions(self, capsys):
        """Lists multiple sessions."""
        def setup(ctx):
            ctx.paths.user.state_dir.mkdir(parents=True, exist_ok=True)
            session1 = Session(
                id="abc123",
                task="Task one",
                started=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                mind="wren",
                short_id=1,
            )
            session2 = Session(
                id="def456",
                task="Task two",
                started=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
                mind="robin",
                short_id=2,
            )
            save_session(ctx.paths.user.sessions_file, session1)
            save_session(ctx.paths.user.sessions_file, session2)

        test.execute("sessions", setup=setup)

        captured = capsys.readouterr()
        assert "Task one" in captured.out
        assert "Task two" in captured.out
        assert "wren" in captured.out
        assert "robin" in captured.out


class TestSessionsRemoveExecution:
    """Test sessions remove command execution."""

    def test_removes_session(self, capsys):
        """Removes session and prints confirmation."""
        def setup(ctx):
            ctx.paths.user.state_dir.mkdir(parents=True, exist_ok=True)
            session = Session(
                id="abc123-def456",
                task="Task to remove",
                started=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                mind="wren",
                short_id=5,
            )
            save_session(ctx.paths.user.sessions_file, session)

        def mock_resolve(req: ResolveRequest) -> Any:
            if req.resolver == "session":
                return Session(
                    id="abc123-def456",
                    task="Task to remove",
                    started=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                    mind="wren",
                    short_id=5,
                )
            return req.value

        test.execute("sessions 5 remove", setup=setup, resolve=mock_resolve)

        captured = capsys.readouterr()
        assert "Removed session [5]" in captured.out
        assert "Task to remove" in captured.out

    def test_session_actually_removed_from_file(self):
        """Session is actually removed from the sessions file."""
        removed_session_id = None

        def setup(ctx):
            nonlocal removed_session_id
            ctx.paths.user.state_dir.mkdir(parents=True, exist_ok=True)
            session = Session(
                id="abc123-def456",
                task="Task to remove",
                started=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                mind="wren",
                short_id=5,
            )
            save_session(ctx.paths.user.sessions_file, session)
            removed_session_id = session.id

        def mock_resolve(req: ResolveRequest) -> Any:
            if req.resolver == "session":
                return Session(
                    id="abc123-def456",
                    task="Task to remove",
                    started=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                    mind="wren",
                    short_id=5,
                )
            return req.value

        result = test.execute("sessions 5 remove", setup=setup, resolve=mock_resolve)

        # Verify session was removed
        from mg.helpers.sessions import load_sessions
        remaining = load_sessions(result.ctx.paths.user.sessions_file)
        assert len(remaining) == 0
