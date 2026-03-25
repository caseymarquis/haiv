"""Command dispatcher for the TUI.

Receives TuiCommand envelopes from the poll loop, deserializes
payloads into typed requests, and routes to handler methods.

The Any payload is an internal transport concern — handlers only
receive fully typed request objects.
"""

from __future__ import annotations

from typing import Callable

from haiv._infrastructure.TuiServer import TuiCommand, TuiCommandType
from haiv.helpers.tui.commands import BounceRequest, RestartRequest


class CommandDispatcher:
    """Routes TUI commands to typed handlers.

    Owns type translation: converts TuiCommand(type, payload: Any)
    into typed requests before calling handlers. No handler ever
    sees the Any payload.

    Constructor takes handler callables so the dispatcher stays
    decoupled from widgets and app internals.
    """

    def __init__(
        self,
        *,
        on_restart: Callable[[RestartRequest], None],
        on_bounce: Callable[[BounceRequest], None],
    ) -> None:
        self._on_restart = on_restart
        self._on_bounce = on_bounce

    def dispatch(self, commands: list[TuiCommand]) -> None:
        """Dispatch a batch of commands from the poll loop."""
        for command in commands:
            self._dispatch_one(command)

    def _dispatch_one(self, command: TuiCommand) -> None:
        """Route a single command to its typed handler."""
        match command.type:
            case TuiCommandType.RESTART:
                request: RestartRequest = command.payload
                self._on_restart(request)
            case TuiCommandType.BOUNCE:
                request: BounceRequest = command.payload
                self._on_bounce(request)
