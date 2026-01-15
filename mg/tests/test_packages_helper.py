"""Tests for mg.helpers.packages module."""

import pytest
from pathlib import Path

from mg.helpers.packages import (
    PackageSource,
    PackageInfo,
    PkgSearchResult,
    PkgDiscoveryResult,
    discover_packages,
    discover_packages_detailed,
)
from mg.helpers.users import UserInfo, UserPaths
from mg._infrastructure.identity import Identity


def make_user(tmp_path: Path, name: str = "testuser") -> UserInfo:
    """Create a UserInfo for testing."""
    user_root = tmp_path / "users" / name
    user_root.mkdir(parents=True)
    return UserInfo(
        paths=UserPaths(root=user_root),
        identity=Identity(name=name, path=user_root, matched_by="test"),
    )


def make_valid_package(pkg_root: Path) -> None:
    """Create a valid package structure (commands/ with __init__.py)."""
    commands = pkg_root / "commands"
    commands.mkdir(parents=True, exist_ok=True)
    (commands / "__init__.py").write_text("# commands")


class TestDiscoverPackages:
    """Tests for discover_packages function."""

    def test_core_only_when_no_mg_root(self):
        """Only core package returned when mg_root is None."""
        result = discover_packages(mg_root=None)

        assert len(result) == 1
        assert result[0].name == "mg_core"
        assert result[0].source == PackageSource.CORE

    def test_core_always_included(self, tmp_path):
        """Core package is always included even with empty mg_root."""
        result = discover_packages(tmp_path)

        assert len(result) >= 1
        core = result[0]
        assert core.name == "mg_core"
        assert core.source == PackageSource.CORE

    def test_project_local_included_when_valid(self, tmp_path):
        """Project package included when src/mg_project/commands/__init__.py exists."""
        make_valid_package(tmp_path / "src" / "mg_project")

        result = discover_packages(tmp_path)

        sources = [p.source for p in result]
        assert PackageSource.PROJECT_LOCAL in sources
        project = next(p for p in result if p.source == PackageSource.PROJECT_LOCAL)
        assert project.name == "mg_project"
        assert project.paths.root == tmp_path / "src" / "mg_project"

    def test_project_local_omitted_when_no_init(self, tmp_path):
        """Project package omitted when commands/__init__.py missing."""
        (tmp_path / "src" / "mg_project" / "commands").mkdir(parents=True)
        # No __init__.py

        result = discover_packages(tmp_path)

        sources = [p.source for p in result]
        assert PackageSource.PROJECT_LOCAL not in sources

    def test_project_local_omitted_when_no_commands(self, tmp_path):
        """Project package omitted when commands/ directory missing."""
        (tmp_path / "src" / "mg_project").mkdir(parents=True)
        # No commands/ directory

        result = discover_packages(tmp_path)

        sources = [p.source for p in result]
        assert PackageSource.PROJECT_LOCAL not in sources

    def test_project_local_omitted_when_no_mg_project(self, tmp_path):
        """Project package omitted when src/mg_project/ doesn't exist."""
        result = discover_packages(tmp_path)

        sources = [p.source for p in result]
        assert PackageSource.PROJECT_LOCAL not in sources

    def test_user_local_included_when_valid(self, tmp_path):
        """User package included when user provided and package is valid."""
        user = make_user(tmp_path)
        make_valid_package(user.paths.mg_user.root)

        result = discover_packages(tmp_path, user=user)

        sources = [p.source for p in result]
        assert PackageSource.USER_LOCAL in sources
        user_pkg = next(p for p in result if p.source == PackageSource.USER_LOCAL)
        assert user_pkg.name == "mg_user"
        assert user_pkg.paths.root == user.paths.mg_user.root

    def test_user_local_omitted_when_no_user(self, tmp_path):
        """User package omitted when no user provided."""
        result = discover_packages(tmp_path, user=None)

        sources = [p.source for p in result]
        assert PackageSource.USER_LOCAL not in sources

    def test_user_local_omitted_when_no_init(self, tmp_path):
        """User package omitted when commands/__init__.py missing."""
        user = make_user(tmp_path)
        (user.paths.mg_user.commands_dir).mkdir(parents=True)
        # No __init__.py

        result = discover_packages(tmp_path, user=user)

        sources = [p.source for p in result]
        assert PackageSource.USER_LOCAL not in sources

    def test_user_local_omitted_when_no_commands(self, tmp_path):
        """User package omitted when user's commands/ doesn't exist."""
        user = make_user(tmp_path)
        (user.paths.mg_user.root).mkdir(parents=True)
        # No commands/ directory

        result = discover_packages(tmp_path, user=user)

        sources = [p.source for p in result]
        assert PackageSource.USER_LOCAL not in sources

    def test_discovery_order(self, tmp_path):
        """Packages returned in discovery order: CORE, PROJECT_LOCAL, USER_LOCAL."""
        make_valid_package(tmp_path / "src" / "mg_project")
        user = make_user(tmp_path)
        make_valid_package(user.paths.mg_user.root)

        result = discover_packages(tmp_path, user=user)

        sources = [p.source for p in result]
        assert sources == [
            PackageSource.CORE,
            PackageSource.PROJECT_LOCAL,
            PackageSource.USER_LOCAL,
        ]

    def test_core_paths_from_installed_module(self, tmp_path):
        """Core package paths come from the installed mg_core module."""
        import mg_core
        from mg.paths import PkgPaths

        result = discover_packages(tmp_path)

        core = result[0]
        expected_paths = PkgPaths.from_module(mg_core)
        assert core.paths.root == expected_paths.root


class TestDiscoverPackagesDetailed:
    """Tests for discover_packages_detailed function."""

    def test_returns_discovery_result(self, tmp_path):
        """Returns a PkgDiscoveryResult."""
        result = discover_packages_detailed(tmp_path)

        assert isinstance(result, PkgDiscoveryResult)
        assert isinstance(result.packages, list)
        assert isinstance(result.included, list)
        assert isinstance(result.skipped, list)

    def test_included_matches_packages(self, tmp_path):
        """Included list has same packages as packages list."""
        make_valid_package(tmp_path / "src" / "mg_project")

        result = discover_packages_detailed(tmp_path)

        assert len(result.included) == len(result.packages)
        for pkg, inc in zip(result.packages, result.included):
            assert pkg.name == inc.name
            assert pkg.source == inc.source

    def test_skipped_has_reasons(self, tmp_path):
        """Skipped packages have skip reasons."""
        # Don't create mg_project - it will be skipped

        result = discover_packages_detailed(tmp_path)

        project_skipped = [s for s in result.skipped if s.source == PackageSource.PROJECT_LOCAL]
        assert len(project_skipped) == 1
        assert project_skipped[0].reason is not None

    def test_skip_reason_no_commands_dir(self, tmp_path):
        """Skip reason when commands/ directory missing."""
        (tmp_path / "src" / "mg_project").mkdir(parents=True)

        result = discover_packages_detailed(tmp_path)

        project_skipped = [s for s in result.skipped if s.source == PackageSource.PROJECT_LOCAL]
        assert project_skipped[0].reason is not None
        assert "commands/ directory not found" in project_skipped[0].reason

    def test_skip_reason_no_init(self, tmp_path):
        """Skip reason when commands/__init__.py missing."""
        (tmp_path / "src" / "mg_project" / "commands").mkdir(parents=True)

        result = discover_packages_detailed(tmp_path)

        project_skipped = [s for s in result.skipped if s.source == PackageSource.PROJECT_LOCAL]
        assert project_skipped[0].reason is not None
        assert "commands/__init__.py not found" in project_skipped[0].reason

    def test_included_has_no_reason(self, tmp_path):
        """Included packages have None for reason."""
        make_valid_package(tmp_path / "src" / "mg_project")

        result = discover_packages_detailed(tmp_path)

        project_included = [i for i in result.included if i.source == PackageSource.PROJECT_LOCAL]
        assert len(project_included) == 1
        assert project_included[0].reason is None

    def test_user_skipped_when_no_user(self, tmp_path):
        """User package skipped with reason when no user provided."""
        result = discover_packages_detailed(tmp_path, user=None)

        user_entries = [s for s in result.skipped if s.source == PackageSource.USER_LOCAL]
        assert len(user_entries) == 1
        assert user_entries[0].reason == "user not provided"

    def test_user_in_skipped_when_invalid(self, tmp_path):
        """User package in skipped when user provided but package invalid."""
        user = make_user(tmp_path)
        # Don't create valid package structure

        result = discover_packages_detailed(tmp_path, user=user)

        user_skipped = [s for s in result.skipped if s.source == PackageSource.USER_LOCAL]
        assert len(user_skipped) == 1
        assert user_skipped[0].reason is not None

    def test_always_five_results(self, tmp_path):
        """Always returns 5 results (one per PackageSource)."""
        result = discover_packages_detailed(tmp_path)

        total = len(result.included) + len(result.skipped)
        assert total == 5

    def test_installed_packages_not_implemented(self, tmp_path):
        """Installed package sources are skipped as not implemented."""
        result = discover_packages_detailed(tmp_path)

        project_installed = [s for s in result.skipped if s.source == PackageSource.PROJECT_INSTALLED]
        user_installed = [s for s in result.skipped if s.source == PackageSource.USER_INSTALLED]

        assert len(project_installed) == 1
        assert project_installed[0].reason == "not implemented"
        assert len(user_installed) == 1
        assert user_installed[0].reason == "not implemented"

    def test_mg_root_none_skips_project_and_user(self):
        """When mg_root is None, project and user are skipped."""
        result = discover_packages_detailed(mg_root=None)

        project = [s for s in result.skipped if s.source == PackageSource.PROJECT_LOCAL]
        user = [s for s in result.skipped if s.source == PackageSource.USER_LOCAL]

        assert len(project) == 1
        assert project[0].reason == "mg_root not provided"
        assert len(user) == 1
        assert user[0].reason == "mg_root not provided"
