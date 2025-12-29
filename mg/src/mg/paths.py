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
    """Standard paths for an mg project."""

    root: Path
    pkg: PkgPaths

    # TODO: Add user: PkgPaths after user identification is implemented
    # user will point to users/{current_user}/src/mg_user/

    # TODO: Add state: Path after user identification is implemented
    # state will point to users/{current_user}/src/mg_user/state/

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
