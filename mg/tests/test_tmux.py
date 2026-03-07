"""Tests for the Tmux wrapper class."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from haiv.wrappers.tmux import Tmux, TmuxWindow, TmuxError
from haiv.errors import CommandError


@pytest.fixture
def tmux():
    """Create a Tmux instance with quiet=True for testing."""
    return Tmux(hv_root=Path("/home/user/haiv"), quiet=True)


class TestTmuxInit:
    def test_session_derived_from_hv_root_name(self, tmux):
        assert tmux.session == "haiv"

    def test_session_with_different_path(self):
        t = Tmux(hv_root=Path("/some/other/project"))
        assert t.session == "project"


class TestTmuxRun:
    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_run_creates_session_then_executes(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")

        result = tmux.run("list-sessions")

        # First call: has-session check, second call: actual command
        assert mock_run.call_count == 2
        assert "has-session" in mock_run.call_args_list[0][0][0]
        assert "list-sessions" in mock_run.call_args_list[1][0][0]
        assert result == "output"

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_run_raises_tmux_error_on_failure(self, mock_run, tmux):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="no server running"
        )

        with pytest.raises(TmuxError) as exc_info:
            tmux.run("list-sessions")

        assert "tmux command failed" in str(exc_info.value)
        assert exc_info.value.stderr == "no server running"


class TestCreateSessionIfNeeded:
    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_creates_session_when_missing(self, mock_run, tmux):
        # First call (has-session) fails, second call (new-session) succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="no session"),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]

        created = tmux.create_session_if_needed()

        assert created is True
        assert mock_run.call_count == 2
        assert "new-session -d -s haiv" in mock_run.call_args_list[1][0][0]

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_skips_creation_when_exists(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        created = tmux.create_session_if_needed()

        assert created is False
        mock_run.assert_called_once()  # Only has-session check


class TestHasSession:
    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_has_session_returns_true_when_exists(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        assert tmux.has_session() is True
        mock_run.assert_called_once()
        assert "has-session -t haiv" in mock_run.call_args[0][0]

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_has_session_returns_false_when_missing(self, mock_run, tmux):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="no session"
        )

        assert tmux.has_session() is False


class TestListWindows:
    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_list_windows_parses_output(self, mock_run, tmux):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="0:main\n1:editor\n2:tests\n",
            stderr="",
        )

        windows = tmux.list_windows()

        assert windows == ["0:main", "1:editor", "2:tests"]
        assert "list-windows -t haiv" in mock_run.call_args[0][0]

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_list_windows_with_custom_format(self, mock_run, tmux):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="main\neditor\n", stderr=""
        )

        tmux.list_windows(format="#{window_name}")

        assert "-F '#{window_name}'" in mock_run.call_args[0][0]

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_list_windows_handles_empty_output(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        windows = tmux.list_windows()

        assert windows == []


class TestCapturPane:
    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_capture_pane_default_target(self, mock_run, tmux):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="pane content\n", stderr=""
        )

        result = tmux.capture_pane()

        assert result == "pane content\n"
        assert "capture-pane -p -t haiv" in mock_run.call_args[0][0]

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_capture_pane_with_target(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="content", stderr="")

        tmux.capture_pane(target="1.0")

        assert "-t haiv:1.0" in mock_run.call_args[0][0]

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_capture_pane_with_line_range(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="content", stderr="")

        tmux.capture_pane(start=-100, end=0)

        cmd = mock_run.call_args[0][0]
        assert "-S -100" in cmd
        assert "-E 0" in cmd


class TestSendKeys:
    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_send_keys_with_enter(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        tmux.send_keys("ls -la")

        cmd = mock_run.call_args[0][0]
        assert "send-keys -t haiv" in cmd
        assert "'ls -la'" in cmd
        assert "Enter" in cmd

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_send_keys_without_enter(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        tmux.send_keys("partial", enter=False)

        cmd = mock_run.call_args[0][0]
        assert "'partial'" in cmd
        assert "Enter" not in cmd

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_send_keys_with_target(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        tmux.send_keys("cmd", target="2")

        assert "-t haiv:2" in mock_run.call_args[0][0]

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_send_keys_escapes_single_quotes(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        tmux.send_keys("echo 'hello'")

        cmd = mock_run.call_args[0][0]
        # Single quotes should be escaped as '\''
        assert "'\\''hello'\\'''" in cmd or "echo '\\''hello'\\''" in cmd


class TestAttach:
    def test_attach_raises_in_claude_code(self, tmux, monkeypatch):
        monkeypatch.setenv("CLAUDECODE", "1")
        monkeypatch.delenv("TMUX", raising=False)

        with pytest.raises(CommandError) as exc_info:
            tmux.attach()

        assert "Claude Code" in str(exc_info.value)

    def test_attach_raises_in_tmux(self, tmux, monkeypatch):
        monkeypatch.delenv("CLAUDECODE", raising=False)
        monkeypatch.setenv("TMUX", "/tmp/tmux-1000/default,12345,0")

        with pytest.raises(CommandError) as exc_info:
            tmux.attach()

        assert "Already inside tmux" in str(exc_info.value)
        assert "switch-client" in str(exc_info.value)

    @patch("haiv.wrappers.tmux.os.execvp")
    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_attach_creates_session_and_execs(self, mock_run, mock_execvp, tmux, monkeypatch):
        monkeypatch.delenv("CLAUDECODE", raising=False)
        monkeypatch.delenv("TMUX", raising=False)
        # Session doesn't exist, then creation succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="no session"),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]

        tmux.attach()

        mock_execvp.assert_called_once_with(
            "tmux", ["tmux", "attach-session", "-t", "haiv"]
        )


class TestGetWindow:
    @patch("haiv.v.wrappers.tmux.subprocess.run")
    def test_get_window_creates_when_missing(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="bash\n", stderr="")

        window = tmux.get_window("wren")

        assert isinstance(window, TmuxWindow)
        assert window.name == "wren"
        assert window.created is True
        # Should have called list-windows and new-window
        assert any("new-window" in str(call) for call in mock_run.call_args_list)

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_get_window_returns_existing(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="bash\nwren\n", stderr="")

        window = tmux.get_window("wren")

        assert window.name == "wren"
        assert window.created is False
        # Should NOT have called new-window
        assert not any("new-window" in str(call) for call in mock_run.call_args_list)

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_get_window_raises_when_must_create_and_exists(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="wren\n", stderr="")

        with pytest.raises(TmuxError) as exc_info:
            tmux.get_window("wren", must_create=True)

        assert "already exists" in str(exc_info.value)


class TestSetenv:
    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_setenv_session_scope(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        tmux.setenv("HV_MIND", "wren")

        cmd = mock_run.call_args[0][0]
        assert "setenv" in cmd
        assert "-t haiv" in cmd
        assert "HV_MIND" in cmd
        assert "'wren'" in cmd
        # Check -g flag is not present (but -g in haiv is fine)
        assert "setenv -g" not in cmd

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_setenv_global_scope(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        tmux.setenv("HV_ROOT", "/path/to/root", global_=True)

        cmd = mock_run.call_args[0][0]
        assert "-g" in cmd

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_setenv_escapes_single_quotes(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        tmux.setenv("VAR", "it's a value")

        cmd = mock_run.call_args[0][0]
        assert "'\\''s a value" in cmd or "it'\\''s" in cmd


class TestHasWindow:
    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_has_window_returns_true_when_exists(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="bash\nwren\n", stderr="")

        assert tmux.has_window("wren") is True

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_has_window_returns_false_when_missing(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="bash\nother\n", stderr="")

        assert tmux.has_window("wren") is False

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_has_window_returns_false_when_empty(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        assert tmux.has_window("wren") is False


class TestKillWindow:
    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_kill_window_sends_correct_command(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        tmux.kill_window("wren")

        cmd = mock_run.call_args[0][0]
        assert "kill-window" in cmd
        assert "-t haiv:wren" in cmd

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_kill_window_raises_on_failure(self, mock_run, tmux):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="no such window"
        )

        with pytest.raises(TmuxError):
            tmux.kill_window("nonexistent")


class TestTmuxWindowKill:
    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_window_kill(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        window = TmuxWindow(tmux, "wren", created=True)

        window.kill()

        cmd = mock_run.call_args[0][0]
        assert "kill-window" in cmd
        assert "-t haiv:wren" in cmd


class TestTmuxWindow:
    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_window_send_keys(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        window = TmuxWindow(tmux, "wren", created=True)

        window.send_keys("echo hello")

        cmd = mock_run.call_args[0][0]
        assert "send-keys" in cmd
        assert "-t haiv:wren" in cmd
        assert "'echo hello'" in cmd

    @patch("haiv.wrappers.tmux.subprocess.run")
    def test_window_capture_pane(self, mock_run, tmux):
        mock_run.return_value = MagicMock(returncode=0, stdout="pane content\n", stderr="")
        window = TmuxWindow(tmux, "wren", created=True)

        result = window.capture_pane()

        assert result == "pane content\n"
        cmd = mock_run.call_args[0][0]
        assert "-t haiv:wren" in cmd

    def test_window_attributes(self, tmux):
        window = TmuxWindow(tmux, "wren", created=True)

        assert window.tmux is tmux
        assert window.name == "wren"
        assert window.created is True
