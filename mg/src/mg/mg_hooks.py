"""mg hook system for mg commands.

Commands define mg hook points (typed extension points) and emit them during
execution. Other packages subscribe by placing handler modules in their
mg_hook_handlers/ directory.

This module is distinct from Claude hooks (claude_hooks/), which integrate
with Claude Code's hook system.

Usage -- defining an mg hook point (in an mg_hook_points.py module):

    from mg.mg_hooks import MgHookPoint

    @dataclass
    class WorktreeCreated:
        worktree_path: Path
        mind_name: str

    AFTER_WORKTREE_CREATED = MgHookPoint[WorktreeCreated, None](
        guid="mg-core:minds:stage:after-worktree-created"
    )

Usage -- emitting (in a command with enable_mg_hooks=True):

    from mg_core.mg_hook_points import AFTER_WORKTREE_CREATED, WorktreeCreated

    AFTER_WORKTREE_CREATED.emit(WorktreeCreated(...), ctx)

Usage -- handling (in an mg_hook_handlers/ module):

    from mg.mg_hooks import mg_hook
    from mg_core.mg_hook_points import AFTER_WORKTREE_CREATED, WorktreeCreated

    @mg_hook(AFTER_WORKTREE_CREATED)
    def sync_packages(req: WorktreeCreated, ctx: cmd.Ctx) -> None:
        ...

mg hook modules are discovered at CLI startup when the command declares
enable_mg_hooks=True. Discovery follows the package hierarchy:
core -> project -> user. All handlers run (accumulate).
Exceptions from handlers may propagate to the caller.
This is by design. Callers may choose to guard against this
or allow hooks to halt execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Protocol, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from mg import cmd

TReq = TypeVar("TReq")
TRes = TypeVar("TRes")


class MgHookHandler(Protocol):
    """A callable that has been marked as an mg hook handler.

    Created by the ``@mg_hook`` decorator, which stamps ``_mg_hook_guid``
    on the function. Used by ``collect_mg_handlers()`` during discovery.
    """

    _mg_hook_guid: str

    def __call__(self, req: Any, ctx: Any) -> Any: ...


@dataclass
class MgHookPoint(Generic[TReq, TRes]):
    """A typed extension point that commands can emit and mg hooks can subscribe to.

    Type parameters:
        TReq: The request type passed to handlers.
        TRes: The response type returned by handlers (use None for fire-and-forget).

    Attributes:
        guid: Unique identifier (e.g., "mg-core:minds:stage:after-worktree-created").
    """

    guid: str

    def emit(self, request: TReq, ctx: cmd.Ctx) -> list[TRes]:
        """Emit this mg hook point, calling all registered handlers.

        Resolves the MgHookRegistry from ctx._mg_hook_registry. Raises if mg hooks
        are not enabled for the current command (enable_mg_hooks=True).

        Args:
            request: The event data to pass to handlers.
            ctx: Command context (paths, settings, git, etc.).

        Returns:
            List of results from each handler.
        """
        registry = ctx._mg_hook_registry
        if registry is None:
            raise RuntimeError(
                "mg hooks not enabled for this command. "
                "Add enable_mg_hooks=True to the command definition."
            )
        return registry.emit(self.guid, request, ctx)


def mg_hook(
    point: MgHookPoint[TReq, TRes],
) -> Callable[[Callable[..., TRes]], MgHookHandler]:
    """Decorator to mark a function as an mg hook handler.

    Sets ``_mg_hook_guid`` on the function for later collection by
    collect_mg_handlers(). Does not register immediately -- registration
    happens at CLI startup during configure_mg_hooks().

    Handler signature: (request: TReq, ctx: cmd.Ctx) -> TRes

    Example::

        @mg_hook(AFTER_WORKTREE_CREATED)
        def sync_packages(req: WorktreeCreated, ctx: cmd.Ctx) -> None:
            run_uv_sync(req.worktree_path)
    """

    def decorator(fn: Callable[..., TRes]) -> MgHookHandler:
        fn._mg_hook_guid = point.guid  # type: ignore[attr-defined]
        return fn  # type: ignore[return-value]

    return decorator
