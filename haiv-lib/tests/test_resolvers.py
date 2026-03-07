"""Tests for haiv.resolvers module."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from haiv._infrastructure.resolvers import (
    discover_resolvers,
    load_resolver,
    make_resolver,
    ResolverContext,
    ResolverError,
    UnknownResolverError,
    UserRequiredError,
)
from haiv._infrastructure.args import ResolveRequest


class TestDiscoverResolvers:
    """Tests for discover_resolvers()."""

    def test_finds_resolver_files(self, tmp_path):
        """Discovers .py files in resolvers/ directory."""
        resolvers_dir = tmp_path / "resolvers"
        resolvers_dir.mkdir()
        (resolvers_dir / "mind.py").write_text("def resolve(v, ctx): pass")
        (resolvers_dir / "message.py").write_text("def resolve(v, ctx): pass")

        result = discover_resolvers(tmp_path)

        assert "mind" in result
        assert "message" in result
        assert result["mind"] == resolvers_dir / "mind.py"
        assert result["message"] == resolvers_dir / "message.py"

    def test_ignores_underscore_files(self, tmp_path):
        """Files starting with underscore are ignored."""
        resolvers_dir = tmp_path / "resolvers"
        resolvers_dir.mkdir()
        (resolvers_dir / "mind.py").write_text("def resolve(v, ctx): pass")
        (resolvers_dir / "_helpers.py").write_text("# helper module")
        (resolvers_dir / "__init__.py").write_text("")

        result = discover_resolvers(tmp_path)

        assert "mind" in result
        assert "_helpers" not in result
        assert "__init__" not in result

    def test_empty_when_no_resolvers_dir(self, tmp_path):
        """Returns empty dict when resolvers/ doesn't exist."""
        result = discover_resolvers(tmp_path)

        assert result == {}

    def test_empty_when_resolvers_dir_empty(self, tmp_path):
        """Returns empty dict when resolvers/ is empty."""
        resolvers_dir = tmp_path / "resolvers"
        resolvers_dir.mkdir()

        result = discover_resolvers(tmp_path)

        assert result == {}

    def test_ignores_non_py_files(self, tmp_path):
        """Only .py files are discovered."""
        resolvers_dir = tmp_path / "resolvers"
        resolvers_dir.mkdir()
        (resolvers_dir / "mind.py").write_text("def resolve(v, ctx): pass")
        (resolvers_dir / "README.md").write_text("# Resolvers")
        (resolvers_dir / "config.json").write_text("{}")

        result = discover_resolvers(tmp_path)

        assert list(result.keys()) == ["mind"]

    def test_ignores_subdirectories(self, tmp_path):
        """Subdirectories are not discovered as resolvers."""
        resolvers_dir = tmp_path / "resolvers"
        resolvers_dir.mkdir()
        (resolvers_dir / "mind.py").write_text("def resolve(v, ctx): pass")
        subdir = resolvers_dir / "helpers"
        subdir.mkdir()
        (subdir / "utils.py").write_text("# utils")

        result = discover_resolvers(tmp_path)

        assert list(result.keys()) == ["mind"]


class TestLoadResolver:
    """Tests for load_resolver()."""

    def test_returns_module_with_resolve(self, tmp_path):
        """Loaded module has a resolve() function."""
        resolver_file = tmp_path / "mind.py"
        resolver_file.write_text("""
def resolve(value, ctx):
    return f"resolved_{value}"
""")

        module = load_resolver(resolver_file)

        assert module is not None
        assert hasattr(module, "resolve")
        assert callable(module.resolve)

    def test_resolve_function_works(self, tmp_path):
        """The loaded resolve() function can be called."""
        resolver_file = tmp_path / "mind.py"
        resolver_file.write_text("""
def resolve(value, ctx):
    return f"resolved_{value}"
""")

        module = load_resolver(resolver_file)
        assert module is not None
        result = module.resolve("forge", None)

        assert result == "resolved_forge"

    def test_returns_none_if_no_resolve_function(self, tmp_path, capsys):
        """Returns None if module lacks resolve()."""
        resolver_file = tmp_path / "broken.py"
        resolver_file.write_text("""
def something_else():
    pass
""")

        result = load_resolver(resolver_file)

        assert result is None
        captured = capsys.readouterr()
        assert "missing resolve()" in captured.out

    def test_returns_none_on_syntax_error(self, tmp_path, capsys):
        """Returns None for invalid Python."""
        resolver_file = tmp_path / "bad.py"
        resolver_file.write_text("this is not valid python {{{{")

        result = load_resolver(resolver_file)

        assert result is None
        captured = capsys.readouterr()
        assert "Error loading resolver" in captured.out

    def test_quiet_suppresses_warnings(self, tmp_path, capsys):
        """quiet=True suppresses warning messages."""
        resolver_file = tmp_path / "broken.py"
        resolver_file.write_text("def something(): pass")

        result = load_resolver(resolver_file, quiet=True)

        assert result is None
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_each_load_is_fresh(self, tmp_path):
        """Each load gets a fresh module (not cached)."""
        resolver_file = tmp_path / "counter.py"
        resolver_file.write_text("""
count = 0
def resolve(value, ctx):
    return count
""")

        mod1 = load_resolver(resolver_file)
        assert mod1 is not None
        setattr(mod1, "count", 42)

        mod2 = load_resolver(resolver_file)
        assert mod2 is not None
        assert getattr(mod2, "count") == 0  # Fresh load


class TestMakeResolver:
    """Tests for make_resolver()."""

    def test_creates_working_callback(self, tmp_path):
        """Returns a callable that resolves values."""
        # Create a resolver
        resolvers_dir = tmp_path / "resolvers"
        resolvers_dir.mkdir()
        (resolvers_dir / "mind.py").write_text("""
def resolve(value, ctx):
    return f"Mind({value})"
""")

        paths = Mock()

        resolve = make_resolver([tmp_path], paths, has_user=True)
        req = ResolveRequest(param="mind", resolver="mind", value="forge")
        result = resolve(req)

        assert result == "Mind(forge)"

    def test_later_packages_override_earlier(self, tmp_path):
        """Later pkg_roots override earlier resolvers."""
        # First package
        pkg1 = tmp_path / "pkg1"
        pkg1.mkdir()
        (pkg1 / "resolvers").mkdir()
        (pkg1 / "resolvers" / "mind.py").write_text("""
def resolve(value, ctx):
    return f"pkg1_{value}"
""")

        # Second package (should win)
        pkg2 = tmp_path / "pkg2"
        pkg2.mkdir()
        (pkg2 / "resolvers").mkdir()
        (pkg2 / "resolvers" / "mind.py").write_text("""
def resolve(value, ctx):
    return f"pkg2_{value}"
""")

        paths = Mock()

        resolve = make_resolver([pkg1, pkg2], paths, has_user=True)
        req = ResolveRequest(param="mind", resolver="mind", value="forge")
        result = resolve(req)

        assert result == "pkg2_forge"

    def test_implicit_resolver_not_found_returns_raw_value(self, tmp_path):
        """Implicit resolver (param==resolver) returns raw value if not found."""
        # No resolvers directory - nothing available
        paths = Mock()

        resolve = make_resolver([tmp_path], paths, has_user=True)
        # param == resolver means implicit (from _name_/ syntax)
        req = ResolveRequest(param="name", resolver="name", value="alice")
        result = resolve(req)

        assert result == "alice"  # Raw value returned

    def test_explicit_resolver_not_found_raises_error(self, tmp_path):
        """Explicit resolver (param!=resolver) raises if not found."""
        # Create one resolver (not the one we're looking for)
        resolvers_dir = tmp_path / "resolvers"
        resolvers_dir.mkdir()
        (resolvers_dir / "mind.py").write_text("def resolve(v, ctx): return v")

        paths = Mock()

        resolve = make_resolver([tmp_path], paths, has_user=True)
        # param != resolver means explicit (from _target_as_message_/ syntax)
        req = ResolveRequest(param="target", resolver="message", value="123")

        with pytest.raises(UnknownResolverError) as exc_info:
            resolve(req)

        assert exc_info.value.resolver_name == "message"
        assert "mind" in exc_info.value.available

    def test_unknown_resolver_shows_available(self, tmp_path):
        """Error message lists available resolvers."""
        resolvers_dir = tmp_path / "resolvers"
        resolvers_dir.mkdir()
        (resolvers_dir / "mind.py").write_text("def resolve(v, ctx): pass")
        (resolvers_dir / "message.py").write_text("def resolve(v, ctx): pass")

        paths = Mock()

        resolve = make_resolver([tmp_path], paths, has_user=True)
        # Explicit resolver request (param != resolver)
        req = ResolveRequest(param="x", resolver="unknown", value="y")

        with pytest.raises(UnknownResolverError) as exc_info:
            resolve(req)

        error_msg = str(exc_info.value)
        assert "mind" in error_msg
        assert "message" in error_msg

    def test_resolver_without_user_raises_error(self, tmp_path):
        """Raises UserRequiredError when has_user=False and resolver found."""
        resolvers_dir = tmp_path / "resolvers"
        resolvers_dir.mkdir()
        (resolvers_dir / "mind.py").write_text("""
def resolve(value, ctx):
    return value
""")

        paths = Mock()

        resolve = make_resolver([tmp_path], paths, has_user=False)
        req = ResolveRequest(param="mind", resolver="mind", value="forge")

        with pytest.raises(UserRequiredError) as exc_info:
            resolve(req)

        assert exc_info.value.resolver_name == "mind"
        assert "user context" in str(exc_info.value).lower()

    def test_implicit_no_resolver_no_user_returns_raw(self, tmp_path):
        """Implicit resolver not found + no user = returns raw value (no error)."""
        # No resolvers
        paths = Mock()

        resolve = make_resolver([tmp_path], paths, has_user=False)
        # Implicit: param == resolver
        req = ResolveRequest(param="name", resolver="name", value="alice")
        result = resolve(req)

        assert result == "alice"  # No error, just raw value

    def test_resolver_receives_context(self, tmp_path):
        """Resolver function receives ResolverContext."""
        resolvers_dir = tmp_path / "resolvers"
        resolvers_dir.mkdir()
        (resolvers_dir / "mind.py").write_text("""
def resolve(value, ctx):
    # Access ctx to verify it's passed
    return f"{value}_from_{ctx.paths.user.name}"
""")

        paths = Mock()
        paths.user.name = "casey"

        resolve = make_resolver([tmp_path], paths, has_user=True)
        req = ResolveRequest(param="mind", resolver="mind", value="forge")
        result = resolve(req)

        assert result == "forge_from_casey"

    def test_empty_pkg_roots_implicit_returns_raw(self, tmp_path):
        """Empty pkg_roots with implicit resolver returns raw value."""
        paths = Mock()

        resolve = make_resolver([], paths, has_user=True)
        # Implicit: param == resolver
        req = ResolveRequest(param="name", resolver="name", value="alice")
        result = resolve(req)

        assert result == "alice"

    def test_empty_pkg_roots_explicit_raises(self, tmp_path):
        """Empty pkg_roots with explicit resolver raises error."""
        paths = Mock()

        resolve = make_resolver([], paths, has_user=True)
        # Explicit: param != resolver
        req = ResolveRequest(param="target", resolver="mind", value="forge")

        with pytest.raises(UnknownResolverError) as exc_info:
            resolve(req)

        assert exc_info.value.available == []

    def test_has_user_defaults_to_false(self, tmp_path):
        """has_user defaults to False, so resolvers error by default."""
        resolvers_dir = tmp_path / "resolvers"
        resolvers_dir.mkdir()
        (resolvers_dir / "mind.py").write_text("def resolve(v, ctx): pass")

        paths = Mock()

        # Don't pass has_user - should default to False
        resolve = make_resolver([tmp_path], paths)
        req = ResolveRequest(param="mind", resolver="mind", value="forge")

        with pytest.raises(UserRequiredError):
            resolve(req)


class TestResolverContext:
    """Tests for ResolverContext dataclass."""

    def test_has_paths_attribute(self):
        """ResolverContext has paths attribute."""
        paths = Mock()
        ctx = ResolverContext(paths=paths)

        assert ctx.paths is paths

    def test_container_defaults_to_none(self):
        """Container defaults to None."""
        paths = Mock()
        ctx = ResolverContext(paths=paths)

        assert ctx.container is None

    def test_container_can_be_set(self):
        """Container can be provided."""
        paths = Mock()
        container = Mock()
        ctx = ResolverContext(paths=paths, container=container)

        assert ctx.container is container
