"""Tests for haiv hook system.

Tests the haiv hook infrastructure (discovery, loading, collection, registration)
and the public API (HvHookPoint, @hv_hook decorator). Mirrors the structure
of test_resolvers.py.

This tests the haiv hook system specifically -- distinct from Claude hooks.
"""

import pytest
from pathlib import Path
from typing import cast
from types import ModuleType
from unittest.mock import Mock

from haiv._infrastructure.hv_hooks import (
    HvHookRegistry,
    collect_hv_handlers,
    configure_hv_hooks,
    discover_hv_hooks,
    load_hv_hook_module,
)
from haiv.hv_hooks import HvHookHandler, HvHookPoint, hv_hook


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stamp_handler(fn, *, source="/tmp/hv_hook_handlers/test.py", description="test handler") -> HvHookHandler:
    """Stamp required haiv hook attributes on a plain function for registry tests."""
    fn._hv_hook_description = description
    fn._hv_hook_source = source
    return cast(HvHookHandler, fn)


def _mock_ctx(root=Path("/tmp")):
    """Create a mock ctx with paths.root set."""
    ctx = Mock()
    ctx.paths.root = root
    return ctx


# ---------------------------------------------------------------------------
# discover_hv_hooks
# ---------------------------------------------------------------------------


class TestDiscoverHvHooks:
    """Tests for discover_hv_hooks()."""

    def test_finds_hook_files(self, tmp_path):
        """Discovers .py files in hv_hook_handlers/ directory."""
        handlers_dir = tmp_path / "hv_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "sync_packages.py").write_text("pass")
        (handlers_dir / "notify.py").write_text("pass")

        result = discover_hv_hooks(tmp_path)

        assert len(result) == 2
        assert handlers_dir / "notify.py" in result
        assert handlers_dir / "sync_packages.py" in result

    def test_returns_sorted_by_name(self, tmp_path):
        """Results are sorted by filename for deterministic order."""
        handlers_dir = tmp_path / "hv_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "zebra.py").write_text("pass")
        (handlers_dir / "alpha.py").write_text("pass")
        (handlers_dir / "middle.py").write_text("pass")

        result = discover_hv_hooks(tmp_path)

        names = [p.name for p in result]
        assert names == ["alpha.py", "middle.py", "zebra.py"]

    def test_ignores_underscore_files(self, tmp_path):
        """Files starting with underscore are ignored."""
        handlers_dir = tmp_path / "hv_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "sync_packages.py").write_text("pass")
        (handlers_dir / "_helpers.py").write_text("pass")
        (handlers_dir / "__init__.py").write_text("")

        result = discover_hv_hooks(tmp_path)

        names = [p.name for p in result]
        assert names == ["sync_packages.py"]

    def test_empty_when_no_handlers_dir(self, tmp_path):
        """Returns empty list when hv_hook_handlers/ doesn't exist."""
        result = discover_hv_hooks(tmp_path)

        assert result == []

    def test_empty_when_handlers_dir_empty(self, tmp_path):
        """Returns empty list when hv_hook_handlers/ is empty."""
        handlers_dir = tmp_path / "hv_hook_handlers"
        handlers_dir.mkdir()

        result = discover_hv_hooks(tmp_path)

        assert result == []

    def test_ignores_non_py_files(self, tmp_path):
        """Only .py files are discovered."""
        handlers_dir = tmp_path / "hv_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "sync_packages.py").write_text("pass")
        (handlers_dir / "README.md").write_text("# Handlers")
        (handlers_dir / "config.json").write_text("{}")

        result = discover_hv_hooks(tmp_path)

        assert len(result) == 1
        assert result[0].name == "sync_packages.py"

    def test_ignores_subdirectories(self, tmp_path):
        """Subdirectories are not discovered as haiv hook modules."""
        handlers_dir = tmp_path / "hv_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "sync_packages.py").write_text("pass")
        subdir = handlers_dir / "helpers"
        subdir.mkdir()
        (subdir / "utils.py").write_text("pass")

        result = discover_hv_hooks(tmp_path)

        assert len(result) == 1
        assert result[0].name == "sync_packages.py"


# ---------------------------------------------------------------------------
# load_hv_hook_module
# ---------------------------------------------------------------------------


class TestLoadHvHookModule:
    """Tests for load_hv_hook_module()."""

    def test_loads_valid_module(self, tmp_path):
        """Returns a loaded module for valid Python."""
        hook_file = tmp_path / "sync_packages.py"
        hook_file.write_text("def handle(req, ctx): return 'ok'\n")

        module = load_hv_hook_module(hook_file)

        assert module is not None
        assert isinstance(module, ModuleType)
        assert hasattr(module, "handle")

    def test_loaded_function_is_callable(self, tmp_path):
        """Functions in the loaded module can be called."""
        hook_file = tmp_path / "sync_packages.py"
        hook_file.write_text("def handle(req, ctx): return f'got_{req}'\n")

        module = load_hv_hook_module(hook_file)
        assert module is not None
        result = module.handle("event", None)

        assert result == "got_event"

    def test_returns_none_on_syntax_error(self, tmp_path, capsys):
        """Returns None for invalid Python, prints warning."""
        hook_file = tmp_path / "bad.py"
        hook_file.write_text("this is not valid python {{{{")

        result = load_hv_hook_module(hook_file)

        assert result is None
        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_returns_none_on_import_error(self, tmp_path, capsys):
        """Returns None when module has import errors, prints warning."""
        hook_file = tmp_path / "bad_import.py"
        hook_file.write_text("import nonexistent_module_xyz_123\n")

        result = load_hv_hook_module(hook_file)

        assert result is None
        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_quiet_suppresses_warnings(self, tmp_path, capsys):
        """quiet=True suppresses warning messages."""
        hook_file = tmp_path / "bad.py"
        hook_file.write_text("this is not valid python {{{{")

        result = load_hv_hook_module(hook_file, quiet=True)

        assert result is None
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_each_load_is_fresh(self, tmp_path):
        """Each load gets a fresh module (not cached)."""
        hook_file = tmp_path / "counter.py"
        hook_file.write_text("count = 0\n")

        mod1 = load_hv_hook_module(hook_file)
        assert mod1 is not None
        mod1.count = 42  # type: ignore[attr-defined]

        mod2 = load_hv_hook_module(hook_file)
        assert mod2 is not None
        assert mod2.count == 0  # Fresh load, not cached


# ---------------------------------------------------------------------------
# collect_hv_handlers
# ---------------------------------------------------------------------------


class TestCollectHvHandlers:
    """Tests for collect_hv_handlers()."""

    def test_finds_marked_functions(self):
        """Finds functions with _hv_hook_guid attribute."""
        module = ModuleType("test_module")
        point = HvHookPoint[str, str](guid="test:my-hook")

        @hv_hook(point, description="test handler")
        def handler(req, ctx):
            return "handled"

        module.handler = handler  # type: ignore[attr-defined]

        result = collect_hv_handlers(module)

        assert len(result) == 1
        guid, fn = result[0]
        assert guid == "test:my-hook"
        assert fn is handler

    def test_finds_multiple_handlers(self):
        """Finds all marked functions in a module."""
        module = ModuleType("test_module")
        point_a = HvHookPoint[str, str](guid="test:hook-a")
        point_b = HvHookPoint[str, str](guid="test:hook-b")

        @hv_hook(point_a, description="handler a")
        def handler_a(req, ctx):
            return "a"

        @hv_hook(point_b, description="handler b")
        def handler_b(req, ctx):
            return "b"

        module.handler_a = handler_a  # type: ignore[attr-defined]
        module.handler_b = handler_b  # type: ignore[attr-defined]

        result = collect_hv_handlers(module)

        guids = {guid for guid, _ in result}
        assert guids == {"test:hook-a", "test:hook-b"}

    def test_ignores_unmarked_functions(self):
        """Functions without _hv_hook_guid are ignored."""
        module = ModuleType("test_module")
        point = HvHookPoint[str, str](guid="test:hook")

        @hv_hook(point, description="marked handler")
        def marked(req, ctx):
            return "yes"

        def unmarked(req, ctx):
            return "no"

        module.marked = marked  # type: ignore[attr-defined]
        module.unmarked = unmarked  # type: ignore[attr-defined]

        result = collect_hv_handlers(module)

        assert len(result) == 1
        assert result[0][1] is marked

    def test_ignores_non_callable_attributes(self):
        """Non-callable module attributes are ignored."""
        module = ModuleType("test_module")
        module.SOME_CONSTANT = "hello"  # type: ignore[attr-defined]
        module.A_NUMBER = 42  # type: ignore[attr-defined]

        result = collect_hv_handlers(module)

        assert result == []

    def test_empty_module(self):
        """Returns empty list for module with no handlers."""
        module = ModuleType("empty_module")

        result = collect_hv_handlers(module)

        assert result == []

    def test_ignores_private_attributes(self):
        """Attributes starting with underscore are skipped."""
        module = ModuleType("test_module")
        point = HvHookPoint[str, str](guid="test:hook")

        @hv_hook(point, description="private handler")
        def _private(req, ctx):
            return "private"

        module._private = _private  # type: ignore[attr-defined]

        result = collect_hv_handlers(module)

        assert result == []


# ---------------------------------------------------------------------------
# HvHookRegistry
# ---------------------------------------------------------------------------


class TestHvHookRegistry:
    """Tests for HvHookRegistry."""

    def test_register_and_emit(self, tmp_path):
        """Registered handler is called on emit."""
        registry = HvHookRegistry()
        calls = []

        def handler(req, ctx):
            calls.append(req)
            return "done"

        stamped = _stamp_handler(handler, source=str(tmp_path / "h.py"))
        registry.register("test:hook", stamped)
        ctx = _mock_ctx(root=tmp_path)
        results = registry.emit("test:hook", "my-request", ctx)

        assert calls == ["my-request"]
        assert results == ["done"]

    def test_emit_passes_ctx_to_handler(self, tmp_path):
        """Handler receives both request and ctx."""
        registry = HvHookRegistry()
        received = {}

        def handler(req, ctx):
            received["req"] = req
            received["ctx"] = ctx

        stamped = _stamp_handler(handler, source=str(tmp_path / "h.py"))
        registry.register("test:hook", stamped)
        ctx = _mock_ctx(root=tmp_path)
        registry.emit("test:hook", "data", ctx)

        assert received["req"] == "data"
        assert received["ctx"] is ctx

    def test_emit_preserves_registration_order(self, tmp_path):
        """Handlers are called in the order they were registered."""
        registry = HvHookRegistry()
        order = []

        h1 = _stamp_handler(lambda req, ctx: order.append("first"), source=str(tmp_path / "h1.py"))
        h2 = _stamp_handler(lambda req, ctx: order.append("second"), source=str(tmp_path / "h2.py"))
        h3 = _stamp_handler(lambda req, ctx: order.append("third"), source=str(tmp_path / "h3.py"))
        registry.register("test:hook", h1)
        registry.register("test:hook", h2)
        registry.register("test:hook", h3)

        registry.emit("test:hook", None, _mock_ctx(root=tmp_path))

        assert order == ["first", "second", "third"]

    def test_emit_returns_all_results(self, tmp_path):
        """Results from all handlers are collected in order."""
        registry = HvHookRegistry()

        registry.register("test:hook", _stamp_handler(lambda req, ctx: "a", source=str(tmp_path / "a.py")))
        registry.register("test:hook", _stamp_handler(lambda req, ctx: "b", source=str(tmp_path / "b.py")))
        registry.register("test:hook", _stamp_handler(lambda req, ctx: "c", source=str(tmp_path / "c.py")))

        results = registry.emit("test:hook", None, _mock_ctx(root=tmp_path))

        assert results == ["a", "b", "c"]

    def test_emit_no_handlers_returns_empty(self):
        """Emitting a guid with no handlers returns empty list."""
        registry = HvHookRegistry()

        results = registry.emit("test:unknown", None, _mock_ctx())

        assert results == []

    def test_emit_propagates_handler_exceptions(self, tmp_path):
        """Handler exceptions propagate to the caller."""
        registry = HvHookRegistry()

        def exploding_handler(req, ctx):
            raise ValueError("boom")

        stamped = _stamp_handler(exploding_handler, source=str(tmp_path / "h.py"))
        registry.register("test:hook", stamped)

        with pytest.raises(ValueError, match="boom"):
            registry.emit("test:hook", None, _mock_ctx(root=tmp_path))

    def test_handlers_for_different_guids_are_independent(self, tmp_path):
        """Handlers registered under different guids don't interfere."""
        registry = HvHookRegistry()

        registry.register("test:hook-a", _stamp_handler(lambda req, ctx: "a", source=str(tmp_path / "a.py")))
        registry.register("test:hook-b", _stamp_handler(lambda req, ctx: "b", source=str(tmp_path / "b.py")))

        ctx = _mock_ctx(root=tmp_path)
        results_a = registry.emit("test:hook-a", None, ctx)
        results_b = registry.emit("test:hook-b", None, ctx)

        assert results_a == ["a"]
        assert results_b == ["b"]

    def test_reset_clears_all_handlers(self, tmp_path):
        """Reset removes all registered handlers."""
        registry = HvHookRegistry()
        registry.register("test:hook", _stamp_handler(lambda req, ctx: "value", source=str(tmp_path / "h.py")))

        registry.reset()

        results = registry.emit("test:hook", None, _mock_ctx(root=tmp_path))
        assert results == []

    def test_emit_prints_description_and_source(self, tmp_path, capsys):
        """emit() prints handler description and relative source path."""
        registry = HvHookRegistry()
        source = tmp_path / "hv_hook_handlers" / "sync.py"

        def handler(req, ctx):
            return "ok"

        stamped = _stamp_handler(handler, description="Syncing packages", source=str(source))
        registry.register("test:hook", stamped)

        ctx = _mock_ctx(root=tmp_path)
        registry.emit("test:hook", None, ctx)

        ctx.print.assert_called_once_with("Syncing packages (hv_hook_handlers/sync.py)")

    def test_emit_rejects_handler_missing_description(self, tmp_path):
        """emit() raises RuntimeError for handler without _hv_hook_description."""
        registry = HvHookRegistry()

        def handler(req, ctx):
            return "ok"

        handler._hv_hook_source = str(tmp_path / "h.py")  # type: ignore[attr-defined]
        registry.register("test:hook", handler)  # type: ignore[arg-type]

        with pytest.raises(RuntimeError, match="missing required attributes"):
            registry.emit("test:hook", None, _mock_ctx(root=tmp_path))

    def test_emit_rejects_handler_missing_source(self, tmp_path):
        """emit() raises RuntimeError for handler without _hv_hook_source."""
        registry = HvHookRegistry()

        def handler(req, ctx):
            return "ok"

        handler._hv_hook_description = "test"  # type: ignore[attr-defined]
        registry.register("test:hook", handler)  # type: ignore[arg-type]

        with pytest.raises(RuntimeError, match="missing required attributes"):
            registry.emit("test:hook", None, _mock_ctx(root=tmp_path))

    def test_emit_rejects_plain_function(self):
        """emit() raises RuntimeError for a plain function with no haiv hook attributes."""
        registry = HvHookRegistry()

        def handler(req, ctx):
            return "ok"

        registry.register("test:hook", handler)  # type: ignore[arg-type]

        with pytest.raises(RuntimeError, match="missing required attributes"):
            registry.emit("test:hook", None, _mock_ctx())


# ---------------------------------------------------------------------------
# HvHookPoint
# ---------------------------------------------------------------------------


class TestHvHookPoint:
    """Tests for HvHookPoint."""

    def test_emit_delegates_to_registry(self, tmp_path):
        """emit() calls registry.emit() with correct args."""
        point = HvHookPoint[str, str](guid="test:my-hook")
        registry = HvHookRegistry()
        received = {}

        def handler(req, ctx):
            received["req"] = req
            received["ctx"] = ctx
            return "result"

        stamped = _stamp_handler(handler, source=str(tmp_path / "h.py"))
        registry.register("test:my-hook", stamped)

        ctx = _mock_ctx(root=tmp_path)
        ctx._hv_hook_registry = registry
        results = point.emit("hello", ctx)

        assert results == ["result"]
        assert received["req"] == "hello"
        assert received["ctx"] is ctx

    def test_emit_raises_when_hooks_not_enabled(self):
        """emit() raises when ctx._hv_hook_registry is None."""
        point = HvHookPoint[str, None](guid="test:hook")

        ctx = Mock()
        ctx._hv_hook_registry = None

        with pytest.raises(Exception):
            point.emit("data", ctx)

    def test_emit_returns_handler_results(self, tmp_path):
        """emit() passes through the list of results from handlers."""
        point = HvHookPoint[str, str](guid="test:hook")
        registry = HvHookRegistry()
        registry.register("test:hook", _stamp_handler(lambda req, ctx: "one", source=str(tmp_path / "a.py")))
        registry.register("test:hook", _stamp_handler(lambda req, ctx: "two", source=str(tmp_path / "b.py")))

        ctx = _mock_ctx(root=tmp_path)
        ctx._hv_hook_registry = registry
        results = point.emit("data", ctx)

        assert results == ["one", "two"]


# ---------------------------------------------------------------------------
# @hv_hook decorator
# ---------------------------------------------------------------------------


class TestHvHookDecorator:
    """Tests for the @hv_hook decorator."""

    def test_sets_hv_hook_guid(self):
        """Decorator sets _hv_hook_guid attribute on the function."""
        point = HvHookPoint[str, None](guid="test:my-hook")

        @hv_hook(point, description="test handler")
        def handler(req, ctx):
            pass

        assert hasattr(handler, "_hv_hook_guid")
        assert handler._hv_hook_guid == "test:my-hook"

    def test_sets_hv_hook_description(self):
        """Decorator sets _hv_hook_description attribute on the function."""
        point = HvHookPoint[str, None](guid="test:hook")

        @hv_hook(point, description="Syncing packages")
        def handler(req, ctx):
            pass

        assert hasattr(handler, "_hv_hook_description")
        assert handler._hv_hook_description == "Syncing packages"

    def test_returns_function_unchanged(self):
        """Decorated function is the same object (not wrapped)."""
        point = HvHookPoint[str, None](guid="test:hook")

        def handler(req, ctx):
            return "value"

        decorated = hv_hook(point, description="test")(handler)

        assert decorated is handler

    def test_decorated_function_still_callable(self):
        """Decorated function can still be called normally."""
        point = HvHookPoint[str, str](guid="test:hook")

        @hv_hook(point, description="test handler")
        def handler(req, ctx):
            return f"handled_{req}"

        result = handler("event", None)
        assert result == "handled_event"


# ---------------------------------------------------------------------------
# configure_hv_hooks
# ---------------------------------------------------------------------------


def _trusted_root(tmp_path, name="hv_project"):
    """Create a trusted package root directory for testing."""
    root = tmp_path / name
    root.mkdir(exist_ok=True)
    return root


class TestConfigureHvHooks:
    """Tests for configure_hv_hooks()."""

    def test_returns_registry_with_handlers(self, tmp_path):
        """Discovers, loads, and registers handlers from pkg_roots."""
        pkg = _trusted_root(tmp_path)
        handlers_dir = pkg / "hv_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "my_handler.py").write_text(
            "from haiv.hv_hooks import hv_hook, HvHookPoint\n"
            "\n"
            'HOOK = HvHookPoint(guid="test:configure-hook")\n'
            "\n"
            '@hv_hook(HOOK, description="Configuring")\n'
            "def handle(req, ctx):\n"
            "    return 'configured'\n"
        )

        registry = configure_hv_hooks([pkg])

        assert isinstance(registry, HvHookRegistry)
        results = registry.emit("test:configure-hook", None, _mock_ctx(root=tmp_path))
        assert results == ["configured"]

    def test_multiple_pkg_roots(self, tmp_path):
        """Handlers from all pkg_roots are registered."""
        pkg1 = _trusted_root(tmp_path, "haiv_core")
        (pkg1 / "hv_hook_handlers").mkdir()
        (pkg1 / "hv_hook_handlers" / "h1.py").write_text(
            "from haiv.hv_hooks import hv_hook, HvHookPoint\n"
            'HOOK = HvHookPoint(guid="test:shared")\n'
            '@hv_hook(HOOK, description="From core")\n'
            "def handle(req, ctx): return 'from_core'\n"
        )

        pkg2 = _trusted_root(tmp_path, "hv_project")
        (pkg2 / "hv_hook_handlers").mkdir()
        (pkg2 / "hv_hook_handlers" / "h2.py").write_text(
            "from haiv.hv_hooks import hv_hook, HvHookPoint\n"
            'HOOK = HvHookPoint(guid="test:shared")\n'
            '@hv_hook(HOOK, description="From project")\n'
            "def handle(req, ctx): return 'from_project'\n"
        )

        registry = configure_hv_hooks([pkg1, pkg2])
        ctx = _mock_ctx(root=tmp_path)
        results = registry.emit("test:shared", None, ctx)

        assert results == ["from_core", "from_project"]

    def test_empty_pkg_roots(self):
        """Empty pkg_roots returns an empty registry."""
        registry = configure_hv_hooks([])

        assert isinstance(registry, HvHookRegistry)
        results = registry.emit("test:anything", None, _mock_ctx())
        assert results == []

    def test_skips_broken_modules(self, tmp_path, capsys):
        """Broken modules are skipped, valid ones still load."""
        pkg = _trusted_root(tmp_path)
        handlers_dir = pkg / "hv_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "aaa_broken.py").write_text("this is not valid python {{{{")
        (handlers_dir / "zzz_good.py").write_text(
            "from haiv.hv_hooks import hv_hook, HvHookPoint\n"
            'HOOK = HvHookPoint(guid="test:good")\n'
            '@hv_hook(HOOK, description="Good handler")\n'
            "def handle(req, ctx): return 'good'\n"
        )

        registry = configure_hv_hooks([pkg])
        results = registry.emit("test:good", None, _mock_ctx(root=tmp_path))

        assert results == ["good"]
        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_pkg_root_without_handlers_dir(self, tmp_path):
        """pkg_root with no hv_hook_handlers/ is silently skipped."""
        pkg = _trusted_root(tmp_path)
        registry = configure_hv_hooks([pkg])

        assert isinstance(registry, HvHookRegistry)

    def test_stamps_source_on_handlers(self, tmp_path):
        """configure_hv_hooks stamps _hv_hook_source with the handler file path."""
        pkg = _trusted_root(tmp_path)
        handlers_dir = pkg / "hv_hook_handlers"
        handlers_dir.mkdir()
        handler_file = handlers_dir / "my_handler.py"
        handler_file.write_text(
            "from haiv.hv_hooks import hv_hook, HvHookPoint\n"
            'HOOK = HvHookPoint(guid="test:source")\n'
            '@hv_hook(HOOK, description="Source test")\n'
            "def handle(req, ctx): return 'ok'\n"
        )

        registry = configure_hv_hooks([pkg])

        # Get the handler out of the registry to check the stamp
        handlers = registry._handlers["test:source"]
        assert len(handlers) == 1
        assert handlers[0]._hv_hook_source == str(handler_file)

    def test_rejects_untrusted_package(self, tmp_path):
        """Untrusted package roots are rejected with RuntimeError."""
        untrusted = tmp_path / "evil_package"
        untrusted.mkdir()
        (untrusted / "hv_hook_handlers").mkdir()
        (untrusted / "hv_hook_handlers" / "backdoor.py").write_text(
            "from haiv.hv_hooks import hv_hook, HvHookPoint\n"
            'HOOK = HvHookPoint(guid="test:evil")\n'
            '@hv_hook(HOOK, description="Totally safe")\n'
            "def handle(req, ctx): return 'pwned'\n"
        )

        with pytest.raises(RuntimeError, match="Untrusted package"):
            configure_hv_hooks([untrusted])

    def test_rejects_untrusted_even_with_trusted(self, tmp_path):
        """One untrusted root in the list rejects the whole configuration."""
        trusted = _trusted_root(tmp_path, "haiv_core")
        untrusted = tmp_path / "sneaky_pkg"
        untrusted.mkdir()

        with pytest.raises(RuntimeError, match="Untrusted package"):
            configure_hv_hooks([trusted, untrusted])


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


class TestHvHookIntegration:
    """End-to-end test: define hook point, register handler, emit."""

    def test_full_flow(self, tmp_path):
        """Define a point, write a handler file, load, collect, register, emit."""
        # 1. Define a haiv hook point
        point = HvHookPoint[str, str](guid="test:integration")

        # 2. Write a handler module that uses @hv_hook
        pkg = _trusted_root(tmp_path)
        handlers_dir = pkg / "hv_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "responder.py").write_text(
            "from haiv.hv_hooks import hv_hook, HvHookPoint\n"
            "\n"
            'MY_POINT = HvHookPoint(guid="test:integration")\n'
            "\n"
            '@hv_hook(MY_POINT, description="Responding")\n'
            "def respond(req, ctx):\n"
            "    return f'received_{req}'\n"
        )

        # 3. Use configure_hv_hooks to wire everything up
        registry = configure_hv_hooks([pkg])

        # 4. Emit through the HvHookPoint (as a command would)
        ctx = _mock_ctx(root=tmp_path)
        ctx._hv_hook_registry = registry
        results = point.emit("hello", ctx)

        assert results == ["received_hello"]

    def test_multiple_handlers_same_point(self, tmp_path):
        """Multiple handlers for the same haiv hook point all fire."""
        point = HvHookPoint[str, str](guid="test:multi")

        pkg = _trusted_root(tmp_path)
        handlers_dir = pkg / "hv_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "aaa_first.py").write_text(
            "from haiv.hv_hooks import hv_hook, HvHookPoint\n"
            'P = HvHookPoint(guid="test:multi")\n'
            '@hv_hook(P, description="First handler")\n'
            "def handle(req, ctx): return 'first'\n"
        )
        (handlers_dir / "zzz_second.py").write_text(
            "from haiv.hv_hooks import hv_hook, HvHookPoint\n"
            'P = HvHookPoint(guid="test:multi")\n'
            '@hv_hook(P, description="Second handler")\n'
            "def handle(req, ctx): return 'second'\n"
        )

        registry = configure_hv_hooks([pkg])

        ctx = _mock_ctx(root=tmp_path)
        ctx._hv_hook_registry = registry
        results = point.emit("data", ctx)

        # Sorted discovery order: aaa_first.py before zzz_second.py
        assert results == ["first", "second"]
