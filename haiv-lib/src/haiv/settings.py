"""Settings for haiv projects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HaivSettings:
    """Settings for a haiv project.

    Private fields hold loaded values (None = not set).
    Public properties provide effective values with fallbacks.
    """

    _default_branch: str | None = None
    _wezterm_command: list[str] | None = None
    _tui_command: list[str] | None = None
    _keybindings: dict[str, str] | None = None
    _file_explorer_command: list[str] | None = None
    _editor_command: list[str] | None = None

    @property
    def default_branch(self) -> str:
        """The default branch name. Falls back to 'main' if not set."""
        return self._default_branch if self._default_branch is not None else "main"

    @property
    def wezterm_command(self) -> list[str]:
        """The command to invoke WezTerm CLI. Falls back to ['wezterm']."""
        return self._wezterm_command if self._wezterm_command is not None else ["wezterm"]

    @property
    def tui_command(self) -> list[str]:
        """The command to launch the TUI application. Falls back to ['hv-tui']."""
        return self._tui_command if self._tui_command is not None else ["hv-tui"]

    @property
    def keybindings(self) -> dict[str, str]:
        """User keybinding overrides. Maps binding IDs to key strings."""
        return self._keybindings if self._keybindings is not None else {}

    @property
    def file_explorer_command(self) -> list[str]:
        """Command to open a directory in the file explorer.

        Falls back to platform default: xdg-open (Linux), open (macOS), explorer (Windows).
        """
        if self._file_explorer_command is not None:
            return self._file_explorer_command
        import sys
        if sys.platform == "darwin":
            return ["open"]
        elif sys.platform == "win32":
            return ["explorer"]
        return ["xdg-open"]

    @property
    def editor_command(self) -> list[str]:
        """Command to open a directory in an editor. Falls back to ['code']."""
        return self._editor_command if self._editor_command is not None else ["code"]
