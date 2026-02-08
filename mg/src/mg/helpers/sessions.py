"""Session management for minds.

Sessions track mind assignments. Each session represents a unit of delegated
work — who's doing it, what they're doing, and who asked for it.

Stored in sessions.ig.toml (git-ignored). One active session per mind.
"""

from __future__ import annotations

import uuid
import tomllib
import tomli_w
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


MAX_SESSIONS = 20


@dataclass
class Session:
    """A tracked session for a mind."""

    id: str  # mg session UUID
    task: str  # Short summary (commit title convention)
    started: datetime
    mind: str = ""
    short_id: int = 0  # Rolling integer for easy user reference
    status: str = "started"  # staged / started
    parent: str = ""  # Parent mg session id (empty = human root)
    description: str = ""  # Long-form body (commit body convention)
    claude_session_id: str = ""  # Current Claude session id
    old_claude_session_ids: list[str] = field(default_factory=list)


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
                status=entry.get("status", "started"),
                parent=entry.get("parent", ""),
                description=entry.get("description", ""),
                claude_session_id=entry.get("claude_session_id", ""),
                old_claude_session_ids=entry.get("old_claude_session_ids", []),
            )
        )
    return sessions


def get_next_short_id(sessions: list[Session]) -> int:
    """Get the next short_id by incrementing the highest existing value."""
    if not sessions:
        return 1
    return max(s.short_id for s in sessions) + 1


def _write_sessions(sessions_file: Path, sessions: list[Session]) -> None:
    """Write a full session list to disk."""
    data = {"sessions": [_session_to_dict(s) for s in sessions]}
    sessions_file.parent.mkdir(parents=True, exist_ok=True)
    with open(sessions_file, "wb") as f:
        tomli_w.dump(data, f)


def save_session(sessions_file: Path, session: Session) -> None:
    """Prepend a new session to the file (most recent first).

    Keeps at most MAX_SESSIONS entries, dropping oldest.
    """
    existing = load_sessions(sessions_file)
    all_sessions = [session] + existing
    all_sessions = all_sessions[:MAX_SESSIONS]
    _write_sessions(sessions_file, all_sessions)


def _session_to_dict(s: Session) -> dict:
    """Convert a Session to a TOML-serializable dict."""
    d = {
        "id": s.id,
        "task": s.task,
        "started": s.started,
        "mind": s.mind,
        "short_id": s.short_id,
        "status": s.status,
    }
    if s.parent:
        d["parent"] = s.parent
    if s.description:
        d["description"] = s.description
    if s.claude_session_id:
        d["claude_session_id"] = s.claude_session_id
    if s.old_claude_session_ids:
        d["old_claude_session_ids"] = s.old_claude_session_ids
    return d


def create_session(
    sessions_file: Path,
    task: str,
    mind: str,
    *,
    status: str = "started",
    parent: str = "",
    description: str = "",
) -> Session:
    """Create and save a new session.

    Generates UUID, calculates next short_id, saves to file, and returns
    the session. If the mind already has an active session, it is removed
    first (one active session per mind).
    """
    existing = load_sessions(sessions_file)

    # Enforce one active session per mind — remove any existing
    existing = [s for s in existing if s.mind != mind]

    session = Session(
        id=str(uuid.uuid4()),
        task=task,
        started=datetime.now(timezone.utc),
        mind=mind,
        short_id=get_next_short_id(existing),
        status=status,
        parent=parent,
        description=description,
    )
    all_sessions = [session] + existing
    all_sessions = all_sessions[:MAX_SESSIONS]
    _write_sessions(sessions_file, all_sessions)
    return session


def get_most_recent_session(sessions_file: Path) -> Session | None:
    """Get the most recently started session."""
    sessions = load_sessions(sessions_file)
    return sessions[0] if sessions else None


def get_most_recent_session_for_mind(sessions_file: Path, mind_name: str) -> Session | None:
    """Get the most recently started session for a specific mind.

    Args:
        sessions_file: Path to the sessions TOML file.
        mind_name: The mind name to filter by.

    Returns:
        Most recent session for the mind, or None if not found.
    """
    sessions = load_sessions(sessions_file)
    for session in sessions:
        if session.mind == mind_name:
            return session
    return None


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


def get_session(sessions_file: Path, identifier: str) -> Session | None:
    """Find session by short_id (if numeric) or UUID prefix.

    Args:
        sessions_file: Path to the sessions TOML file.
        identifier: Either a short_id (e.g., "3") or partial/full UUID.

    Returns:
        Session if found, None otherwise.
    """
    sessions = load_sessions(sessions_file)

    # Try short_id first if identifier is numeric
    if identifier.isdigit():
        short_id = int(identifier)
        for session in sessions:
            if session.short_id == short_id:
                return session

    # Try UUID prefix match
    for session in sessions:
        if session.id.startswith(identifier):
            return session

    return None


def update_session(
    sessions_file: Path,
    session_id: str,
    mutator: Callable[[Session], None],
) -> Session:
    """Update an existing session via mutator callback.

    Loads all sessions, finds the target by ID, calls mutator(session),
    and writes back to disk. Automatically rotates old claude_session_id
    if the mutator changes it.

    Raises:
        KeyError: If no session matches the given ID.
    """
    sessions = load_sessions(sessions_file)

    target = None
    for s in sessions:
        if s.id == session_id:
            target = s
            break

    if target is None:
        raise KeyError(f"Session not found: {session_id}")

    # Snapshot claude_session_id before mutation for rotation
    old_claude_id = target.claude_session_id

    mutator(target)

    # Rotate claude_session_id if it changed
    if old_claude_id and target.claude_session_id != old_claude_id:
        target.old_claude_session_ids.append(old_claude_id)

    _write_sessions(sessions_file, sessions)
    return target


def resolve_session(
    sessions_file: Path,
    mind_name: str,
    *,
    task: str | None = None,
    parent: str = "",
) -> Session:
    """Ensure a mind has a started session, creating one if needed.

    If the mind has an existing session, transitions it to started and
    assigns a new claude_session_id. If no session exists, creates one
    (using the provided task, or "" if task is None).

    Args:
        sessions_file: Path to the sessions TOML file.
        mind_name: The mind to resolve a session for.
        task: Task description for new sessions. If None and no existing
              session, creates one with an empty task.
        parent: Parent session id (for delegation chains).

    Returns:
        A session in 'started' status with a claude_session_id set.
    """
    session = get_most_recent_session_for_mind(sessions_file, mind_name)

    if session is not None:
        # Transition staged → started (or re-start an existing session)
        claude_session_id = str(uuid.uuid4())

        def transition(s: Session) -> None:
            s.status = "started"
            s.claude_session_id = claude_session_id

        return update_session(sessions_file, session.id, transition)

    # No existing session — create one
    claude_session_id = str(uuid.uuid4())
    session = create_session(
        sessions_file, task or "", mind_name,
        status="started", parent=parent,
    )

    def set_claude_id(s: Session) -> None:
        s.claude_session_id = claude_session_id

    return update_session(sessions_file, session.id, set_claude_id)


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

    _write_sessions(sessions_file, sessions)
    return True
