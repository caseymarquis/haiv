"""Path utilities for mg projects."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from mg import env


def _is_valid_mg_root(path: Path) -> bool:
    """Check if a directory is a valid mg root.

    A valid mg root has both a .git folder and a worktrees folder.
    """
    return (path / ".git").is_dir() and (path / "worktrees").is_dir()


def get_mg_root(cwd: Path) -> Path:
    """Get mg root from environment variable or by searching upward from cwd.

    Resolution order:
    1. If MG_ROOT env var is set, validate and return it
    2. Otherwise, walk up from cwd looking for a valid mg root

    Args:
        cwd: Current working directory to search from if env var not set

    Returns:
        Path to the mg root directory

    Raises:
        ValueError: If MG_ROOT is set but invalid, or if no mg root can be found.
    """
    value = os.environ.get(env.MG_ROOT, "")

    if value:
        path = Path(value)
        if not path.is_absolute():
            raise ValueError(
                f"{env.MG_ROOT} must be an absolute path, got: {value}\n"
                "Run 'mg start' in your mg-managed repository root to set this correctly."
            )
        if not path.exists():
            raise ValueError(
                f"{env.MG_ROOT} path does not exist: {value}\n"
                "Run 'mg start' in your mg-managed repository root to set this correctly."
            )
        if not _is_valid_mg_root(path):
            raise ValueError(
                f"{env.MG_ROOT} is not a valid mg root (missing .git or worktrees): {value}\n"
                "Run 'mg start' in your mg-managed repository root to set this correctly."
            )
        return path

    # Walk up from cwd looking for mg root
    current = cwd.resolve()
    while current != current.parent:
        if _is_valid_mg_root(current):
            return current
        current = current.parent

    # Check root as well
    if _is_valid_mg_root(current):
        return current

    raise ValueError(
        "Could not find mg root.\n"
        "Run 'mg start' in your mg-managed repository root, or set MG_ROOT."
    )


@dataclass
class PkgPaths:
    """Paths for a package module (mg_core, mg_project, mg_user, or installed).

    Points to the module root (e.g., src/mg_core/), not the package root.
    This is what gets installed - tests and pyproject.toml are not included.
    """

    root: Path

    @property
    def assets(self) -> Path:
        """The __assets__ directory for non-code assets."""
        return self.root / "__assets__"

    @property
    def commands(self) -> Path:
        """The commands directory."""
        return self.root / "commands"

    @property
    def resolvers(self) -> Path:
        """The resolvers directory."""
        return self.root / "resolvers"


@dataclass
class Paths:
    """Standard paths for an mg project.

    Constructed with base paths; properties throw clear errors if the
    required base path wasn't provided. All parameters are required but
    can be None.

    Args:
        _called_from: Directory where the command was invoked.
        _pkg_root: Root of the package containing the command (e.g., mg_core/).
        _mg_root: Root of the mg project (e.g., some-project-mg/).
        _user_name: Name of the current user (folder name in users/).
    """

    _called_from: Path | None
    _pkg_root: Path | None
    _mg_root: Path | None
    _user_name: str | None = None

    @property
    def called_from(self) -> Path:
        """Directory where the command was invoked."""
        if self._called_from is None:
            raise RuntimeError("called_from not set. This is a bug in mg.")
        return self._called_from

    @property
    def pkg(self) -> PkgPaths:
        """Package paths for the command's package."""
        if self._pkg_root is None:
            raise RuntimeError("Package root not set. This is a bug in mg.")
        return PkgPaths(root=self._pkg_root)

    @property
    def root(self) -> Path:
        """The mg project root directory."""
        if self._mg_root is None:
            raise RuntimeError("mg project root not set. Run 'mg start' first.")
        return self._mg_root

    @property
    def project(self) -> PkgPaths:
        """Project package paths (src/mg_project/)."""
        return PkgPaths(root=self.root / "src" / "mg_project")

    @property
    def git_dir(self) -> Path:
        """The .git directory."""
        return self.root / ".git"

    @property
    def worktrees(self) -> Path:
        """The worktrees directory."""
        return self.root / "worktrees"

    @property
    def users(self) -> Path:
        """The users directory."""
        return self.root / "users"

    @property
    def user(self) -> PkgPaths:
        """User package paths (users/{name}/src/mg_user/)."""
        if self._user_name is None:
            raise RuntimeError(
                "No user identity found.\n"
                "Run 'mg users new --name <name>' to create one."
            )
        return PkgPaths(root=self.users / self._user_name / "src" / "mg_user")

    @property
    def state(self) -> Path:
        """User state directory (users/{name}/state/)."""
        if self._user_name is None:
            raise RuntimeError(
                "No user identity found.\n"
                "Run 'mg users new --name <name>' to create one."
            )
        return self.users / self._user_name / "state"
