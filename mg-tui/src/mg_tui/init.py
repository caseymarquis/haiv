"""Dependency initialization for mg-tui.

Consolidates mg dependency resolution (paths, settings, keybindings)
so the app class stays focused on UI concerns.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from mg.helpers.tui.terminal import TerminalManager
from mg.paths import Paths
from mg.settings import MgSettings
from mg.wrappers.wezterm import WezTerm


def resolve_paths(on_error: Callable[[str], None]) -> Paths | None:
    """Detect user identity and build Paths, or None with an error."""
    from mg._infrastructure.identity import detect_user
    from mg.paths import get_mg_root

    try:
        mg_root = get_mg_root(Path.cwd())
    except ValueError as e:
        on_error(f"paths: {e}")
        return None

    user = detect_user(mg_root / "users")
    if user is None:
        on_error(
            f"No user identity found (mg_root={mg_root}). "
            "Run 'mg users new --name <name>'."
        )
        return None

    return Paths(_called_from=None, _pkg_root=None, _mg_root=mg_root, _user_name=user.name)


def load_settings(paths: Paths, on_error: Callable[[str], None]) -> MgSettings:
    """Load merged project+user settings."""
    try:
        from mg._infrastructure.settings import SettingsCache, get_settings

        return get_settings(paths, SettingsCache())
    except Exception as e:
        on_error(f"settings: {e}")
        return MgSettings()


@dataclass
class MgDeps:
    """Resolved mg dependencies for the TUI."""

    paths: Paths | None
    settings: MgSettings
    terminal: TerminalManager | None


def init(on_error: Callable[[str], None]) -> MgDeps:
    """Resolve all mg dependencies in one shot."""
    paths = resolve_paths(on_error)
    settings = load_settings(paths, on_error) if paths else MgSettings()

    if paths is not None:
        wezterm = WezTerm(settings.wezterm_command)
        terminal = TerminalManager(wezterm, paths.root, settings.tui_command)
    else:
        terminal = None

    return MgDeps(paths=paths, settings=settings, terminal=terminal)
