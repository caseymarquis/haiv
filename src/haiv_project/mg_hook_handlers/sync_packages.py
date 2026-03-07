"""Auto-run uv sync after worktree creation (haiv hook handler).

When a new worktree is created by ``hv minds stage``, this haiv hook handler
runs ``uv sync --all-packages`` at the worktree root to install dependencies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from haiv.haiv_hooks import haiv_hook
from haiv_core.haiv_hook_points import AFTER_WORKTREE_CREATED, WorktreeCreated

if TYPE_CHECKING:
    from haiv import cmd


@haiv_hook(AFTER_WORKTREE_CREATED, description="Syncing packages")
def sync_packages(req: WorktreeCreated, ctx: cmd.Ctx) -> None:
    """Run ``uv sync --all-packages`` at the new worktree root."""
    import subprocess

    try:
        subprocess.run(
            ["uv", "sync", "--all-packages", "--quiet"],
            cwd=req.worktree_path,
            check=True,
        )
    except Exception as e:
        ctx.print(f"Warning: uv sync failed in {req.worktree_path}: {e}")
