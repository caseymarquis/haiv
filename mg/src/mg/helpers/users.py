"""User enumeration and path resolution.

Users are directories in users/ containing identity configuration
and optional mg_user packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mg._infrastructure.identity import Identity
from mg.paths import UserPaths


class UserNotFoundError(Exception):
    """Raised when a user cannot be found."""

    def __init__(self, name: str, available: list[str]):
        self.name = name
        self.available = available
        if available:
            available_str = ", ".join(sorted(available))
            super().__init__(f"User '{name}' not found. Available users: {available_str}")
        else:
            super().__init__(f"User '{name}' not found.")


@dataclass
class UserInfo:
    """A resolved user with paths and identity."""

    paths: UserPaths
    identity: Identity

    @property
    def name(self) -> str:
        """The user's name (derived from folder name)."""
        return self.paths.root.name


def _make_user_info(user_path: Path) -> UserInfo:
    """Create UserInfo from a user directory path."""
    name = user_path.name
    paths = UserPaths(root=user_path)
    identity = Identity(name=name, path=user_path, matched_by="manual")
    return UserInfo(paths=paths, identity=identity)


def list_users(users_dir: Path) -> list[UserInfo]:
    """List all users in the users directory.

    A user directory is any directory not starting with '.'.
    Returns list sorted by name.
    """
    if not users_dir.exists():
        return []

    users: list[UserInfo] = []
    for entry in users_dir.iterdir():
        if entry.name.startswith(".") or not entry.is_dir():
            continue
        users.append(_make_user_info(entry))

    return sorted(users, key=lambda u: u.name)


def resolve_user(name: str, users_dir: Path) -> UserInfo:
    """Get UserInfo for a specific user by name.

    Raises:
        UserNotFoundError: If user not found.
    """
    all_users = list_users(users_dir)
    available = [u.name for u in all_users]

    for user in all_users:
        if user.name == name:
            return user

    raise UserNotFoundError(name, available)
