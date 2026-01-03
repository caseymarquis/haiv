"""User identity detection and matching.

This module handles detecting which user is running mg commands by matching
the current environment (git config, system user) against identity.toml
files in the users/ directory.
"""

import os
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path

from mg.git import Git


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------


class IdentityLoadError(Exception):
    """Failed to load or parse identity.toml."""

    pass


class AmbiguousIdentityError(Exception):
    """Multiple users match the current environment."""

    def __init__(self, paths: list[Path]):
        self.paths = paths

    def __str__(self) -> str:
        paths_str = "\n  ".join(str(p) for p in self.paths)
        return (
            f"Multiple users match the current environment:\n  {paths_str}\n"
            f"Edit one of the identity.toml files to resolve the conflict."
        )


# -----------------------------------------------------------------------------
# Data structures
# -----------------------------------------------------------------------------


@dataclass
class CurrentEnv:
    """Current environment values for identity matching.

    This is the source of truth for valid match field names.
    The [match] section in identity.toml uses these same field names.
    """

    git_email: str | None = None
    git_name: str | None = None
    system_user: str | None = None


@dataclass
class Identity:
    """A detected user identity.

    Returned by detect_user() when a match is found.
    """

    name: str  # User folder name
    path: Path  # Full path to user directory
    matched_by: str  # Which field matched (for debugging)


# Type alias for the [match] section from identity.toml
MatchConfig = dict[str, list[str]]


# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


def valid_match_fields() -> set[str]:
    """Return the set of valid field names for identity matching.

    Based on CurrentEnv dataclass fields.
    """
    return {f.name for f in fields(CurrentEnv)}


def get_current_env() -> CurrentEnv:
    """Gather current environment for identity matching.

    Collects:
    - git_email: from `git config user.email`
    - git_name: from `git config user.name`
    - system_user: from $USER env var, falling back to os.getlogin()

    Returns:
        CurrentEnv with current values (None for unavailable values)
    """
    git = Git(Path.cwd(), quiet=True)

    system_user = os.environ.get("USER")
    if system_user is None:
        try:
            system_user = os.getlogin()
        except OSError:
            system_user = None

    return CurrentEnv(
        git_email=git.config("user.email"),
        git_name=git.config("user.name"),
        system_user=system_user,
    )


def load_match_config(path: Path) -> MatchConfig:
    """Load the [match] section from an identity.toml file.

    Args:
        path: Path to identity.toml file

    Returns:
        Dict mapping field names to lists of acceptable values.
        Returns empty dict if file missing or has no [match] section.

    Raises:
        IdentityLoadError: If file exists but cannot be parsed
    """
    if not path.exists():
        return {}

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise IdentityLoadError(f"Failed to parse {path}: {e}") from e

    return data.get("match", {})


def matches(match_config: MatchConfig, env: CurrentEnv) -> str | None:
    """Check if a match config matches the current environment.

    Matching is case-insensitive. Any single field match is sufficient.
    Iterates over CurrentEnv fields to ensure consistent ordering.

    Args:
        match_config: Dict of field names to acceptable values
        env: Current environment values

    Returns:
        Name of the field that matched (e.g., "git_email"), or None if no match
    """
    for f in fields(CurrentEnv):
        env_value = getattr(env, f.name)
        if env_value is None:
            continue

        match_values = match_config.get(f.name, [])
        env_folded = env_value.strip().casefold()

        if any(v.strip().casefold() == env_folded for v in match_values):
            return f.name

    return None


def detect_user(users_dir: Path) -> Identity | None:
    """Detect current user from environment.

    Checks MG_SESSION cache first, then scans the users directory for
    identity.toml files that match the current environment.

    Args:
        users_dir: Path to the users/ directory

    Returns:
        Identity if a match is found, None otherwise

    Raises:
        AmbiguousIdentityError: If multiple users match
    """
    # TODO: Check MG_SESSION cache first

    if not users_dir.exists():
        return None

    env = get_current_env()
    found: list[tuple[str, Path, str]] = []  # (name, path, matched_by)

    for entry in users_dir.iterdir():
        # Skip dotfiles and regular files
        if entry.name.startswith(".") or not entry.is_dir():
            continue

        identity_file = entry / "identity.toml"
        match_config = load_match_config(identity_file)
        matched_by = matches(match_config, env)

        if matched_by:
            found.append((entry.name, entry, matched_by))

    if len(found) == 0:
        return None

    if len(found) > 1:
        paths = [entry / "identity.toml" for _, entry, _ in found]
        raise AmbiguousIdentityError(paths)

    name, path, matched_by = found[0]
    return Identity(name=name, path=path, matched_by=matched_by)
