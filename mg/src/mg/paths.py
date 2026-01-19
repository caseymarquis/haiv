"""Path utilities for mg projects.

Naming conventions:
- `root` - base anchor path (exception to suffix rule)
- `*_dir` - directory path (e.g., `state_dir`, `minds_dir`)
- `*_file` - file path (e.g., `sessions_file`, `welcome_file`)
- no suffix - container object (e.g., `pkgs`, `user` returns UserPaths)

The lack of suffix distinguishes container objects from raw Path values.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from mg._infrastructure import env
from mg.util import module_to_folder


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

    @classmethod
    def from_module(cls, module: ModuleType) -> PkgPaths:
        """Create PkgPaths from a module.

        Args:
            module: A Python module (e.g., mg_core).

        Returns:
            PkgPaths pointing to the module's root directory.
        """
        return cls(root=module_to_folder(module))

    @property
    def assets_dir(self) -> Path:
        """The __assets__ directory for non-code assets."""
        return self.root / "__assets__"

    @property
    def commands_dir(self) -> Path:
        """The commands directory."""
        return self.root / "commands"

    @property
    def resolvers_dir(self) -> Path:
        """The resolvers directory."""
        return self.root / "resolvers"


@dataclass
class UserPaths:
    """Paths for a user's directory structure.

    Provides access to user state (minds, sessions) and user package.
    """

    root: Path  # users/{name}/

    @property
    def mg_user(self) -> PkgPaths:
        """Package paths for users/{name}/src/mg_user/"""
        return PkgPaths(root=self.root / "src" / "mg_user")

    @property
    def state_dir(self) -> Path:
        """users/{name}/state/"""
        return self.root / "state"

    @property
    def minds_dir(self) -> Path:
        """users/{name}/state/minds/"""
        return self.state_dir / "minds"

    @property
    def sessions_file(self) -> Path:
        """users/{name}/state/sessions.ig.toml"""
        return self.state_dir / "sessions.ig.toml"

    @property
    def settings_file(self) -> Path:
        """users/{name}/mg.toml"""
        return self.root / "mg.toml"


@dataclass
class WorkPaths:
    """Paths within a mind's work/ directory (assignment docs).

    Work contains assignment-specific documents that may be cleared
    between assignments.
    """

    root: Path

    @property
    def docs_dir(self) -> Path:
        """Path to work/docs/ directory."""
        return self.root / "docs"

    @property
    def welcome_file(self) -> Path:
        """Path to welcome.md (task assignment from creator)."""
        return self.root / "welcome.md"

    @property
    def immediate_plan_file(self) -> Path:
        """Path to immediate-plan.md (tactical, current work)."""
        return self.root / "immediate-plan.md"

    @property
    def long_term_vision_file(self) -> Path:
        """Path to long-term-vision.md (strategic, direction)."""
        return self.root / "long-term-vision.md"

    @property
    def my_process_file(self) -> Path:
        """Path to my-process.md (how I work, lessons learned)."""
        return self.root / "my-process.md"

    @property
    def scratchpad_file(self) -> Path:
        """Path to scratchpad.md (messy thinking, notes)."""
        return self.root / "scratchpad.md"


@dataclass
class HomePaths:
    """Paths within a mind's home/ directory (personal continuity).

    Home contains personal documents that persist across assignments.
    """

    root: Path

    @property
    def journal_file(self) -> Path:
        """Path to journal.md (personal notes, reflections)."""
        return self.root / "journal.md"


@dataclass
class MindPaths:
    """Paths for a mind's directory structure.

    Structure:
        minds/{mind}/
        ├── work/              # Assignment docs (cleared between assignments)
        │   ├── welcome.md
        │   ├── immediate-plan.md
        │   ├── long-term-vision.md
        │   ├── my-process.md
        │   ├── scratchpad.md
        │   └── docs/
        ├── home/              # Personal continuity (persists)
        │   └── journal.md
        └── references.toml

    Args:
        root: The mind's root directory (e.g., minds/wren/).
        mg_root: The mg project root (needed to resolve references.toml paths).
    """

    root: Path
    mg_root: Path | None = None

    @property
    def work(self) -> WorkPaths:
        """Paths within work/ directory."""
        return WorkPaths(root=self.root / "work")

    @property
    def home(self) -> HomePaths:
        """Paths within home/ directory."""
        return HomePaths(root=self.root / "home")

    @property
    def references_file(self) -> Path:
        """Path to references.toml (at root level)."""
        return self.root / "references.toml"


@dataclass
class Pkgs:
    """Package paths for command/resolver discovery.

    All mg packages follow the same structure with commands/, resolvers/,
    and __assets__/ directories.
    """

    _current_root: Path | None
    _mg_root: Path | None
    _user_name: str | None
    _core_root: Path | None = None

    @property
    def current(self) -> PkgPaths:
        """The package containing the current command."""
        if self._current_root is None:
            raise RuntimeError("Package root not set. This is a bug in mg.")
        return PkgPaths(root=self._current_root)

    @property
    def core(self) -> PkgPaths:
        """mg_core package (installed)."""
        if self._core_root is None:
            raise RuntimeError("Core package root not set. This is a bug in mg.")
        return PkgPaths(root=self._core_root)

    @property
    def project(self) -> PkgPaths:
        """mg_project package (src/mg_project/)."""
        if self._mg_root is None:
            raise RuntimeError("mg project root not set. Run 'mg start' first.")
        return PkgPaths(root=self._mg_root / "src" / "mg_project")

    @property
    def user(self) -> PkgPaths:
        """mg_user package (users/{name}/src/mg_user/)."""
        if self._mg_root is None:
            raise RuntimeError("mg project root not set. Run 'mg start' first.")
        if self._user_name is None:
            raise RuntimeError(
                "No user identity found.\n"
                "Run 'mg users new --name <name>' to create one."
            )
        return PkgPaths(root=self._mg_root / "users" / self._user_name / "src" / "mg_user")


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
        _core_root: Root of the mg_core package (passed in by CLI).
    """

    _called_from: Path | None
    _pkg_root: Path | None
    _mg_root: Path | None
    _user_name: str | None = None
    _core_root: Path | None = None

    @property
    def called_from(self) -> Path:
        """Directory where the command was invoked."""
        if self._called_from is None:
            raise RuntimeError("called_from not set. This is a bug in mg.")
        return self._called_from

    @property
    def pkgs(self) -> Pkgs:
        """Package paths for command/resolver discovery."""
        return Pkgs(
            _current_root=self._pkg_root,
            _mg_root=self._mg_root,
            _user_name=self._user_name,
            _core_root=self._core_root,
        )

    @property
    def root(self) -> Path:
        """The mg project root directory."""
        if self._mg_root is None:
            raise RuntimeError("mg project root not set. Run 'mg start' first.")
        return self._mg_root

    @property
    def git_dir(self) -> Path:
        """The .git directory."""
        return self.root / ".git"

    @property
    def worktrees_dir(self) -> Path:
        """The worktrees directory."""
        return self.root / "worktrees"

    @property
    def users_dir(self) -> Path:
        """The users directory."""
        return self.root / "users"

    @property
    def user(self) -> UserPaths:
        """Current user's paths (state, sessions, etc.)."""
        if self._user_name is None:
            raise RuntimeError(
                "No user identity found.\n"
                "Run 'mg users new --name <name>' to create one."
            )
        return UserPaths(root=self.users_dir / self._user_name)

    @property
    def project_settings_file(self) -> Path:
        """The project-level mg.toml settings file."""
        return self.root / "mg.toml"
