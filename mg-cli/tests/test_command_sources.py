"""Integration tests for multi-source command loading."""

import os
import sys
from pathlib import Path

import pytest


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

    # Set MG_ROOT and change to project dir
    monkeypatch.setenv("MG_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    # Reset the cached mg_root lookup
    import mg_cli
    mg_cli._mg_root = None
    mg_cli._mg_root_error = None

    return tmp_path


class TestCommandSources:
    """Tests for command source resolution."""

    def test_core_command_works(self, monkeypatch):
        """Commands from mg_core are found."""
        from mg_cli import _find_command

        # Reset cache
        import mg_cli
        mg_cli._mg_root = None
        mg_cli._mg_root_error = None

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

        # Reset cache
        import mg_cli
        mg_cli._mg_root = None
        mg_cli._mg_root_error = None

        route, mg_root, sources = _find_command("nonexistent")

        assert route is None
        # mg_project should be unchecked
        project_sources = [s for s in sources if s.name == "mg_project"]
        assert len(project_sources) == 1
        assert project_sources[0].checked is False
        assert project_sources[0].error is not None
