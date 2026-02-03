"""mg start {mind} - Launch a mind.

Starts Claude Code with the mind's startup context.
"""

from __future__ import annotations

import os

from mg import cmd
from mg.errors import CommandError
from mg.wrappers.tmux import Tmux

from mg.helpers.minds import Mind
from mg.helpers.sessions import (
    create_session,
    get_most_recent_session_for_mind,
    get_session,
)


def define() -> cmd.Def:
    return cmd.Def(
        description="Launch a mind",
        flags=[
            cmd.Flag("tmux", type=bool, description="Start in a new tmux window"),
            cmd.Flag("tui", type=bool, description="Start as a TUI session"),
            cmd.Flag("task", type=str, description="Task description for new session"),
            cmd.Flag(
                "resume",
                type=str,
                description="Resume session by short_id or UUID",
            ),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    mind = ctx.args.get_one("mind", type=Mind)
    use_tmux = ctx.args.has("tmux")
    use_tui = ctx.args.has("tui")
    has_task = ctx.args.has("task")
    has_resume = ctx.args.has("resume")

    # Validate: --tmux and --tui are mutually exclusive
    if use_tmux and use_tui:
        raise CommandError("Cannot use --tmux and --tui together")

    # Validate: --task and --resume require --tmux or --tui
    if (has_task or has_resume) and not (use_tmux or use_tui):
        raise CommandError("--task and --resume require --tmux or --tui")

    # Validate: --task and --resume are mutually exclusive
    if has_task and has_resume:
        raise CommandError("Cannot use --task and --resume together")

    if use_tmux:
        _start_in_tmux(ctx, mind)
    elif use_tui:
        _start_in_tui(ctx, mind)
    else:
        _start_in_terminal(ctx, mind)


def _start_in_terminal(ctx: cmd.Ctx, mind: Mind) -> None:
    """Start claude in the current terminal."""
    # Set MG_MIND (required) - inherited by exec'd process
    os.environ["MG_MIND"] = mind.name

    # Set MG_ROOT as optimization if not already set (auto-discovery works without it)
    if not os.environ.get("MG_ROOT"):
        os.environ["MG_ROOT"] = str(ctx.paths.root)

    # Clear terminal
    os.system("clear")

    # Replace this process with claude (no return on success)
    # Prompt must come before flags
    prompt = f"Run `mg become {mind.name}`"
    allowed = f"Bash(mg become {mind.name})"
    os.execlp("claude", "claude", prompt, "--allowedTools", allowed)


def _start_in_tmux(ctx: cmd.Ctx, mind: Mind) -> None:
    """Start claude in a new tmux window."""
    tmux = Tmux(ctx.paths.root)

    # Set environment in tmux session BEFORE creating window
    # (so the shell inherits the vars when it assigns)
    tmux.setenv("MG_MIND", mind.name)
    tmux.setenv("MG_ROOT", str(ctx.paths.root))

    # Get or create window for this mind
    window = tmux.get_window(mind.name)

    # Clear terminal
    window.send_keys("clear")

    # Build claude command with allowlist for mg become
    # Prompt must come before flags
    prompt = f"Run `mg become {mind.name}`"
    allowed = f'--allowedTools "Bash(mg become {mind.name})"'

    sessions_file = ctx.paths.user.sessions_file

    if ctx.args.has("resume"):
        # Resume existing session - no prompt needed, context is restored
        session_id = ctx.args.get_one("resume")
        session = get_session(sessions_file, session_id)

        if not session:
            raise CommandError(f"Session not found: {session_id}")

        window.send_keys(f"claude --resume {session.id} {allowed}")

    elif ctx.args.has("task"):
        # Start new tracked session
        task = ctx.args.get_one("task")
        session = create_session(sessions_file, task, mind.name)

        window.send_keys(f'claude "{prompt}" --session-id {session.id} {allowed}')

    else:
        # Untracked session (existing behavior)
        window.send_keys(f'claude "{prompt}" {allowed}')


def _start_in_tui(ctx: cmd.Ctx, mind: Mind) -> None:
    """Start a mind as a TUI session."""
    sessions_file = ctx.paths.user.sessions_file

    # Find or create session for this mind
    session = get_most_recent_session_for_mind(sessions_file, mind.name)

    if not session:
        task = ctx.args.get_one("task") if ctx.args.has("task") else "No Task"
        session = create_session(sessions_file, task, mind.name)

    # Set environment
    os.environ["MG_MIND"] = mind.name
    if not os.environ.get("MG_ROOT"):
        os.environ["MG_ROOT"] = str(ctx.paths.root)

    os.system("clear")

    # Replace this process with claude, bound to the session
    prompt = f"Run `mg become {mind.name}`"
    allowed = f"Bash(mg become {mind.name})"
    os.execlp(
        "claude", "claude", prompt,
        "--session-id", session.id,
        "--allowedTools", allowed,
    )
