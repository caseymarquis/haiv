"""Tests for mg hook system.

Tests the mg hook infrastructure (discovery, loading, collection, registration)
and the public API (MgHookPoint, @mg_hook decorator). Mirrors the structure
of test_resolvers.py.

This tests the mg hook system specifically -- distinct from Claude hooks.
"""

import pytest
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

from mg._infrastructure.mg_hooks import (
    MgHookRegistry,
    collect_mg_handlers,
    configure_mg_hooks,
    discover_mg_hooks,
    load_mg_hook_module,
)
from mg.mg_hooks import MgHookPoint, mg_hook


# ---------------------------------------------------------------------------
# discover_mg_hooks
# ---------------------------------------------------------------------------


class TestDiscoverMgHooks:
    """Tests for discover_mg_hooks()."""

    def test_finds_hook_files(self, tmp_path):
        """Discovers .py files in mg_hook_handlers/ directory."""
        handlers_dir = tmp_path / "mg_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "sync_packages.py").write_text("pass")
        (handlers_dir / "notify.py").write_text("pass")

        result = discover_mg_hooks(tmp_path)

        assert len(result) == 2
        assert handlers_dir / "notify.py" in result
        assert handlers_dir / "sync_packages.py" in result

    def test_returns_sorted_by_name(self, tmp_path):
        """Results are sorted by filename for deterministic order."""
        handlers_dir = tmp_path / "mg_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "zebra.py").write_text("pass")
        (handlers_dir / "alpha.py").write_text("pass")
        (handlers_dir / "middle.py").write_text("pass")

        result = discover_mg_hooks(tmp_path)

        names = [p.name for p in result]
        assert names == ["alpha.py", "middle.py", "zebra.py"]

    def test_ignores_underscore_files(self, tmp_path):
        """Files starting with underscore are ignored."""
        handlers_dir = tmp_path / "mg_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "sync_packages.py").write_text("pass")
        (handlers_dir / "_helpers.py").write_text("pass")
        (handlers_dir / "__init__.py").write_text("")

        result = discover_mg_hooks(tmp_path)

        names = [p.name for p in result]
        assert names == ["sync_packages.py"]

    def test_empty_when_no_handlers_dir(self, tmp_path):
        """Returns empty list when mg_hook_handlers/ doesn't exist."""
        result = discover_mg_hooks(tmp_path)

        assert result == []

    def test_empty_when_handlers_dir_empty(self, tmp_path):
        """Returns empty list when mg_hook_handlers/ is empty."""
        handlers_dir = tmp_path / "mg_hook_handlers"
        handlers_dir.mkdir()

        result = discover_mg_hooks(tmp_path)

        assert result == []

    def test_ignores_non_py_files(self, tmp_path):
        """Only .py files are discovered."""
        handlers_dir = tmp_path / "mg_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "sync_packages.py").write_text("pass")
        (handlers_dir / "README.md").write_text("# Handlers")
        (handlers_dir / "config.json").write_text("{}")

        result = discover_mg_hooks(tmp_path)

        assert len(result) == 1
        assert result[0].name == "sync_packages.py"

    def test_ignores_subdirectories(self, tmp_path):
        """Subdirectories are not discovered as mg hook modules."""
        handlers_dir = tmp_path / "mg_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "sync_packages.py").write_text("pass")
        subdir = handlers_dir / "helpers"
        subdir.mkdir()
        (subdir / "utils.py").write_text("pass")

        result = discover_mg_hooks(tmp_path)

        assert len(result) == 1
        assert result[0].name == "sync_packages.py"


# ---------------------------------------------------------------------------
# load_mg_hook_module
# ---------------------------------------------------------------------------


class TestLoadMgHookModule:
    """Tests for load_mg_hook_module()."""

    def test_loads_valid_module(self, tmp_path):
        """Returns a loaded module for valid Python."""
        hook_file = tmp_path / "sync_packages.py"
        hook_file.write_text("def handle(req, ctx): return 'ok'\n")

        module = load_mg_hook_module(hook_file)

        assert module is not None
        assert isinstance(module, ModuleType)
        assert hasattr(module, "handle")

    def test_loaded_function_is_callable(self, tmp_path):
        """Functions in the loaded module can be called."""
        hook_file = tmp_path / "sync_packages.py"
        hook_file.write_text("def handle(req, ctx): return f'got_{req}'\n")

        module = load_mg_hook_module(hook_file)
        assert module is not None
        result = module.handle("event", None)

        assert result == "got_event"

    def test_returns_none_on_syntax_error(self, tmp_path, capsys):
        """Returns None for invalid Python, prints warning."""
        hook_file = tmp_path / "bad.py"
        hook_file.write_text("this is not valid python {{{{")

        result = load_mg_hook_module(hook_file)

        assert result is None
        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_returns_none_on_import_error(self, tmp_path, capsys):
        """Returns None when module has import errors, prints warning."""
        hook_file = tmp_path / "bad_import.py"
        hook_file.write_text("import nonexistent_module_xyz_123\n")

        result = load_mg_hook_module(hook_file)

        assert result is None
        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_quiet_suppresses_warnings(self, tmp_path, capsys):
        """quiet=True suppresses warning messages."""
        hook_file = tmp_path / "bad.py"
        hook_file.write_text("this is not valid python {{{{")

        result = load_mg_hook_module(hook_file, quiet=True)

        assert result is None
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_each_load_is_fresh(self, tmp_path):
        """Each load gets a fresh module (not cached)."""
        hook_file = tmp_path / "counter.py"
        hook_file.write_text("count = 0\n")

        mod1 = load_mg_hook_module(hook_file)
        assert mod1 is not None
        mod1.count = 42

        mod2 = load_mg_hook_module(hook_file)
        assert mod2 is not None
        assert mod2.count == 0  # Fresh load, not cached


# ---------------------------------------------------------------------------
# collect_mg_handlers
# ---------------------------------------------------------------------------


class TestCollectMgHandlers:
    """Tests for collect_mg_handlers()."""

    def test_finds_marked_functions(self):
        """Finds functions with _mg_hook_guid attribute."""
        module = ModuleType("test_module")

        def handler(req, ctx):
            return "handled"

        handler._mg_hook_guid = "test:my-hook"
        module.handler = handler

        result = collect_mg_handlers(module)

        assert len(result) == 1
        guid, fn = result[0]
        assert guid == "test:my-hook"
        assert fn is handler

    def test_finds_multiple_handlers(self):
        """Finds all marked functions in a module."""
        module = ModuleType("test_module")

        def handler_a(req, ctx):
            return "a"

        def handler_b(req, ctx):
            return "b"

        handler_a._mg_hook_guid = "test:hook-a"
        handler_b._mg_hook_guid = "test:hook-b"
        module.handler_a = handler_a
        module.handler_b = handler_b

        result = collect_mg_handlers(module)

        guids = {guid for guid, _ in result}
        assert guids == {"test:hook-a", "test:hook-b"}

    def test_ignores_unmarked_functions(self):
        """Functions without _mg_hook_guid are ignored."""
        module = ModuleType("test_module")

        def marked(req, ctx):
            return "yes"

        def unmarked(req, ctx):
            return "no"

        marked._mg_hook_guid = "test:hook"
        module.marked = marked
        module.unmarked = unmarked

        result = collect_mg_handlers(module)

        assert len(result) == 1
        assert result[0][1] is marked

    def test_ignores_non_callable_attributes(self):
        """Non-callable module attributes are ignored."""
        module = ModuleType("test_module")
        module.SOME_CONSTANT = "hello"
        module.A_NUMBER = 42

        result = collect_mg_handlers(module)

        assert result == []

    def test_empty_module(self):
        """Returns empty list for module with no handlers."""
        module = ModuleType("empty_module")

        result = collect_mg_handlers(module)

        assert result == []

    def test_ignores_private_attributes(self):
        """Attributes starting with underscore are skipped."""
        module = ModuleType("test_module")

        def _private(req, ctx):
            return "private"

        _private._mg_hook_guid = "test:hook"
        module._private = _private

        result = collect_mg_handlers(module)

        assert result == []


# ---------------------------------------------------------------------------
# MgHookRegistry
# ---------------------------------------------------------------------------


class TestMgHookRegistry:
    """Tests for MgHookRegistry."""

    def test_register_and_emit(self):
        """Registered handler is called on emit."""
        registry = MgHookRegistry()
        calls = []

        def handler(req, ctx):
            calls.append(req)
            return "done"

        registry.register("test:hook", handler)
        ctx = Mock()
        results = registry.emit("test:hook", "my-request", ctx)

        assert calls == ["my-request"]
        assert results == ["done"]

    def test_emit_passes_ctx_to_handler(self):
        """Handler receives both request and ctx."""
        registry = MgHookRegistry()
        received = {}

        def handler(req, ctx):
            received["req"] = req
            received["ctx"] = ctx

        registry.register("test:hook", handler)
        mock_ctx = Mock()
        registry.emit("test:hook", "data", mock_ctx)

        assert received["req"] == "data"
        assert received["ctx"] is mock_ctx

    def test_emit_preserves_registration_order(self):
        """Handlers are called in the order they were registered."""
        registry = MgHookRegistry()
        order = []

        registry.register("test:hook", lambda req, ctx: order.append("first"))
        registry.register("test:hook", lambda req, ctx: order.append("second"))
        registry.register("test:hook", lambda req, ctx: order.append("third"))

        registry.emit("test:hook", None, Mock())

        assert order == ["first", "second", "third"]

    def test_emit_returns_all_results(self):
        """Results from all handlers are collected in order."""
        registry = MgHookRegistry()

        registry.register("test:hook", lambda req, ctx: "a")
        registry.register("test:hook", lambda req, ctx: "b")
        registry.register("test:hook", lambda req, ctx: "c")

        results = registry.emit("test:hook", None, Mock())

        assert results == ["a", "b", "c"]

    def test_emit_no_handlers_returns_empty(self):
        """Emitting a guid with no handlers returns empty list."""
        registry = MgHookRegistry()

        results = registry.emit("test:unknown", None, Mock())

        assert results == []

    def test_emit_propagates_handler_exceptions(self):
        """Handler exceptions propagate to the caller."""
        registry = MgHookRegistry()

        def exploding_handler(req, ctx):
            raise ValueError("boom")

        registry.register("test:hook", exploding_handler)

        with pytest.raises(ValueError, match="boom"):
            registry.emit("test:hook", None, Mock())

    def test_handlers_for_different_guids_are_independent(self):
        """Handlers registered under different guids don't interfere."""
        registry = MgHookRegistry()

        registry.register("test:hook-a", lambda req, ctx: "a")
        registry.register("test:hook-b", lambda req, ctx: "b")

        results_a = registry.emit("test:hook-a", None, Mock())
        results_b = registry.emit("test:hook-b", None, Mock())

        assert results_a == ["a"]
        assert results_b == ["b"]

    def test_reset_clears_all_handlers(self):
        """Reset removes all registered handlers."""
        registry = MgHookRegistry()
        registry.register("test:hook", lambda req, ctx: "value")

        registry.reset()

        results = registry.emit("test:hook", None, Mock())
        assert results == []


# ---------------------------------------------------------------------------
# MgHookPoint
# ---------------------------------------------------------------------------


class TestMgHookPoint:
    """Tests for MgHookPoint."""

    def test_emit_delegates_to_registry(self):
        """emit() calls registry.emit() with correct args."""
        point = MgHookPoint[str, str](guid="test:my-hook")
        registry = MgHookRegistry()
        received = {}

        def handler(req, ctx):
            received["req"] = req
            received["ctx"] = ctx
            return "result"

        registry.register("test:my-hook", handler)

        ctx = Mock()
        ctx._mg_hook_registry = registry
        results = point.emit("hello", ctx)

        assert results == ["result"]
        assert received["req"] == "hello"
        assert received["ctx"] is ctx

    def test_emit_raises_when_hooks_not_enabled(self):
        """emit() raises when ctx._mg_hook_registry is None."""
        point = MgHookPoint[str, None](guid="test:hook")

        ctx = Mock()
        ctx._mg_hook_registry = None

        with pytest.raises(Exception):
            point.emit("data", ctx)

    def test_emit_returns_handler_results(self):
        """emit() passes through the list of results from handlers."""
        point = MgHookPoint[str, str](guid="test:hook")
        registry = MgHookRegistry()
        registry.register("test:hook", lambda req, ctx: "one")
        registry.register("test:hook", lambda req, ctx: "two")

        ctx = Mock()
        ctx._mg_hook_registry = registry
        results = point.emit("data", ctx)

        assert results == ["one", "two"]


# ---------------------------------------------------------------------------
# @mg_hook decorator
# ---------------------------------------------------------------------------


class TestMgHookDecorator:
    """Tests for the @mg_hook decorator."""

    def test_sets_mg_hook_guid(self):
        """Decorator sets _mg_hook_guid attribute on the function."""
        point = MgHookPoint[str, None](guid="test:my-hook")

        @mg_hook(point)
        def handler(req, ctx):
            pass

        assert hasattr(handler, "_mg_hook_guid")
        assert handler._mg_hook_guid == "test:my-hook"

    def test_returns_function_unchanged(self):
        """Decorated function is the same object (not wrapped)."""
        point = MgHookPoint[str, None](guid="test:hook")

        def handler(req, ctx):
            return "value"

        decorated = mg_hook(point)(handler)

        assert decorated is handler

    def test_decorated_function_still_callable(self):
        """Decorated function can still be called normally."""
        point = MgHookPoint[str, str](guid="test:hook")

        @mg_hook(point)
        def handler(req, ctx):
            return f"handled_{req}"

        result = handler("event", None)
        assert result == "handled_event"


# ---------------------------------------------------------------------------
# configure_mg_hooks
# ---------------------------------------------------------------------------


class TestConfigureMgHooks:
    """Tests for configure_mg_hooks()."""

    def test_returns_registry_with_handlers(self, tmp_path):
        """Discovers, loads, and registers handlers from pkg_roots."""
        handlers_dir = tmp_path / "mg_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "my_handler.py").write_text(
            "from mg.mg_hooks import mg_hook, MgHookPoint\n"
            "\n"
            'HOOK = MgHookPoint(guid="test:configure-hook")\n'
            "\n"
            "@mg_hook(HOOK)\n"
            "def handle(req, ctx):\n"
            "    return 'configured'\n"
        )

        registry = configure_mg_hooks([tmp_path])

        assert isinstance(registry, MgHookRegistry)
        results = registry.emit("test:configure-hook", None, Mock())
        assert results == ["configured"]

    def test_multiple_pkg_roots(self, tmp_path):
        """Handlers from all pkg_roots are registered."""
        pkg1 = tmp_path / "pkg1"
        pkg1.mkdir()
        (pkg1 / "mg_hook_handlers").mkdir()
        (pkg1 / "mg_hook_handlers" / "h1.py").write_text(
            "from mg.mg_hooks import mg_hook, MgHookPoint\n"
            'HOOK = MgHookPoint(guid="test:shared")\n'
            "@mg_hook(HOOK)\n"
            "def handle(req, ctx): return 'from_pkg1'\n"
        )

        pkg2 = tmp_path / "pkg2"
        pkg2.mkdir()
        (pkg2 / "mg_hook_handlers").mkdir()
        (pkg2 / "mg_hook_handlers" / "h2.py").write_text(
            "from mg.mg_hooks import mg_hook, MgHookPoint\n"
            'HOOK = MgHookPoint(guid="test:shared")\n'
            "@mg_hook(HOOK)\n"
            "def handle(req, ctx): return 'from_pkg2'\n"
        )

        registry = configure_mg_hooks([pkg1, pkg2])
        results = registry.emit("test:shared", None, Mock())

        assert results == ["from_pkg1", "from_pkg2"]

    def test_empty_pkg_roots(self):
        """Empty pkg_roots returns an empty registry."""
        registry = configure_mg_hooks([])

        assert isinstance(registry, MgHookRegistry)
        results = registry.emit("test:anything", None, Mock())
        assert results == []

    def test_skips_broken_modules(self, tmp_path, capsys):
        """Broken modules are skipped, valid ones still load."""
        handlers_dir = tmp_path / "mg_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "aaa_broken.py").write_text("this is not valid python {{{{")
        (handlers_dir / "zzz_good.py").write_text(
            "from mg.mg_hooks import mg_hook, MgHookPoint\n"
            'HOOK = MgHookPoint(guid="test:good")\n'
            "@mg_hook(HOOK)\n"
            "def handle(req, ctx): return 'good'\n"
        )

        registry = configure_mg_hooks([tmp_path])
        results = registry.emit("test:good", None, Mock())

        assert results == ["good"]
        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_pkg_root_without_handlers_dir(self, tmp_path):
        """pkg_root with no mg_hook_handlers/ is silently skipped."""
        registry = configure_mg_hooks([tmp_path])

        assert isinstance(registry, MgHookRegistry)


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


class TestMgHookIntegration:
    """End-to-end test: define hook point, register handler, emit."""

    def test_full_flow(self, tmp_path):
        """Define a point, write a handler file, load, collect, register, emit."""
        # 1. Define an mg hook point
        point = MgHookPoint[str, str](guid="test:integration")

        # 2. Write a handler module that uses @mg_hook
        handlers_dir = tmp_path / "mg_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "responder.py").write_text(
            "from mg.mg_hooks import mg_hook, MgHookPoint\n"
            "\n"
            'MY_POINT = MgHookPoint(guid="test:integration")\n'
            "\n"
            "@mg_hook(MY_POINT)\n"
            "def respond(req, ctx):\n"
            "    return f'received_{req}'\n"
        )

        # 3. Use configure_mg_hooks to wire everything up
        registry = configure_mg_hooks([tmp_path])

        # 4. Emit through the MgHookPoint (as a command would)
        ctx = Mock()
        ctx._mg_hook_registry = registry
        results = point.emit("hello", ctx)

        assert results == ["received_hello"]

    def test_multiple_handlers_same_point(self, tmp_path):
        """Multiple handlers for the same mg hook point all fire."""
        point = MgHookPoint[str, str](guid="test:multi")

        handlers_dir = tmp_path / "mg_hook_handlers"
        handlers_dir.mkdir()
        (handlers_dir / "aaa_first.py").write_text(
            "from mg.mg_hooks import mg_hook, MgHookPoint\n"
            'P = MgHookPoint(guid="test:multi")\n'
            "@mg_hook(P)\n"
            "def handle(req, ctx): return 'first'\n"
        )
        (handlers_dir / "zzz_second.py").write_text(
            "from mg.mg_hooks import mg_hook, MgHookPoint\n"
            'P = MgHookPoint(guid="test:multi")\n'
            "@mg_hook(P)\n"
            "def handle(req, ctx): return 'second'\n"
        )

        registry = configure_mg_hooks([tmp_path])

        ctx = Mock()
        ctx._mg_hook_registry = registry
        results = point.emit("data", ctx)

        # Sorted discovery order: aaa_first.py before zzz_second.py
        assert results == ["first", "second"]
