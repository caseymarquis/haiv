"""Integration tests for multi-source command loading."""

import os
import sys
from pathlib import Path

import pytest


def _reset_cli_cache():
    """Reset all cached lookups in mg_cli."""
    import mg_cli
    mg_cli._mg_root = None
    mg_cli._mg_root_error = None
    mg_cli._user = None
    mg_cli._user_error = None


@pytest.fixture
def mg_project(tmp_path, monkeypatch):
    """Create a minimal mg project structure."""
    # Create mg root markers
    (tmp_path / ".git").mkdir()
    (tmp_path / "worktrees").mkdir()

    # Create mg_project commands
    commands_dir = tmp_path / "src" / "mg_project" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "__init__.py").write_text("# mg_project commands")

    # Create users directory (empty)
    (tmp_path / "users").mkdir()

    # Set MG_ROOT and change to project dir
    monkeypatch.setenv("MG_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    _reset_cli_cache()

    return tmp_path


@pytest.fixture
def mg_project_with_user(mg_project, monkeypatch):
    """Create an mg project with a user that matches current env."""
    # Create user directory with identity.toml
    user_dir = mg_project / "users" / "testuser"
    user_dir.mkdir(parents=True)

    # Get current system user for matching
    system_user = os.environ.get("USER", "nobody")
    (user_dir / "identity.toml").write_text(f'''\
[match]
system_user = ["{system_user}"]
''')

    # Create mg_user commands
    commands_dir = user_dir / "src" / "mg_user" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "__init__.py").write_text("# mg_user commands")

    _reset_cli_cache()

    return mg_project


class TestCommandSources:
    """Tests for command source resolution."""

    def test_core_command_works(self, monkeypatch):
        """Commands from mg_core are found."""
        from mg_cli import _find_command

        _reset_cli_cache()

        route, mg_root, sources = _find_command("test_cmd")

        assert route is not None
        assert route.file.name == "test_cmd.py"
        # mg_core should be in checked sources
        core_sources = [s for s in sources if s.name == "mg_core"]
        assert len(core_sources) == 1
        assert core_sources[0].checked is True

    def test_project_command_takes_precedence(self, mg_project):
        """mg_project commands override mg_core commands."""
        from mg_cli import _find_command

        # Create a test_cmd in mg_project that shadows mg_core's
        commands_dir = mg_project / "src" / "mg_project" / "commands"
        (commands_dir / "test_cmd.py").write_text('''
from mg import cmd

def define() -> cmd.Def:
    return cmd.Def(description="Project test command")

def execute(ctx: cmd.Ctx) -> None:
    print("Hello from mg_project!")
''')

        route, mg_root, sources = _find_command("test_cmd")

        assert route is not None
        # Should come from mg_project, not mg_core
        assert "mg_project" in str(route.file)
        assert mg_root == mg_project

    def test_project_only_command(self, mg_project):
        """Commands only in mg_project are found."""
        from mg_cli import _find_command

        # Create a command only in mg_project
        commands_dir = mg_project / "src" / "mg_project" / "commands"
        (commands_dir / "project_only.py").write_text('''
from mg import cmd

def define() -> cmd.Def:
    return cmd.Def(description="Project-only command")

def execute(ctx: cmd.Ctx) -> None:
    print("Only in project!")
''')

        route, mg_root, sources = _find_command("project_only")

        assert route is not None
        assert route.file.name == "project_only.py"

    def test_fallback_to_core_when_not_in_project(self, mg_project):
        """Falls back to mg_core when command not in mg_project."""
        from mg_cli import _find_command

        # mg_project exists but doesn't have test_cmd
        route, mg_root, sources = _find_command("test_cmd")

        assert route is not None
        assert "mg_core" in str(route.file)

    def test_reports_unchecked_sources(self, tmp_path, monkeypatch):
        """Reports sources that couldn't be checked."""
        from mg_cli import _find_command

        # Not in an mg project
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("MG_ROOT", raising=False)

        _reset_cli_cache()

        route, mg_root, sources = _find_command("nonexistent")

        assert route is None
        # mg_project should be unchecked
        project_sources = [s for s in sources if s.name == "mg_project"]
        assert len(project_sources) == 1
        assert project_sources[0].checked is False
        assert project_sources[0].error is not None


class TestUserCommandSources:
    """Tests for user command source resolution."""

    def test_user_command_takes_precedence_over_project(self, mg_project_with_user):
        """mg_user commands override mg_project commands."""
        from mg_cli import _find_command

        # Create same command in both mg_project and mg_user
        project_commands = mg_project_with_user / "src" / "mg_project" / "commands"
        (project_commands / "shared_cmd.py").write_text('''
from mg import cmd

def define() -> cmd.Def:
    return cmd.Def(description="Project version")

def execute(ctx: cmd.Ctx) -> None:
    print("Hello from mg_project!")
''')

        user_commands = mg_project_with_user / "users" / "testuser" / "src" / "mg_user" / "commands"
        (user_commands / "shared_cmd.py").write_text('''
from mg import cmd

def define() -> cmd.Def:
    return cmd.Def(description="User version")

def execute(ctx: cmd.Ctx) -> None:
    print("Hello from mg_user!")
''')

        route, mg_root, sources = _find_command("shared_cmd")

        assert route is not None
        # Should come from mg_user, not mg_project
        assert "mg_user" in str(route.file)

    def test_user_only_command(self, mg_project_with_user):
        """Commands only in mg_user are found."""
        from mg_cli import _find_command

        user_commands = mg_project_with_user / "users" / "testuser" / "src" / "mg_user" / "commands"
        (user_commands / "user_only.py").write_text('''
from mg import cmd

def define() -> cmd.Def:
    return cmd.Def(description="User-only command")

def execute(ctx: cmd.Ctx) -> None:
    print("Only in user!")
''')

        route, mg_root, sources = _find_command("user_only")

        assert route is not None
        assert route.file.name == "user_only.py"

    def test_fallback_to_project_when_not_in_user(self, mg_project_with_user):
        """Falls back to mg_project when command not in mg_user."""
        from mg_cli import _find_command

        project_commands = mg_project_with_user / "src" / "mg_project" / "commands"
        (project_commands / "project_cmd.py").write_text('''
from mg import cmd

def define() -> cmd.Def:
    return cmd.Def(description="Project command")

def execute(ctx: cmd.Ctx) -> None:
    print("From project!")
''')

        route, mg_root, sources = _find_command("project_cmd")

        assert route is not None
        assert "mg_project" in str(route.file)

    def test_no_user_reports_unchecked(self, mg_project):
        """Reports mg_user as unchecked when no user identity found."""
        from mg_cli import _find_command

        # mg_project exists but no user
        route, mg_root, sources = _find_command("test_cmd")

        # mg_user should be unchecked
        user_sources = [s for s in sources if s.name == "mg_user"]
        assert len(user_sources) == 1
        assert user_sources[0].checked is False
        assert "No user identity found" in user_sources[0].error
