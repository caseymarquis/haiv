"""Hook discovery and registration for mg.

Hooks are event handlers that respond to hook points emitted by commands.
Hook files live in `hooks/` within each package (mg_core, mg_project, mg_user).

Discovery follows the package hierarchy: core -> project -> user.
All hooks run (accumulate), unlike resolvers which override.

Hook modules are loaded lazily -- only on first emit() call.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


class HookRegistry:
    """Central registry for hook handlers.

    Stores package roots and lazily discovers/loads hook modules
    on first emit() call. Handlers are keyed by hook point GUID.
    """

    def __init__(self) -> None:
        self._pkg_roots: list[Path] = []
        self._handlers: dict[str, list[Callable]] = {}
        self._loaded: bool = False

    def configure(self, pkg_roots: list[Path]) -> None:
        """Store package roots for later discovery.

        Args:
            pkg_roots: Package roots in discovery order (core first, user last).
        """
        ...

    def register(self, guid: str, handler: Callable) -> None:
        """Register a handler for a hook point GUID.

        Called by the @hook decorator at module import time.

        Args:
            guid: The hook point GUID to subscribe to.
            handler: Callable with signature (request, ctx) -> response.
        """
        ...

    def emit(self, guid: str, request: Any, ctx: Any) -> list[Any]:
        """Emit a hook point, calling all registered handlers.

        Lazily loads hook modules on first call. Handlers are called
        in registration order (core -> project -> user).

        Args:
            guid: The hook point GUID.
            request: Event data to pass to handlers.
            ctx: Command context (cmd.Ctx).

        Returns:
            List of results from each handler.
        """
        ...

    def _ensure_loaded(self) -> None:
        """Discover and load all hook modules if not yet loaded."""
        ...

    def reset(self) -> None:
        """Reset all state. For testing only."""
        ...


# Module-level singleton shared by the public API (mg.hooks).
_registry = HookRegistry()


def discover_hooks(pkg_root: Path) -> list[Path]:
    """Find hook files in pkg_root/hooks/.

    Follows the same conventions as discover_resolvers:
    - Only .py files
    - Ignores underscore-prefixed files
    - Ignores subdirectories

    Args:
        pkg_root: Root of a package (e.g., mg_core, mg_project).

    Returns:
        List of paths to hook .py files, sorted by name for deterministic order.
    """
    ...


def load_hook_module(path: Path, *, quiet: bool = False) -> ModuleType | None:
    """Load a hook module, triggering @hook decorators at import time.

    Invalid or broken modules are skipped with a warning (unless quiet=True).

    Args:
        path: Path to the hook .py file.
        quiet: If True, suppress warning messages.

    Returns:
        Loaded module, or None if invalid/broken.
    """
    ...
