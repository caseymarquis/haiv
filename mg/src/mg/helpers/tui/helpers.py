"""TUI helper functions — all real logic lives here.

This module contains every TUI operation as a standalone function. Each
function receives all of its dependencies as parameters (client, file paths,
etc.) and has no implicit state. This makes them independently testable and
callable from anywhere — the TUI app, mg commands, tests — without pulling
in a dependency graph.

The Tui class (tui.py) is a thin convenience wrapper that holds pre-loaded
dependencies and delegates to these functions. No logic should live in the
Tui class itself. If you're adding a new TUI capability, put it here as a
function, then add a one-line passthrough in the Tui class.

Naming convention: noun_verb (e.g. sessions_refresh, hud_update) so that
related functions sort together.
"""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import TYPE_CHECKING

from mg.helpers.sessions import (
    Session,
    get_most_recent_session_for_mind,
    load_sessions,
    resolve_session,
)
from mg.helpers.tui._base import ModelClient
from mg.helpers.tui.TuiModel import SessionEntry, TuiModel

if TYPE_CHECKING:
    from mg.helpers.tui.terminal import TerminalManager


# -- Model operations --


def sessions_refresh(client: ModelClient, sessions_file: Path) -> None:
    """Read sessions from disk and push them into the TUI model.

    Args:
        client: A TuiClient or TuiLocalClient.
        sessions_file: Path to the sessions.ig.toml file.
    """
    sessions = load_sessions(sessions_file)
    entries = [
        SessionEntry(
            id=s.id, mind=s.mind, task=s.task,
            short_id=s.short_id, status=s.status, parent_id=s.parent_id,
        )
        for s in sessions
    ]
    client.write(lambda m: _set_entries(m, entries))


def errors_append(client: ModelClient, message: str) -> None:
    """Append an error message to the TUI error display.

    Args:
        client: A TuiClient or TuiLocalClient.
        message: The error message to display.
    """
    client.write(lambda m: m.errors.messages.append(message))


# -- Workspace operations --


def workspace_start(terminal: TerminalManager) -> None:
    """Ensure the mg workspace exists (window, hud tab, layout).

    Args:
        terminal: TerminalManager for pane operations.
    """
    terminal.ensure_workspace()


# -- Mind operations --


def mind_launch(
    terminal: TerminalManager,
    client: ModelClient,
    sessions_file: Path,
    mind_name: str,
    mg_root: Path,
    *,
    task: str | None = None,
    parent_id: str = "",
) -> Session:
    """Put a mind in the hud — switching, launching, or restarting as needed.

    If the mind is already active in the hud, this is a no-op (just refreshes
    the model). If the mind has a parked pane, switches to it. Otherwise,
    resolves a session and launches a new pane with Claude Code.

    Args:
        terminal: TerminalManager for pane operations.
        client: A TuiClient or TuiLocalClient for model updates.
        sessions_file: Path to sessions.ig.toml.
        mind_name: Name of the mind to launch.
        mg_root: Project root path (for environment variables).
        task: Task description for new sessions. If None and no existing
              session, creates one with an empty task.
        parent_id: Parent session id (for delegation chains).

    Returns:
        The session for this mind.
    """
    # Already showing — just refresh the model
    if terminal.is_mind_active(mind_name):
        session = get_most_recent_session_for_mind(sessions_file, mind_name)
        if session is not None:
            print(
                f"Mind '{mind_name}' is already active in the hud.\n"
                f"To relaunch here: mg start {mind_name} --here"
            )
            sessions_refresh(client, sessions_file)
            return session

    # Parked pane exists — switch to it
    if terminal.is_mind_parked(mind_name):
        session = get_most_recent_session_for_mind(sessions_file, mind_name)
        if session is not None:
            terminal.switch_to_mind(mind_name)
            sessions_refresh(client, sessions_file)
            return session

    # Need to launch a new pane — resolve or create session
    session = resolve_session(sessions_file, mind_name, task=task, parent_id=parent_id)

    sessions_refresh(client, sessions_file)

    # Build claude command and launch
    claude_cmd = build_claude_command(mind_name, session.claude_session_id)
    env = build_env(mind_name, session.id, mg_root)
    terminal.launch_in_mind_pane(mind_name, env, [claude_cmd])

    return session


def mind_close_pane(terminal: TerminalManager, mind_name: str) -> None:
    """Close a parked mind's pane.

    Args:
        terminal: TerminalManager for pane operations.
        mind_name: Name of the mind whose parked pane to close.
    """
    terminal.close_parked_mind(mind_name)


# -- Claude launch helpers --
# These aren't really TUI concerns — they're about constructing the claude
# invocation. They live here for now because mind_launch is the primary
# consumer, but they should move if a better home emerges.


def build_claude_command(mind_name: str, claude_session_id: str) -> str:
    """Build the claude CLI command for launching a mind."""
    prompt = f"Run `mg become {mind_name}`"
    allowed = f"Bash(mg become {mind_name})"
    return (
        f"claude {shlex.quote(prompt)} "
        f"--session-id {shlex.quote(claude_session_id)} "
        f"--allowedTools {shlex.quote(allowed)}"
    )


def build_env(mind_name: str, session_id: str, mg_root: Path) -> dict[str, str]:
    """Build environment variables for a mind pane."""
    from mg._infrastructure.env import MG_MIND, MG_ROOT, MG_SESSION

    return {
        MG_MIND: mind_name,
        MG_SESSION: session_id,
        MG_ROOT: str(mg_root),
    }


# -- Internal helpers --


def _set_entries(model: TuiModel, entries: list[SessionEntry]) -> None:
    """Mutator for sessions_refresh — separated for picklability."""
    model.sessions.entries = entries
