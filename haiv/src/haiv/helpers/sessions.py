"""Session management for minds.

Sessions track mind assignments. Each session represents a unit of delegated
work — who's doing it, what they're doing, and who asked for it.

Stored in sessions.ig.toml (git-ignored). One active session per mind.
"""

from __future__ import annotations

import hashlib
import re
import uuid
import tomllib
import tomli_w
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from haiv.helpers.utils.trees import TreeNode, build_tree


MAX_SESSIONS = 20


@dataclass
class Session:
    """A tracked session for a mind."""

    id: str  # haiv session UUID
    task: str  # Short summary (commit title convention)
    started: datetime
    mind: str = ""
    short_id: int = 0  # Rolling integer for easy user reference
    status: str = "started"  # staged / started
    parent_id: str = ""  # Parent haiv session id (empty = human root)
    description: str = ""  # Long-form body (commit body convention)
    branch: str = ""  # Branch this mind's worktree is on
    base_branch: str = ""  # Branch this worktree was created from
    claude_session_id: str = ""  # Current Claude session id
    old_claude_session_ids: list[str] = field(default_factory=list)

    _MAX_FILENAME_LENGTH = 50

    def as_filename(self) -> str:
        """Return a sanitized, filesystem-safe filename from the task.

        Lowercase, replaces non-alphanumeric runs with hyphens, strips edges.
        Long names are truncated at a word boundary with a short hash appended
        to avoid collisions. Returns without extension.
        """
        name = re.sub(r"[^a-z0-9]+", "-", self.task.lower()).strip("-")

        if not name or len(name) <= self._MAX_FILENAME_LENGTH:
            return name

        task_hash = hashlib.sha256(self.task.encode()).hexdigest()[:4]
        max_base = self._MAX_FILENAME_LENGTH - len(task_hash) - 1  # room for "-" + hash

        truncated = name[:max_base]
        last_hyphen = truncated.rfind("-")
        if last_hyphen > max_base // 2:
            truncated = truncated[:last_hyphen]

        return f"{truncated}-{task_hash}"


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
                parent_id=entry.get("parent", ""),
                description=entry.get("description", ""),
                branch=entry.get("branch", ""),
                base_branch=entry.get("base_branch", ""),
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


def _session_to_dict(s: Session) -> dict[str, object]:
    """Convert a Session to a TOML-serializable dict."""
    d: dict[str, object] = {
        "id": s.id,
        "task": s.task,
        "started": s.started,
        "mind": s.mind,
        "short_id": s.short_id,
        "status": s.status,
    }
    if s.parent_id:
        d["parent"] = s.parent_id
    if s.branch:
        d["branch"] = s.branch
    if s.base_branch:
        d["base_branch"] = s.base_branch
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
    parent_id: str = "",
    branch: str = "",
    base_branch: str = "",
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
        parent_id=parent_id,
        branch=branch,
        base_branch=base_branch,
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


def get_current_session(sessions_file: Path) -> Session:
    """Get the current session from the HV_SESSION environment variable.

    Raises:
        CommandError: If HV_SESSION is not set or session not found.
    """
    import os
    from haiv._infrastructure.env import HV_SESSION
    from haiv.errors import CommandError

    session_id = os.environ.get(HV_SESSION, "")
    if not session_id:
        raise CommandError(
            "HV_SESSION is not set — cannot detect current session.\n\n"
            "  Set it to your session ID:  export HV_SESSION=<your-session-id>"
        )

    session = find_session(sessions_file, session_id)
    if not session:
        raise CommandError(f"Session not found: {session_id}")

    return session


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
    parent_id: str = "",
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
        parent_id: Parent session id (for delegation chains).

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
        status="started", parent_id=parent_id,
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


SessionNode = TreeNode[Session]


def build_session_tree(sessions: list[Session]) -> list[SessionNode]:
    """Build a tree from sessions using their parent_id field.

    Sessions with no parent or whose parent is missing become roots.
    """
    by_id = {s.id: s for s in sessions}
    pairs = [(s, by_id.get(s.parent_id) if s.parent_id else None) for s in sessions]
    return build_tree(pairs)
