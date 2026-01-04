"""Tests for mg.routing module.

Tests are split into two groups:
1. Core routing logic (find_route_in_paths) - works with path lists
2. Module integration (find_route) - extracts paths from module
"""

import pytest
from pathlib import Path

from mg.routing import (
    find_route_in_paths,
    find_route,
    paths_from_module,
    ParamCapture,
    AmbiguousRouteError,
)


# Note: At the routing layer, flags are raw/unparsed (list[str]).
# Flag parsing (expanding -la, extracting values) happens at parse() layer.


class TestFindRouteInPathsBasic:
    """Basic routing tests."""

    def test_literal_file_match(self):
        """'simple' matches simple.py."""
        paths = [Path("simple.py")]
        result = find_route_in_paths("simple", paths)
        assert result is not None
        assert result.file == Path("simple.py")
        assert result.params == {}
        assert result.rest == []

    def test_nested_literal_match(self):
        """'foo bar' matches foo/bar.py."""
        paths = [Path("foo/bar.py")]
        result = find_route_in_paths("foo bar", paths)
        assert result is not None
        assert result.file == Path("foo/bar.py")

    def test_deeply_nested_literal(self):
        """'a b c d' matches a/b/c/d.py."""
        paths = [Path("a/b/c/d.py")]
        result = find_route_in_paths("a b c d", paths)
        assert result is not None
        assert result.file == Path("a/b/c/d.py")

    def test_no_match_returns_none(self):
        """Nonexistent command returns None."""
        paths = [Path("simple.py")]
        result = find_route_in_paths("nonexistent", paths)
        assert result is None

    def test_partial_match_not_enough(self):
        """'foo' alone doesn't match foo/bar.py."""
        paths = [Path("foo/bar.py")]
        result = find_route_in_paths("foo", paths)
        assert result is None

    def test_too_many_parts_no_match(self):
        """'simple extra' doesn't match simple.py."""
        paths = [Path("simple.py")]
        result = find_route_in_paths("simple extra", paths)
        assert result is None


class TestParamFileCapture:
    """Tests for parameter file capture (_name_.py at leaf level)."""

    def test_basic_param_file(self):
        """'wake wren' matches wake/_mind_.py where _mind_.py captures param."""
        paths = [Path("wake/_mind_.py")]
        result = find_route_in_paths("wake wren", paths)
        assert result is not None
        assert result.file == Path("wake/_mind_.py")
        assert "mind" in result.params
        assert result.params["mind"].value == "wren"
        assert result.params["mind"].resolver == "mind"
        assert result.params["mind"].explicit_resolver is False

    def test_param_file_explicit_resolver(self):
        """'wake specs' with _target_as_mind_.py captures with explicit resolver."""
        paths = [Path("wake/_target_as_mind_.py")]
        result = find_route_in_paths("wake specs", paths)
        assert result is not None
        assert result.file == Path("wake/_target_as_mind_.py")
        assert "target" in result.params
        assert result.params["target"].value == "specs"
        assert result.params["target"].resolver == "mind"
        assert result.params["target"].explicit_resolver is True

    @pytest.mark.parametrize("paths", [
        [Path("wake/status.py"), Path("wake/_mind_.py")],
        [Path("wake/_mind_.py"), Path("wake/status.py")],
    ])
    def test_literal_file_over_param_file(self, paths):
        """Literal file preferred over param file at same level."""
        result = find_route_in_paths("wake status", paths)
        assert result is not None
        assert result.file == Path("wake/status.py")
        assert result.params == {}

    @pytest.mark.parametrize("paths", [
        [Path("wake/_mind_.py"), Path("wake/_mind_/action.py")],
        [Path("wake/_mind_/action.py"), Path("wake/_mind_.py")],
    ])
    def test_param_file_vs_param_dir_single_arg(self, paths):
        """'wake wren' matches param file, not incomplete param dir route."""
        result = find_route_in_paths("wake wren", paths)
        assert result is not None
        assert result.file == Path("wake/_mind_.py")
        assert result.params["mind"].value == "wren"

    @pytest.mark.parametrize("paths", [
        [Path("wake/_mind_.py"), Path("wake/_mind_/action.py")],
        [Path("wake/_mind_/action.py"), Path("wake/_mind_.py")],
    ])
    def test_param_file_vs_param_dir_with_subcommand(self, paths):
        """'wake wren action' matches param dir path, not param file."""
        result = find_route_in_paths("wake wren action", paths)
        assert result is not None
        assert result.file == Path("wake/_mind_/action.py")
        assert result.params["mind"].value == "wren"

    @pytest.mark.parametrize("paths", [
        [Path("wake/_name_.py"), Path("wake/_id_.py")],
        [Path("wake/_id_.py"), Path("wake/_name_.py")],
    ])
    def test_ambiguous_param_files_raises(self, paths):
        """Two param files at same level raises AmbiguousRouteError."""
        with pytest.raises(AmbiguousRouteError):
            find_route_in_paths("wake foo", paths)

    @pytest.mark.parametrize("paths", [
        [Path("wake/_name_.py"), Path("wake/_id_.py"), Path("wake/status.py")],
        [Path("wake/status.py"), Path("wake/_name_.py"), Path("wake/_id_.py")],
    ])
    def test_literal_resolves_param_file_ambiguity(self, paths):
        """Literal file resolves ambiguity between param files."""
        result = find_route_in_paths("wake status", paths)
        assert result is not None
        assert result.file == Path("wake/status.py")
        assert result.params == {}

    def test_param_file_with_flags(self):
        """Param file captures param, flags go to raw_flags."""
        paths = [Path("wake/_mind_.py")]
        result = find_route_in_paths("wake wren --verbose --debug", paths)
        assert result is not None
        assert result.params["mind"].value == "wren"
        assert result.raw_flags == ["--verbose", "--debug"]

    def test_nested_param_file(self):
        """Param file after param directory."""
        paths = [Path("_user_/settings/_option_.py")]
        result = find_route_in_paths("bob settings theme", paths)
        assert result is not None
        assert result.file == Path("_user_/settings/_option_.py")
        assert result.params["user"].value == "bob"
        assert result.params["option"].value == "theme"

    def test_param_file_after_literal_dir(self):
        """Param file after literal directory."""
        paths = [Path("admin/users/_id_.py")]
        result = find_route_in_paths("admin users 123", paths)
        assert result is not None
        assert result.file == Path("admin/users/_id_.py")
        assert result.params["id"].value == "123"

    def test_dunder_file_not_param(self):
        """__init__.py is not treated as a param file."""
        paths = [Path("wake/__init__.py")]
        result = find_route_in_paths("wake foo", paths)
        assert result is None


class TestParamCapture:
    """Tests for parameter directory capture."""

    def test_implicit_resolver(self):
        """_name_/ captures with implicit resolver."""
        paths = [Path("_name_/greet.py")]
        result = find_route_in_paths("alice greet", paths)
        assert result is not None
        assert result.file == Path("_name_/greet.py")
        assert "name" in result.params
        param = result.params["name"]
        assert param.value == "alice"
        assert param.resolver == "name"
        assert param.explicit_resolver is False

    def test_explicit_resolver(self):
        """_target_as_mind_/ captures with explicit resolver."""
        paths = [Path("_target_as_mind_/send.py")]
        result = find_route_in_paths("specs send", paths)
        assert result is not None
        assert "target" in result.params
        param = result.params["target"]
        assert param.value == "specs"
        assert param.resolver == "mind"
        assert param.explicit_resolver is True

    def test_multiple_params_mixed_resolvers(self):
        """Multiple params with mixed implicit/explicit resolvers."""
        paths = [Path("_mind_/message/_target_as_mind_/send.py")]
        result = find_route_in_paths("forge message specs send", paths)
        assert result is not None

        mind_param = result.params["mind"]
        assert mind_param.value == "forge"
        assert mind_param.resolver == "mind"
        assert mind_param.explicit_resolver is False

        target_param = result.params["target"]
        assert target_param.value == "specs"
        assert target_param.resolver == "mind"
        assert target_param.explicit_resolver is True

    def test_param_then_literal(self):
        """Param directory followed by literal directory."""
        paths = [Path("_name_/status/show.py")]
        result = find_route_in_paths("forge status show", paths)
        assert result is not None
        assert result.params["name"].value == "forge"
        assert result.file == Path("_name_/status/show.py")

    def test_literal_then_param(self):
        """Literal directory followed by param directory."""
        paths = [Path("admin/_user_/delete.py")]
        result = find_route_in_paths("admin bob delete", paths)
        assert result is not None
        assert result.params["user"].value == "bob"

    def test_same_resolver_different_params(self):
        """Two params using same resolver (explicit)."""
        paths = [Path("_source_as_mind_/copy/_dest_as_mind_/run.py")]
        result = find_route_in_paths("forge copy specs run", paths)
        assert result is not None
        assert result.params["source"].value == "forge"
        assert result.params["source"].resolver == "mind"
        assert result.params["dest"].value == "specs"
        assert result.params["dest"].resolver == "mind"


class TestRestFileAsLeaf:
    """Tests for _rest_.py as a leaf file and its interactions."""

    def test_rest_only_valid_as_file(self):
        """_rest_ as directory name doesn't capture - only _rest_.py works."""
        # _rest_/foo.py should NOT work - _rest_ is only valid as a file
        paths = [Path("echo/_rest_/foo.py")]
        result = find_route_in_paths("echo hello foo", paths)
        # This should NOT match because _rest_ directories aren't supported
        assert result is None

    @pytest.mark.parametrize("paths", [
        [Path("wake/_rest_.py"), Path("wake/_mind_.py")],
        [Path("wake/_mind_.py"), Path("wake/_rest_.py")],
    ])
    def test_param_file_with_rest_peer_is_ambiguous(self, paths):
        """Param file at same level as _rest_.py is always ambiguous."""
        # _rest_.py captures everything, param file captures specific thing
        # These conflict - should raise even with single arg
        with pytest.raises(AmbiguousRouteError):
            find_route_in_paths("wake foo", paths)

    @pytest.mark.parametrize("paths", [
        [Path("wake/_rest_.py"), Path("wake/_mind_.py")],
        [Path("wake/_mind_.py"), Path("wake/_rest_.py")],
    ])
    def test_param_file_with_rest_peer_ambiguous_multiple_args(self, paths):
        """Param file + rest peer is ambiguous even when only rest could match."""
        # Even though param file can't match 2 args, the file structure is ambiguous
        with pytest.raises(AmbiguousRouteError):
            find_route_in_paths("wake foo bar", paths)

    @pytest.mark.parametrize("paths", [
        [Path("wake/_rest_.py"), Path("wake/_mind_/status.py")],
        [Path("wake/_mind_/status.py"), Path("wake/_rest_.py")],
    ])
    def test_param_dir_with_rest_peer_is_ambiguous(self, paths):
        """Param directory at same level as _rest_.py is always ambiguous."""
        with pytest.raises(AmbiguousRouteError):
            find_route_in_paths("wake foo status", paths)

    @pytest.mark.parametrize("paths", [
        [Path("wake/_rest_.py"), Path("wake/status.py")],
        [Path("wake/status.py"), Path("wake/_rest_.py")],
    ])
    def test_literal_over_rest(self, paths):
        """Literal file beats _rest_.py."""
        result = find_route_in_paths("wake status", paths)
        assert result is not None
        assert result.file == Path("wake/status.py")

    @pytest.mark.parametrize("paths", [
        [Path("wake/_rest_.py"), Path("wake/_mind_.py"), Path("wake/status.py")],
        [Path("wake/status.py"), Path("wake/_rest_.py"), Path("wake/_mind_.py")],
    ])
    def test_literal_resolves_rest_and_param_ambiguity(self, paths):
        """Literal file resolves ambiguity between rest and param file."""
        result = find_route_in_paths("wake status", paths)
        assert result is not None
        assert result.file == Path("wake/status.py")


class TestRestCapture:
    """Tests for _rest_.py capture."""

    def test_rest_captures_remaining(self):
        """'echo hello world' captures rest args."""
        paths = [Path("echo/_rest_.py")]
        result = find_route_in_paths("echo hello world", paths)
        assert result is not None
        assert result.file == Path("echo/_rest_.py")
        assert result.rest == ["hello", "world"]

    def test_rest_with_no_remaining(self):
        """'echo' with _rest_.py works with empty rest."""
        paths = [Path("echo/_rest_.py")]
        result = find_route_in_paths("echo", paths)
        assert result is not None
        assert result.rest == []

    def test_rest_with_many_args(self):
        """Rest captures arbitrary number of args."""
        paths = [Path("echo/_rest_.py")]
        result = find_route_in_paths("echo a b c d e f", paths)
        assert result is not None
        assert result.rest == ["a", "b", "c", "d", "e", "f"]

    def test_rest_after_param(self):
        """Rest after param directory."""
        paths = [Path("_mind_/exec/_rest_.py")]
        result = find_route_in_paths("forge exec ls -la /tmp", paths)
        assert result is not None
        assert result.params["mind"].value == "forge"
        assert result.rest == ["ls", "-la", "/tmp"]

    def test_rest_stops_at_flag(self):
        """_rest_.py: rest gets pre-flag args only."""
        paths = [Path("exec/_rest_.py")]
        result = find_route_in_paths("exec script.py --verbose", paths)
        assert result is not None
        assert result.rest == ["script.py"]
        assert result.raw_flags == ["--verbose"]

    def test_everything_after_flag_is_raw(self):
        """Everything from first flag onward goes to raw_flags."""
        paths = [Path("run/_rest_.py")]
        result = find_route_in_paths("run a --flag1 b --flag2 c", paths)
        assert result is not None
        assert result.rest == ["a"]
        assert result.raw_flags == ["--flag1", "b", "--flag2", "c"]


class TestParamsAndFlags:
    """Tests for combined param capture and flag handling."""

    def test_param_with_flag(self):
        """Param captured, then flag goes to raw_flags."""
        paths = [Path("_mind_/status.py")]
        result = find_route_in_paths("forge status --verbose", paths)
        assert result is not None
        assert result.params["mind"].value == "forge"
        assert result.raw_flags == ["--verbose"]

    def test_multiple_params_with_flags(self):
        """Multiple params and multiple flags."""
        paths = [Path("_source_as_mind_/copy/_dest_as_mind_/run.py")]
        result = find_route_in_paths("forge copy specs run --force --dry-run", paths)
        assert result is not None
        assert result.params["source"].value == "forge"
        assert result.params["dest"].value == "specs"
        assert result.raw_flags == ["--force", "--dry-run"]

    def test_param_rest_and_flags(self):
        """Param, rest args, and flags all captured."""
        paths = [Path("_mind_/exec/_rest_.py")]
        result = find_route_in_paths("forge exec script.py arg1 --verbose", paths)
        assert result is not None
        assert result.params["mind"].value == "forge"
        assert result.rest == ["script.py", "arg1"]
        assert result.raw_flags == ["--verbose"]


class TestFlags:
    """Tests for flag handling at routing layer.

    At routing: flags terminate routing. Everything from first flag → raw_flags.
    No parsing here - that happens in the parse() layer.
    """

    def test_flag_after_complete_route(self):
        """'simple --verbose' matches simple.py, flag goes to raw_flags."""
        paths = [Path("simple.py")]
        result = find_route_in_paths("simple --verbose", paths)
        assert result is not None
        assert result.file == Path("simple.py")
        assert result.raw_flags == ["--verbose"]

    def test_flag_terminates_before_route_complete(self):
        """'forge --verbose status' fails - flag before route complete."""
        paths = [Path("forge/status.py")]
        result = find_route_in_paths("forge --verbose status", paths)
        assert result is None

    def test_flag_only_no_match(self):
        """'--help' alone doesn't match any route."""
        paths = [Path("help.py")]
        result = find_route_in_paths("--help", paths)
        assert result is None

    def test_multiple_flags_raw(self):
        """Multiple flags all go to raw_flags."""
        paths = [Path("run.py")]
        result = find_route_in_paths("run --verbose --debug", paths)
        assert result is not None
        assert result.raw_flags == ["--verbose", "--debug"]

    def test_single_dash_not_a_flag(self):
        """'-v' is NOT a flag - only -- style flags are recognized."""
        paths = [Path("run/_rest_.py")]
        result = find_route_in_paths("run -v file.txt", paths)
        assert result is not None
        # -v is not a flag, goes to rest with file.txt
        assert result.rest == ["-v", "file.txt"]
        assert result.raw_flags == []

    def test_single_dash_passthrough(self):
        """Single-dash args pass through to rest for subprocess use."""
        paths = [Path("exec/_rest_.py")]
        result = find_route_in_paths("exec ls -la /tmp", paths)
        assert result is not None
        assert result.rest == ["ls", "-la", "/tmp"]
        assert result.raw_flags == []

    def test_flag_with_equals_raw(self):
        """'--config=foo.yaml' goes to raw_flags as-is."""
        paths = [Path("run.py")]
        result = find_route_in_paths("run --config=foo.yaml", paths)
        assert result is not None
        assert result.raw_flags == ["--config=foo.yaml"]

    def test_flag_with_following_value_raw(self):
        """'--config foo.yaml' - both go to raw_flags."""
        paths = [Path("run.py")]
        result = find_route_in_paths("run --config foo.yaml", paths)
        assert result is not None
        assert result.raw_flags == ["--config", "foo.yaml"]

    def test_double_dash_in_raw_flags(self):
        """'-- --notaflag' - everything goes to raw_flags."""
        paths = [Path("echo/_rest_.py")]
        result = find_route_in_paths("echo -- --notaflag", paths)
        assert result is not None
        # -- terminates rest capture, goes to raw_flags
        assert result.rest == []
        assert result.raw_flags == ["--", "--notaflag"]

    def test_mixed_flags_and_args_raw(self):
        """'--flag1 b --flag2' - all go to raw_flags."""
        paths = [Path("cmd/_rest_.py")]
        result = find_route_in_paths("cmd a --flag1 b --flag2", paths)
        assert result is not None
        assert result.rest == ["a"]
        assert result.raw_flags == ["--flag1", "b", "--flag2"]


class TestDunderExclusion:
    """Tests for __dunder__ exclusion."""

    def test_dunder_file_excluded(self):
        """__init__.py is not routable."""
        paths = [Path("__init__.py")]
        result = find_route_in_paths("__init__", paths)
        assert result is None

    def test_dunder_directory_excluded(self):
        """__pycache__/ is not routable."""
        paths = [Path("__pycache__/foo.py")]
        result = find_route_in_paths("__pycache__ foo", paths)
        assert result is None

    def test_dunder_mid_path_excluded(self):
        """__private__/ mid-path is not routable."""
        paths = [Path("foo/__private__/bar.py")]
        result = find_route_in_paths("foo __private__ bar", paths)
        assert result is None


class TestPrecedence:
    """Tests for routing precedence rules.

    Each test has order variations to ensure we're not passing by luck.
    """

    @pytest.mark.parametrize("paths", [
        [Path("admin/greet.py"), Path("_name_/greet.py")],
        [Path("_name_/greet.py"), Path("admin/greet.py")],
    ])
    def test_literal_over_param(self, paths):
        """Literal directory preferred over param directory."""
        result = find_route_in_paths("admin greet", paths)
        assert result is not None
        assert result.file == Path("admin/greet.py")
        assert result.params == {}

    @pytest.mark.parametrize("paths", [
        [Path("status.py"), Path("_name_/status.py")],
        [Path("_name_/status.py"), Path("status.py")],
    ])
    def test_literal_file_over_param_dir(self, paths):
        """Literal file preferred over descending into param dir."""
        result = find_route_in_paths("status", paths)
        assert result is not None
        assert result.file == Path("status.py")

    @pytest.mark.parametrize("paths", [
        [Path("echo/test.py"), Path("echo/_rest_.py")],
        [Path("echo/_rest_.py"), Path("echo/test.py")],
    ])
    def test_specific_over_rest(self, paths):
        """Specific file preferred over _rest_.py."""
        result = find_route_in_paths("echo test", paths)
        assert result is not None
        assert result.file == Path("echo/test.py")
        assert result.rest == []

    @pytest.mark.parametrize("paths", [
        [Path("a/b/c.py"), Path("a/_x_/c.py")],
        [Path("a/_x_/c.py"), Path("a/b/c.py")],
    ])
    def test_nested_literal_over_param(self, paths):
        """Nested literal preferred over param at same level."""
        result = find_route_in_paths("a b c", paths)
        assert result is not None
        assert result.file == Path("a/b/c.py")
        assert result.params == {}

    @pytest.mark.parametrize("paths", [
        [Path("a/b/c/d.py"), Path("a/b/_x_/d.py"), Path("a/_y_/c/d.py")],
        [Path("a/_y_/c/d.py"), Path("a/b/c/d.py"), Path("a/b/_x_/d.py")],
        [Path("a/b/_x_/d.py"), Path("a/_y_/c/d.py"), Path("a/b/c/d.py")],
    ])
    def test_deeply_nested_literal_precedence(self, paths):
        """Fully literal path preferred at any nesting depth."""
        result = find_route_in_paths("a b c d", paths)
        assert result is not None
        assert result.file == Path("a/b/c/d.py")
        assert result.params == {}


class TestAmbiguousRoutes:
    """Tests for ambiguous route detection.

    Each test has order variations to ensure detection works regardless of order.
    """

    @pytest.mark.parametrize("paths", [
        [Path("_name_/greet.py"), Path("_id_/greet.py")],
        [Path("_id_/greet.py"), Path("_name_/greet.py")],
    ])
    def test_two_param_dirs_same_leaf_raises(self, paths):
        """Two param dirs with same leaf file raises error."""
        with pytest.raises(AmbiguousRouteError) as exc_info:
            find_route_in_paths("alice greet", paths)
        assert "_name_" in str(exc_info.value) or "_id_" in str(exc_info.value)

    @pytest.mark.parametrize("paths", [
        [Path("cmd/_x_/action.py"), Path("cmd/_y_/action.py")],
        [Path("cmd/_y_/action.py"), Path("cmd/_x_/action.py")],
    ])
    def test_ambiguous_at_deeper_level(self, paths):
        """Ambiguity detected at deeper nesting."""
        with pytest.raises(AmbiguousRouteError):
            find_route_in_paths("cmd foo action", paths)

    @pytest.mark.parametrize("paths", [
        [Path("_name_/greet.py"), Path("_id_/lookup.py")],
        [Path("_id_/lookup.py"), Path("_name_/greet.py")],
    ])
    def test_not_ambiguous_if_different_leaves(self, paths):
        """Different leaf files are not ambiguous."""
        result = find_route_in_paths("alice greet", paths)
        assert result is not None
        assert result.file == Path("_name_/greet.py")

    @pytest.mark.parametrize("paths", [
        [Path("admin/greet.py"), Path("_name_/greet.py"), Path("_id_/greet.py")],
        [Path("_name_/greet.py"), Path("admin/greet.py"), Path("_id_/greet.py")],
        [Path("_id_/greet.py"), Path("_name_/greet.py"), Path("admin/greet.py")],
    ])
    def test_not_ambiguous_if_literal_exists(self, paths):
        """Literal match resolves ambiguity."""
        result = find_route_in_paths("admin greet", paths)
        assert result is not None
        assert result.file == Path("admin/greet.py")

    @pytest.mark.parametrize("paths", [
        [Path("_a_/_b_/cmd.py"), Path("_a_/_c_/cmd.py")],
        [Path("_a_/_c_/cmd.py"), Path("_a_/_b_/cmd.py")],
    ])
    def test_ambiguous_nested_params(self, paths):
        """Nested param directories can be ambiguous."""
        with pytest.raises(AmbiguousRouteError):
            find_route_in_paths("x y cmd", paths)


class TestPathsFromModule:
    """Tests for extracting paths from a module."""

    def test_extracts_py_files(self):
        """Extracts .py files from module's directory."""
        from tests.fixtures.fake_commands import commands

        paths = paths_from_module(commands)
        # Should include simple.py, _name_/greet.py, echo/_rest_.py
        names = [str(p) for p in paths]
        assert any("simple.py" in n for n in names)
        assert any("greet.py" in n for n in names)
        assert any("_rest_.py" in n for n in names)

    def test_paths_are_relative(self):
        """Paths are relative to module directory."""
        from tests.fixtures.fake_commands import commands

        paths = paths_from_module(commands)
        for p in paths:
            assert not p.is_absolute()


class TestFindRoute:
    """Integration tests for module-based routing."""

    def test_routes_through_module(self):
        """find_route works with module input."""
        from tests.fixtures.fake_commands import commands

        result = find_route("simple", commands)
        assert result is not None
        assert result.file.name == "simple.py"

    def test_param_capture_through_module(self):
        """Params captured correctly through module interface."""
        from tests.fixtures.fake_commands import commands

        result = find_route("alice greet", commands)
        assert result is not None
        assert "name" in result.params
        assert result.params["name"].value == "alice"
        assert result.params["name"].resolver == "name"
        assert result.params["name"].explicit_resolver is False

    def test_rest_capture_through_module(self):
        """Rest captured correctly through module interface."""
        from tests.fixtures.fake_commands import commands

        result = find_route("echo hello world", commands)
        assert result is not None
        assert result.file.name == "_rest_.py"
        assert result.rest == ["hello", "world"]
