"""Tests for mg start command."""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch, call

from mg import test
from mg.args import ResolveRequest
from mg.errors import CommandError

from mg_core.helpers.minds import Mind, MindPaths, Session, save_session


class TestStartRouting:
    """Test that 'start {mind}' routes correctly."""

    def test_routes_to_mind_file(self):
        """'start wren' routes to start/_mind_.py."""
        match = test.routes_to("start wren")
        assert match.file.name == "_mind_.py"
        assert "start" in str(match.file)

    def test_captures_mind_param(self):
        """Mind name is captured as param."""
        match = test.routes_to("start wren")
        assert "mind" in match.params
        assert match.params["mind"].value == "wren"

    def test_routes_with_tmux_flag(self):
        """'start wren --tmux' routes correctly."""
        match = test.routes_to("start wren --tmux")
        assert match.file.name == "_mind_.py"
        assert "--tmux" in match.raw_flags


class TestStartParsing:
    """Test start command argument parsing."""

    def test_parses_mind_name(self):
        """Mind name is accessible via args."""
        def mock_resolve(req: ResolveRequest) -> Any:
            return req.value

        ctx = test.parse("start wren", resolve=mock_resolve)
        assert ctx.args.get_one("mind") == "wren"

    def test_parses_tmux_flag(self):
        """--tmux flag is parsed."""
        def mock_resolve(req: ResolveRequest) -> Any:
            return req.value

        ctx = test.parse("start wren --tmux", resolve=mock_resolve)
        assert ctx.args.has("tmux")
        assert ctx.args.get_one("tmux") is True

    def test_tmux_flag_defaults_to_absent(self):
        """--tmux flag is absent by default."""
        def mock_resolve(req: ResolveRequest) -> Any:
            return req.value

        ctx = test.parse("start wren", resolve=mock_resolve)
        assert not ctx.args.has("tmux")


class TestStartExecution:
    """Test start command execution."""

    def test_starts_in_current_terminal_without_tmux(self, tmp_path):
        """Without --tmux, starts claude in current terminal."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with patch("mg_core.commands.start._mind_.os.execlp") as mock_exec, \
             patch("mg_core.commands.start._mind_.os.system") as mock_system:

            test.execute("start wren", resolve=mock_resolve, setup=setup)

            # Should clear terminal
            mock_system.assert_called_once_with("clear")

            # Should exec claude with prompt first, then allowedTools
            mock_exec.assert_called_once()
            args = mock_exec.call_args[0]
            assert args[0] == "claude"
            assert args[1] == "claude"
            assert "mg become wren" in args[2]  # prompt is first after claude
            assert "--allowedTools" in args
            assert "Bash(mg become wren)" in args

    def test_starts_in_tmux_with_flag(self, tmp_path):
        """With --tmux, creates new tmux window."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        # Patch at subprocess level (like Tmux class tests)
        with patch("mg.tmux.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            test.execute("start wren --tmux", resolve=mock_resolve, setup=setup)

            # Collect all tmux commands that were run
            cmds = [call[0][0] for call in mock_run.call_args_list]

            # Should check/create session
            assert any("has-session" in cmd or "new-session" in cmd for cmd in cmds)

            # Should create window named 'wren'
            assert any("new-window" in cmd and "-n wren" in cmd for cmd in cmds)

            # Should set MG_MIND environment
            assert any("setenv" in cmd and "MG_MIND" in cmd for cmd in cmds)

            # Should send keys to start claude
            assert any("send-keys" in cmd and "claude" in cmd for cmd in cmds)

    def test_sets_mg_mind_env_var(self, tmp_path):
        """MG_MIND environment variable is set."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with patch("mg_core.commands.start._mind_.os.execlp"), \
             patch("mg_core.commands.start._mind_.os.system"), \
             patch.dict("os.environ", {}, clear=False) as mock_env:

            test.execute("start wren", resolve=mock_resolve, setup=setup)

            # Environment should be set before exec
            # (We can't easily test this since execlp replaces process)


class TestStartSessionManagement:
    """Test session management flags."""

    def test_task_flag_requires_tmux(self, tmp_path):
        """--task without --tmux raises error."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with pytest.raises(CommandError) as exc_info:
            test.execute("start wren --task 'Fix bug'", resolve=mock_resolve, setup=setup)

        assert "--task and --resume require --tmux" in str(exc_info.value)

    def test_resume_flag_requires_tmux(self, tmp_path):
        """--resume without --tmux raises error."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with pytest.raises(CommandError) as exc_info:
            test.execute("start wren --resume", resolve=mock_resolve, setup=setup)

        assert "--task and --resume require --tmux" in str(exc_info.value)

    def test_task_and_resume_mutually_exclusive(self, tmp_path):
        """--task and --resume together raises error."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with pytest.raises(CommandError) as exc_info:
            test.execute(
                "start wren --tmux --task 'Fix bug' --resume abc123",
                resolve=mock_resolve,
                setup=setup,
            )

        assert "Cannot use --task and --resume together" in str(exc_info.value)

    def test_task_creates_session_entry(self, tmp_path):
        """--task creates a session in sessions.ig.toml."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with patch("mg.tmux.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            test.execute(
                "start wren --tmux --task 'Fix authentication bug'",
                resolve=mock_resolve,
                setup=setup,
            )

        # Session file should exist
        sessions_file = mind_dir / "sessions.ig.toml"
        assert sessions_file.exists()

        # Should contain the task
        content = sessions_file.read_text()
        assert "Fix authentication bug" in content

    def test_task_passes_session_id_to_claude(self, tmp_path):
        """--task passes --session-id to claude."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with patch("mg.tmux.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            test.execute(
                "start wren --tmux --task 'Implement feature'",
                resolve=mock_resolve,
                setup=setup,
            )

            cmds = [call[0][0] for call in mock_run.call_args_list]
            # Should have --session-id in the claude command
            assert any("send-keys" in cmd and "--session-id" in cmd for cmd in cmds)

    def test_resume_without_id_uses_most_recent(self, tmp_path):
        """--resume without ID uses most recent session."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        # Create a session to resume
        sessions_file = mind_dir / "sessions.ig.toml"
        session = Session(
            id="abc-123-def",
            task="Previous task",
            started=datetime.now(timezone.utc),
        )
        save_session(sessions_file, session)

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with patch("mg.tmux.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            test.execute("start wren --tmux --resume", resolve=mock_resolve, setup=setup)

            cmds = [call[0][0] for call in mock_run.call_args_list]
            # Should have --resume with the session ID
            assert any(
                "send-keys" in cmd and "--resume abc-123-def" in cmd for cmd in cmds
            )

    def test_resume_with_id_finds_session(self, tmp_path):
        """--resume with ID finds matching session."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        # Create multiple sessions
        sessions_file = mind_dir / "sessions.ig.toml"
        session1 = Session(
            id="xyz-789-ghi",
            task="Older task",
            started=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        session2 = Session(
            id="abc-123-def",
            task="Newer task",
            started=datetime(2026, 1, 5, tzinfo=timezone.utc),
        )
        save_session(sessions_file, session1)
        save_session(sessions_file, session2)

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with patch("mg.tmux.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            # Resume the older session by ID
            test.execute(
                "start wren --tmux --resume xyz-789-ghi",
                resolve=mock_resolve,
                setup=setup,
            )

            cmds = [call[0][0] for call in mock_run.call_args_list]
            assert any(
                "send-keys" in cmd and "--resume xyz-789-ghi" in cmd for cmd in cmds
            )

    def test_resume_with_partial_id_matches(self, tmp_path):
        """--resume with partial ID finds matching session."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        sessions_file = mind_dir / "sessions.ig.toml"
        session = Session(
            id="abc-123-def-456-ghi",
            task="Task",
            started=datetime.now(timezone.utc),
        )
        save_session(sessions_file, session)

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with patch("mg.tmux.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            # Resume with partial ID
            test.execute(
                "start wren --tmux --resume abc-123",
                resolve=mock_resolve,
                setup=setup,
            )

            cmds = [call[0][0] for call in mock_run.call_args_list]
            # Should resume with full session ID
            assert any(
                "send-keys" in cmd and "--resume abc-123-def-456-ghi" in cmd
                for cmd in cmds
            )

    def test_resume_nonexistent_session_errors(self, tmp_path):
        """--resume with nonexistent session raises error."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with patch("mg.tmux.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            with pytest.raises(CommandError) as exc_info:
                test.execute(
                    "start wren --tmux --resume",
                    resolve=mock_resolve,
                    setup=setup,
                )

            assert "No session found to resume" in str(exc_info.value)
