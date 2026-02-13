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
from typing import Callable, Generic, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from mg import cmd

TReq = TypeVar("TReq")
TRes = TypeVar("TRes")


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
        ...


def mg_hook(
    point: MgHookPoint[TReq, TRes],
) -> Callable[[Callable[..., TRes]], Callable[..., TRes]]:
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
    ...
