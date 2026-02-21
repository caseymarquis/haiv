"""mg minds {mind} prompt - Send a message to a running mind.

Injects text into the mind's terminal pane. The message is submitted
as user input, so the mind receives it as if the user typed it.
"""

from __future__ import annotations

import os
import time

from mg import cmd
from mg._infrastructure.env import MG_MIND
from mg.errors import CommandError
from mg.helpers.minds import Mind


def define() -> cmd.Def:
    return cmd.Def(
        description="Send a message to a running mind",
        flags=[
            cmd.Flag("with", type=str, description="Message to send"),
            cmd.Flag("as", type=str, min_args=0, max_args=1, description="Who is speaking"),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    mind = ctx.args.get_one("mind", type=Mind)

    if not ctx.args.has("with"):
        raise CommandError("--with is required\n\n  mg minds <mind> prompt --with \"message\"")

    message = ctx.args.get_one("with")
    sender = ctx.args.get_one("as") if ctx.args.has("as") else os.environ.get(MG_MIND)

    if sender:
        message = f"<mg>Message from {sender}: {message}</mg>"

    if not ctx.tui.mind_try_send_text(mind.name, message, submit=False):
        raise CommandError(f"No pane found for mind: {mind.name}")

    ctx.print(f"Sent to {mind.name}.")
    ctx.tui.mind_launch(mind.name)
