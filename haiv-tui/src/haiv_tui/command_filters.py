"""Filters for command dispatcher listeners.

Helpers that check incoming commands for common patterns.
Workers use these to decide which events they care about.
"""

from __future__ import annotations

from haiv._infrastructure.TuiServer._TuiIpc import TuiCommandType
from haiv.helpers.tui.commands import ClaudeHookEventRequest


def is_claude_hook(command_type: TuiCommandType, payload: object, hook: str) -> bool:
    """Check if a dispatched command is a specific Claude hook event."""
    return (
        command_type == TuiCommandType.CLAUDE_HOOK_EVENT
        and isinstance(payload, ClaudeHookEventRequest)
        and payload.hook == hook
    )


def is_claude_hook_stop(command_type: TuiCommandType, payload: object) -> bool:
    return is_claude_hook(command_type, payload, "Stop")
