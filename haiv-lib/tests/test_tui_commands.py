"""Tests for TUI command helpers."""

from unittest.mock import MagicMock, call

from haiv._infrastructure.TuiServer import TuiCommand, TuiCommandType
from haiv.helpers.tui.commands import (
    BounceRequest,
    RestartRequest,
    tui_bounce,
    tui_restart,
)
from haiv.helpers.tui.protocol import ModelClient


class TestTuiRestart:
    """tui_restart() helper."""

    def test_sends_restart_command(self):
        """tui_restart sends a RESTART command with RestartRequest payload."""
        client = MagicMock(spec=ModelClient)
        tui_restart(client)

        client.send_command.assert_called_once()
        cmd: TuiCommand = client.send_command.call_args[0][0]
        assert cmd.type == TuiCommandType.RESTART
        assert isinstance(cmd.payload, RestartRequest)


class TestTuiBounce:
    """tui_bounce() helper."""

    def test_sends_bounce_command(self):
        """tui_bounce sends a BOUNCE command with BounceRequest payload."""
        client = MagicMock(spec=ModelClient)
        tui_bounce(client)

        client.send_command.assert_called_once()
        cmd: TuiCommand = client.send_command.call_args[0][0]
        assert cmd.type == TuiCommandType.BOUNCE
        assert isinstance(cmd.payload, BounceRequest)
