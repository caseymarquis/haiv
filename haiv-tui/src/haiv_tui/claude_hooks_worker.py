"""Claude hooks worker — accumulates hook events and pushes to the model.

Receives ClaudeHookEventRequest commands, maintains a bounded buffer,
and pushes the full buffer as a ClaudeHookEventsRaw section via write_raw.

IDs are sequential, wrapping at 999.
"""

from __future__ import annotations

from collections import deque

from haiv.helpers.tui.commands import ClaudeHookEventRequest
from haiv.helpers.tui.protocol import ModelClient
from haiv.helpers.tui.TuiModel import ClaudeHookEntry, ClaudeHookEventsRaw

MAX_EVENTS = 20
MAX_ID = 999


class ClaudeHooksWorker:
    """Accumulates Claude hook events and pushes to the TUI model."""

    def __init__(self, client: ModelClient) -> None:
        self._client = client
        self._events: deque[ClaudeHookEntry] = deque(maxlen=MAX_EVENTS)
        self._next_id = 1

    def _assign_id(self) -> int:
        id = self._next_id
        self._next_id = (self._next_id % MAX_ID) + 1
        return id

    def handle(self, request: ClaudeHookEventRequest) -> None:
        """Receive a hook event, buffer it, and push to the model."""
        entry = ClaudeHookEntry(
            id=self._assign_id(),
            ts=request.ts,
            hook=request.hook,
            session_id=request.session_id,
            payload=request.payload,
        )
        self._events.append(entry)
        self._client.write_raw(
            claude_hook_events=ClaudeHookEventsRaw(events=list(self._events)),
        )
