"""Tui — thin convenience wrapper for mg command authors.

This class exists purely for ergonomics. It holds pre-loaded dependencies
(client, paths, settings) so command authors can write simple calls like
ctx.tui.refresh_sessions() without assembling dependencies themselves.

ALL real logic lives in helpers.py. Every method here should be a one-line
passthrough that forwards to a helpers.py function with the appropriate
dependencies. If you're adding a new capability, put the logic in helpers.py
first, then add a passthrough here.

The TUI application (mg-tui) calls helpers.py functions directly — it does
not use this class. This keeps the app decoupled from the dependency bag.
"""

from __future__ import annotations

from pathlib import Path

from mg.helpers.tui import helpers
from mg.helpers.tui.terminal import TerminalManager
from mg.settings import MgSettings
from mg.wrappers.wezterm import WezTerm


class Tui:
    """Convenience facade for TUI operations.

    Pre-loads dependencies at construction so call sites are simple.
    See module docstring — no logic belongs here.
    """

    def __init__(
        self,
        mg_root: Path,
        settings: MgSettings,
        client=None,
        sessions_file: Path | None = None,
    ) -> None:
        wezterm = WezTerm(settings.wezterm_command)
        self._terminal = TerminalManager(wezterm, mg_root, settings.tui_command)
        self._client = client
        self._sessions_file = sessions_file

    def start(self) -> None:
        """Start the TUI workspace."""
        self._terminal.ensure_workspace()

    def sessions_refresh(self) -> None:
        """Read sessions from disk and push into the TUI model."""
        helpers.sessions_refresh(self._client, self._sessions_file)
