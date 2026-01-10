"""Tests for mg_core.helpers.users module."""

import pytest
from pathlib import Path

from mg_core.helpers.users import (
    UserPaths,
    UserInfo,
    UserNotFoundError,
    list_users,
    resolve_user,
)
from mg.paths import PkgPaths


class TestUserPaths:
    """Tests for UserPaths dataclass."""

    def test_mg_user_returns_pkg_paths(self, tmp_path):
        """mg_user property returns PkgPaths for src/mg_user/."""
        paths = UserPaths(root=tmp_path / "casey")
        result = paths.mg_user

        assert isinstance(result, PkgPaths)
        assert result.root == tmp_path / "casey" / "src" / "mg_user"

    def test_state_path(self, tmp_path):
        """state property returns root/state/."""
        paths = UserPaths(root=tmp_path / "casey")
        assert paths.state == tmp_path / "casey" / "state"

    def test_minds_path(self, tmp_path):
        """minds property returns root/state/minds/."""
        paths = UserPaths(root=tmp_path / "casey")
        assert paths.minds == tmp_path / "casey" / "state" / "minds"


class TestUserInfo:
    """Tests for UserInfo dataclass."""

    def test_name_derived_from_path(self, tmp_path):
        """name property returns folder name."""
        paths = UserPaths(root=tmp_path / "casey")
        # Create a minimal Identity
        from mg.identity import Identity
        identity = Identity(name="casey", path=tmp_path / "casey", matched_by="manual")

        user = UserInfo(paths=paths, identity=identity)

        assert user.name == "casey"


class TestListUsers:
    """Tests for list_users function."""

    def test_empty_when_dir_not_exists(self, tmp_path):
        """Returns empty list when users_dir doesn't exist."""
        result = list_users(tmp_path / "nonexistent")
        assert result == []

    def test_finds_user_directories(self, tmp_path):
        """Finds user directories in users_dir."""
        users_dir = tmp_path / "users"
        users_dir.mkdir()
        (users_dir / "alice").mkdir()
        (users_dir / "bob").mkdir()

        result = list_users(users_dir)

        assert len(result) == 2
        names = [u.name for u in result]
        assert "alice" in names
        assert "bob" in names

    def test_excludes_dotfiles(self, tmp_path):
        """Excludes directories starting with '.'."""
        users_dir = tmp_path / "users"
        users_dir.mkdir()
        (users_dir / "casey").mkdir()
        (users_dir / ".hidden").mkdir()

        result = list_users(users_dir)

        assert len(result) == 1
        assert result[0].name == "casey"

    def test_excludes_files(self, tmp_path):
        """Ignores files in users_dir."""
        users_dir = tmp_path / "users"
        users_dir.mkdir()
        (users_dir / "casey").mkdir()
        (users_dir / "README.md").write_text("# Users")

        result = list_users(users_dir)

        assert len(result) == 1
        assert result[0].name == "casey"

    def test_sorted_by_name(self, tmp_path):
        """Returns results sorted by name."""
        users_dir = tmp_path / "users"
        users_dir.mkdir()
        (users_dir / "zara").mkdir()
        (users_dir / "alice").mkdir()
        (users_dir / "bob").mkdir()

        result = list_users(users_dir)

        names = [u.name for u in result]
        assert names == ["alice", "bob", "zara"]

    def test_returns_user_info_objects(self, tmp_path):
        """Returns list of UserInfo objects with proper structure."""
        users_dir = tmp_path / "users"
        (users_dir / "casey").mkdir(parents=True)

        result = list_users(users_dir)

        assert len(result) == 1
        user = result[0]
        assert isinstance(user, UserInfo)
        assert isinstance(user.paths, UserPaths)
        assert user.paths.root == users_dir / "casey"

    def test_identity_has_manual_matched_by(self, tmp_path):
        """Identity has matched_by='manual' for listed users."""
        users_dir = tmp_path / "users"
        (users_dir / "casey").mkdir(parents=True)

        result = list_users(users_dir)

        assert result[0].identity.matched_by == "manual"


class TestResolveUser:
    """Tests for resolve_user function."""

    def test_resolves_existing_user(self, tmp_path):
        """Resolves user that exists."""
        users_dir = tmp_path / "users"
        (users_dir / "casey").mkdir(parents=True)

        user = resolve_user("casey", users_dir)

        assert user.name == "casey"
        assert user.paths.root == users_dir / "casey"

    def test_raises_when_not_found(self, tmp_path):
        """Raises UserNotFoundError when user doesn't exist."""
        users_dir = tmp_path / "users"
        (users_dir / "alice").mkdir(parents=True)

        with pytest.raises(UserNotFoundError) as exc_info:
            resolve_user("unknown", users_dir)

        assert exc_info.value.name == "unknown"
        assert "alice" in exc_info.value.available

    def test_raises_when_users_dir_not_exists(self, tmp_path):
        """Raises UserNotFoundError when users_dir doesn't exist."""
        with pytest.raises(UserNotFoundError) as exc_info:
            resolve_user("casey", tmp_path / "nonexistent")

        assert exc_info.value.name == "casey"
        assert exc_info.value.available == []

    def test_identity_has_correct_fields(self, tmp_path):
        """Identity has correct name, path, and matched_by."""
        users_dir = tmp_path / "users"
        (users_dir / "casey").mkdir(parents=True)

        user = resolve_user("casey", users_dir)

        assert user.identity.name == "casey"
        assert user.identity.path == users_dir / "casey"
        assert user.identity.matched_by == "manual"


class TestUserNotFoundError:
    """Tests for UserNotFoundError exception."""

    def test_error_message_with_available(self):
        """Error message includes available users."""
        error = UserNotFoundError("unknown", ["alice", "bob"])

        message = str(error)

        assert "unknown" in message
        assert "alice" in message or "bob" in message

    def test_error_message_without_available(self):
        """Error message works when no users available."""
        error = UserNotFoundError("unknown", [])

        message = str(error)

        assert "unknown" in message
