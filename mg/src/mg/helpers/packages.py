"""Package discovery for haiv.

haiv commands are organized into packages at three levels:
- haiv_core: Core commands, always available (installed package)
- hv_project: Project-specific commands in src/hv_project/
- hv_user: User-specific commands in users/{user}/src/hv_user/

Each package has a commands/ directory containing command files.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

from haiv.paths import Paths, PkgPaths

if TYPE_CHECKING:
    from haiv.helpers.users import UserInfo


class PackageSource(Enum):
    """Where a package was discovered from.

    Listed in discovery order (inverse of precedence).
    Later sources override earlier ones.
    """

    CORE = auto()
    """Built-in package providing system primitives. Always available."""

    PROJECT_INSTALLED = auto()
    """Python packages installed with uv at project level.
    Must follow haiv conventions (commands/, resolvers/, etc).
    Applies to all users."""

    PROJECT_LOCAL = auto()
    """Local package in src/hv_project/. Applies to all users."""

    USER_INSTALLED = auto()
    """Python packages installed with uv at user level.
    Must follow haiv conventions. Applies to this user only."""

    USER_LOCAL = auto()
    """Local package in users/{user}/src/hv_user/. Applies to this user only."""


@dataclass
class PackageInfo:
    """Information about a haiv package."""

    name: str
    source: PackageSource
    paths: PkgPaths


@dataclass
class PkgSearchResult:
    """Details about a searched package location."""

    name: str
    source: PackageSource
    paths: PkgPaths | None = None
    """Package paths, or None if not applicable (e.g., not implemented)."""
    reason: str | None = None
    """Skip reason, or None if included."""


@dataclass
class PkgDiscoveryResult:
    """Result of package discovery with details."""

    packages: list[PackageInfo]
    """Valid packages in discovery order."""

    included: list[PkgSearchResult]
    """Packages that were included."""

    skipped: list[PkgSearchResult]
    """Packages that were skipped (with reasons)."""


def _check_package(pkg_paths: PkgPaths) -> str | None:
    """Check if a package is valid.

    Returns:
        None if valid, or a skip reason string.
    """
    try:
        if not pkg_paths.commands_dir.is_dir():
            return "commands/ directory not found"
        if not (pkg_paths.commands_dir / "__init__.py").is_file():
            return "commands/__init__.py not found"
        return None
    except PermissionError as e:
        return f"permission denied: {e}"
    except OSError as e:
        return f"filesystem error: {e}"
    except Exception as e:
        return f"unexpected error: {e}"


def _add_result(
    source: PackageSource,
    name: str,
    paths: PkgPaths | None,
    skip_reason: str | None,
    packages: list[PackageInfo],
    included: list[PkgSearchResult],
    skipped: list[PkgSearchResult],
) -> None:
    """Add a search result to the appropriate lists."""
    if skip_reason is None and paths is not None:
        packages.append(PackageInfo(name=name, source=source, paths=paths))
        included.append(PkgSearchResult(name=name, source=source, paths=paths))
    else:
        skipped.append(
            PkgSearchResult(name=name, source=source, paths=paths, reason=skip_reason)
        )


def discover_packages_detailed(
    hv_root: Path | None = None,
    user: UserInfo | None = None,
) -> PkgDiscoveryResult:
    """Discover all haiv packages with detailed results.

    Always searches all 5 package sources and returns a result for each.

    Args:
        hv_root: Root of the haiv-managed repository. If None, project and user
            packages are skipped with "hv_root not provided".
        user: Current user info. If None, user-level packages are skipped
            with "user not provided".

    Returns:
        PkgDiscoveryResult with packages, included, and skipped lists.
        The combined length of included + skipped is always 5.
    """
    packages: list[PackageInfo] = []
    included: list[PkgSearchResult] = []
    skipped: list[PkgSearchResult] = []

    # CORE - dynamically import to handle edge cases
    try:
        haiv_core = importlib.import_module("haiv_core")
        core_paths = PkgPaths.from_module(haiv_core)
        skip_reason = _check_package(core_paths)
    except ImportError as e:
        core_paths = None
        skip_reason = f"import failed: {e}"
    except Exception as e:
        core_paths = None
        skip_reason = f"unexpected error: {e}"

    _add_result(
        PackageSource.CORE, "haiv_core", core_paths, skip_reason,
        packages, included, skipped
    )

    # PROJECT_INSTALLED - not yet implemented
    _add_result(
        PackageSource.PROJECT_INSTALLED, "project_installed", None, "not implemented",
        packages, included, skipped
    )

    # PROJECT_LOCAL - src/hv_project/
    if hv_root is None:
        project_paths = None
        skip_reason = "hv_root not provided"
    else:
        try:
            paths = Paths(
                _called_from=None,
                _pkg_root=None,
                _hv_root=hv_root,
                _user_name=user.name if user else None,
            )
            project_paths = paths.pkgs.project
            skip_reason = _check_package(project_paths)
        except Exception as e:
            project_paths = None
            skip_reason = f"unexpected error: {e}"

    _add_result(
        PackageSource.PROJECT_LOCAL, "hv_project", project_paths, skip_reason,
        packages, included, skipped
    )

    # USER_INSTALLED - not yet implemented
    _add_result(
        PackageSource.USER_INSTALLED, "user_installed", None, "not implemented",
        packages, included, skipped
    )

    # USER_LOCAL - users/{user}/src/hv_user/
    if hv_root is None:
        user_paths = None
        skip_reason = "hv_root not provided"
    elif user is None:
        user_paths = None
        skip_reason = "user not provided"
    else:
        try:
            paths = Paths(
                _called_from=None,
                _pkg_root=None,
                _hv_root=hv_root,
                _user_name=user.name,
            )
            user_paths = paths.pkgs.user
            skip_reason = _check_package(user_paths)
        except Exception as e:
            user_paths = None
            skip_reason = f"unexpected error: {e}"

    _add_result(
        PackageSource.USER_LOCAL, "hv_user", user_paths, skip_reason,
        packages, included, skipped
    )

    return PkgDiscoveryResult(packages=packages, included=included, skipped=skipped)


def discover_packages(
    hv_root: Path | None = None,
    user: UserInfo | None = None,
) -> list[PackageInfo]:
    """Discover all haiv packages.

    Args:
        hv_root: Root of the haiv-managed repository. If None, only core packages
            are discovered.
        user: Current user info. If None, user-level packages are not included.

    Returns:
        List of packages in discovery order (core first, user_local last).
        Only includes valid packages (have commands/ with __init__.py).
    """
    return discover_packages_detailed(hv_root, user).packages
