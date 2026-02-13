"""Hook system for mg commands.

Commands define hook points (typed extension points) and emit them during
execution. Other packages subscribe by placing handler modules in their
hooks/ directory.

Usage -- defining a hook point (in an events module):

    from mg.hooks import HookPoint

    @dataclass
    class WorktreeCreated:
        worktree_path: Path
        mind_name: str

    AFTER_WORKTREE_CREATED = HookPoint[WorktreeCreated, None](
        guid="mg-core:minds:stage:after-worktree-created"
    )

Usage -- emitting (in a command):

    from mg_core.events import AFTER_WORKTREE_CREATED, WorktreeCreated

    AFTER_WORKTREE_CREATED.emit(WorktreeCreated(...), ctx)

Usage -- handling (in a hooks/ module):

    from mg.hooks import hook
    from mg_core.events import AFTER_WORKTREE_CREATED, WorktreeCreated

    @hook(AFTER_WORKTREE_CREATED)
    def sync_packages(req: WorktreeCreated, ctx: cmd.Ctx) -> None:
        ...

Hook modules are discovered lazily on first emit() call, following the
package hierarchy: core -> project -> user. All handlers run (accumulate).
Exceptions from handlers propagate to the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar, TYPE_CHECKING

from mg._infrastructure.hooks import _registry

if TYPE_CHECKING:
    from mg import cmd

TReq = TypeVar("TReq")
TRes = TypeVar("TRes")


@dataclass
class HookPoint(Generic[TReq, TRes]):
    """A typed extension point that commands can emit and hooks can subscribe to.

    Type parameters:
        TReq: The request type passed to handlers.
        TRes: The response type returned by handlers (use None for fire-and-forget).

    Attributes:
        guid: Unique identifier (e.g., "mg-core:minds:stage:after-worktree-created").
    """

    guid: str

    def emit(self, request: TReq, ctx: cmd.Ctx) -> list[TRes]:
        """Emit this hook point, calling all registered handlers.

        Triggers lazy discovery/loading of hook modules on first call.
        Handlers are called in package order: core -> project -> user.
        Exceptions from handlers propagate to the caller.

        Args:
            request: The event data to pass to handlers.
            ctx: Command context (paths, settings, git, etc.).

        Returns:
            List of results from each handler.
        """
        ...


def hook(
    point: HookPoint[TReq, TRes],
) -> Callable[[Callable[..., TRes]], Callable[..., TRes]]:
    """Decorator to register a handler for a hook point.

    Handler signature: (request: TReq, ctx: cmd.Ctx) -> TRes

    Example::

        @hook(AFTER_WORKTREE_CREATED)
        def sync_packages(req: WorktreeCreated, ctx: cmd.Ctx) -> None:
            run_uv_sync(req.worktree_path)
    """
    ...


def configure(pkg_roots: list[Path]) -> None:
    """Store package roots for lazy hook discovery.

    Called by the CLI at startup. Does not load any hook modules --
    that happens lazily on first emit() call.

    Args:
        pkg_roots: Package roots in discovery order (core first, user last).
    """
    ...
