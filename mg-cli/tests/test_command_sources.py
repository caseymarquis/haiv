"""Integration tests for multi-source command loading."""

import os
import sys
from pathlib import Path

import pytest


def _reset_cli_cache():
    """Reset all cached lookups in haiv_cli."""
    import haiv_cli
    haiv_cli._hv_root = None
    haiv_cli._hv_root_error = None
    haiv_cli._user = None
    haiv_cli._user_error = None


@pytest.fixture
def hv_project(tmp_path, monkeypatch):
    """Create a minimal haiv project structure."""
    # Create haiv root markers
    (tmp_path / ".git").mkdir()
    (tmp_path / "worktrees").mkdir()

    # Create hv_project commands
    commands_dir = tmp_path / "src" / "hv_project" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "__init__.py").write_text("# hv_project commands")

    # Create users directory (empty)
    (tmp_path / "users").mkdir()

    # Set HV_ROOT and change to project dir
    monkeypatch.setenv("HV_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    _reset_cli_cache()

    return tmp_path


@pytest.fixture
def hv_project_with_user(hv_project, monkeypatch):
    """Create a haiv project with a user that matches current env."""
    # Create user directory with identity.toml
    user_dir = hv_project / "users" / "testuser"
    user_dir.mkdir(parents=True)

    # Get current system user for matching
    system_user = os.environ.get("USER", "nobody")
    (user_dir / "identity.toml").write_text(f'''\
[match]
system_user = ["{system_user}"]
''')

    # Create hv_user commands
    commands_dir = user_dir / "src" / "hv_user" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "__init__.py").write_text("# hv_user commands")

    _reset_cli_cache()

    return hv_project


class TestCommandSources:
    """Tests for command source resolution."""

    def test_core_command_works(self, monkeypatch):
        """Commands from haiv_core are found."""
        from haiv_cli import _find_command

        _reset_cli_cache()

        route, hv_root, sources = _find_command("test_cmd")

        assert route is not None
        assert route.file is not None
        assert route.file.name == "test_cmd.py"
        # haiv_core should be in checked sources
        core_sources = [s for s in sources if s.name == "haiv_core"]
        assert len(core_sources) == 1
        assert core_sources[0].checked is True

    def test_project_command_takes_precedence(self, hv_project):
        """hv_project commands override haiv_core commands."""
        from haiv_cli import _find_command

        # Create a test_cmd in hv_project that shadows haiv_core's
        commands_dir = hv_project / "src" / "hv_project" / "commands"
        (commands_dir / "test_cmd.py").write_text('''
from haiv import cmd

def define() -> cmd.Def:
    return cmd.Def(description="Project test command")

def execute(ctx: cmd.Ctx) -> None:
    print("Hello from hv_project!")
''')

        route, hv_root, sources = _find_command("test_cmd")

        assert route is not None
        # Should come from hv_project, not haiv_core
        assert "hv_project" in str(route.file)
        assert hv_root == hv_project

    def test_project_only_command(self, hv_project):
        """Commands only in hv_project are found."""
        from haiv_cli import _find_command

        # Create a command only in hv_project
        commands_dir = hv_project / "src" / "hv_project" / "commands"
        (commands_dir / "project_only.py").write_text('''
from haiv import cmd

def define() -> cmd.Def:
    return cmd.Def(description="Project-only command")

def execute(ctx: cmd.Ctx) -> None:
    print("Only in project!")
''')

        route, hv_root, sources = _find_command("project_only")

        assert route is not None
        assert route.file is not None
        assert route.file.name == "project_only.py"

    def test_fallback_to_core_when_not_in_project(self, hv_project):
        """Falls back to haiv_core when command not in hv_project."""
        from haiv_cli import _find_command

        # hv_project exists but doesn't have test_cmd
        route, hv_root, sources = _find_command("test_cmd")

        assert route is not None
        assert "haiv_core" in str(route.file)

    def test_reports_unchecked_sources(self, tmp_path, monkeypatch):
        """Reports sources that couldn't be checked."""
        from haiv_cli import _find_command

        # Not in a haiv project
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("HV_ROOT", raising=False)

        _reset_cli_cache()

        route, hv_root, sources = _find_command("nonexistent")

        assert route is None
        # hv_project should be unchecked
        project_sources = [s for s in sources if s.name == "hv_project"]
        assert len(project_sources) == 1
        assert project_sources[0].checked is False
        assert project_sources[0].error is not None


class TestUserCommandSources:
    """Tests for user command source resolution."""

    def test_user_command_takes_precedence_over_project(self, hv_project_with_user):
        """hv_user commands override hv_project commands."""
        from haiv_cli import _find_command

        # Create same command in both hv_project and hv_user
        project_commands = hv_project_with_user / "src" / "hv_project" / "commands"
        (project_commands / "shared_cmd.py").write_text('''
from haiv import cmd

def define() -> cmd.Def:
    return cmd.Def(description="Project version")

def execute(ctx: cmd.Ctx) -> None:
    print("Hello from hv_project!")
''')

        user_commands = hv_project_with_user / "users" / "testuser" / "src" / "hv_user" / "commands"
        (user_commands / "shared_cmd.py").write_text('''
from haiv import cmd

def define() -> cmd.Def:
    return cmd.Def(description="User version")

def execute(ctx: cmd.Ctx) -> None:
    print("Hello from hv_user!")
''')

        route, hv_root, sources = _find_command("shared_cmd")

        assert route is not None
        # Should come from hv_user, not hv_project
        assert "hv_user" in str(route.file)

    def test_user_only_command(self, hv_project_with_user):
        """Commands only in hv_user are found."""
        from haiv_cli import _find_command

        user_commands = hv_project_with_user / "users" / "testuser" / "src" / "hv_user" / "commands"
        (user_commands / "user_only.py").write_text('''
from haiv import cmd

def define() -> cmd.Def:
    return cmd.Def(description="User-only command")

def execute(ctx: cmd.Ctx) -> None:
    print("Only in user!")
''')

        route, hv_root, sources = _find_command("user_only")

        assert route is not None
        assert route.file is not None
        assert route.file.name == "user_only.py"

    def test_fallback_to_project_when_not_in_user(self, hv_project_with_user):
        """Falls back to hv_project when command not in hv_user."""
        from haiv_cli import _find_command

        project_commands = hv_project_with_user / "src" / "hv_project" / "commands"
        (project_commands / "project_cmd.py").write_text('''
from haiv import cmd

def define() -> cmd.Def:
    return cmd.Def(description="Project command")

def execute(ctx: cmd.Ctx) -> None:
    print("From project!")
''')

        route, hv_root, sources = _find_command("project_cmd")

        assert route is not None
        assert "hv_project" in str(route.file)

    def test_no_user_reports_unchecked(self, hv_project):
        """Reports hv_user as unchecked when no user identity found."""
        from haiv_cli import _find_command

        # hv_project exists but no user
        route, hv_root, sources = _find_command("test_cmd")

        # hv_user should be unchecked
        user_sources = [s for s in sources if s.name == "hv_user"]
        assert len(user_sources) == 1
        assert user_sources[0].checked is False
        assert user_sources[0].error is not None
        assert "No user identity found" in user_sources[0].error


class TestResolverIntegration:
    """Integration tests for resolver wiring in haiv_cli."""

    def test_implicit_resolver_without_file_returns_raw_value(self, hv_project_with_user):
        """Implicit resolver (_name_/) without resolver file returns raw string."""
        from haiv_cli import _find_command, main
        from haiv._infrastructure.loader import load_command
        from haiv._infrastructure.args import build_ctx
        from haiv._infrastructure.resolvers import make_resolver

        # Create command with implicit param resolver
        commands_dir = hv_project_with_user / "src" / "hv_project" / "commands" / "_name_"
        commands_dir.mkdir(parents=True)
        (commands_dir.parent / "__init__.py").touch()
        (commands_dir / "greet.py").write_text('''
from haiv import cmd

def define() -> cmd.Def:
    return cmd.Def(description="Greet by name")

def execute(ctx: cmd.Ctx) -> None:
    name = ctx.args.get_one("name")
    print(f"Hello, {name}!")
''')

        route, hv_root, sources = _find_command("alice greet")

        assert route is not None
        assert route.params["name"].value == "alice"
        assert route.params["name"].resolver == "name"

        # Build resolve callback - no resolver file exists
        pkg_roots = [hv_project_with_user / "src" / "hv_project"]
        resolve = make_resolver(pkg_roots, None, has_user=True)

        # Implicit resolver should return raw value
        from haiv._infrastructure.args import ResolveRequest
        req = ResolveRequest(param="name", resolver="name", value="alice")
        result = resolve(req)

        assert result == "alice"  # Raw value, no transformation

    def test_explicit_resolver_without_file_raises_error(self, hv_project_with_user):
        """Explicit resolver (_target_as_mind_/) without file raises UnknownResolverError."""
        from haiv_cli import _find_command
        from haiv._infrastructure.resolvers import make_resolver, UnknownResolverError

        # Create command with explicit param resolver
        commands_dir = hv_project_with_user / "src" / "hv_project" / "commands" / "_target_as_mind_"
        commands_dir.mkdir(parents=True)
        (commands_dir.parent / "__init__.py").touch()
        (commands_dir / "send.py").write_text('''
from haiv import cmd

def define() -> cmd.Def:
    return cmd.Def(description="Send to mind")

def execute(ctx: cmd.Ctx) -> None:
    pass
''')

        route, hv_root, sources = _find_command("forge send")

        assert route is not None
        assert route.params["target"].resolver == "mind"

        # Build resolve callback - no resolver file exists
        pkg_roots = [hv_project_with_user / "src" / "hv_project"]
        resolve = make_resolver(pkg_roots, None, has_user=True)

        # Explicit resolver should raise error
        from haiv._infrastructure.args import ResolveRequest
        req = ResolveRequest(param="target", resolver="mind", value="forge")

        with pytest.raises(UnknownResolverError) as exc_info:
            resolve(req)

        assert exc_info.value.resolver_name == "mind"

    def test_resolver_file_is_discovered_and_used(self, hv_project_with_user):
        """Resolver file in resolvers/ is discovered and used."""
        from haiv._infrastructure.resolvers import make_resolver

        # Create resolver file
        resolvers_dir = hv_project_with_user / "src" / "hv_project" / "resolvers"
        resolvers_dir.mkdir(parents=True)
        (resolvers_dir / "mind.py").write_text('''
def resolve(value, ctx):
    return f"Mind({value})"
''')

        pkg_roots = [hv_project_with_user / "src" / "hv_project"]
        resolve = make_resolver(pkg_roots, None, has_user=True)

        from haiv._infrastructure.args import ResolveRequest
        req = ResolveRequest(param="mind", resolver="mind", value="forge")
        result = resolve(req)

        assert result == "Mind(forge)"

    def test_resolver_requires_user_when_found(self, hv_project):
        """Resolver raises UserRequiredError when has_user=False."""
        from haiv._infrastructure.resolvers import make_resolver, UserRequiredError

        # Create resolver file
        resolvers_dir = hv_project / "src" / "hv_project" / "resolvers"
        resolvers_dir.mkdir(parents=True)
        (resolvers_dir / "mind.py").write_text('''
def resolve(value, ctx):
    return f"Mind({value})"
''')

        pkg_roots = [hv_project / "src" / "hv_project"]
        resolve = make_resolver(pkg_roots, None, has_user=False)

        from haiv._infrastructure.args import ResolveRequest
        req = ResolveRequest(param="mind", resolver="mind", value="forge")

        with pytest.raises(UserRequiredError) as exc_info:
            resolve(req)

        assert exc_info.value.resolver_name == "mind"

    def test_user_resolver_overrides_project_resolver(self, hv_project_with_user):
        """User resolvers override project resolvers."""
        from haiv._infrastructure.resolvers import make_resolver

        # Create resolver in project
        project_resolvers = hv_project_with_user / "src" / "hv_project" / "resolvers"
        project_resolvers.mkdir(parents=True)
        (project_resolvers / "mind.py").write_text('''
def resolve(value, ctx):
    return f"ProjectMind({value})"
''')

        # Create resolver in user (should win)
        user_resolvers = hv_project_with_user / "users" / "testuser" / "src" / "hv_user" / "resolvers"
        user_resolvers.mkdir(parents=True)
        (user_resolvers / "mind.py").write_text('''
def resolve(value, ctx):
    return f"UserMind({value})"
''')

        pkg_roots = [
            hv_project_with_user / "src" / "hv_project",
            hv_project_with_user / "users" / "testuser" / "src" / "hv_user",
        ]
        resolve = make_resolver(pkg_roots, None, has_user=True)

        from haiv._infrastructure.args import ResolveRequest
        req = ResolveRequest(param="mind", resolver="mind", value="forge")
        result = resolve(req)

        assert result == "UserMind(forge)"  # User wins
