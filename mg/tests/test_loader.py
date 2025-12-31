"""Tests for mg.loader module."""

import pytest
from pathlib import Path

from mg.loader import load_command, Command
from mg import cmd
from mg.paths import Paths


def make_paths() -> Paths:
    """Create a minimal Paths for testing."""
    return Paths(
        _called_from=Path("/test/cwd"),
        _pkg_root=Path("/test/pkg"),
        _mg_root=None,
    )


class TestLoadCommand:
    """Tests for load_command() returning a Command wrapper."""

    def test_returns_command_instance(self):
        """Returns a Command wrapper, not raw module."""
        from tests.fixtures.fake_commands import commands

        commands_dir = Path(commands.__file__).parent
        command = load_command(commands_dir / "simple.py")

        assert isinstance(command, Command)

    def test_define_returns_def(self):
        """Command.define() returns cmd.Def."""
        from tests.fixtures.fake_commands import commands

        commands_dir = Path(commands.__file__).parent
        command = load_command(commands_dir / "simple.py")

        result = command.define()
        assert isinstance(result, cmd.Def)
        assert result.description == "A simple command"

    def test_execute_is_callable(self):
        """Command.execute() is callable."""
        from tests.fixtures.fake_commands import commands

        commands_dir = Path(commands.__file__).parent
        command = load_command(commands_dir / "simple.py")

        assert callable(command.execute)

    def test_loads_nested_module(self):
        """Loads command from nested path."""
        from tests.fixtures.fake_commands import commands

        commands_dir = Path(commands.__file__).parent
        command = load_command(commands_dir / "_name_" / "greet.py")

        result = command.define()
        assert "greet" in result.description.lower()

    def test_nonexistent_file_raises(self):
        """Raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_command(Path("/nonexistent/path/cmd.py"))

    def test_invalid_python_raises(self, tmp_path):
        """Raises SyntaxError for invalid Python."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("this is not valid python {{{{")

        with pytest.raises(SyntaxError):
            load_command(bad_file)

    def test_each_load_is_fresh(self, tmp_path):
        """Each load gets a fresh module (not cached)."""
        cmd_file = tmp_path / "counter.py"
        cmd_file.write_text("""
from mg import cmd
count = 0
def define():
    return cmd.Def(description="Counter")
def execute(ctx):
    pass
""")
        cmd1 = load_command(cmd_file)
        cmd1._module.count = 42

        cmd2 = load_command(cmd_file)
        assert cmd2._module.count == 0  # Fresh load


class TestCommandLifecycle:
    """Tests for Command lifecycle methods."""

    def test_setup_called_when_present(self, tmp_path):
        """Command.setup() delegates to module's setup()."""
        cmd_file = tmp_path / "with_setup.py"
        cmd_file.write_text("""
from mg import cmd

setup_called = False

def define():
    return cmd.Def(description="Has setup")

def setup(ctx):
    global setup_called
    setup_called = True

def execute(ctx):
    pass
""")
        command = load_command(cmd_file)
        ctx = cmd.Ctx(args=cmd.Args(), paths=make_paths())

        command.setup(ctx)
        assert command._module.setup_called is True

    def test_setup_noop_when_absent(self, tmp_path):
        """Command.setup() is no-op when module lacks setup()."""
        cmd_file = tmp_path / "no_setup.py"
        cmd_file.write_text("""
from mg import cmd

def define():
    return cmd.Def(description="No setup")

def execute(ctx):
    pass
""")
        command = load_command(cmd_file)
        ctx = cmd.Ctx(args=cmd.Args(), paths=make_paths())

        # Should not raise
        command.setup(ctx)

    def test_teardown_called_when_present(self, tmp_path):
        """Command.teardown() delegates to module's teardown()."""
        cmd_file = tmp_path / "with_teardown.py"
        cmd_file.write_text("""
from mg import cmd

teardown_called = False

def define():
    return cmd.Def(description="Has teardown")

def execute(ctx):
    pass

def teardown(ctx):
    global teardown_called
    teardown_called = True
""")
        command = load_command(cmd_file)
        ctx = cmd.Ctx(args=cmd.Args(), paths=make_paths())

        command.teardown(ctx)
        assert command._module.teardown_called is True

    def test_teardown_noop_when_absent(self, tmp_path):
        """Command.teardown() is no-op when module lacks teardown()."""
        cmd_file = tmp_path / "no_teardown.py"
        cmd_file.write_text("""
from mg import cmd

def define():
    return cmd.Def(description="No teardown")

def execute(ctx):
    pass
""")
        command = load_command(cmd_file)
        ctx = cmd.Ctx(args=cmd.Args(), paths=make_paths())

        # Should not raise
        command.teardown(ctx)

    def test_full_lifecycle(self, tmp_path):
        """All lifecycle methods work together."""
        cmd_file = tmp_path / "full.py"
        cmd_file.write_text("""
from mg import cmd

calls = []

def define():
    return cmd.Def(description="Full lifecycle")

def setup(ctx):
    calls.append("setup")

def execute(ctx):
    calls.append("execute")

def teardown(ctx):
    calls.append("teardown")
""")
        command = load_command(cmd_file)
        ctx = cmd.Ctx(args=cmd.Args(), paths=make_paths())

        command.setup(ctx)
        command.execute(ctx)
        command.teardown(ctx)

        assert command._module.calls == ["setup", "execute", "teardown"]


class TestCommandValidation:
    """Tests for command validation."""

    def test_missing_define_raises(self, tmp_path):
        """Command without define() raises on define() call."""
        cmd_file = tmp_path / "no_define.py"
        cmd_file.write_text("""
def execute(ctx):
    pass
""")
        command = load_command(cmd_file)

        with pytest.raises(AttributeError):
            command.define()

    def test_missing_execute_raises(self, tmp_path):
        """Command without execute() raises on execute() call."""
        cmd_file = tmp_path / "no_execute.py"
        cmd_file.write_text("""
from mg import cmd

def define():
    return cmd.Def(description="No execute")
""")
        command = load_command(cmd_file)
        ctx = cmd.Ctx(args=cmd.Args(), paths=make_paths())

        with pytest.raises(AttributeError):
            command.execute(ctx)
