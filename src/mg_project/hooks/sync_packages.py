"""Auto-run uv sync after worktree creation.

When a new worktree is created by ``mg minds stage``, this hook discovers
Python packages in the worktree and runs ``uv sync`` for each one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mg.hooks import hook
from mg_core.events import AFTER_WORKTREE_CREATED, WorktreeCreated

if TYPE_CHECKING:
    from mg import cmd


@hook(AFTER_WORKTREE_CREATED)
def sync_packages(req: WorktreeCreated, ctx: cmd.Ctx) -> None:
    """Find pyproject.toml files in the worktree and run uv sync for each."""
    ...
