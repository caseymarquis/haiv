"""Tests for haiv.helpers.commands module."""

import pytest
from pathlib import Path

from haiv import cmd
from haiv.helpers.commands import (
    CommandInfo,
    PackageCommands,
    path_to_command_name,
    commands_for_package,
    discover_commands,
)
from haiv.helpers.packages import PackageInfo, PackageSource
from haiv.paths import PkgPaths


class TestPathToCommandName:
    """Tests for path_to_command_name function."""

    def test_simple_file(self):
        """Simple .py file becomes command name."""
        assert path_to_command_name(Path("init.py")) == "init"

    def test_nested_file(self):
        """Nested file uses directory as prefix."""
        assert path_to_command_name(Path("minds/new.py")) == "minds new"

    def test_deeply_nested(self):
        """Multiple levels of nesting."""
        assert path_to_command_name(Path("a/b/c.py")) == "a b c"

    def test_index_in_directory(self):
        """_index_.py becomes just the directory name."""
        assert path_to_command_name(Path("start/_index_.py")) == "start"

    def test_index_nested(self):
        """Nested _index_.py includes parent directories."""
        assert path_to_command_name(Path("users/new/_index_.py")) == "users new"

    def test_param_file(self):
        """Param file _name_.py becomes <name>."""
        assert path_to_command_name(Path("start/_mind_.py")) == "start <mind>"

    def test_param_directory(self):
        """Param directory _name_/ becomes <name>."""
        assert path_to_command_name(Path("_mind_/status.py")) == "<mind> status"

    def test_param_both(self):
        """Param directory and param file."""
        assert path_to_command_name(Path("_user_/_mind_.py")) == "<user> <mind>"

    def test_param_with_resolver(self):
        """Param with explicit resolver uses param name, not resolver."""
        assert path_to_command_name(Path("_target_as_mind_.py")) == "<target>"

    def test_param_dir_with_resolver(self):
        """Param directory with explicit resolver uses param name."""
        assert path_to_command_name(Path("_target_as_mind_/status.py")) == "<target> status"

    def test_root_index(self):
        """Root _index_.py returns empty string."""
        assert path_to_command_name(Path("_index_.py")) == ""


class TestCommandInfo:
    """Tests for CommandInfo dataclass."""

    def test_name_and_file_accessible(self, tmp_path):
        """name and file are directly accessible without loading."""
        info = CommandInfo(name="test", file=tmp_path / "test.py")
        assert info.name == "test"
        assert info.file == tmp_path / "test.py"

    def test_load_definition_caches(self, tmp_path):
        """load_definition() caches the result."""
        cmd_file = tmp_path / "test.py"
        cmd_file.write_text('''
from haiv import cmd

def define() -> cmd.Def:
    return cmd.Def(description="Test command")

def execute(ctx: cmd.Ctx) -> None:
    pass
''')
        info = CommandInfo(name="test", file=cmd_file)

        # First call loads
        defn1 = info.load_definition()
        assert defn1.description == "Test command"

        # Second call returns cached
        defn2 = info.load_definition()
        assert defn1 is defn2


# Helper functions for tests

def make_command_file(path: Path, description: str) -> None:
    """Create a command file with a define() function."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'''"""Test command."""
from haiv import cmd

def define() -> cmd.Def:
    return cmd.Def(description="{description}")

def execute(ctx: cmd.Ctx) -> None:
    pass
''')


def make_valid_package(pkg_root: Path, source: PackageSource = PackageSource.CORE) -> PackageInfo:
    """Create a valid package structure and return PackageInfo."""
    commands = pkg_root / "commands"
    commands.mkdir(parents=True, exist_ok=True)
    (commands / "__init__.py").write_text("# commands")
    return PackageInfo(
        name=pkg_root.name,
        source=source,
        paths=PkgPaths(root=pkg_root),
    )


class TestCommandsForPackage:
    """Tests for commands_for_package function."""

    def test_empty_package(self, tmp_path):
        """Package with only __init__.py returns empty list."""
        pkg = make_valid_package(tmp_path / "pkg")

        result = commands_for_package(pkg)

        assert result == []

    def test_single_command(self, tmp_path):
        """Package with one command file."""
        pkg = make_valid_package(tmp_path / "pkg")
        make_command_file(pkg.paths.commands_dir / "init.py", "Initialize")

        result = commands_for_package(pkg)

        assert len(result) == 1
        assert result[0].name == "init"
        assert result[0].file == pkg.paths.commands_dir / "init.py"

    def test_multiple_commands_sorted(self, tmp_path):
        """Multiple commands returned sorted by name."""
        pkg = make_valid_package(tmp_path / "pkg")
        make_command_file(pkg.paths.commands_dir / "zzz.py", "Last")
        make_command_file(pkg.paths.commands_dir / "aaa.py", "First")
        make_command_file(pkg.paths.commands_dir / "mmm.py", "Middle")

        result = commands_for_package(pkg)

        assert len(result) == 3
        assert [c.name for c in result] == ["aaa", "mmm", "zzz"]

    def test_nested_command(self, tmp_path):
        """Nested command file has compound name."""
        pkg = make_valid_package(tmp_path / "pkg")
        make_command_file(pkg.paths.commands_dir / "users" / "new.py", "Create user")

        result = commands_for_package(pkg)

        assert len(result) == 1
        assert result[0].name == "users new"

    def test_excludes_init_files(self, tmp_path):
        """__init__.py files at root are excluded."""
        pkg = make_valid_package(tmp_path / "pkg")
        make_command_file(pkg.paths.commands_dir / "real.py", "Real command")
        # __init__.py already exists from make_valid_package

        result = commands_for_package(pkg)

        assert len(result) == 1
        assert result[0].name == "real"

    def test_excludes_dunder_in_subdirectory(self, tmp_path):
        """__init__.py in subdirectory is also excluded (dunder rule)."""
        pkg = make_valid_package(tmp_path / "pkg")
        make_command_file(pkg.paths.commands_dir / "start" / "__init__.py", "Start command")
        make_command_file(pkg.paths.commands_dir / "real.py", "Real command")

        result = commands_for_package(pkg)

        assert len(result) == 1
        assert result[0].name == "real"

    def test_param_command_name(self, tmp_path):
        """Param file names convert to <param>."""
        pkg = make_valid_package(tmp_path / "pkg")
        make_command_file(pkg.paths.commands_dir / "_mind_.py", "Mind command")

        result = commands_for_package(pkg)

        assert len(result) == 1
        assert result[0].name == "<mind>"

    def test_definition_not_loaded_during_discovery(self, tmp_path):
        """Commands are discovered without loading definitions."""
        pkg = make_valid_package(tmp_path / "pkg")
        make_command_file(pkg.paths.commands_dir / "test.py", "Test")

        result = commands_for_package(pkg)

        # _definition should be None (not loaded yet)
        assert result[0]._definition is None


class TestDiscoverCommands:
    """Tests for discover_commands function."""

    def test_returns_package_commands_list(self, tmp_path):
        """Returns list of PackageCommands."""
        make_valid_package(tmp_path / "src" / "hv_project", PackageSource.PROJECT_LOCAL)

        result = discover_commands(tmp_path)

        assert isinstance(result, list)
        assert all(isinstance(pc, PackageCommands) for pc in result)

    def test_includes_core_package(self, tmp_path):
        """Core package is always included."""
        result = discover_commands(tmp_path)

        sources = [pc.package.source for pc in result]
        assert PackageSource.CORE in sources

    def test_includes_project_package(self, tmp_path):
        """Project package included when it exists."""
        make_valid_package(tmp_path / "src" / "hv_project", PackageSource.PROJECT_LOCAL)
        make_command_file(
            tmp_path / "src" / "hv_project" / "commands" / "custom.py",
            "Custom command"
        )

        result = discover_commands(tmp_path)

        sources = [pc.package.source for pc in result]
        assert PackageSource.PROJECT_LOCAL in sources

        project_pkg = next(pc for pc in result if pc.package.source == PackageSource.PROJECT_LOCAL)
        assert len(project_pkg.commands) == 1
        assert project_pkg.commands[0].name == "custom"

    def test_discovery_order(self, tmp_path):
        """Packages returned in discovery order (core first)."""
        make_valid_package(tmp_path / "src" / "hv_project", PackageSource.PROJECT_LOCAL)

        result = discover_commands(tmp_path)

        sources = [pc.package.source for pc in result]
        # Core comes before project
        core_idx = sources.index(PackageSource.CORE)
        project_idx = sources.index(PackageSource.PROJECT_LOCAL)
        assert core_idx < project_idx

    def test_no_deduplication(self, tmp_path):
        """Same command name in multiple packages is not deduplicated."""
        make_valid_package(tmp_path / "src" / "hv_project", PackageSource.PROJECT_LOCAL)
        # Create 'init' command in project (core also has 'init')
        make_command_file(
            tmp_path / "src" / "hv_project" / "commands" / "init.py",
            "Project init"
        )

        result = discover_commands(tmp_path)

        # Both packages should have their own 'init' command
        core_pkg = next(pc for pc in result if pc.package.source == PackageSource.CORE)
        project_pkg = next(pc for pc in result if pc.package.source == PackageSource.PROJECT_LOCAL)

        core_names = [c.name for c in core_pkg.commands]
        project_names = [c.name for c in project_pkg.commands]

        assert "init" in core_names
        assert "init" in project_names

    def test_empty_package_included(self, tmp_path):
        """Package with no commands still appears in results."""
        make_valid_package(tmp_path / "src" / "hv_project", PackageSource.PROJECT_LOCAL)
        # Don't add any commands to project

        result = discover_commands(tmp_path)

        project_pkg = next(pc for pc in result if pc.package.source == PackageSource.PROJECT_LOCAL)
        assert project_pkg.commands == []
