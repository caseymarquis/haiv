"""Tests for mg.args module."""

import pytest
from unittest.mock import Mock

from mg import cmd
from mg.args import build_ctx
from mg.routing import RouteMatch, ParamCapture
from mg.loader import Command


def make_command(flags: list[cmd.Flag] | None = None) -> Command:
    """Create a mock Command with given flag definitions."""
    module = Mock()
    module.define.return_value = cmd.Def(
        description="Test command",
        flags=flags or [],
    )
    return Command(module)


class TestBuildCtxBasic:
    """Basic build_ctx tests."""

    def test_returns_ctx(self):
        """Returns a Ctx instance."""
        route = RouteMatch(file=Mock())
        command = make_command()

        ctx = build_ctx(route, command)

        assert isinstance(ctx, cmd.Ctx)
        assert isinstance(ctx.args, cmd.Args)

    def test_rest_populated(self):
        """Rest args are populated from route."""
        route = RouteMatch(file=Mock(), rest=["a", "b", "c"])
        command = make_command()

        ctx = build_ctx(route, command)

        assert ctx.args.rest == ["a", "b", "c"]

    def test_called_from_set_to_cwd(self):
        """called_from is set to current working directory."""
        import os
        from pathlib import Path

        route = RouteMatch(file=Mock())
        command = make_command()

        ctx = build_ctx(route, command)

        assert ctx.called_from == Path(os.getcwd())


class TestBuildCtxParams:
    """Tests for parameter resolution."""

    def test_param_added_to_values(self):
        """Route params are added to args values."""
        route = RouteMatch(
            file=Mock(),
            params={"name": ParamCapture(value="alice", resolver="name", explicit_resolver=False)},
        )
        command = make_command()

        ctx = build_ctx(route, command)

        assert ctx.args.get_one("name") == "alice"

    def test_param_resolved_when_resolver_provided(self):
        """Params are resolved via resolve callback."""
        route = RouteMatch(
            file=Mock(),
            params={"mind": ParamCapture(value="forge", resolver="mind", explicit_resolver=False)},
        )
        command = make_command()

        resolved_mind = Mock(name="ResolvedMind")

        def resolve(req):
            assert req.param == "mind"
            assert req.resolver == "mind"
            assert req.value == "forge"
            return resolved_mind

        ctx = build_ctx(route, command, resolve=resolve)

        assert ctx.args.get_one("mind") is resolved_mind

    def test_multiple_params_resolved(self):
        """Multiple params are all resolved."""
        route = RouteMatch(
            file=Mock(),
            params={
                "mind": ParamCapture(value="forge", resolver="mind", explicit_resolver=False),
                "target": ParamCapture(value="specs", resolver="mind", explicit_resolver=True),
            },
        )
        command = make_command()

        calls = []

        def resolve(req):
            calls.append((req.param, req.resolver, req.value))
            return f"resolved_{req.value}"

        ctx = build_ctx(route, command, resolve=resolve)

        assert len(calls) == 2
        assert ("mind", "mind", "forge") in calls
        assert ("target", "mind", "specs") in calls
        assert ctx.args.get_one("mind") == "resolved_forge"
        assert ctx.args.get_one("target") == "resolved_specs"


class TestBuildCtxBooleanFlags:
    """Tests for boolean flag parsing."""

    def test_boolean_flag_present(self):
        """Boolean flag present sets True."""
        route = RouteMatch(file=Mock(), raw_flags=["--verbose"])
        command = make_command(flags=[cmd.Flag("verbose", type=bool)])

        ctx = build_ctx(route, command)

        assert ctx.args.has("verbose")
        assert ctx.args.get_one("verbose") is True

    def test_boolean_flag_absent(self):
        """Boolean flag absent means not in args."""
        route = RouteMatch(file=Mock(), raw_flags=[])
        command = make_command(flags=[cmd.Flag("verbose", type=bool)])

        ctx = build_ctx(route, command)

        assert not ctx.args.has("verbose")


class TestBuildCtxValueFlags:
    """Tests for flags that take values."""

    def test_single_value_flag(self):
        """Flag with single value."""
        route = RouteMatch(file=Mock(), raw_flags=["--file", "path.txt"])
        command = make_command(flags=[cmd.Flag("file")])

        ctx = build_ctx(route, command)

        assert ctx.args.get_one("file") == "path.txt"

    def test_flag_with_equals_syntax(self):
        """Flag with --flag=value syntax."""
        route = RouteMatch(file=Mock(), raw_flags=["--file=path.txt"])
        command = make_command(flags=[cmd.Flag("file")])

        ctx = build_ctx(route, command)

        assert ctx.args.get_one("file") == "path.txt"

    def test_multi_value_flag(self):
        """Flag accepting multiple values."""
        route = RouteMatch(file=Mock(), raw_flags=["--include", "a", "b", "c"])
        command = make_command(flags=[cmd.Flag("include", max_args=None)])

        ctx = build_ctx(route, command)

        assert ctx.args.get_list("include") == ["a", "b", "c"]

    def test_multi_value_stops_at_next_flag(self):
        """Multi-value flag stops consuming at next flag."""
        route = RouteMatch(
            file=Mock(), raw_flags=["--include", "a", "b", "--verbose"]
        )
        command = make_command(
            flags=[
                cmd.Flag("include", max_args=None),
                cmd.Flag("verbose", type=bool),
            ]
        )

        ctx = build_ctx(route, command)

        assert ctx.args.get_list("include") == ["a", "b"]
        assert ctx.args.get_one("verbose") is True

    def test_flag_with_resolver(self):
        """Flag values are resolved when resolver specified."""
        route = RouteMatch(file=Mock(), raw_flags=["--reply-to", "msg-123"])
        command = make_command(flags=[cmd.Flag("reply-to", resolver="message")])

        resolved_msg = Mock(name="Message")

        def resolve(req):
            assert req.param == "reply-to"
            assert req.resolver == "message"
            assert req.value == "msg-123"
            return resolved_msg

        ctx = build_ctx(route, command, resolve=resolve)

        assert ctx.args.get_one("reply-to") is resolved_msg


class TestBuildCtxFlagErrors:
    """Tests for flag parsing errors."""

    def test_unknown_flag_raises(self):
        """Unknown flag raises error."""
        route = RouteMatch(file=Mock(), raw_flags=["--unknown"])
        command = make_command(flags=[])

        with pytest.raises(ValueError, match="Unknown flag.*unknown"):
            build_ctx(route, command)

    def test_missing_required_value_raises(self):
        """Flag missing required value raises error."""
        route = RouteMatch(file=Mock(), raw_flags=["--file"])
        command = make_command(flags=[cmd.Flag("file")])  # min_args=1 by default

        with pytest.raises(ValueError, match="requires.*value"):
            build_ctx(route, command)

    def test_too_many_values_raises(self):
        """Flag with too many values raises error."""
        route = RouteMatch(file=Mock(), raw_flags=["--file", "a", "b"])
        command = make_command(flags=[cmd.Flag("file")])  # max_args=1 by default

        with pytest.raises(ValueError, match="too many values"):
            build_ctx(route, command)
