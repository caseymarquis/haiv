"""mg start {mind} - Launch a mind.

Puts the mind in the hud — switching to a parked pane if one exists,
or launching a new pane with Claude Code if not.

With --here, skips pane management and launches Claude directly in the
current terminal.
"""

from __future__ import annotations

import os
import subprocess

from mg import cmd
from mg._infrastructure.env import MG_SESSION
from mg.helpers.minds import Mind
from mg.helpers.sessions import resolve_session
from mg.helpers.tui.helpers import build_claude_command, build_env


def define() -> cmd.Def:
    return cmd.Def(
        description="Launch a mind",
        flags=[
            cmd.Flag("task", type=str, description="Task description (creates session if needed)"),
            cmd.Flag("here", type=bool, description="Launch Claude in the current terminal"),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    mind = ctx.args.get_one("mind", type=Mind)
    task = ctx.args.get_one("task") if ctx.args.has("task") else None
    parent = os.environ.get(MG_SESSION, "")

    if ctx.args.has("here"):
        _launch_here(ctx, mind.name, task=task, parent=parent)
    else:
        ctx.tui.mind_launch(mind.name, task=task, parent=parent)


def _launch_here(
    ctx: cmd.Ctx, mind_name: str, *, task: str | None, parent: str,
) -> None:
    """Resolve a session and launch Claude in the current terminal."""
    session = resolve_session(ctx.paths.user.sessions_file, mind_name, task=task, parent=parent)
    env = build_env(mind_name, session.id, ctx.paths.root)
    claude_cmd = build_claude_command(mind_name, session.claude_session_id)

    # Set env vars in current process so Claude inherits them
    os.environ.update(env)
    subprocess.run(claude_cmd, shell=True)
