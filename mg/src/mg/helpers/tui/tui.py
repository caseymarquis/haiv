"""Tui — thin convenience wrapper for mg command authors.

This class exists purely for ergonomics. It holds pre-loaded dependencies
(client, paths, settings) so command authors can write simple calls like
ctx.tui.mind_launch(mind) without assembling dependencies themselves.

ALL real logic lives in helpers.py. Every method here should be a one-line
passthrough that forwards to a helpers.py function with the appropriate
dependencies. If you're adding a new capability, put the logic in helpers.py
first, then add a passthrough here.

The TUI application (mg-tui) calls helpers.py functions directly — it does
not use this class. This keeps the app decoupled from the dependency bag.

terminal.py (TerminalManager) encapsulates WezTerm specifics — tab naming
conventions, pane splitting, parking. Helpers may take a TerminalManager as
a dependency but should not leak WezTerm details to their own callers.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from mg.helpers.sessions import Session
from mg.helpers.tui import helpers
from mg.helpers.tui.TuiClient import TuiClient
from mg.helpers.tui.TuiModel import TuiModel
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
        client: TuiClient | None,
        sessions_file: Path,
    ) -> None:
        wezterm = WezTerm(settings.wezterm_command)
        self._terminal = TerminalManager(wezterm, mg_root, settings.tui_command)
        self._mg_root = mg_root
        self._client = client
        self._sessions_file = sessions_file

    def _require_client(self) -> TuiClient:
        if self._client is None:
            raise RuntimeError("Tui client is required but was not provided")
        return self._client

    def start(self) -> None:
        """Ensure the mg workspace exists."""
        helpers.workspace_start(self._terminal)

    def read(self) -> TuiModel:
        """Read the current TUI state."""
        return self._require_client().read()

    def write(self, mutator: Callable[[TuiModel], None]) -> None:
        """Apply a mutation to the TUI state."""
        self._require_client().write(mutator)

    def sessions_refresh(self) -> None:
        """Read sessions from disk and push into the TUI model."""
        helpers.sessions_refresh(self._require_client(), self._sessions_file)

    def mind_launch(
        self,
        mind_name: str,
        *,
        task: str | None = None,
        parent: str = "",
    ) -> Session:
        """Put a mind in the hud — switching, launching, or restarting as needed."""
        return helpers.mind_launch(
            self._terminal, self._require_client(), self._sessions_file,
            mind_name, self._mg_root, task=task, parent=parent,
        )

