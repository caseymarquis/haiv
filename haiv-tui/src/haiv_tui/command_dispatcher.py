"""Command dispatcher for the TUI.

Receives TuiCommand envelopes from the poll loop, deserializes
payloads into typed requests, and routes to handler methods.

The Any payload is an internal transport concern — handlers only
receive fully typed request objects.
"""

from __future__ import annotations

from typing import Callable

from haiv._infrastructure.TuiServer import TuiCommand, TuiCommandType
from haiv.helpers.tui.commands import BounceRequest, ClaudeHookEventRequest, RestartRequest


class CommandDispatcher:
    """Routes TUI commands to typed handlers.

    Owns type translation: converts TuiCommand(type, payload: Any)
    into typed requests before calling handlers. No handler ever
    sees the Any payload.

    Constructor takes handler callables so the dispatcher stays
    decoupled from widgets and app internals.

    Listeners can be added after construction to observe dispatched
    commands. They receive the typed payload after the primary handler.
    """

    def __init__(
        self,
        *,
        on_restart: Callable[[RestartRequest], None],
        on_bounce: Callable[[BounceRequest], None],
        on_claude_hook_event: Callable[[ClaudeHookEventRequest], None],
        error_sink: Callable[[str], None] | None = None,
    ) -> None:
        self._on_restart = on_restart
        self._on_bounce = on_bounce
        self._on_claude_hook_event = on_claude_hook_event
        self._error_sink = error_sink
        self._listeners: list[Callable[[TuiCommandType, object], None]] = []

    def add_listener(self, callback: Callable[[TuiCommandType, object], None]) -> None:
        """Register a listener that receives (command_type, typed_payload) after dispatch."""
        self._listeners.append(callback)

    def dispatch(self, commands: list[TuiCommand]) -> None:
        """Dispatch a batch of commands from the poll loop."""
        for command in commands:
            self._dispatch_one(command)

    def _notify_listeners(self, command_type: TuiCommandType, payload: object) -> None:
        for listener in self._listeners:
            try:
                listener(command_type, payload)
            except Exception as e:
                if self._error_sink is not None:
                    self._error_sink(f"listener: {e}")

    def _dispatch_one(self, command: TuiCommand) -> None:
        """Route a single command to its typed handler."""
        match command.type:
            case TuiCommandType.RESTART:
                request: RestartRequest = command.payload
                self._on_restart(request)
            case TuiCommandType.BOUNCE:
                request: BounceRequest = command.payload
                self._on_bounce(request)
            case TuiCommandType.CLAUDE_HOOK_EVENT:
                request: ClaudeHookEventRequest = command.payload
                self._on_claude_hook_event(request)

        self._notify_listeners(command.type, command.payload)
