"""haiv hook system for haiv commands.

Commands define haiv hook points (typed extension points) and emit them during
execution. Other packages subscribe by placing handler modules in their
hv_hook_handlers/ directory.

This module is distinct from Claude hooks (claude_hooks/), which integrate
with Claude Code's hook system.

Usage -- defining a haiv hook point (in an hv_hook_points.py module):

    from haiv.hv_hooks import HvHookPoint

    @dataclass
    class WorktreeCreated:
        worktree_path: Path
        mind_name: str

    AFTER_WORKTREE_CREATED = HvHookPoint[WorktreeCreated, None](
        guid="haiv-core:minds:stage:after-worktree-created"
    )

Usage -- emitting (in a command with enable_hv_hooks=True):

    from haiv_core.hv_hook_points import AFTER_WORKTREE_CREATED, WorktreeCreated

    AFTER_WORKTREE_CREATED.emit(WorktreeCreated(...), ctx)

Usage -- handling (in an hv_hook_handlers/ module):

    from haiv.hv_hooks import hv_hook
    from haiv_core.hv_hook_points import AFTER_WORKTREE_CREATED, WorktreeCreated

    @hv_hook(AFTER_WORKTREE_CREATED, description="Syncing packages")
    def sync_packages(req: WorktreeCreated, ctx: cmd.Ctx) -> None:
        ...

haiv hook modules are discovered at CLI startup when the command declares
enable_hv_hooks=True. Discovery follows the package hierarchy:
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


class HvHookHandler(Protocol):
    """A callable that has been marked as a haiv hook handler.

    Created by the ``@hv_hook`` decorator, which stamps ``_hv_hook_guid``
    and ``_hv_hook_description`` on the function. ``_hv_hook_source`` is
    stamped later during ``configure_hv_hooks()`` when the file path is known.

    Used by ``collect_hv_handlers()`` during discovery.
    """

    _hv_hook_guid: str
    _hv_hook_description: str
    _hv_hook_source: str

    def __call__(self, req: Any, ctx: Any) -> Any: ...


@dataclass
class HvHookPoint(Generic[TReq, TRes]):
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

        Resolves the HvHookRegistry from ctx._hv_hook_registry. Raises if haiv hooks
        are not enabled for the current command (enable_hv_hooks=True).

        Args:
            request: The event data to pass to handlers.
            ctx: Command context (paths, settings, git, etc.).

        Returns:
            List of results from each handler.
        """
        registry = ctx._hv_hook_registry
        if registry is None:
            raise RuntimeError(
                "haiv hooks not enabled for this command. "
                "Add enable_hv_hooks=True to the command definition."
            )
        return registry.emit(self.guid, request, ctx)


def hv_hook(
    point: HvHookPoint[TReq, TRes],
    *,
    description: str,
) -> Callable[[Callable[..., TRes]], HvHookHandler]:
    """Decorator to mark a function as a haiv hook handler.

    Sets ``_hv_hook_guid`` and ``_hv_hook_description`` on the function for
    later collection by collect_hv_handlers(). Does not register immediately --
    registration happens at CLI startup during configure_hv_hooks().

    Handler signature: (request: TReq, ctx: cmd.Ctx) -> TRes

    Example::

        @hv_hook(AFTER_WORKTREE_CREATED, description="Syncing packages")
        def sync_packages(req: WorktreeCreated, ctx: cmd.Ctx) -> None:
            run_uv_sync(req.worktree_path)
    """

    def decorator(fn: Callable[..., TRes]) -> HvHookHandler:
        fn._hv_hook_guid = point.guid  # type: ignore[attr-defined]
        fn._hv_hook_description = description  # type: ignore[attr-defined]
        return fn  # type: ignore[return-value]

    return decorator
