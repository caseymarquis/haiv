"""haiv hook system for haiv commands.

Commands define haiv hook points (typed extension points) and emit them during
execution. Other packages subscribe by placing handler modules in their
haiv_hook_handlers/ directory.

This module is distinct from Claude hooks (claude_hooks/), which integrate
with Claude Code's hook system.

Usage -- defining a haiv hook point (in an haiv_hook_points.py module):

    from haiv.haiv_hooks import HaivHookPoint

    @dataclass
    class WorktreeCreated:
        worktree_path: Path
        mind_name: str

    AFTER_WORKTREE_CREATED = HaivHookPoint[WorktreeCreated, None](
        guid="haiv-core:minds:stage:after-worktree-created"
    )

Usage -- emitting (in a command with enable_haiv_hooks=True):

    from haiv_core.haiv_hook_points import AFTER_WORKTREE_CREATED, WorktreeCreated

    AFTER_WORKTREE_CREATED.emit(WorktreeCreated(...), ctx)

Usage -- handling (in an haiv_hook_handlers/ module):

    from haiv.haiv_hooks import haiv_hook
    from haiv_core.haiv_hook_points import AFTER_WORKTREE_CREATED, WorktreeCreated

    @haiv_hook(AFTER_WORKTREE_CREATED, description="Syncing packages")
    def sync_packages(req: WorktreeCreated, ctx: cmd.Ctx) -> None:
        ...

haiv hook modules are discovered at CLI startup when the command declares
enable_haiv_hooks=True. Discovery follows the package hierarchy:
core -> project -> user. All handlers run (accumulate).
Exceptions from handlers may propagate to the caller.
This is by design. Callers may choose to guard against this
or allow hooks to halt execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Protocol, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from haiv import cmd

TReq = TypeVar("TReq")
TRes = TypeVar("TRes")


class HaivHookHandler(Protocol):
    """A callable that has been marked as a haiv hook handler.

    Created by the ``@haiv_hook`` decorator, which stamps ``_haiv_hook_guid``
    and ``_haiv_hook_description`` on the function. ``_haiv_hook_source`` is
    stamped later during ``configure_haiv_hooks()`` when the file path is known.

    Used by ``collect_haiv_handlers()`` during discovery.
    """

    _haiv_hook_guid: str
    _haiv_hook_description: str
    _haiv_hook_source: str

    def __call__(self, req: Any, ctx: Any) -> Any: ...


@dataclass
class HaivHookPoint(Generic[TReq, TRes]):
    """A typed extension point that commands can emit and haiv hooks can subscribe to.

    Type parameters:
        TReq: The request type passed to handlers.
        TRes: The response type returned by handlers (use None for fire-and-forget).

    Attributes:
        guid: Unique identifier (e.g., "haiv-core:minds:stage:after-worktree-created").
    """

    guid: str

    def emit(self, request: TReq, ctx: cmd.Ctx) -> list[TRes]:
        """Emit this haiv hook point, calling all registered handlers.

        Resolves the HaivHookRegistry from ctx._haiv_hook_registry. Raises if haiv hooks
        are not enabled for the current command (enable_haiv_hooks=True).

        Args:
            request: The event data to pass to handlers.
            ctx: Command context (paths, settings, git, etc.).

        Returns:
            List of results from each handler.
        """
        registry = ctx._haiv_hook_registry
        if registry is None:
            raise RuntimeError(
                "haiv hooks not enabled for this command. "
                "Add enable_haiv_hooks=True to the command definition."
            )
        return registry.emit(self.guid, request, ctx)


def haiv_hook(
    point: HaivHookPoint[TReq, TRes],
    *,
    description: str,
) -> Callable[[Callable[..., TRes]], HaivHookHandler]:
    """Decorator to mark a function as a haiv hook handler.

    Sets ``_haiv_hook_guid`` and ``_haiv_hook_description`` on the function for
    later collection by collect_haiv_handlers(). Does not register immediately --
    registration happens at CLI startup during configure_haiv_hooks().

    Handler signature: (request: TReq, ctx: cmd.Ctx) -> TRes

    Example::

        @haiv_hook(AFTER_WORKTREE_CREATED, description="Syncing packages")
        def sync_packages(req: WorktreeCreated, ctx: cmd.Ctx) -> None:
            run_uv_sync(req.worktree_path)
    """

    def decorator(fn: Callable[..., TRes]) -> HaivHookHandler:
        fn._haiv_hook_guid = point.guid  # type: ignore[attr-defined]
        fn._haiv_hook_description = description  # type: ignore[attr-defined]
        return fn  # type: ignore[return-value]

    return decorator
