"""hv fix {mind} - Recover a frozen Claude session.

Step-based recovery workflow:
- hv fix <mind>: Launch recovery Claude
- hv fix <mind> --stage discover: Show diagnostics
- hv fix <mind> --stage capture: Capture pane content
- hv fix <mind> --stage kill: Kill the frozen window
- hv fix <mind> --stage resume: Resume the session
- hv fix <mind> --stage restore: Instructions for restoring captured input
"""

from __future__ import annotations

import os
import subprocess

from haiv import cmd
from haiv.errors import CommandError
from haiv.helpers.minds import Mind
from haiv.helpers.sessions import get_most_recent_session_for_mind
from haiv.wrappers.tmux import Tmux


def define() -> cmd.Def:
    return cmd.Def(
        description="Recover a frozen Claude session",
        flags=[
            cmd.Flag("stage", type=str, description="Recovery stage"),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    mind = ctx.args.get_one("mind", type=Mind)

    if not ctx.args.has("stage"):
        _launch_recovery_claude(ctx, mind)
        return

    stage = ctx.args.get_one("stage")

    match stage:
        case "discover":
            _step_discover(ctx, mind)
        case "capture":
            _step_capture(ctx, mind)
        case "kill":
            _step_kill(ctx, mind)
        case "resume":
            _step_resume(ctx, mind)
        case "restore":
            _step_restore(ctx, mind)
        case _:
            raise CommandError(f"Unknown stage: {stage}")


def _step_discover(ctx: cmd.Ctx, mind: Mind) -> None:
    """Step 1: Show diagnostics."""
    tmux = Tmux(ctx.paths.root, quiet=True)
    sessions_file = ctx.paths.user.sessions_file

    ctx.print(f"# Recovery Diagnostics: {mind.name}\n")

    # Check tmux session
    has_session = tmux.has_session()
    ctx.print(f"Tmux session '{tmux.session}': {'exists' if has_session else 'NOT FOUND'}")

    # Check window
    has_window = False
    if has_session:
        has_window = tmux.has_window(mind.name)
        ctx.print(f"Window '{mind.name}': {'exists' if has_window else 'NOT FOUND'}")
    ctx.print()

    # Check session tracking
    session = get_most_recent_session_for_mind(sessions_file, mind.name)
    if session:
        ctx.print("## Tracked Session")
        ctx.print(f"  short_id: {session.short_id}")
        ctx.print(f"  uuid: {session.id}")
        ctx.print(f"  task: {session.task}")
    else:
        ctx.print("## Tracked Session")
        ctx.print("  None found (session may have started without --task)")
    ctx.print()

    # Next step guidance
    ctx.print("## Next Step")
    if not has_session:
        ctx.print("No tmux session found. Nothing to recover.")
    elif not has_window:
        ctx.print("Window already closed.")
        if session:
            ctx.print(f"Run: hv fix {mind.name} --stage resume")
        else:
            ctx.print(f"Start fresh: hv start {mind.name} --tmux --task \"<task>\"")
    else:
        ctx.print(f"Run: hv fix {mind.name} --stage capture")


def _step_capture(ctx: cmd.Ctx, mind: Mind) -> None:
    """Step 2: Capture pane content."""
    tmux = Tmux(ctx.paths.root, quiet=True)

    if not tmux.has_window(mind.name):
        raise CommandError(f"Window '{mind.name}' not found. It may already be closed.")

    ctx.print(f"# Capturing pane: {mind.name}\n")

    # Capture with scrollback
    target = f"{tmux.session}:{mind.name}"
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", target, "-p", "-S", "-500"],
        capture_output=True,
        text=True,
    )
    pane_content = result.stdout

    ctx.print("## Pane Content (last 500 lines of scrollback)")
    ctx.print("```")
    ctx.print(pane_content)
    ctx.print("```")
    ctx.print()

    ctx.print("## Your Task")
    ctx.print("Look for user input after the '> ' prompt near the end.")
    ctx.print("If you find pending input, save it - you'll restore it later.")
    ctx.print()
    ctx.print("## Next Step")
    ctx.print(f"Run: hv fix {mind.name} --stage kill")


def _step_kill(ctx: cmd.Ctx, mind: Mind) -> None:
    """Step 3: Kill the frozen window."""
    tmux = Tmux(ctx.paths.root, quiet=True)

    if not tmux.has_window(mind.name):
        ctx.print(f"Window '{mind.name}' already closed.")
    else:
        ctx.print(f"Killing window: {mind.name}")
        tmux.kill_window(mind.name)
        ctx.print("Done.")
    ctx.print()

    ctx.print("## Next Step")
    ctx.print(f"Run: hv fix {mind.name} --stage resume")


def _step_resume(ctx: cmd.Ctx, mind: Mind) -> None:
    """Step 4: Resume the session."""
    tmux = Tmux(ctx.paths.root, quiet=True)
    sessions_file = ctx.paths.user.sessions_file
    session = get_most_recent_session_for_mind(sessions_file, mind.name)

    if not session:
        ctx.print("No tracked session found.")
        ctx.print(f"Start fresh: hv start {mind.name} --tmux --task \"<task>\"")
        return

    ctx.print(f"# Resuming session [{session.short_id}]: {session.task}\n")

    # Run hv start with resume
    subprocess.run([
        "hv", "start", mind.name, "--tmux", "--resume", str(session.short_id)
    ])

    ctx.print()
    ctx.print("## Next Step")
    ctx.print("Clear the tmux scrollback buffer to prevent context overload:")
    ctx.print()
    ctx.print(f"  tmux clear-history -t {tmux.session}:{mind.name}")
    ctx.print()
    ctx.print("The user will approve this command when the session has fully loaded.")
    ctx.print()
    ctx.print("## Then (if you captured pending input)")
    ctx.print(f"Run: hv fix {mind.name} --stage restore")
    ctx.print()
    ctx.print("If no pending input was captured, recovery is complete after clearing the buffer.")


def _step_restore(ctx: cmd.Ctx, mind: Mind) -> None:
    """Step 5: Restore captured input."""
    tmux = Tmux(ctx.paths.root, quiet=True)

    if not tmux.has_window(mind.name):
        raise CommandError(f"Window '{mind.name}' not found. Resume the session first.")

    ctx.print(f"# Restore Input: {mind.name}\n")

    target = f"{tmux.session}:{mind.name}"

    ctx.print("## Your Task")
    ctx.print("YOU must now send the captured user input to the restored session.")
    ctx.print("Do NOT ask the user to do this - execute the command yourself.")
    ctx.print()
    ctx.print("Run this command (replacing <captured input> with the actual text):")
    ctx.print()
    ctx.print(f"  tmux send-keys -t {target} '<captured input>' Enter")
    ctx.print()
    ctx.print("For multi-line input, you may need to send it in parts.")
    ctx.print()
    ctx.print("## Recovery Complete")
    ctx.print("After you send the input, recovery is complete.")


def _launch_recovery_claude(ctx: cmd.Ctx, mind: Mind) -> None:
    """Launch a recovery Claude instance."""
    if os.environ.get("TMUX"):
        raise CommandError(
            "Run 'hv fix' from outside tmux.\n"
            "The recovery Claude needs to operate on tmux externally."
        )

    tmux = Tmux(ctx.paths.root, quiet=True)
    target = f"{tmux.session}:{mind.name}"

    # Build the allowlist - stage commands plus tmux send-keys for restore
    allowed_tools = [
        f"Bash(hv fix {mind.name} --stage *)",
        f"Bash(tmux send-keys -t {target} *)",
    ]

    # Initial prompt
    prompt = (
        f"You are recovering a frozen Claude session for mind '{mind.name}'. "
        f"Run `hv fix {mind.name} --stage discover` to begin. "
        "Follow the 'Next Step' instructions after each command. "
        "Proceed autonomously. Only stop if you encounter a problem."
    )

    os.system("clear")

    claude_args = ["claude", prompt]
    for tool in allowed_tools:
        claude_args.extend(["--allowedTools", tool])

    os.execvp("claude", claude_args)
