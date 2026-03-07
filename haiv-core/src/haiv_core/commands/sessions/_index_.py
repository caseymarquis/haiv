"""hv sessions - List active sessions.

Shows all tracked sessions across minds with their short_id, mind, task, and start time.
Displays parent-child delegation chains as a tree.
"""

from __future__ import annotations

from haiv import cmd
from haiv.helpers.sessions import Session, build_session_tree, load_sessions
from haiv.helpers.utils.trees import render_tree
from haiv.wrappers.git import BranchStats, Git


def define() -> cmd.Def:
    return cmd.Def(description="List active sessions")


def _format_session(s: Session, stats: BranchStats) -> str:
    return f"[{s.short_id}] {s.mind}: {s.task}  {stats.format()}"


def execute(ctx: cmd.Ctx) -> None:
    sessions = load_sessions(ctx.paths.user.sessions_file)

    if not sessions:
        ctx.print("No active sessions.")
        return

    git = Git(ctx.paths.root, quiet=True)
    stats_by_id: dict[str, BranchStats] = {}
    for s in sessions:
        if s.branch:
            try:
                stats_by_id[s.id] = git.branch_stats(s.branch, s.base_branch)
            except Exception:
                stats_by_id[s.id] = BranchStats()
        else:
            stats_by_id[s.id] = BranchStats()

    tree = build_session_tree(sessions)
    lines = render_tree(tree, lambda s: _format_session(s, stats_by_id.get(s.id, BranchStats())))

    ctx.print("Active sessions:\n")
    for line in lines:
        ctx.print(f"  {line}" if line else "")
    ctx.print()
