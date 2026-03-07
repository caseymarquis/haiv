"""Tests for haiv.paths module."""

from pathlib import Path

import pytest

from haiv.paths import Paths, PkgPaths


class TestPkgPaths:
    """Tests for PkgPaths - package/module paths."""

    def test_root_is_stored(self, tmp_path):
        """root is stored as provided."""
        pkg = PkgPaths(root=tmp_path)
        assert pkg.root == tmp_path

    def test_assets_is_relative_to_root(self, tmp_path):
        """assets is __assets__ under root."""
        pkg = PkgPaths(root=tmp_path)
        assert pkg.assets_dir == tmp_path / "__assets__"


class TestPaths:
    """Tests for Paths - haiv project paths."""

    @pytest.fixture
    def paths(self, tmp_path):
        """Create Paths with all fields set."""
        pkg_root = tmp_path / "src" / "haiv_core"
        pkg_root.mkdir(parents=True)

        return Paths(
            _called_from=tmp_path / "workdir",
            _pkg_root=pkg_root,
            _haiv_root=tmp_path,
        )

    def test_called_from(self, paths, tmp_path):
        """called_from returns the invocation directory."""
        assert paths.called_from == tmp_path / "workdir"

    def test_called_from_raises_if_none(self, tmp_path):
        """called_from raises if not set."""
        paths = Paths(_called_from=None, _pkg_root=tmp_path, _haiv_root=None)
        with pytest.raises(RuntimeError, match="called_from not set"):
            _ = paths.called_from

    def test_root(self, paths, tmp_path):
        """root returns haiv_root."""
        assert paths.root == tmp_path

    def test_root_raises_if_none(self, tmp_path):
        """root raises if haiv_root not set."""
        paths = Paths(_called_from=tmp_path, _pkg_root=tmp_path, _haiv_root=None)
        with pytest.raises(RuntimeError, match="haiv project root not set"):
            _ = paths.root

    def test_git_dir(self, paths, tmp_path):
        """git_dir is .git under root."""
        assert paths.git_dir == tmp_path / ".git"

    def test_worktrees(self, paths, tmp_path):
        """worktrees is worktrees under root."""
        assert paths.worktrees_dir == tmp_path / "worktrees"

    def test_pkg_is_pkg_paths(self, paths):
        """pkg is a PkgPaths instance."""
        assert isinstance(paths.pkgs.current, PkgPaths)

    def test_pkg_raises_if_none(self, tmp_path):
        """pkgs.current raises if pkg_root not set."""
        paths = Paths(_called_from=tmp_path, _pkg_root=None, _haiv_root=None)
        with pytest.raises(RuntimeError, match="Package root not set"):
            _ = paths.pkgs.current

    def test_pkg_assets(self, paths, tmp_path):
        """pkg.assets_dir points to package's __assets__."""
        assert paths.pkgs.current.assets_dir == tmp_path / "src" / "haiv_core" / "__assets__"

    def test_project_is_pkg_paths(self, paths):
        """project is a PkgPaths instance (computed from root)."""
        assert isinstance(paths.pkgs.project, PkgPaths)

    def test_project_root_derived_from_root(self, paths, tmp_path):
        """project.root is derived from paths.root."""
        assert paths.pkgs.project.root == tmp_path / "src" / "haiv_project"

    def test_project_assets(self, paths, tmp_path):
        """project.assets_dir points to project's __assets__."""
        assert paths.pkgs.project.assets_dir == tmp_path / "src" / "haiv_project" / "__assets__"


# TODO: Add paths.user after user identification is implemented
# paths.user will point to users/{current_user}/src/haiv_user/


class TestIsValidHaivRoot:
    """Tests for _is_valid_haiv_root helper."""

    def test_valid_when_has_git_and_worktrees(self, tmp_path):
        """Valid haiv root has .git and worktrees directories."""
        from haiv.paths import _is_valid_haiv_root

        (tmp_path / ".git").mkdir()
        (tmp_path / "worktrees").mkdir()
        assert _is_valid_haiv_root(tmp_path) is True

    def test_invalid_when_missing_git(self, tmp_path):
        """Invalid if .git is missing."""
        from haiv.paths import _is_valid_haiv_root

        (tmp_path / "worktrees").mkdir()
        assert _is_valid_haiv_root(tmp_path) is False

    def test_invalid_when_missing_worktrees(self, tmp_path):
        """Invalid if worktrees is missing."""
        from haiv.paths import _is_valid_haiv_root

        (tmp_path / ".git").mkdir()
        assert _is_valid_haiv_root(tmp_path) is False

    def test_invalid_when_empty(self, tmp_path):
        """Invalid if directory is empty."""
        from haiv.paths import _is_valid_haiv_root

        assert _is_valid_haiv_root(tmp_path) is False


class TestGetHaivRoot:
    """Tests for get_haiv_root function."""

    @pytest.fixture
    def valid_haiv_root(self, tmp_path):
        """Create a valid haiv root directory."""
        (tmp_path / ".git").mkdir()
        (tmp_path / "worktrees").mkdir()
        return tmp_path

    # --- Environment variable tests ---

    def test_returns_env_var_when_valid(self, valid_haiv_root, monkeypatch):
        """Returns HV_ROOT env var when set and valid."""
        from haiv._infrastructure import env
        from haiv.paths import get_haiv_root

        monkeypatch.setenv(env.HV_ROOT, str(valid_haiv_root))
        assert get_haiv_root(cwd=Path("/some/other/path")) == valid_haiv_root

    def test_raises_if_env_not_absolute(self, tmp_path, monkeypatch):
        """Raises if HV_ROOT is not absolute."""
        from haiv._infrastructure import env
        from haiv.paths import get_haiv_root

        monkeypatch.setenv(env.HV_ROOT, "relative/path")
        with pytest.raises(ValueError, match="must be an absolute path"):
            get_haiv_root(cwd=tmp_path)

    def test_raises_if_env_path_missing(self, tmp_path, monkeypatch):
        """Raises if HV_ROOT path doesn't exist."""
        from haiv._infrastructure import env
        from haiv.paths import get_haiv_root

        monkeypatch.setenv(env.HV_ROOT, "/nonexistent/path")
        with pytest.raises(ValueError, match="path does not exist"):
            get_haiv_root(cwd=tmp_path)

    def test_raises_if_env_not_valid_haiv_root(self, tmp_path, monkeypatch):
        """Raises if HV_ROOT exists but is not a valid haiv root."""
        from haiv._infrastructure import env
        from haiv.paths import get_haiv_root

        monkeypatch.setenv(env.HV_ROOT, str(tmp_path))
        with pytest.raises(ValueError, match="not a valid haiv root"):
            get_haiv_root(cwd=tmp_path)

    # --- Walking upward tests ---

    def test_finds_haiv_root_in_cwd(self, valid_haiv_root, monkeypatch):
        """Finds haiv root when cwd is the root."""
        from haiv._infrastructure import env
        from haiv.paths import get_haiv_root

        monkeypatch.delenv(env.HV_ROOT, raising=False)
        assert get_haiv_root(cwd=valid_haiv_root) == valid_haiv_root

    def test_finds_haiv_root_in_parent(self, valid_haiv_root, monkeypatch):
        """Finds haiv root by walking up from subdirectory."""
        from haiv._infrastructure import env
        from haiv.paths import get_haiv_root

        subdir = valid_haiv_root / "some" / "nested" / "dir"
        subdir.mkdir(parents=True)

        monkeypatch.delenv(env.HV_ROOT, raising=False)
        assert get_haiv_root(cwd=subdir) == valid_haiv_root

    def test_raises_when_no_haiv_root_found(self, tmp_path, monkeypatch):
        """Raises when no haiv root can be found walking up."""
        from haiv._infrastructure import env
        from haiv.paths import get_haiv_root

        monkeypatch.delenv(env.HV_ROOT, raising=False)
        with pytest.raises(ValueError, match="Could not find haiv root"):
            get_haiv_root(cwd=tmp_path)

    # --- Error message tests ---

    def test_error_suggests_haiv_start(self, tmp_path, monkeypatch):
        """Error messages guide user to run hv start."""
        from haiv._infrastructure import env
        from haiv.paths import get_haiv_root

        monkeypatch.delenv(env.HV_ROOT, raising=False)
        with pytest.raises(ValueError, match="hv start"):
            get_haiv_root(cwd=tmp_path)
