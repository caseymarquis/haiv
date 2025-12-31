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
        """Create Paths with all fields set."""
        pkg_root = tmp_path / "src" / "mg_core"
        pkg_root.mkdir(parents=True)

        return Paths(
            _called_from=tmp_path / "workdir",
            _pkg_root=pkg_root,
            _mg_root=tmp_path,
        )

    def test_called_from(self, paths, tmp_path):
        """called_from returns the invocation directory."""
        assert paths.called_from == tmp_path / "workdir"

    def test_called_from_raises_if_none(self, tmp_path):
        """called_from raises if not set."""
        paths = Paths(_called_from=None, _pkg_root=tmp_path, _mg_root=None)
        with pytest.raises(RuntimeError, match="called_from not set"):
            _ = paths.called_from

    def test_root(self, paths, tmp_path):
        """root returns mg_root."""
        assert paths.root == tmp_path

    def test_root_raises_if_none(self, tmp_path):
        """root raises if mg_root not set."""
        paths = Paths(_called_from=tmp_path, _pkg_root=tmp_path, _mg_root=None)
        with pytest.raises(RuntimeError, match="mg project root not set"):
            _ = paths.root

    def test_git_dir(self, paths, tmp_path):
        """git_dir is .git under root."""
        assert paths.git_dir == tmp_path / ".git"

    def test_worktrees(self, paths, tmp_path):
        """worktrees is worktrees under root."""
        assert paths.worktrees == tmp_path / "worktrees"

    def test_pkg_is_pkg_paths(self, paths):
        """pkg is a PkgPaths instance."""
        assert isinstance(paths.pkg, PkgPaths)

    def test_pkg_raises_if_none(self, tmp_path):
        """pkg raises if pkg_root not set."""
        paths = Paths(_called_from=tmp_path, _pkg_root=None, _mg_root=None)
        with pytest.raises(RuntimeError, match="Package root not set"):
            _ = paths.pkg

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
