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

from pathlib import Path

from mg.helpers.sessions import load_sessions
from mg.helpers.tui._base import ModelClient
from mg.helpers.tui.TuiModel import SessionEntry, TuiModel


def sessions_refresh(client: ModelClient, sessions_file: Path) -> None:
    """Read sessions from disk and push them into the TUI model.

    Args:
        client: A TuiClient or TuiLocalClient.
        sessions_file: Path to the sessions.ig.toml file.
    """
    sessions = load_sessions(sessions_file)
    entries = [
        SessionEntry(mind=s.mind, task=s.task, short_id=s.short_id)
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


def _set_entries(model: TuiModel, entries: list[SessionEntry]) -> None:
    """Mutator for sessions_refresh — separated for picklability."""
    model.sessions.entries = entries
