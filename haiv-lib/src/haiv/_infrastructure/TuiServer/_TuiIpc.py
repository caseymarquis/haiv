"""TUI IPC shared contract.

Message types and address resolution used by both the client and server.
Callers of TuiClient don't need to know about this module — it's an
internal detail of the IPC transport.
"""

from __future__ import annotations

import enum
import platform
from dataclasses import dataclass
from typing import Any

from haiv.helpers.tui.TuiModel import TuiModel


# ---------------------------------------------------------------------------
# Process lifecycle
# ---------------------------------------------------------------------------

RESTART_EXIT_CODE = 75
"""Exit code used by haiv-tui to signal the restart loop."""


# ---------------------------------------------------------------------------
# Address resolution
# ---------------------------------------------------------------------------


def pipe_address(project: str) -> str:
    """Derive the IPC address from the project name.

    Unix:    /tmp/haiv-{project}.sock
    Windows: \\\\.\\pipe\\haiv-{project}
    """
    if platform.system() == "Windows":
        return rf"\\.\pipe\haiv-{project}"
    return f"/tmp/haiv-{project}.sock"


# ---------------------------------------------------------------------------
# Command envelope
# ---------------------------------------------------------------------------


class TuiCommandType(enum.Enum):
    """Command types for TUI control requests."""

    RESTART = "restart"
    BOUNCE = "bounce"
    CLAUDE_HOOK_EVENT = "claude_hook_event"


@dataclass(frozen=True)
class TuiCommand:
    """Typed envelope for a UI control request.

    type: routing key for dispatch
    payload: command-specific data (typed at both ends, Any in transit)
    """

    type: TuiCommandType
    payload: Any


# ---------------------------------------------------------------------------
# Request messages
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReadRequest:
    """Request to read the current model state."""

    pass


@dataclass(frozen=True)
class WriteRequest:
    """Request to overwrite model sections with incoming data."""

    model: TuiModel


@dataclass(frozen=True)
class CommandRequest:
    """Request to enqueue a UI control command."""

    command: TuiCommand


Request = ReadRequest | WriteRequest | CommandRequest


# ---------------------------------------------------------------------------
# Response messages
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OkResponse:
    """Successful response, optionally carrying a result."""

    result: TuiModel | None = None


@dataclass(frozen=True)
class ErrorResponse:
    """Failed response with an error category and message."""

    kind: str  # "internal"
    message: str


Response = OkResponse | ErrorResponse
