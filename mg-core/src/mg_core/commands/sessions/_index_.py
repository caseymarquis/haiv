"""mg sessions - List active sessions.

Shows all tracked sessions across minds with their short_id, mind, task, and start time.
"""

from __future__ import annotations

from mg import cmd
from mg.helpers.sessions import load_sessions


def define() -> cmd.Def:
    return cmd.Def(description="List active sessions")


def execute(ctx: cmd.Ctx) -> None:
    sessions = load_sessions(ctx.paths.user.sessions_file)

    if not sessions:
        ctx.print("No active sessions.")
        return

    ctx.print("Active sessions:\n")
    for session in sessions:
        # Format: [short_id] mind: task (started)
        started = session.started
        if hasattr(started, "strftime"):
            started_str = started.strftime("%Y-%m-%d %H:%M")
        else:
            # Handle string format from TOML
            started_str = str(started)[:16]

        ctx.print(f"  [{session.short_id}] {session.mind}: {session.task}")
        ctx.print(f"      started {started_str}")
        ctx.print()
