"""Session management for minds.

Sessions track Claude Code conversations. Each mind stores its sessions in
sessions.ig.toml (git-ignored). Sessions have a rolling integer short_id for
easy user reference - internally everything uses the full UUID.
"""

from __future__ import annotations

import uuid
import tomllib
import tomli_w
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


MAX_SESSIONS = 20


@dataclass
class Session:
    """A tracked Claude session for a mind."""

    id: str
    task: str
    started: datetime
    mind: str = ""  # Mind name (empty for backwards compatibility)
    short_id: int = 0  # Rolling integer for easy user reference


def load_sessions(sessions_file: Path) -> list[Session]:
    """Load sessions from TOML file.

    Returns sessions ordered most-recent-first.
    """
    if not sessions_file.exists():
        return []

    with open(sessions_file, "rb") as f:
        data = tomllib.load(f)

    sessions = []
    for entry in data.get("sessions", []):
        sessions.append(
            Session(
                id=entry["id"],
                task=entry["task"],
                started=entry["started"],
                mind=entry.get("mind", ""),
                short_id=entry.get("short_id", 0),
            )
        )
    return sessions


def get_next_short_id(sessions: list[Session]) -> int:
    """Get the next short_id by incrementing the highest existing value."""
    if not sessions:
        return 1
    return max(s.short_id for s in sessions) + 1


def save_session(sessions_file: Path, session: Session) -> None:
    """Prepend a new session to the file (most recent first).

    Keeps at most MAX_SESSIONS entries, dropping oldest.
    """
    existing = load_sessions(sessions_file)
    all_sessions = [session] + existing

    # Keep only the most recent MAX_SESSIONS
    all_sessions = all_sessions[:MAX_SESSIONS]

    data = {
        "sessions": [
            {
                "id": s.id,
                "task": s.task,
                "started": s.started,
                "mind": s.mind,
                "short_id": s.short_id,
            }
            for s in all_sessions
        ]
    }

    sessions_file.parent.mkdir(parents=True, exist_ok=True)
    with open(sessions_file, "wb") as f:
        tomli_w.dump(data, f)


def create_session(sessions_file: Path, task: str, mind: str) -> Session:
    """Create and save a new session.

    Generates UUID, calculates next short_id, saves to file, and returns the session.
    """
    existing = load_sessions(sessions_file)
    session = Session(
        id=str(uuid.uuid4()),
        task=task,
        started=datetime.now(timezone.utc),
        mind=mind,
        short_id=get_next_short_id(existing),
    )
    save_session(sessions_file, session)
    return session


def get_most_recent_session(sessions_file: Path) -> Session | None:
    """Get the most recently started session."""
    sessions = load_sessions(sessions_file)
    return sessions[0] if sessions else None


def find_session(sessions_file: Path, session_id: str) -> Session | None:
    """Find session by full ID (or partial UUID match)."""
    sessions = load_sessions(sessions_file)
    for session in sessions:
        if session.id.startswith(session_id):
            return session
    return None


def resolve_short_id(sessions_file: Path, short_id: int) -> str | None:
    """Translate a short_id to the full session ID.

    Returns None if no session with that short_id exists.
    """
    sessions = load_sessions(sessions_file)
    for session in sessions:
        if session.short_id == short_id:
            return session.id
    return None


def remove_session(sessions_file: Path, session_id: str) -> bool:
    """Remove a session by full ID (or partial UUID match).

    Returns True if a session was removed, False if not found.
    """
    if not sessions_file.exists():
        return False

    sessions = load_sessions(sessions_file)
    original_count = len(sessions)

    sessions = [s for s in sessions if not s.id.startswith(session_id)]

    if len(sessions) == original_count:
        return False

    data = {
        "sessions": [
            {
                "id": s.id,
                "task": s.task,
                "started": s.started,
                "mind": s.mind,
                "short_id": s.short_id,
            }
            for s in sessions
        ]
    }

    with open(sessions_file, "wb") as f:
        tomli_w.dump(data, f)

    return True
