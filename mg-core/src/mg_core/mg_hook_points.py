"""mg hook point definitions for mg-core commands.

This file defines the mg hook points that mg-core commands emit, along with
the request/response types that handlers receive and return.

Convention
----------
Each package that emits mg hooks should have an ``mg_hook_points.py`` at its
root. This is the single source of truth for:

- **Request dataclasses** -- the data passed to handlers when a hook fires.
- **Response types** -- what handlers return (use None for fire-and-forget).
- **MgHookPoint constants** -- the named extension points that connect
  emitters to handlers.

Both the emitting command and remote handlers import from this file, so all
user-facing types live here. Keep this module lightweight -- only import from
``mg.mg_hooks`` and the standard library.

Naming
------
- Hook point constants: ``AFTER_<EVENT>`` or ``BEFORE_<EVENT>``, uppercase.
- GUIDs: ``{package}:{command-path}:{timing}-{event}``, e.g.
  ``mg-core:minds:stage:after-worktree-created``.
- Request dataclasses: named after the event, e.g. ``WorktreeCreated``.

Relationship to mg_hook_handlers/
---------------------------------
This file defines *what* can happen (hook points and their types).
The ``mg_hook_handlers/`` directory in any package defines *how to respond*
(handler functions decorated with ``@mg_hook``).

Handlers import from here::

    from mg_core.mg_hook_points import AFTER_WORKTREE_CREATED, WorktreeCreated

Example
-------
Defining a new hook point::

    @dataclass
    class BranchMerged:
        branch: str
        target: str
        worktree_path: Path

    AFTER_BRANCH_MERGED = MgHookPoint[BranchMerged, None](
        guid="mg-core:pop:after-branch-merged",
    )

Emitting from a command (requires ``enable_mg_hooks=True`` in define())::

    AFTER_BRANCH_MERGED.emit(BranchMerged(...), ctx)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mg.mg_hooks import MgHookPoint


@dataclass
class WorktreeCreated:
    """Emitted after a worktree is created by ``mg minds stage``.

    Attributes:
        worktree_path: Absolute path to the new worktree directory.
        branch: The branch name created for the worktree.
        base_branch: The branch the worktree was created from.
        mind_name: Name of the mind this worktree belongs to.
    """

    worktree_path: Path
    branch: str
    base_branch: str
    mind_name: str


AFTER_WORKTREE_CREATED = MgHookPoint[WorktreeCreated, None](
    guid="mg-core:minds:stage:after-worktree-created",
)
