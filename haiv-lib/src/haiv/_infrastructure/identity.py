"""User identity detection and matching.

This module handles detecting which user is running haiv commands by matching
the current environment (git config, system user) against identity.toml
files in the users/ directory.
"""

import os
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path

from haiv.wrappers.git import Git


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


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------


class IdentityLoadError(Exception):
    """Failed to load or parse identity.toml."""

    pass


class AmbiguousIdentityError(Exception):
    """Multiple users match the current environment."""

    def __init__(
        self, matches: list[tuple[str, Path, str]], env: CurrentEnv
    ):
        self.matches = matches
        self.env = env

    def __str__(self) -> str:
        lines = ["Multiple users match the current environment:\n"]
        for name, path, matched_by in self.matches:
            env_value = getattr(self.env, matched_by, "?")
            identity_file = path / "identity.toml"
            lines.append(
                f"  {name} ({identity_file.as_posix()})"
                f"\n    matched on {matched_by} = {env_value!r}"
            )
        lines.append(
            "\nEdit one of the identity.toml files to resolve the conflict."
        )
        return "\n".join(lines)


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

    Matching is case-insensitive. ALL specified fields must match — identity
    works like a fingerprint, not a keyword search. Fields present in the
    config with a non-empty list must match the environment. Fields omitted
    or set to an empty list are not considered.

    Args:
        match_config: Dict of field names to acceptable values
        env: Current environment values

    Returns:
        Name of the last field that matched (for diagnostics), or None
    """
    matched_field = None

    for f in fields(CurrentEnv):
        match_values = match_config.get(f.name, [])
        if not match_values:
            continue

        env_value = getattr(env, f.name)
        if env_value is None:
            return None

        env_folded = env_value.strip().casefold()
        if not any(v.strip().casefold() == env_folded for v in match_values):
            return None

        matched_field = f.name

    return matched_field


def detect_user(users_dir: Path) -> Identity | None:
    """Detect current user from environment.

    Checks HV_SESSION cache first, then scans the users directory for
    identity.toml files that match the current environment.

    Args:
        users_dir: Path to the users/ directory

    Returns:
        Identity if a match is found, None otherwise

    Raises:
        AmbiguousIdentityError: If multiple users match
    """
    # TODO: Check HV_SESSION cache first

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
        raise AmbiguousIdentityError(found, env)

    name, path, matched_by = found[0]
    return Identity(name=name, path=path, matched_by=matched_by)
