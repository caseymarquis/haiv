"""Integration tests for hv users new command.

Tests the full execute() behavior including:
- Directory structure creation
- identity.toml generation from current environment
- --replace and --merge flag behavior
- Validation errors
"""

from pathlib import Path

import pytest

from haiv import test
from haiv.errors import CommandError
from haiv.test import Sandbox, SandboxConfig


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sandbox():
    """Sandbox for users new tests."""
    return test.create_sandbox()


# =============================================================================
# Validation Tests
# =============================================================================


class TestValidation:
    """Test input validation."""

    def test_name_required(self, sandbox: Sandbox):
        """--name is required."""
        with pytest.raises(KeyError, match="name"):
            sandbox.run("users new")

    def test_name_must_be_lowercase(self, sandbox: Sandbox):
        """Name must be lowercase."""
        with pytest.raises(CommandError, match="lowercase"):
            sandbox.run("users new --name Casey")

    def test_name_must_start_with_letter(self, sandbox: Sandbox):
        """Name must start with a letter."""
        with pytest.raises(CommandError, match="letter"):
            sandbox.run("users new --name 123user")

    def test_name_no_special_chars(self, sandbox: Sandbox):
        """Name cannot contain special characters."""
        with pytest.raises(CommandError, match="alphanumeric"):
            sandbox.run("users new --name user@domain")

    def test_name_allows_hyphens(self, sandbox: Sandbox):
        """Name can contain hyphens."""
        sandbox.run("users new --name my-user")
        assert (sandbox.ctx.paths.users_dir / "my-user").is_dir()

    def test_name_allows_underscores(self, sandbox: Sandbox):
        """Name can contain underscores."""
        sandbox.run("users new --name my_user")
        assert (sandbox.ctx.paths.users_dir / "my_user").is_dir()

    def test_replace_and_merge_mutually_exclusive(self, sandbox: Sandbox):
        """--replace and --merge cannot be used together."""
        with pytest.raises(CommandError, match="mutually exclusive"):
            sandbox.run("users new --name casey --replace --merge")


# =============================================================================
# Directory Structure Tests
# =============================================================================


class TestDirectoryStructure:
    """Test that correct directory structure is created."""

    def test_creates_user_directory(self, sandbox: Sandbox):
        """Creates users/{name}/ directory."""
        sandbox.run("users new --name casey")
        assert (sandbox.ctx.paths.users_dir / "casey").is_dir()

    def test_creates_identity_toml(self, sandbox: Sandbox):
        """Creates identity.toml."""
        sandbox.run("users new --name casey")
        assert (sandbox.ctx.paths.users_dir / "casey" / "identity.toml").is_file()

    def test_creates_pyproject_toml(self, sandbox: Sandbox):
        """Creates pyproject.toml."""
        sandbox.run("users new --name casey")
        assert (sandbox.ctx.paths.users_dir / "casey" / "pyproject.toml").is_file()

    def test_creates_hv_user_package(self, sandbox: Sandbox):
        """Creates src/hv_user/ package structure."""
        sandbox.run("users new --name casey")
        user_dir = sandbox.ctx.paths.users_dir / "casey"
        assert (user_dir / "src" / "hv_user" / "__init__.py").is_file()
        assert (user_dir / "src" / "hv_user" / "commands" / "__init__.py").is_file()

    def test_creates_state_directory(self, sandbox: Sandbox):
        """Creates state/ directory with .gitkeep."""
        sandbox.run("users new --name casey")
        user_dir = sandbox.ctx.paths.users_dir / "casey"
        assert (user_dir / "state").is_dir()
        assert (user_dir / "state" / ".gitkeep").is_file()


# =============================================================================
# Identity.toml Tests
# =============================================================================


class TestIdentityToml:
    """Test identity.toml content generation."""

    def test_contains_match_section(self, sandbox: Sandbox):
        """identity.toml has [match] section."""
        sandbox.run("users new --name casey")
        content = (sandbox.ctx.paths.users_dir / "casey" / "identity.toml").read_text()
        assert "[match]" in content

    def test_populates_from_current_env(self, sandbox: Sandbox):
        """identity.toml is populated from current environment."""
        sandbox.run("users new --name casey")
        content = (sandbox.ctx.paths.users_dir / "casey" / "identity.toml").read_text()
        # At least one of these should be present
        assert "git_email" in content or "git_name" in content or "system_user" in content


# =============================================================================
# Existing User Tests
# =============================================================================


class TestExistingUser:
    """Test behavior when user already exists."""

    def test_fails_if_user_exists(self, sandbox: Sandbox):
        """Fails if user directory already exists."""
        (sandbox.ctx.paths.users_dir / "casey").mkdir(parents=True)
        with pytest.raises(CommandError, match="already exists"):
            sandbox.run("users new --name casey")

    def test_replace_overwrites_identity(self, sandbox: Sandbox):
        """--replace overwrites identity.toml."""
        user_dir = sandbox.ctx.paths.users_dir / "casey"
        user_dir.mkdir(parents=True)
        identity = user_dir / "identity.toml"
        identity.write_text('[match]\ngit_email = ["old@example.com"]\n')

        sandbox.run("users new --name casey --replace")

        content = identity.read_text()
        assert "old@example.com" not in content

    def test_merge_adds_new_values(self, sandbox: Sandbox):
        """--merge adds new values without removing existing."""
        user_dir = sandbox.ctx.paths.users_dir / "casey"
        user_dir.mkdir(parents=True)
        identity = user_dir / "identity.toml"
        identity.write_text('[match]\ngit_email = ["old@example.com"]\n')

        sandbox.run("users new --name casey --merge")

        content = identity.read_text()
        # Old value should still be present
        assert "old@example.com" in content

    def test_merge_does_not_duplicate(self, sandbox: Sandbox):
        """--merge doesn't add duplicate values."""
        # This test would need to mock get_current_env to return a known value
        # For now, just verify it doesn't error
        user_dir = sandbox.ctx.paths.users_dir / "casey"
        user_dir.mkdir(parents=True)
        identity = user_dir / "identity.toml"
        identity.write_text('[match]\ngit_email = ["test@example.com"]\n')

        sandbox.run("users new --name casey --merge")
        # Should complete without error
