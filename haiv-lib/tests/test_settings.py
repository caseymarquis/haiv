"""Tests for settings infrastructure."""

from pathlib import Path

import pytest

from haiv._infrastructure.settings import (
    PROJECT_SETTINGS_TEMPLATE,
    SettingsCache,
    get_settings,
    load_project_settings,
    load_user_settings,
    merge_settings,
)
from haiv.cmd import Args, Ctx
from haiv.paths import Paths
from haiv.settings import HaivSettings


class TestHaivSettings:
    """Tests for HaivSettings dataclass."""

    def test_default_branch_fallback(self):
        """default_branch falls back to 'main' when not set."""
        settings = HaivSettings()
        assert settings.default_branch == "main"

    def test_default_branch_returns_value_when_set(self):
        """default_branch returns value when set."""
        settings = HaivSettings(_default_branch="develop")
        assert settings.default_branch == "develop"


class TestLoadProjectSettings:
    """Tests for load_project_settings()."""

    def test_loads_valid_toml(self, tmp_path):
        """Loads settings from valid TOML file."""
        settings_file = tmp_path / "haiv.toml"
        settings_file.write_text('default_branch = "develop"\n')

        result = load_project_settings(settings_file)
        assert result._default_branch == "develop"

    def test_creates_file_when_missing(self, tmp_path):
        """Creates file with commented defaults when missing."""
        settings_file = tmp_path / "haiv.toml"

        result = load_project_settings(settings_file)

        assert settings_file.exists()
        assert settings_file.read_text() == PROJECT_SETTINGS_TEMPLATE
        assert result._default_branch is None

    def test_returns_empty_settings_for_empty_file(self, tmp_path):
        """Returns empty settings for empty file."""
        settings_file = tmp_path / "haiv.toml"
        settings_file.write_text("")

        result = load_project_settings(settings_file)
        assert result._default_branch is None


class TestLoadUserSettings:
    """Tests for load_user_settings()."""

    def test_loads_valid_toml(self, tmp_path):
        """Loads settings from valid TOML file."""
        settings_file = tmp_path / "haiv.toml"
        settings_file.write_text('default_branch = "feature"\n')

        result = load_user_settings(settings_file)
        assert result._default_branch == "feature"

    def test_creates_empty_file_when_missing(self, tmp_path):
        """Creates empty file when missing."""
        settings_file = tmp_path / "haiv.toml"

        result = load_user_settings(settings_file)

        assert settings_file.exists()
        assert settings_file.read_text() == ""
        assert result._default_branch is None

    def test_returns_empty_settings_for_empty_file(self, tmp_path):
        """Returns empty settings for empty file."""
        settings_file = tmp_path / "haiv.toml"
        settings_file.write_text("")

        result = load_user_settings(settings_file)
        assert result._default_branch is None


class TestMergeSettings:
    """Tests for merge_settings()."""

    def test_returns_project_when_user_is_none(self):
        """Returns project settings when user is None."""
        project = HaivSettings(_default_branch="develop")

        result = merge_settings(project, None)

        assert result._default_branch == "develop"

    def test_user_overrides_project(self):
        """User value overrides project value."""
        project = HaivSettings(_default_branch="develop")
        user = HaivSettings(_default_branch="feature")

        result = merge_settings(project, user)

        assert result._default_branch == "feature"

    def test_project_used_when_user_is_none_value(self):
        """Project value used when user value is None."""
        project = HaivSettings(_default_branch="develop")
        user = HaivSettings(_default_branch=None)

        result = merge_settings(project, user)

        assert result._default_branch == "develop"

    def test_both_none_stays_none(self):
        """Result is None when both are None."""
        project = HaivSettings(_default_branch=None)
        user = HaivSettings(_default_branch=None)

        result = merge_settings(project, user)

        assert result._default_branch is None


class TestSettingsCache:
    """Tests for SettingsCache."""

    def test_starts_empty(self):
        """Cache starts with None values."""
        cache = SettingsCache()
        assert cache.project is None
        assert cache.user is None

    def test_can_store_settings(self):
        """Cache can store settings."""
        cache = SettingsCache()
        cache.project = HaivSettings(_default_branch="main")
        cache.user = HaivSettings(_default_branch="feature")

        assert cache.project._default_branch == "main"
        assert cache.user._default_branch == "feature"


class TestGetSettings:
    """Tests for get_settings()."""

    @pytest.fixture
    def haiv_root(self, tmp_path):
        """Create a minimal haiv root structure."""
        root = tmp_path / "project"
        root.mkdir()
        (root / ".git").mkdir()
        (root / "worktrees").mkdir()
        return root

    @pytest.fixture
    def user_dir(self, haiv_root):
        """Create a user directory."""
        users = haiv_root / "users"
        users.mkdir()
        user = users / "testuser"
        user.mkdir()
        return user

    def test_loads_project_settings(self, haiv_root):
        """Loads and caches project settings."""
        (haiv_root / "haiv.toml").write_text('default_branch = "develop"\n')

        paths = Paths(
            _called_from=haiv_root,
            _pkg_root=None,
            _haiv_root=haiv_root,
            _user_name=None,
        )
        cache = SettingsCache()

        result = get_settings(paths, cache)

        assert result.default_branch == "develop"
        assert cache.project is not None
        assert cache.project._default_branch == "develop"

    def test_loads_user_settings_when_available(self, haiv_root, user_dir):
        """Loads user settings when user is available."""
        (haiv_root / "haiv.toml").write_text('default_branch = "develop"\n')
        (user_dir / "haiv.toml").write_text('default_branch = "feature"\n')

        paths = Paths(
            _called_from=haiv_root,
            _pkg_root=None,
            _haiv_root=haiv_root,
            _user_name="testuser",
        )
        cache = SettingsCache()

        result = get_settings(paths, cache)

        assert result.default_branch == "feature"
        assert cache.user is not None
        assert cache.user._default_branch == "feature"

    def test_caches_project_settings(self, haiv_root):
        """Project settings are cached."""
        (haiv_root / "haiv.toml").write_text('default_branch = "develop"\n')

        paths = Paths(
            _called_from=haiv_root,
            _pkg_root=None,
            _haiv_root=haiv_root,
            _user_name=None,
        )
        cache = SettingsCache()

        # First call
        get_settings(paths, cache)

        # Modify file - should not affect cached result
        (haiv_root / "haiv.toml").write_text('default_branch = "changed"\n')

        result = get_settings(paths, cache)
        assert result.default_branch == "develop"

    def test_skips_user_settings_when_no_user(self, haiv_root):
        """Does not load user settings when no user."""
        (haiv_root / "haiv.toml").write_text('default_branch = "develop"\n')

        paths = Paths(
            _called_from=haiv_root,
            _pkg_root=None,
            _haiv_root=haiv_root,
            _user_name=None,
        )
        cache = SettingsCache()

        result = get_settings(paths, cache)

        assert result.default_branch == "develop"
        assert cache.user is None


class TestCtxSettings:
    """Tests for Ctx.settings property."""

    @pytest.fixture
    def haiv_root(self, tmp_path):
        """Create a minimal haiv root structure."""
        root = tmp_path / "project"
        root.mkdir()
        (root / ".git").mkdir()
        (root / "worktrees").mkdir()
        return root

    def test_settings_throws_without_haiv_root(self):
        """Accessing settings throws when haiv_root is None."""
        paths = Paths(
            _called_from=Path("/test"),
            _pkg_root=None,
            _haiv_root=None,
        )
        ctx = Ctx(args=Args(), paths=paths)

        with pytest.raises(RuntimeError, match="haiv project root not set"):
            _ = ctx.settings

    def test_settings_returns_merged_settings(self, haiv_root):
        """settings property returns merged settings."""
        (haiv_root / "haiv.toml").write_text('default_branch = "develop"\n')

        paths = Paths(
            _called_from=haiv_root,
            _pkg_root=None,
            _haiv_root=haiv_root,
        )
        ctx = Ctx(args=Args(), paths=paths)

        assert ctx.settings.default_branch == "develop"

    def test_settings_caches_between_accesses(self, haiv_root):
        """settings property caches between accesses."""
        (haiv_root / "haiv.toml").write_text('default_branch = "develop"\n')

        paths = Paths(
            _called_from=haiv_root,
            _pkg_root=None,
            _haiv_root=haiv_root,
        )
        ctx = Ctx(args=Args(), paths=paths)

        # First access
        _ = ctx.settings

        # Modify file
        (haiv_root / "haiv.toml").write_text('default_branch = "changed"\n')

        # Should still return cached value
        assert ctx.settings.default_branch == "develop"
