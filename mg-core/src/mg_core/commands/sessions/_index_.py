"""mg sessions - List active sessions.

Shows all tracked sessions across minds with their short_id, mind, task, and start time.
Displays parent-child delegation chains as a tree.
"""

from __future__ import annotations

from mg import cmd
from mg.helpers.sessions import build_session_tree, load_sessions
from mg.helpers.utils.trees import render_tree


def define() -> cmd.Def:
    return cmd.Def(description="List active sessions")


def _format_session(short_id: int | str, mind: str, task: str) -> str:
    return f"[{short_id}] {mind}: {task}"


def execute(ctx: cmd.Ctx) -> None:
    sessions = load_sessions(ctx.paths.user.sessions_file)

    if not sessions:
        ctx.print("No active sessions.")
        return

    tree = build_session_tree(sessions)
    lines = render_tree(tree, lambda s: _format_session(s.short_id, s.mind, s.task))

    ctx.print("Active sessions:\n")
    for line in lines:
        ctx.print(f"  {line}" if line else "")
    ctx.print()
    ctx.print(f"  {_format_session('id', 'mind', 'task')}")
