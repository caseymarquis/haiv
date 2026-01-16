"""mg sessions {id} remove - Remove a session.

Removes a session from the sessions file by short_id or UUID.
"""

from __future__ import annotations

from mg import cmd
from mg.helpers.sessions import Session, remove_session


def define() -> cmd.Def:
    return cmd.Def(description="Remove a session")


def execute(ctx: cmd.Ctx) -> None:
    session = ctx.args.get_one("session", type=Session)

    # Remove the session
    removed = remove_session(ctx.paths.user.sessions_file, session.id)

    if removed:
        ctx.print(f"Removed session [{session.short_id}]: {session.task}")
    else:
        ctx.print(f"Session not found: {session.id}")
