"""TUI IPC shared contract.

Message types and address resolution used by both the client and server.
Callers of TuiClient don't need to know about this module — it's an
internal detail of the IPC transport.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass

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
# Request messages
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReadRequest:
    """Request to read the current model state."""

    pass


@dataclass(frozen=True)
class WriteRequest:
    """Request to apply a modified model via version-checked merge."""

    model: TuiModel


Request = ReadRequest | WriteRequest


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

    kind: str  # "concurrency", "internal"
    message: str


Response = OkResponse | ErrorResponse


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ConcurrencyError(Exception):
    """Raised when a write fails due to a version mismatch."""

    pass
