"""haiv hook point definitions for haiv-core commands.

This file defines the haiv hook points that haiv-core commands emit, along with
the request/response types that handlers receive and return.

Convention
----------
Each package that emits haiv hooks should have an ``hv_hook_points.py`` at its
root. This is the single source of truth for:

- **Request dataclasses** -- the data passed to handlers when a hook fires.
- **Response types** -- what handlers return (use None for fire-and-forget).
- **HvHookPoint constants** -- the named extension points that connect
  emitters to handlers.

Both the emitting command and remote handlers import from this file, so all
user-facing types live here. Keep this module lightweight -- only import from
``haiv.hv_hooks`` and the standard library.

Naming
------
- Hook point constants: ``AFTER_<EVENT>`` or ``BEFORE_<EVENT>``, uppercase.
- GUIDs: ``{package}:{command-path}:{timing}-{event}``, e.g.
  ``haiv-core:minds:stage:after-worktree-created``.
- Request dataclasses: named after the event, e.g. ``WorktreeCreated``.

Relationship to hv_hook_handlers/
---------------------------------
This file defines *what* can happen (hook points and their types).
The ``hv_hook_handlers/`` directory in any package defines *how to respond*
(handler functions decorated with ``@hv_hook``).

Handlers import from here::

    from haiv_core.hv_hook_points import AFTER_WORKTREE_CREATED, WorktreeCreated

Example
-------
Defining a new hook point::

    @dataclass
    class BranchMerged:
        branch: str
        target: str
        worktree_path: Path

    AFTER_BRANCH_MERGED = HvHookPoint[BranchMerged, None](
        guid="haiv-core:pop:after-branch-merged",
    )

Emitting from a command (requires ``enable_hv_hooks=True`` in define())::

    AFTER_BRANCH_MERGED.emit(BranchMerged(...), ctx)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from haiv.hv_hooks import HvHookPoint


@dataclass
class WorktreeCreated:
    """Emitted after a worktree is created by ``hv minds stage``.

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


AFTER_WORKTREE_CREATED = HvHookPoint[WorktreeCreated, None](
    guid="haiv-core:minds:stage:after-worktree-created",
)
