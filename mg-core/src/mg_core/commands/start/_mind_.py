"""mg start {mind} - Launch a mind.

Puts the mind in the hud — switching to a parked pane if one exists,
or launching a new pane with Claude Code if not.
"""

from __future__ import annotations

import os

from mg import cmd
from mg._infrastructure.env import MG_SESSION
from mg.helpers.minds import Mind


def define() -> cmd.Def:
    return cmd.Def(
        description="Launch a mind",
        flags=[
            cmd.Flag("task", type=str, description="Task description (creates session if needed)"),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    mind = ctx.args.get_one("mind", type=Mind)
    task = ctx.args.get_one("task") if ctx.args.has("task") else None
    parent = os.environ.get(MG_SESSION, "")

    ctx.tui.mind_launch(mind.name, task=task, parent=parent)
