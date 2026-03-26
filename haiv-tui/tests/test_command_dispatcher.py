"""Tests for CommandDispatcher."""

from haiv._infrastructure.TuiServer import TuiCommand, TuiCommandType
from haiv.helpers.tui.commands import BounceRequest, RestartRequest
from haiv_tui.command_dispatcher import CommandDispatcher


class TestCommandDispatcher:
    """Dispatcher routes commands to typed handlers."""

    def test_restart_dispatches_with_typed_request(self):
        """RESTART command calls on_restart with a RestartRequest."""
        received = []
        dispatcher = CommandDispatcher(
            on_restart=lambda req: received.append(req),
            on_bounce=lambda req: None,
            on_claude_hook_event=lambda req: None,
        )

        cmd = TuiCommand(type=TuiCommandType.RESTART, payload=RestartRequest())
        dispatcher.dispatch([cmd])

        assert len(received) == 1
        assert isinstance(received[0], RestartRequest)

    def test_bounce_dispatches_with_typed_request(self):
        """BOUNCE command calls on_bounce with a BounceRequest."""
        received = []
        dispatcher = CommandDispatcher(
            on_restart=lambda req: None,
            on_bounce=lambda req: received.append(req),
            on_claude_hook_event=lambda req: None,
        )

        cmd = TuiCommand(type=TuiCommandType.BOUNCE, payload=BounceRequest())
        dispatcher.dispatch([cmd])

        assert len(received) == 1
        assert isinstance(received[0], BounceRequest)

    def test_multiple_commands_dispatch_in_order(self):
        """Commands dispatch in submission order."""
        order = []
        dispatcher = CommandDispatcher(
            on_restart=lambda req: order.append("restart"),
            on_bounce=lambda req: order.append("bounce"),
            on_claude_hook_event=lambda req: None,
        )

        commands = [
            TuiCommand(type=TuiCommandType.RESTART, payload=RestartRequest()),
            TuiCommand(type=TuiCommandType.BOUNCE, payload=BounceRequest()),
            TuiCommand(type=TuiCommandType.RESTART, payload=RestartRequest()),
        ]
        dispatcher.dispatch(commands)

        assert order == ["restart", "bounce", "restart"]

    def test_empty_list_is_noop(self):
        """Dispatching an empty list does nothing."""
        dispatcher = CommandDispatcher(
            on_restart=lambda req: None,
            on_bounce=lambda req: None,
            on_claude_hook_event=lambda req: None,
        )
        dispatcher.dispatch([])  # Should not raise
