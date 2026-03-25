"""TUI command helpers.

Typed command payloads and helper functions for sending UI control
requests. Each command is a frozen dataclass paired with a helper
that constructs the envelope and sends it.

Callers use the helpers — never the envelope directly.
"""

from __future__ import annotations

from dataclasses import dataclass

from haiv._infrastructure.TuiServer._TuiIpc import TuiCommand, TuiCommandType
from haiv.helpers.tui.protocol import ModelClient


# ---------------------------------------------------------------------------
# restart — restart the TUI process
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RestartRequest:
    """Request to restart the TUI process."""

    pass


def tui_restart(client: ModelClient) -> None:
    """Send a restart command to the TUI."""
    client.send_command(TuiCommand(type=TuiCommandType.RESTART, payload=RestartRequest()))


# ---------------------------------------------------------------------------
# bounce — switch to the next session
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BounceRequest:
    """Request to switch to the next session in ID order."""

    pass


def tui_bounce(client: ModelClient) -> None:
    """Send a bounce command to the TUI."""
    client.send_command(TuiCommand(type=TuiCommandType.BOUNCE, payload=BounceRequest()))
