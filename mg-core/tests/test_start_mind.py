"""Tests for mg start {mind} command."""

from pathlib import Path
from typing import Any
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from mg import test
from mg._infrastructure.args import ResolveRequest
from mg.errors import CommandError
from mg.helpers.minds import Mind, MindPaths
from mg.helpers.sessions import create_session, load_sessions


# =============================================================================
# Helpers
# =============================================================================


def _mind(tmp_path: Path) -> Mind:
    mind_dir = tmp_path / "wren"
    mind_dir.mkdir(exist_ok=True)
    return Mind(paths=MindPaths(root=mind_dir))


def _resolve(tmp_path: Path):
    def resolve(req: ResolveRequest) -> Any:
        if req.resolver == "mind":
            return _mind(tmp_path)
        return req.value
    return resolve


def _setup(tmp_path: Path):
    def setup(ctx):
        ctx.paths._mg_root = tmp_path
    return setup


# =============================================================================
# Routing Tests
# =============================================================================


class TestStartRouting:
    """Test that 'start {mind}' routes correctly."""

    def test_routes_to_mind_file(self):
        """'start wren' routes to start/_mind_.py."""
        match = test.require_routes_to("start wren")
        assert match.file.name == "_mind_.py"
        assert "start" in str(match.file)

    def test_captures_mind_param(self):
        """Mind name is captured as param."""
        match = test.require_routes_to("start wren")
        assert "mind" in match.params
        assert match.params["mind"].value == "wren"


# =============================================================================
# Parsing Tests
# =============================================================================


class TestStartParsing:
    """Test start command argument parsing."""

    def test_parses_mind_name(self):
        """Mind name is accessible via args."""
        def mock_resolve(req: ResolveRequest) -> Any:
            return req.value

        ctx = test.parse("start wren", resolve=mock_resolve)
        assert ctx.args.get_one("mind") == "wren"

    def test_parses_task_flag(self):
        """--task flag is parsed."""
        def mock_resolve(req: ResolveRequest) -> Any:
            return req.value

        ctx = test.parse("start wren --task 'Fix bug'", resolve=mock_resolve)
        assert ctx.args.has("task")


# =============================================================================
# Session Flow Tests
# =============================================================================


class TestSessionFlow:
    """Test session-aware launch flow."""

    def test_error_without_session_or_task(self, tmp_path):
        """Error when no staged session and no --task."""
        with pytest.raises(CommandError, match="No staged session"):
            test.execute(
                "start wren",
                resolve=_resolve(tmp_path),
                setup=_setup(tmp_path),
            )

    def test_transitions_staged_session_to_started(self, tmp_path):
        """Existing staged session is transitioned to started."""
        def setup(ctx):
            ctx.paths._mg_root = tmp_path
            create_session(
                ctx.paths.user.sessions_file, "staged task", "wren",
                status="staged",
            )

        test.execute("start wren", resolve=_resolve(tmp_path), setup=setup)

        # Reload sessions from the path that setup used
        from mg.paths import Paths
        paths = Paths(_called_from=None, _pkg_root=None, _mg_root=tmp_path, _user_name="testinius")
        sessions = load_sessions(paths.user.sessions_file)
        assert len(sessions) == 1
        assert sessions[0].status == "started"
        assert sessions[0].claude_session_id != ""

    def test_task_creates_started_session(self, tmp_path):
        """--task creates a new session with status started."""
        test.execute(
            'start wren --task "Fix bug"',
            resolve=_resolve(tmp_path),
            setup=_setup(tmp_path),
        )

        from mg.paths import Paths
        paths = Paths(_called_from=None, _pkg_root=None, _mg_root=tmp_path, _user_name="testinius")
        sessions = load_sessions(paths.user.sessions_file)
        assert len(sessions) == 1
        assert sessions[0].task == "Fix bug"
        assert sessions[0].status == "started"
        assert sessions[0].mind == "wren"
        assert sessions[0].claude_session_id != ""

    def test_task_session_parent_from_env(self, tmp_path):
        """Session parent is set from MG_SESSION env var."""
        with patch.dict("os.environ", {"MG_SESSION": "parent-123"}):
            test.execute(
                'start wren --task "Sub-task"',
                resolve=_resolve(tmp_path),
                setup=_setup(tmp_path),
            )

        from mg.paths import Paths
        paths = Paths(_called_from=None, _pkg_root=None, _mg_root=tmp_path, _user_name="testinius")
        sessions = load_sessions(paths.user.sessions_file)
        assert sessions[0].parent == "parent-123"

    def test_calls_sessions_refresh(self, tmp_path):
        """Pushes session state to TUI after session update."""
        def setup(ctx):
            ctx.paths._mg_root = tmp_path
            create_session(
                ctx.paths.user.sessions_file, "task", "wren",
                status="staged",
            )

        result = test.execute("start wren", resolve=_resolve(tmp_path), setup=setup)
        mock_tui = cast(MagicMock, result.ctx.tui)
        mock_tui.sessions_refresh.assert_called_once()

    def test_calls_launch_in_mind_pane(self, tmp_path):
        """Launches claude in the mind pane."""
        def setup(ctx):
            ctx.paths._mg_root = tmp_path
            create_session(
                ctx.paths.user.sessions_file, "task", "wren",
                status="staged",
            )

        result = test.execute("start wren", resolve=_resolve(tmp_path), setup=setup)
        mock_tui = cast(MagicMock, result.ctx.tui)
        mock_tui.launch_in_mind_pane.assert_called_once()

        # Check env vars passed
        call_args = mock_tui.launch_in_mind_pane.call_args
        env = call_args.kwargs["env"]
        assert env["MG_MIND"] == "wren"
        assert "MG_SESSION" in env
        assert "MG_ROOT" in env

        # Check commands passed
        commands = call_args.kwargs["commands"]
        assert len(commands) == 1
        assert "claude" in commands[0]
        assert "mg become wren" in commands[0]
        assert "--session-id" in commands[0]
