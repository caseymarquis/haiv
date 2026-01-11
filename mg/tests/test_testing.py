"""Tests for the testing infrastructure itself."""

import pytest

from mg import cmd, test
from mg._infrastructure.routing import ParamCapture
from mg.test import CommandsNotFoundError
from tests.fixtures.fake_commands import commands as fake_commands


class TestCommandsAutoDiscovery:
    """Tests for auto-discovering the commands module."""

    def test_raises_when_no_commands_module(self):
        """Raises CommandsNotFoundError when package has no commands/."""
        # mg package doesn't have src/mg/commands/, so discovery should fail
        with pytest.raises(CommandsNotFoundError):
            test.routes_to("anything")

    def test_explicit_commands_still_works(self):
        """Explicit commands argument bypasses discovery."""
        match = test.routes_to("simple", fake_commands)
        assert match.file.name == "simple.py"


class TestRoutesTo:
    """Tests for routes_to() - routing only."""

    def test_simple_command_routes(self):
        """'simple' routes to simple.py."""
        match = test.routes_to("simple", fake_commands)
        assert match.file.name == "simple.py"

    def test_param_directory_routes(self):
        """'alice greet' routes through _name_/ directory."""
        match = test.routes_to("alice greet", fake_commands)
        assert match.file.name == "greet.py"
        assert "name" in match.params
        assert match.params["name"].value == "alice"
        assert match.params["name"].resolver == "name"
        assert match.params["name"].explicit_resolver is False

    def test_rest_captures_remaining(self):
        """'echo hello world' captures rest params."""
        match = test.routes_to("echo hello world", fake_commands)
        assert match.file.name == "_rest_.py"
        assert match.rest == ["hello", "world"]

    def test_expected_path_assertion(self):
        """Can assert on expected path."""
        match = test.routes_to("simple", fake_commands, expected="simple.py")
        assert match.file.name == "simple.py"

    def test_nonexistent_raises(self):
        """Nonexistent route raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            test.routes_to("nonexistent", fake_commands)

    def test_exists_false_for_negative_test(self):
        """exists=False asserts route does NOT exist."""
        match = test.routes_to("nonexistent", fake_commands, exists=False)
        assert match.file is None


class TestParse:
    """Tests for parse() - routing + arg parsing."""

    def test_simple_command_parses(self):
        """'simple' parses successfully."""
        ctx = test.parse("simple", fake_commands)
        assert ctx.args is not None

    def test_param_captured_in_args(self):
        """'alice greet' captures name param in args."""
        ctx = test.parse("alice greet", fake_commands)
        assert ctx.args.get_one("name") == "alice"

    def test_resolver_callback_invoked(self):
        """Resolver callback is invoked with ResolveRequest."""
        called_with = []

        def track_resolve(req: test.ResolveRequest):
            called_with.append(req)
            return f"resolved_{req.value}"

        ctx = test.parse("alice greet", fake_commands, resolve=track_resolve)

        assert len(called_with) == 1
        assert called_with[0].param == "name"
        assert called_with[0].resolver == "name"
        assert called_with[0].value == "alice"
        assert ctx.args.get_one("name") == "resolved_alice"

    def test_rest_in_args(self):
        """'echo hello world' has rest in args."""
        ctx = test.parse("echo hello world", fake_commands)
        assert ctx.args.rest == ["hello", "world"]


class TestExecute:
    """Tests for execute() - unit testing commands."""

    def test_execute_simple(self, capsys):
        """Execute simple command, capture output with capsys."""
        test.execute("simple", fake_commands)
        captured = capsys.readouterr()
        assert captured.out == "simple executed\n"

    def test_execute_with_param(self, capsys):
        """Execute command with param."""
        test.execute("alice greet", fake_commands)
        captured = capsys.readouterr()
        assert captured.out == "hello alice\n"

    def test_execute_with_rest(self, capsys):
        """Execute command with rest args."""
        test.execute("echo hello world", fake_commands)
        captured = capsys.readouterr()
        assert captured.out == "hello world\n"

    def test_execute_with_container(self):
        """Execute with custom container for DI mocks."""
        from punq import Container

        container = Container()
        result = test.execute("simple", fake_commands, container=container)
        assert result.ctx.container is container

    def test_execute_returns_ctx(self):
        """Execute returns result with ctx for inspection."""
        result = test.execute("simple", fake_commands)
        assert result.ctx is not None
        assert isinstance(result.ctx.args, cmd.Args)
