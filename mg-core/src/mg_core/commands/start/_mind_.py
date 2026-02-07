"""mg start {mind} - Launch a mind.

Finds or creates a session, transitions it to started, and launches
Claude Code in the hud's mind pane.
"""

from __future__ import annotations

import os
import shlex
import uuid

from mg import cmd
from mg._infrastructure.env import MG_MIND, MG_ROOT, MG_SESSION
from mg.errors import CommandError
from mg.helpers.minds import Mind
from mg.helpers.sessions import (
    Session,
    create_session,
    get_most_recent_session_for_mind,
    update_session,
)


def define() -> cmd.Def:
    return cmd.Def(
        description="Launch a mind",
        flags=[
            cmd.Flag("task", type=str, description="Task description (required if no staged session)"),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    mind = ctx.args.get_one("mind", type=Mind)
    sessions_file = ctx.paths.user.sessions_file

    # Find existing session or create one
    session = get_most_recent_session_for_mind(sessions_file, mind.name)

    if session is not None:
        # Transition staged → started, generate new claude_session_id
        claude_session_id = str(uuid.uuid4())

        def transition(s: Session) -> None:
            s.status = "started"
            s.claude_session_id = claude_session_id

        session = update_session(sessions_file, session.id, transition)
    elif ctx.args.has("task"):
        # Quick-start: create session directly as started
        task = ctx.args.get_one("task")
        parent = os.environ.get(MG_SESSION, "")
        claude_session_id = str(uuid.uuid4())
        session = create_session(
            sessions_file,
            task,
            mind.name,
            status="started",
            parent=parent,
        )

        def set_claude_id(s: Session) -> None:
            s.claude_session_id = claude_session_id

        session = update_session(sessions_file, session.id, set_claude_id)
    else:
        raise CommandError(
            "No staged session for this mind.\n\n"
            "  Stage first:  mg minds stage --task \"description\"\n"
            "  Or quick-start:  mg start <mind> --task \"description\""
        )

    # Push to TUI
    ctx.tui.sessions_refresh()

    # Build claude command
    prompt = f"Run `mg become {mind.name}`"
    allowed = f"Bash(mg become {mind.name})"
    claude_cmd = (
        f"claude {shlex.quote(prompt)} "
        f"--session-id {shlex.quote(session.claude_session_id)} "
        f"--allowedTools {shlex.quote(allowed)}"
    )

    # Launch in mind pane
    ctx.tui.launch_in_mind_pane(
        env={
            MG_MIND: mind.name,
            MG_SESSION: session.id,
            MG_ROOT: str(ctx.paths.root),
        },
        commands=[claude_cmd],
    )
