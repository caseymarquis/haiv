"""Auto-run uv sync after worktree creation (mg hook handler).

When a new worktree is created by ``mg minds stage``, this mg hook handler
runs ``uv sync --all-packages`` at the worktree root to install dependencies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mg.mg_hooks import mg_hook
from mg_core.mg_hook_points import AFTER_WORKTREE_CREATED, WorktreeCreated

if TYPE_CHECKING:
    from mg import cmd


@mg_hook(AFTER_WORKTREE_CREATED, description="Syncing packages")
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
