"""Path utilities for mg projects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
    """

    _called_from: Path | None
    _pkg_root: Path | None
    _mg_root: Path | None

    # TODO: Add user: PkgPaths after user identification is implemented
    # user will point to users/{current_user}/src/mg_user/

    # TODO: Add state: Path after user identification is implemented
    # state will point to users/{current_user}/src/mg_user/state/

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
