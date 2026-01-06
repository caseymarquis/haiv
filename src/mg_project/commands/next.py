"""Switch to the next idle mind in the mind-games tmux session."""

import subprocess

from mg import cmd
from mg.errors import CommandError

SESSION_NAME = "mind-games"
CAPTURE_LINES = 50


def define() -> cmd.Def:
    """Define the next command."""
    return cmd.Def(
        description="Switch to the next idle mind",
        flags=[
            cmd.Flag("reverse", type=bool),
        ],
    )


def execute(ctx: cmd.Ctx) -> None:
    """Execute the next command."""
    reverse = ctx.args.has("reverse")

    # Ensure tmux bindings are set up
    _ensure_bindings()

    # Check if session exists
    if not _session_exists():
        raise CommandError(
            f"tmux session '{SESSION_NAME}' not found.\n\n"
            f"Start it with: tmux new-session -s {SESSION_NAME}"
        )

    current = _get_current_window()
    windows = _get_windows()

    if not windows:
        return

    # Find current window's position in the list
    current_idx = 0
    for i, (idx, _name) in enumerate(windows):
        if idx == current:
            current_idx = i
            break

    # Check windows, direction depends on reverse flag
    for offset in range(1, len(windows) + 1):
        if reverse:
            check_idx = (current_idx - offset) % len(windows)
        else:
            check_idx = (current_idx + offset) % len(windows)
        window_id, window_name = windows[check_idx]

        # Skip current window
        if window_id == current:
            continue

        if _is_idle(window_id):
            _select_window(window_id)
            return

    # No idle windows found - do nothing silently


def _ensure_bindings() -> None:
    """Ensure tmux keybindings are set up."""
    # Enable 256 color and RGB support
    subprocess.run(
        ["tmux", "set-option", "-g", "default-terminal", "tmux-256color"],
        capture_output=True,
    )
    subprocess.run(
        ["tmux", "set-option", "-as", "terminal-features", ",*:RGB"],
        capture_output=True,
    )
    # Enable mouse support
    subprocess.run(["tmux", "set-option", "-g", "mouse", "on"], capture_output=True)
    # Set Ctrl+Space as prefix
    subprocess.run(["tmux", "set-option", "-g", "prefix", "C-Space"], capture_output=True)
    subprocess.run(["tmux", "unbind-key", "C-b"], capture_output=True)
    subprocess.run(["tmux", "bind-key", "C-Space", "send-prefix"], capture_output=True)

    # Bind j/k for next/prev idle mind
    subprocess.run(
        ["tmux", "bind-key", "j", "run-shell", "mg next"],
        capture_output=True,
    )
    subprocess.run(
        ["tmux", "bind-key", "k", "run-shell", "mg next --reverse"],
        capture_output=True,
    )


def _session_exists() -> bool:
    """Check if the tmux session exists."""
    result = subprocess.run(
        ["tmux", "has-session", "-t", SESSION_NAME],
        capture_output=True,
    )
    return result.returncode == 0


def _get_current_window() -> str:
    """Get the active window index for the session."""
    result = subprocess.run(
        ["tmux", "display-message", "-t", SESSION_NAME, "-p", "#{window_index}"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


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


def _is_idle(window_index: str) -> bool:
    """Check if a window is idle (not showing 'esc to interrupt')."""
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", f"{SESSION_NAME}:{window_index}", "-p"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False

    # Get last N lines
    lines = result.stdout.rstrip().split("\n")
    last_lines = lines[-CAPTURE_LINES:] if len(lines) > CAPTURE_LINES else lines
    content = "\n".join(last_lines)

    # If "esc to interrupt" appears, the mind is busy
    return "esc to interrupt" not in content.lower()


def _select_window(window_index: str) -> None:
    """Switch to the specified window."""
    subprocess.run(
        ["tmux", "select-window", "-t", f"{SESSION_NAME}:{window_index}"],
        capture_output=True,
    )
