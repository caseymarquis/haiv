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


class TestResolverIntegration:
    """Integration tests for resolver wiring in mg_cli."""

    def test_implicit_resolver_without_file_returns_raw_value(self, mg_project_with_user):
        """Implicit resolver (_name_/) without resolver file returns raw string."""
        from mg_cli import _find_command, main
        from mg.loader import load_command
        from mg.args import build_ctx
        from mg.resolvers import make_resolver

        # Create command with implicit param resolver
        commands_dir = mg_project_with_user / "src" / "mg_project" / "commands" / "_name_"
        commands_dir.mkdir(parents=True)
        (commands_dir.parent / "__init__.py").touch()
        (commands_dir / "greet.py").write_text('''
from mg import cmd

def define() -> cmd.Def:
    return cmd.Def(description="Greet by name")

def execute(ctx: cmd.Ctx) -> None:
    name = ctx.args.get_one("name")
    print(f"Hello, {name}!")
''')

        route, mg_root, sources = _find_command("alice greet")

        assert route is not None
        assert route.params["name"].value == "alice"
        assert route.params["name"].resolver == "name"

        # Build resolve callback - no resolver file exists
        pkg_roots = [mg_project_with_user / "src" / "mg_project"]
        resolve = make_resolver(pkg_roots, None, has_user=True)

        # Implicit resolver should return raw value
        from mg.args import ResolveRequest
        req = ResolveRequest(param="name", resolver="name", value="alice")
        result = resolve(req)

        assert result == "alice"  # Raw value, no transformation

    def test_explicit_resolver_without_file_raises_error(self, mg_project_with_user):
        """Explicit resolver (_target_as_mind_/) without file raises UnknownResolverError."""
        from mg_cli import _find_command
        from mg.resolvers import make_resolver, UnknownResolverError

        # Create command with explicit param resolver
        commands_dir = mg_project_with_user / "src" / "mg_project" / "commands" / "_target_as_mind_"
        commands_dir.mkdir(parents=True)
        (commands_dir.parent / "__init__.py").touch()
        (commands_dir / "send.py").write_text('''
from mg import cmd

def define() -> cmd.Def:
    return cmd.Def(description="Send to mind")

def execute(ctx: cmd.Ctx) -> None:
    pass
''')

        route, mg_root, sources = _find_command("forge send")

        assert route is not None
        assert route.params["target"].resolver == "mind"

        # Build resolve callback - no resolver file exists
        pkg_roots = [mg_project_with_user / "src" / "mg_project"]
        resolve = make_resolver(pkg_roots, None, has_user=True)

        # Explicit resolver should raise error
        from mg.args import ResolveRequest
        req = ResolveRequest(param="target", resolver="mind", value="forge")

        with pytest.raises(UnknownResolverError) as exc_info:
            resolve(req)

        assert exc_info.value.resolver_name == "mind"

    def test_resolver_file_is_discovered_and_used(self, mg_project_with_user):
        """Resolver file in resolvers/ is discovered and used."""
        from mg.resolvers import make_resolver

        # Create resolver file
        resolvers_dir = mg_project_with_user / "src" / "mg_project" / "resolvers"
        resolvers_dir.mkdir(parents=True)
        (resolvers_dir / "mind.py").write_text('''
def resolve(value, ctx):
    return f"Mind({value})"
''')

        pkg_roots = [mg_project_with_user / "src" / "mg_project"]
        resolve = make_resolver(pkg_roots, None, has_user=True)

        from mg.args import ResolveRequest
        req = ResolveRequest(param="mind", resolver="mind", value="forge")
        result = resolve(req)

        assert result == "Mind(forge)"

    def test_resolver_requires_user_when_found(self, mg_project):
        """Resolver raises UserRequiredError when has_user=False."""
        from mg.resolvers import make_resolver, UserRequiredError

        # Create resolver file
        resolvers_dir = mg_project / "src" / "mg_project" / "resolvers"
        resolvers_dir.mkdir(parents=True)
        (resolvers_dir / "mind.py").write_text('''
def resolve(value, ctx):
    return f"Mind({value})"
''')

        pkg_roots = [mg_project / "src" / "mg_project"]
        resolve = make_resolver(pkg_roots, None, has_user=False)

        from mg.args import ResolveRequest
        req = ResolveRequest(param="mind", resolver="mind", value="forge")

        with pytest.raises(UserRequiredError) as exc_info:
            resolve(req)

        assert exc_info.value.resolver_name == "mind"

    def test_user_resolver_overrides_project_resolver(self, mg_project_with_user):
        """User resolvers override project resolvers."""
        from mg.resolvers import make_resolver

        # Create resolver in project
        project_resolvers = mg_project_with_user / "src" / "mg_project" / "resolvers"
        project_resolvers.mkdir(parents=True)
        (project_resolvers / "mind.py").write_text('''
def resolve(value, ctx):
    return f"ProjectMind({value})"
''')

        # Create resolver in user (should win)
        user_resolvers = mg_project_with_user / "users" / "testuser" / "src" / "mg_user" / "resolvers"
        user_resolvers.mkdir(parents=True)
        (user_resolvers / "mind.py").write_text('''
def resolve(value, ctx):
    return f"UserMind({value})"
''')

        pkg_roots = [
            mg_project_with_user / "src" / "mg_project",
            mg_project_with_user / "users" / "testuser" / "src" / "mg_user",
        ]
        resolve = make_resolver(pkg_roots, None, has_user=True)

        from mg.args import ResolveRequest
        req = ResolveRequest(param="mind", resolver="mind", value="forge")
        result = resolve(req)

        assert result == "UserMind(forge)"  # User wins
