"""Show status of all tmux windows in the haiv session."""

import subprocess

from haiv import cmd
from haiv.errors import CommandError

SESSION_NAME = "haiv"
DEFAULT_LINES = 8
DETAILED_LINES = 30


def define() -> cmd.Def:
    """Define the windows command."""
    return cmd.Def(
        description="Show status of tmux windows in haiv session",
        flags=[
            cmd.Flag("window", min_args=0),
            cmd.Flag("lines", min_args=0),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    """Execute the windows command."""
    specific_window = ctx.args.get_one("window", default_value=None)
    lines_arg = ctx.args.get_one("lines", default_value=None)

    # Check if session exists
    if not _session_exists():
        raise CommandError(
            f"tmux session '{SESSION_NAME}' not found.\n\n"
            f"Start it with: tmux new-session -s {SESSION_NAME}"
        )

    windows = _get_windows()

    if specific_window:
        # Show detailed output for one window
        matching = [w for w in windows if w[0] == specific_window or w[1] == specific_window]
        if not matching:
            available = ", ".join(f"{idx}:{name}" for idx, name in windows)
            raise CommandError(
                f"Window '{specific_window}' not found.\n\n"
                f"Available: {available}"
            )
        idx, name = matching[0]
        lines = int(lines_arg) if lines_arg else DETAILED_LINES
        content = _capture_pane(idx, lines=lines)
        ctx.print(f"=== {idx}:{name} ===")
        ctx.print(content)
    else:
        # Show summary of all windows
        lines = int(lines_arg) if lines_arg else DEFAULT_LINES
        for idx, name in windows:
            content = _capture_pane(idx, lines=lines)
            ctx.print(f"=== {idx}:{name} ===")
            if content:
                ctx.print(content)
            ctx.print()


def _session_exists() -> bool:
    """Check if the tmux session exists."""
    result = subprocess.run(
        ["tmux", "has-session", "-t", SESSION_NAME],
        capture_output=True,
    )
    return result.returncode == 0


def _get_windows() -> list[tuple[str, str]]:
    """Get list of (index, name) for all windows in session."""
    result = subprocess.run(
        ["tmux", "list-windows", "-t", SESSION_NAME, "-F", "#{window_index}:#{window_name}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []

    windows = []
    for line in result.stdout.strip().split("\n"):
        if ":" in line:
            idx, name = line.split(":", 1)
            windows.append((idx, name))
    return windows


def _capture_pane(window_index: str, lines: int = DEFAULT_LINES) -> str:
    """Capture the last N non-blank lines from a window's pane."""
    capture = subprocess.run(
        ["tmux", "capture-pane", "-t", f"{SESSION_NAME}:{window_index}", "-p"],
        capture_output=True,
        text=True,
    )
    if capture.returncode != 0:
        return "(capture failed)"

    # Filter to non-blank lines, take last N
    all_lines = capture.stdout.rstrip().split("\n")
    non_blank = [line for line in all_lines if line.strip()]
    last_n = non_blank[-lines:] if len(non_blank) > lines else non_blank

    return "\n".join(last_n)
