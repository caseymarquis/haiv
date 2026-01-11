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
    find_session,
    get_most_recent_session,
)


def define() -> cmd.Def:
    return cmd.Def(
        description="Launch a mind",
        flags=[
            cmd.Flag("tmux", type=bool, description="Start in a new tmux window"),
            cmd.Flag("task", type=str, description="Task description for new session"),
            cmd.Flag(
                "resume",
                type=str,
                min_args=0,
                max_args=1,
                description="Resume session (most recent if no ID)",
            ),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    mind = ctx.args.get_one("mind", type=Mind)
    use_tmux = ctx.args.has("tmux")
    has_task = ctx.args.has("task")
    has_resume = ctx.args.has("resume")

    # Validate: --task and --resume require --tmux
    if (has_task or has_resume) and not use_tmux:
        raise CommandError("--task and --resume require --tmux")

    # Validate: --task and --resume are mutually exclusive
    if has_task and has_resume:
        raise CommandError("Cannot use --task and --resume together")

    if use_tmux:
        _start_in_tmux(ctx, mind)
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
    # (so the shell inherits the vars when it spawns)
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
        # Resume existing session
        resume_values = ctx.args.get_list("resume", default_value=[])
        if resume_values:
            session = find_session(sessions_file, resume_values[0])
        else:
            session = get_most_recent_session(sessions_file)

        if not session:
            raise CommandError("No session found to resume")

        window.send_keys(f'claude "{prompt}" --resume {session.id} {allowed}')

    elif ctx.args.has("task"):
        # Start new tracked session
        task = ctx.args.get_one("task")
        session = create_session(sessions_file, task, mind.name)

        window.send_keys(f'claude "{prompt}" --session-id {session.id} {allowed}')

    else:
        # Untracked session (existing behavior)
        window.send_keys(f'claude "{prompt}" {allowed}')
