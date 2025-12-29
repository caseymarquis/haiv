"""Tests for mg.paths module."""

from pathlib import Path

import pytest

from mg.paths import Paths, PkgPaths


class TestPkgPaths:
    """Tests for PkgPaths - package/module paths."""

    def test_root_is_stored(self, tmp_path):
        """root is stored as provided."""
        pkg = PkgPaths(root=tmp_path)
        assert pkg.root == tmp_path

    def test_assets_is_relative_to_root(self, tmp_path):
        """assets is __assets__ under root."""
        pkg = PkgPaths(root=tmp_path)
        assert pkg.assets == tmp_path / "__assets__"


class TestPaths:
    """Tests for Paths - mg project paths."""

    @pytest.fixture
    def paths(self, tmp_path):
        """Create Paths with tmp directories."""
        pkg_root = tmp_path / "src" / "mg_core"
        pkg_root.mkdir(parents=True)

        return Paths(
            root=tmp_path,
            pkg=PkgPaths(root=pkg_root),
        )

    def test_root_is_stored(self, paths, tmp_path):
        """root is stored as provided."""
        assert paths.root == tmp_path

    def test_git_dir(self, paths, tmp_path):
        """git_dir is .git under root."""
        assert paths.git_dir == tmp_path / ".git"

    def test_worktrees(self, paths, tmp_path):
        """worktrees is worktrees under root."""
        assert paths.worktrees == tmp_path / "worktrees"

    def test_pkg_is_pkg_paths(self, paths):
        """pkg is a PkgPaths instance."""
        assert isinstance(paths.pkg, PkgPaths)

    def test_pkg_assets(self, paths, tmp_path):
        """pkg.assets points to package's __assets__."""
        assert paths.pkg.assets == tmp_path / "src" / "mg_core" / "__assets__"

    def test_project_is_pkg_paths(self, paths):
        """project is a PkgPaths instance (computed from root)."""
        assert isinstance(paths.project, PkgPaths)

    def test_project_root_derived_from_root(self, paths, tmp_path):
        """project.root is derived from paths.root."""
        assert paths.project.root == tmp_path / "src" / "mg_project"

    def test_project_assets(self, paths, tmp_path):
        """project.assets points to project's __assets__."""
        assert paths.project.assets == tmp_path / "src" / "mg_project" / "__assets__"


# TODO: Add paths.user after user identification is implemented
# paths.user will point to users/{current_user}/src/mg_user/
