"""haiv hook discovery, registration, and lifecycle.

Infrastructure for the haiv hook system. Handles discovering haiv hook modules
in ``haiv_hook_handlers/`` directories, loading them, collecting @haiv_hook-marked
handlers, and registering them on an HaivHookRegistry.

This is the infrastructure layer -- command authors don't interact with it.
They use ``haiv.haiv_hooks.HaivHookPoint`` and ``@haiv.haiv_hooks.haiv_hook`` instead.

This module is distinct from Claude hooks (``claude_hooks/``), which integrate
with Claude Code's hook system.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from haiv.haiv_hooks import HaivHookHandler
from haiv.paths import PkgPaths


class HaivHookRegistry:
    """Central registry for haiv hook handlers.

    Stores handlers keyed by haiv hook point GUID. Populated at CLI startup
    when a command declares ``enable_haiv_hooks=True``.

    Commands don't interact with this directly -- they emit haiv hook points
    via ``HaivHookPoint.emit()``, which delegates here.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[HaivHookHandler]] = {}

    def register(self, guid: str, handler: HaivHookHandler) -> None:
        """Register a handler for a haiv hook point GUID.

        Called by configure_haiv_hooks() during startup, not by user code.

        Args:
            guid: The haiv hook point GUID to subscribe to.
            handler: An HaivHookHandler (decorated with @haiv_hook).
        """
        self._handlers.setdefault(guid, []).append(handler)

    def emit(self, guid: str, request: Any, ctx: Any) -> list[Any]:
        """Emit a haiv hook point, calling all registered handlers.

        Handlers are called in registration order (core -> project -> user).
        Exceptions from handlers propagate to the caller.

        Args:
            guid: The haiv hook point GUID.
            request: Event data to pass to handlers.
            ctx: Command context (cmd.Ctx).

        Returns:
            List of results from each handler.
        """
        results = []
        for handler in self._handlers.get(guid, []):
            if not hasattr(handler, "_haiv_hook_description") or not hasattr(
                handler, "_haiv_hook_source"
            ):
                raise RuntimeError(
                    f"haiv hook handler {handler!r} is missing required attributes. "
                    "All handlers must be registered via @haiv_hook()."
                )
            source = Path(handler._haiv_hook_source).relative_to(ctx.paths.root)
            ctx.print(f"{handler._haiv_hook_description} ({source})")
            results.append(handler(request, ctx))
        return results

    def reset(self) -> None:
        """Reset all state. For testing only."""
        self._handlers.clear()


def discover_haiv_hooks(pkg_root: Path) -> list[Path]:
    """Find haiv hook files in pkg_root/haiv_hook_handlers/.

    Follows the same conventions as discover_resolvers:
    - Only .py files
    - Ignores underscore-prefixed files
    - Ignores subdirectories

    Args:
        pkg_root: Root of a package (e.g., haiv_core, haiv_project).

    Returns:
        List of paths to haiv hook .py files, sorted by name for deterministic order.
    """
    pkg = PkgPaths(root=pkg_root)
    handlers_dir = pkg.haiv_hook_handlers_dir
    if not handlers_dir.exists():
        return []

    paths = []
    for item in handlers_dir.iterdir():
        if item.name.startswith("_"):
            continue
        if item.is_file() and item.suffix == ".py":
            paths.append(item)

    return sorted(paths, key=lambda p: p.name)


def load_haiv_hook_module(path: Path, *, quiet: bool = False) -> ModuleType | None:
    """Load a haiv hook module from a file path.

    Invalid or broken modules are skipped with a warning (unless quiet=True).
    This ensures a broken haiv hook doesn't crash the system.

    Args:
        path: Path to the haiv hook .py file.
        quiet: If True, suppress warning messages.

    Returns:
        Loaded module, or None if invalid/broken.
    """
    try:
        module_name = f"haiv_hook_{path.stem}_{id(path)}"
        spec = importlib.util.spec_from_file_location(module_name, path)

        if spec is None or spec.loader is None:
            if not quiet:
                print(f"Warning: Cannot load haiv hook module from {path}")
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        return module

    except Exception as e:
        if not quiet:
            print(f"Warning: Error loading haiv hook module {path}: {e}")
        return None


def collect_haiv_handlers(module: ModuleType) -> list[tuple[str, HaivHookHandler]]:
    """Scan a loaded module for functions marked with @haiv_hook.

    Looks for the ``_haiv_hook_guid`` attribute set by the @haiv_hook decorator.

    Args:
        module: A loaded haiv hook module.

    Returns:
        List of (guid, handler) pairs found in the module.
    """
    handlers = []
    for name in dir(module):
        if name.startswith("_"):
            continue
        attr = getattr(module, name)
        if callable(attr) and hasattr(attr, "_haiv_hook_guid"):
            handlers.append((attr._haiv_hook_guid, attr))
    return handlers


# Only these first-party packages are allowed to provide haiv hooks.
# Third-party packages must not run hooks without an explicit trust mechanism.
_TRUSTED_HOOK_PACKAGES = {"haiv_core", "haiv_project", "haiv_user"}


def configure_haiv_hooks(pkg_roots: list[Path]) -> HaivHookRegistry:
    """Discover, load, and register all haiv hooks from the given package roots.

    Called by the CLI at startup when the command declares enable_haiv_hooks=True.
    Discovers haiv hook modules in each package's haiv_hook_handlers/ directory, loads them,
    collects @haiv_hook-marked handlers, and registers them on a new HaivHookRegistry.

    Only first-party packages (haiv_core, haiv_project, haiv_user) are trusted to
    provide hooks. Any other package root is rejected with an error.

    Args:
        pkg_roots: Package roots in discovery order (core first, user last).

    Returns:
        Populated HaivHookRegistry ready for use.

    Raises:
        RuntimeError: If a pkg_root is not a trusted first-party package.
    """
    registry = HaivHookRegistry()
    for pkg_root in pkg_roots:
        if pkg_root.name not in _TRUSTED_HOOK_PACKAGES:
            raise RuntimeError(
                f"Untrusted package '{pkg_root.name}' cannot provide haiv hooks. "
                f"Only first-party packages are allowed: {sorted(_TRUSTED_HOOK_PACKAGES)}."
            )
        for path in discover_haiv_hooks(pkg_root):
            module = load_haiv_hook_module(path)
            if module is not None:
                for guid, handler in collect_haiv_handlers(module):
                    handler._haiv_hook_source = str(path)
                    registry.register(guid, handler)
    return registry
