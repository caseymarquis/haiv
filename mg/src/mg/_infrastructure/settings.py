"""Settings loading and merging for mg projects.

This module handles the implementation details of loading TOML files
and merging project/user settings.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from mg.settings import MgSettings

if TYPE_CHECKING:
    from mg.paths import Paths


# -----------------------------------------------------------------------------
# Cache
# -----------------------------------------------------------------------------


@dataclass
class SettingsCache:
    """Cache for loaded project and user settings."""

    project: MgSettings | None = None
    user: MgSettings | None = None


def get_settings(paths: Paths, cache: SettingsCache) -> MgSettings:
    """Get merged settings, loading and caching as needed.

    Loads project settings on first call, caches result. Loads user
    settings if user is available and not yet cached. Always recomputes
    the merge to pick up user settings if they become available later.
    """
    # Load project if not cached
    if cache.project is None:
        cache.project = load_project_settings(paths.project_settings_file)

    # Load user if available and not cached
    if cache.user is None and paths._user_name is not None:
        cache.user = load_user_settings(paths.user.settings_file)

    return merge_settings(cache.project, cache.user)


# -----------------------------------------------------------------------------
# Loading functions
# -----------------------------------------------------------------------------


PROJECT_SETTINGS_TEMPLATE = """\
# mg project settings
# User settings (users/{name}/mg.toml) override these values.

# default_branch = "main"
# wezterm_command = ["flatpak", "run", "org.wezfurlong.wezterm"]
# tui_command = ["mg-tui"]
"""


def _load_settings(path: Path, default_text: str) -> MgSettings:
    """Load settings from a TOML file.

    Args:
        path: Path to the settings file.
        default_text: Text to write if file doesn't exist.

    Returns:
        MgSettings with loaded values.
    """
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(default_text)
        return MgSettings()

    with open(path, "rb") as f:
        data = tomllib.load(f)

    # Build MgSettings from TOML data by matching field names.
    # Field "_foo" is loaded from TOML key "foo".
    from dataclasses import fields

    kwargs = {}
    for field in fields(MgSettings):
        if not field.name.startswith("_"):
            continue
        toml_key = field.name[1:]  # strip leading underscore
        if toml_key in data:
            kwargs[field.name] = data[toml_key]

    return MgSettings(**kwargs)


def load_project_settings(path: Path) -> MgSettings:
    """Load project settings from mg.toml.

    Args:
        path: Path to the mg.toml file

    Returns:
        MgSettings with loaded values

    If file is missing, creates it with commented defaults and returns
    empty MgSettings.
    """
    return _load_settings(path, PROJECT_SETTINGS_TEMPLATE)


def load_user_settings(path: Path) -> MgSettings:
    """Load user settings from mg.toml.

    Args:
        path: Path to the user's mg.toml file

    Returns:
        MgSettings with loaded values

    If file is missing, creates an empty file and returns empty MgSettings.
    """
    return _load_settings(path, "")


# -----------------------------------------------------------------------------
# Merging
# -----------------------------------------------------------------------------


def merge_settings(project: MgSettings, user: MgSettings | None) -> MgSettings:
    """Merge project and user settings.

    User non-None values override project values. Iterates over all private
    fields (starting with underscore) and uses user value if not None.

    Args:
        project: Project-level settings
        user: User-level settings (may be None)

    Returns:
        Merged MgSettings
    """
    if user is None:
        return project

    from dataclasses import fields

    merged = {}
    for field in fields(MgSettings):
        if not field.name.startswith("_"):
            continue
        user_value = getattr(user, field.name)
        project_value = getattr(project, field.name)
        merged[field.name] = user_value if user_value is not None else project_value

    return MgSettings(**merged)
