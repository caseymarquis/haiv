"""Dependency initialization for haiv-tui.

Consolidates haiv dependency resolution (paths, settings, keybindings)
so the app class stays focused on UI concerns.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from haiv.helpers.tui.terminal import TerminalManager
from haiv.paths import Paths
from haiv.settings import HaivSettings
from haiv.wrappers.wezterm import WezTerm


def resolve_paths(on_error: Callable[[str], None]) -> Paths | None:
    """Detect user identity and build Paths, or None with an error."""
    from haiv._infrastructure.identity import detect_user
    from haiv.paths import get_haiv_root

    try:
        haiv_root = get_haiv_root(Path.cwd())
    except ValueError as e:
        on_error(f"paths: {e}")
        return None

    user = detect_user(haiv_root / "users")
    if user is None:
        on_error(
            f"No user identity found (haiv_root={haiv_root}). "
            "Run 'hv users new --name <name>'."
        )
        return None

    return Paths(_called_from=None, _pkg_root=None, _haiv_root=haiv_root, _user_name=user.name)


def load_settings(paths: Paths, on_error: Callable[[str], None]) -> HaivSettings:
    """Load merged project+user settings."""
    try:
        from haiv._infrastructure.settings import SettingsCache, get_settings

        return get_settings(paths, SettingsCache())
    except Exception as e:
        on_error(f"settings: {e}")
        return HaivSettings()


@dataclass
class HaivDeps:
    """Resolved haiv dependencies for the TUI."""

    paths: Paths | None
    settings: HaivSettings
    terminal: TerminalManager | None


def init(on_error: Callable[[str], None]) -> HaivDeps:
    """Resolve all haiv dependencies in one shot."""
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    paths = resolve_paths(on_error)
    settings = load_settings(paths, on_error) if paths else HaivSettings()

    if paths is not None:
        wezterm = WezTerm(settings.wezterm_command)
        terminal = TerminalManager(wezterm, paths.root, settings.tui_command)
    else:
        terminal = None

    return HaivDeps(paths=paths, settings=settings, terminal=terminal)
