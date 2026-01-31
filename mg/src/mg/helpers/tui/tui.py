"""High-level TUI interface for mg."""

from __future__ import annotations

from pathlib import Path

from mg.helpers.tui.terminal import TerminalManager
from mg.settings import MgSettings
from mg.wrappers.wezterm import WezTerm


class Tui:
    """High-level interface for mg TUI operations."""

    def __init__(self, mg_root: Path, settings: MgSettings) -> None:
        wezterm = WezTerm(settings.wezterm_command)
        self._terminal = TerminalManager(wezterm, mg_root, settings.tui_command)

    def start(self) -> None:
        """Start the TUI."""
        self._terminal.ensure_workspace()
