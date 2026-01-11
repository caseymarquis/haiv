"""Tests for mg.identity module - user detection and matching."""

from pathlib import Path

import pytest

from mg._infrastructure.identity import (
    AmbiguousIdentityError,
    CurrentEnv,
    Identity,
    IdentityLoadError,
    MatchConfig,
    detect_user,
    get_current_env,
    load_match_config,
    matches,
    valid_match_fields,
)


class TestValidMatchFields:
    """Tests for valid_match_fields()."""

    def test_returns_set(self):
        """Returns a set of field names."""
        result = valid_match_fields()
        assert isinstance(result, set)

    def test_contains_expected_fields(self):
        """Contains the fields from CurrentEnv."""
        result = valid_match_fields()
        assert "git_email" in result
        assert "git_name" in result
        assert "system_user" in result

    def test_matches_current_env_fields(self):
        """Exactly matches CurrentEnv dataclass fields."""
        from dataclasses import fields

        expected = {f.name for f in fields(CurrentEnv)}
        assert valid_match_fields() == expected


class TestGetCurrentEnv:
    """Tests for get_current_env()."""

    def test_returns_current_env(self):
        """Returns a CurrentEnv instance."""
        result = get_current_env()
        assert isinstance(result, CurrentEnv)

    def test_system_user_from_env(self, monkeypatch):
        """system_user comes from USER env var."""
        monkeypatch.setenv("USER", "testuser")
        result = get_current_env()
        assert result.system_user == "testuser"


class TestLoadMatchConfig:
    """Tests for load_match_config()."""

    def test_loads_valid_toml(self, tmp_path):
        """Parses a valid identity.toml file."""
        identity_file = tmp_path / "identity.toml"
        identity_file.write_text("""\
[match]
git_email = ["casey@example.com", "casey@work.com"]
git_name = ["Casey"]
system_user = ["casey"]
""")

        result = load_match_config(identity_file)
        assert result["git_email"] == ["casey@example.com", "casey@work.com"]
        assert result["git_name"] == ["Casey"]
        assert result["system_user"] == ["casey"]

    def test_returns_empty_dict_when_file_missing(self, tmp_path):
        """Returns empty dict when file doesn't exist."""
        identity_file = tmp_path / "identity.toml"
        result = load_match_config(identity_file)
        assert result == {}

    def test_returns_empty_dict_when_no_match_section(self, tmp_path):
        """Returns empty dict when [match] section missing."""
        identity_file = tmp_path / "identity.toml"
        identity_file.write_text("# Empty file\n")

        result = load_match_config(identity_file)
        assert result == {}

    def test_raises_on_malformed_toml(self, tmp_path):
        """Raises IdentityLoadError on malformed TOML."""
        identity_file = tmp_path / "identity.toml"
        identity_file.write_text("this is not valid [ toml")

        with pytest.raises(IdentityLoadError):
            load_match_config(identity_file)


class TestMatches:
    """Tests for matches()."""

    def test_matches_by_git_email(self):
        """Matches when git_email is in the list."""
        config: MatchConfig = {"git_email": ["casey@example.com"]}
        env = CurrentEnv(git_email="casey@example.com")

        result = matches(config, env)
        assert result == "git_email"

    def test_matches_by_git_name(self):
        """Matches when git_name is in the list."""
        config: MatchConfig = {"git_name": ["Casey"]}
        env = CurrentEnv(git_name="Casey")

        result = matches(config, env)
        assert result == "git_name"

    def test_matches_by_system_user(self):
        """Matches when system_user is in the list."""
        config: MatchConfig = {"system_user": ["casey"]}
        env = CurrentEnv(system_user="casey")

        result = matches(config, env)
        assert result == "system_user"

    def test_case_insensitive_git_email(self):
        """git_email matching is case-insensitive."""
        config: MatchConfig = {"git_email": ["Casey@Example.COM"]}
        env = CurrentEnv(git_email="casey@example.com")

        result = matches(config, env)
        assert result == "git_email"

    def test_case_insensitive_git_name(self):
        """git_name matching is case-insensitive."""
        config: MatchConfig = {"git_name": ["CASEY"]}
        env = CurrentEnv(git_name="casey")

        result = matches(config, env)
        assert result == "git_name"

    def test_case_insensitive_system_user(self):
        """system_user matching is case-insensitive."""
        config: MatchConfig = {"system_user": ["Casey"]}
        env = CurrentEnv(system_user="CASEY")

        result = matches(config, env)
        assert result == "system_user"

    def test_no_match_returns_none(self):
        """Returns None when nothing matches."""
        config: MatchConfig = {"git_email": ["other@example.com"]}
        env = CurrentEnv(git_email="casey@example.com")

        result = matches(config, env)
        assert result is None

    def test_no_match_when_env_value_is_none(self):
        """Returns None when env value is None."""
        config: MatchConfig = {"git_email": ["casey@example.com"]}
        env = CurrentEnv(git_email=None)

        result = matches(config, env)
        assert result is None

    def test_matches_any_of_multiple_values(self):
        """Matches if any value in the list matches."""
        config: MatchConfig = {"git_email": ["personal@example.com", "work@example.com"]}
        env = CurrentEnv(git_email="work@example.com")

        result = matches(config, env)
        assert result == "git_email"

    def test_empty_config_returns_none(self):
        """Returns None when config is empty."""
        config: MatchConfig = {}
        env = CurrentEnv(git_email="casey@example.com")

        result = matches(config, env)
        assert result is None

    def test_first_matching_field_wins(self):
        """Returns first matching field in iteration order."""
        config: MatchConfig = {
            "git_email": ["casey@example.com"],
            "system_user": ["casey"],
        }
        env = CurrentEnv(git_email="casey@example.com", system_user="casey")

        result = matches(config, env)
        # git_email comes before system_user in CurrentEnv
        assert result == "git_email"


class TestDetectUser:
    """Tests for detect_user()."""

    @pytest.fixture
    def users_dir(self, tmp_path):
        """Create a users directory."""
        users = tmp_path / "users"
        users.mkdir()
        return users

    def test_returns_identity_when_match_found(self, users_dir, monkeypatch):
        """Returns Identity when a user matches."""
        user_dir = users_dir / "casey"
        user_dir.mkdir()
        (user_dir / "identity.toml").write_text("""\
[match]
system_user = ["testuser"]
""")

        monkeypatch.setenv("USER", "testuser")

        identity = detect_user(users_dir)
        assert identity is not None
        assert identity.name == "casey"
        assert identity.path == user_dir

    def test_returns_none_when_no_match(self, users_dir, monkeypatch):
        """Returns None when no user matches."""
        user_dir = users_dir / "casey"
        user_dir.mkdir()
        (user_dir / "identity.toml").write_text("""\
[match]
system_user = ["otheruser"]
""")

        monkeypatch.setenv("USER", "testuser")

        identity = detect_user(users_dir)
        assert identity is None

    def test_returns_none_when_dir_missing(self, tmp_path, monkeypatch):
        """Returns None when users directory doesn't exist."""
        monkeypatch.setenv("USER", "testuser")

        identity = detect_user(tmp_path / "nonexistent")
        assert identity is None

    def test_returns_none_when_dir_empty(self, users_dir, monkeypatch):
        """Returns None when users directory is empty."""
        monkeypatch.setenv("USER", "testuser")

        identity = detect_user(users_dir)
        assert identity is None

    def test_skips_users_without_identity_toml(self, users_dir, monkeypatch):
        """Skips user directories that lack identity.toml."""
        # User without identity.toml
        (users_dir / "incomplete").mkdir()

        # User with identity.toml that matches
        user_dir = users_dir / "casey"
        user_dir.mkdir()
        (user_dir / "identity.toml").write_text("""\
[match]
system_user = ["testuser"]
""")

        monkeypatch.setenv("USER", "testuser")

        identity = detect_user(users_dir)
        assert identity is not None
        assert identity.name == "casey"

    def test_raises_on_ambiguous_match(self, users_dir, monkeypatch):
        """Raises AmbiguousIdentityError when multiple users match."""
        for name in ["alice", "bob"]:
            user_dir = users_dir / name
            user_dir.mkdir()
            (user_dir / "identity.toml").write_text("""\
[match]
system_user = ["testuser"]
""")

        monkeypatch.setenv("USER", "testuser")

        with pytest.raises(AmbiguousIdentityError) as exc_info:
            detect_user(users_dir)

        error_msg = str(exc_info.value)
        assert "identity.toml" in error_msg

    def test_ignores_dotfiles(self, users_dir, monkeypatch):
        """Ignores dotfiles in users directory."""
        (users_dir / ".gitkeep").touch()

        monkeypatch.setenv("USER", "testuser")

        identity = detect_user(users_dir)
        assert identity is None

    def test_ignores_regular_files(self, users_dir, monkeypatch):
        """Ignores regular files in users directory."""
        (users_dir / "README.md").write_text("# Users\n")

        monkeypatch.setenv("USER", "testuser")

        identity = detect_user(users_dir)
        assert identity is None

    def test_matched_by_is_set(self, users_dir, monkeypatch):
        """Identity includes which field matched."""
        user_dir = users_dir / "casey"
        user_dir.mkdir()
        (user_dir / "identity.toml").write_text("""\
[match]
git_email = ["casey@example.com"]
""")

        monkeypatch.setenv("USER", "otheruser")
        # We need to mock get_current_env or set git config
        # For now, let's test with system_user which we can control
        (user_dir / "identity.toml").write_text("""\
[match]
system_user = ["testuser"]
""")
        monkeypatch.setenv("USER", "testuser")

        identity = detect_user(users_dir)
        assert identity is not None
        assert identity.matched_by == "system_user"


class TestIdentityDataclass:
    """Tests for Identity dataclass."""

    def test_has_expected_fields(self):
        """Identity has name, path, matched_by fields."""
        identity = Identity(
            name="casey",
            path=Path("/tmp/users/casey"),
            matched_by="git_email",
        )

        assert identity.name == "casey"
        assert identity.path == Path("/tmp/users/casey")
        assert identity.matched_by == "git_email"


class TestAmbiguousIdentityError:
    """Tests for AmbiguousIdentityError exception."""

    def test_stores_paths(self):
        """Stores the conflicting paths."""
        paths = [Path("/a/identity.toml"), Path("/b/identity.toml")]
        error = AmbiguousIdentityError(paths)

        assert error.paths == paths

    def test_str_contains_paths(self):
        """String representation contains the paths."""
        paths = [Path("/a/identity.toml"), Path("/b/identity.toml")]
        error = AmbiguousIdentityError(paths)

        error_str = str(error)
        assert "/a/identity.toml" in error_str
        assert "/b/identity.toml" in error_str
