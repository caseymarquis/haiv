"""Tests for mg.helpers.sessions module."""

import re
import pytest
from datetime import datetime, timezone

from unittest.mock import patch

from mg.errors import CommandError
from mg.helpers.sessions import (
    Session,
    build_session_tree,
    create_session,
    get_current_session,
    load_sessions,
    resolve_session,
    save_session,
    update_session,
    get_session,
    get_most_recent_session_for_mind,
)


def _session(id: str, mind: str = "wren", task: str = "task", parent_id: str = "") -> Session:
    """Helper to create a Session with sensible defaults."""
    return Session(
        id=id, task=task, mind=mind,
        started=datetime.now(timezone.utc),
        short_id=0, parent_id=parent_id,
    )


class TestBuildSessionTree:
    """Tests for build_session_tree()."""

    def test_flat_sessions_all_become_roots(self):
        """Sessions with no parent_id are all roots."""
        a = _session("a")
        b = _session("b", mind="robin")
        roots = build_session_tree([a, b])

        assert len(roots) == 2
        assert roots[0].item is a
        assert roots[1].item is b

    def test_child_linked_to_parent(self):
        """Session with parent_id is nested under its parent."""
        parent = _session("parent-uuid")
        child = _session("child-uuid", mind="spark", parent_id="parent-uuid")
        roots = build_session_tree([parent, child])

        assert len(roots) == 1
        assert roots[0].item is parent
        assert len(roots[0].child_nodes) == 1
        assert roots[0].child_nodes[0].item is child

    def test_orphan_becomes_root(self):
        """Session whose parent_id doesn't match any session is a root."""
        orphan = _session("orphan-uuid", parent_id="gone-uuid")
        roots = build_session_tree([orphan])

        assert len(roots) == 1
        assert roots[0].item is orphan

    def test_mixed_tree(self):
        """Multiple roots with children at different levels."""
        r1 = _session("r1")
        r2 = _session("r2", mind="robin")
        c1 = _session("c1", mind="spark", parent_id="r1")
        c2 = _session("c2", mind="echo", parent_id="c1")
        roots = build_session_tree([r1, r2, c1, c2])

        assert len(roots) == 2
        assert roots[0].item is r1
        assert roots[1].item is r2
        # r1 -> c1 -> c2
        assert roots[0].child_nodes[0].item is c1
        assert roots[0].child_nodes[0].child_nodes[0].item is c2


class TestGetSession:
    """Tests for get_session()."""

    def test_finds_by_short_id(self, tmp_path):
        """Finds session by short_id when identifier is numeric."""
        sessions_file = tmp_path / "sessions.toml"
        session = Session(
            id="abc123-def456",
            task="Test task",
            started=datetime.now(timezone.utc),
            mind="wren",
            short_id=3,
        )
        save_session(sessions_file, session)

        result = get_session(sessions_file, "3")

        assert result is not None
        assert result.id == "abc123-def456"
        assert result.short_id == 3

    def test_finds_by_partial_uuid(self, tmp_path):
        """Finds session by partial UUID prefix."""
        sessions_file = tmp_path / "sessions.toml"
        session = Session(
            id="abc123-def456-ghi789",
            task="Test task",
            started=datetime.now(timezone.utc),
            mind="wren",
            short_id=1,
        )
        save_session(sessions_file, session)

        result = get_session(sessions_file, "abc123")

        assert result is not None
        assert result.id == "abc123-def456-ghi789"

    def test_finds_by_full_uuid(self, tmp_path):
        """Finds session by full UUID."""
        sessions_file = tmp_path / "sessions.toml"
        full_id = "abc123-def456-ghi789"
        session = Session(
            id=full_id,
            task="Test task",
            started=datetime.now(timezone.utc),
            mind="wren",
            short_id=1,
        )
        save_session(sessions_file, session)

        result = get_session(sessions_file, full_id)

        assert result is not None
        assert result.id == full_id

    def test_short_id_takes_precedence_over_uuid(self, tmp_path):
        """When identifier is numeric, short_id match wins over UUID prefix."""
        sessions_file = tmp_path / "sessions.toml"
        # Session with UUID starting with "5"
        session1 = Session(
            id="5abc-def",
            task="Task 1",
            started=datetime.now(timezone.utc),
            mind="wren",
            short_id=1,
        )
        # Session with short_id=5
        session2 = Session(
            id="xyz-123",
            task="Task 2",
            started=datetime.now(timezone.utc),
            mind="robin",
            short_id=5,
        )
        save_session(sessions_file, session1)
        save_session(sessions_file, session2)

        result = get_session(sessions_file, "5")

        # Should find by short_id, not UUID prefix
        assert result is not None
        assert result.id == "xyz-123"
        assert result.short_id == 5

    def test_returns_none_when_not_found(self, tmp_path):
        """Returns None when no session matches."""
        sessions_file = tmp_path / "sessions.toml"
        session = Session(
            id="abc123",
            task="Test task",
            started=datetime.now(timezone.utc),
            mind="wren",
            short_id=1,
        )
        save_session(sessions_file, session)

        result = get_session(sessions_file, "999")

        assert result is None

    def test_returns_none_when_no_sessions(self, tmp_path):
        """Returns None when sessions file doesn't exist."""
        sessions_file = tmp_path / "sessions.toml"

        result = get_session(sessions_file, "1")

        assert result is None

    def test_falls_back_to_uuid_for_non_numeric(self, tmp_path):
        """Non-numeric identifiers skip short_id check."""
        sessions_file = tmp_path / "sessions.toml"
        session = Session(
            id="abc123",
            task="Test task",
            started=datetime.now(timezone.utc),
            mind="wren",
            short_id=1,
        )
        save_session(sessions_file, session)

        result = get_session(sessions_file, "abc")

        assert result is not None
        assert result.id == "abc123"


class TestGetMostRecentSessionForMind:
    """Tests for get_most_recent_session_for_mind()."""

    def test_finds_session_for_mind(self, tmp_path):
        """Finds the most recent session for the specified mind."""
        sessions_file = tmp_path / "sessions.toml"
        session = Session(
            id="abc123",
            task="Test task",
            started=datetime.now(timezone.utc),
            mind="wren",
            short_id=1,
        )
        save_session(sessions_file, session)

        result = get_most_recent_session_for_mind(sessions_file, "wren")

        assert result is not None
        assert result.id == "abc123"
        assert result.mind == "wren"

    def test_returns_most_recent_when_multiple(self, tmp_path):
        """Returns the most recent session when mind has multiple sessions."""
        sessions_file = tmp_path / "sessions.toml"
        # Save older session first
        older = Session(
            id="older-123",
            task="Older task",
            started=datetime.now(timezone.utc),
            mind="wren",
            short_id=1,
        )
        save_session(sessions_file, older)
        # Save newer session (most recent is prepended)
        newer = Session(
            id="newer-456",
            task="Newer task",
            started=datetime.now(timezone.utc),
            mind="wren",
            short_id=2,
        )
        save_session(sessions_file, newer)

        result = get_most_recent_session_for_mind(sessions_file, "wren")

        assert result is not None
        assert result.id == "newer-456"

    def test_filters_by_mind_name(self, tmp_path):
        """Only returns sessions for the specified mind."""
        sessions_file = tmp_path / "sessions.toml"
        wren_session = Session(
            id="wren-123",
            task="Wren task",
            started=datetime.now(timezone.utc),
            mind="wren",
            short_id=1,
        )
        robin_session = Session(
            id="robin-456",
            task="Robin task",
            started=datetime.now(timezone.utc),
            mind="robin",
            short_id=2,
        )
        save_session(sessions_file, wren_session)
        save_session(sessions_file, robin_session)

        result = get_most_recent_session_for_mind(sessions_file, "wren")

        assert result is not None
        assert result.mind == "wren"
        assert result.id == "wren-123"

    def test_returns_none_when_mind_not_found(self, tmp_path):
        """Returns None when no sessions exist for the mind."""
        sessions_file = tmp_path / "sessions.toml"
        session = Session(
            id="robin-123",
            task="Robin task",
            started=datetime.now(timezone.utc),
            mind="robin",
            short_id=1,
        )
        save_session(sessions_file, session)

        result = get_most_recent_session_for_mind(sessions_file, "wren")

        assert result is None

    def test_returns_none_when_no_sessions(self, tmp_path):
        """Returns None when sessions file doesn't exist."""
        sessions_file = tmp_path / "sessions.toml"

        result = get_most_recent_session_for_mind(sessions_file, "wren")

        assert result is None


class TestCreateSession:
    """Tests for create_session()."""

    def test_creates_with_defaults(self, tmp_path):
        """Creates a session with default status='started'."""
        sessions_file = tmp_path / "sessions.toml"

        session = create_session(sessions_file, "Test task", "wren")

        assert session.task == "Test task"
        assert session.mind == "wren"
        assert session.status == "started"
        assert session.parent_id == ""
        assert session.description == ""

    def test_creates_with_staged_status(self, tmp_path):
        """Creates a session with status='staged'."""
        sessions_file = tmp_path / "sessions.toml"

        session = create_session(sessions_file, "Test task", "wren", status="staged")

        assert session.status == "staged"

    def test_creates_with_parent(self, tmp_path):
        """Creates a session with parent link."""
        sessions_file = tmp_path / "sessions.toml"

        session = create_session(
            sessions_file, "Child task", "spark",
            status="staged", parent_id="parent-uuid-123",
        )

        assert session.parent_id == "parent-uuid-123"

    def test_creates_with_description(self, tmp_path):
        """Creates a session with long-form description."""
        sessions_file = tmp_path / "sessions.toml"

        session = create_session(
            sessions_file, "Short title", "wren",
            description="Detailed explanation of what needs doing.",
        )

        assert session.description == "Detailed explanation of what needs doing."

    def test_replaces_existing_session_for_same_mind(self, tmp_path):
        """Creating a session for a mind removes its existing session."""
        sessions_file = tmp_path / "sessions.toml"

        first = create_session(sessions_file, "First task", "wren")
        second = create_session(sessions_file, "Second task", "wren")

        sessions = load_sessions(sessions_file)
        wren_sessions = [s for s in sessions if s.mind == "wren"]
        assert len(wren_sessions) == 1
        assert wren_sessions[0].id == second.id

    def test_does_not_replace_other_minds(self, tmp_path):
        """Creating a session for one mind doesn't affect others."""
        sessions_file = tmp_path / "sessions.toml"

        create_session(sessions_file, "Wren task", "wren")
        create_session(sessions_file, "Robin task", "robin")

        sessions = load_sessions(sessions_file)
        assert len(sessions) == 2

    def test_new_fields_round_trip_through_toml(self, tmp_path):
        """New fields survive save/load cycle."""
        sessions_file = tmp_path / "sessions.toml"

        created = create_session(
            sessions_file, "Task", "wren",
            status="staged", parent_id="parent-123", description="Details",
        )

        loaded = load_sessions(sessions_file)
        session = [s for s in loaded if s.id == created.id][0]
        assert session.status == "staged"
        assert session.parent_id == "parent-123"
        assert session.description == "Details"


class TestResolveSession:
    """Tests for resolve_session()."""

    def test_transitions_staged_to_started(self, tmp_path):
        """Existing staged session is transitioned to started."""
        sessions_file = tmp_path / "sessions.toml"
        create_session(sessions_file, "staged task", "wren", status="staged")

        session = resolve_session(sessions_file, "wren")

        assert session.status == "started"
        assert session.claude_session_id != ""
        assert session.task == "staged task"

    def test_restarts_existing_started_session(self, tmp_path):
        """Existing started session gets a new claude_session_id."""
        sessions_file = tmp_path / "sessions.toml"
        original = create_session(sessions_file, "running task", "wren")
        update_session(
            sessions_file, original.id,
            lambda s: setattr(s, "claude_session_id", "old-claude-id"),
        )

        session = resolve_session(sessions_file, "wren")

        assert session.status == "started"
        assert session.claude_session_id != "old-claude-id"
        assert "old-claude-id" in session.old_claude_session_ids

    def test_creates_session_with_task(self, tmp_path):
        """Creates a new started session when task is provided and no session exists."""
        sessions_file = tmp_path / "sessions.toml"

        session = resolve_session(sessions_file, "wren", task="new task")

        assert session.status == "started"
        assert session.task == "new task"
        assert session.mind == "wren"
        assert session.claude_session_id != ""

    def test_creates_session_with_empty_task_when_none(self, tmp_path):
        """Creates session with empty task when task is None and no session exists."""
        sessions_file = tmp_path / "sessions.toml"

        session = resolve_session(sessions_file, "wren")

        assert session.status == "started"
        assert session.task == ""
        assert session.mind == "wren"
        assert session.claude_session_id != ""

    def test_preserves_existing_task(self, tmp_path):
        """Does not overwrite the task on an existing session."""
        sessions_file = tmp_path / "sessions.toml"
        create_session(sessions_file, "original task", "wren", status="staged")

        session = resolve_session(sessions_file, "wren", task="different task")

        assert session.task == "original task"

    def test_sets_parent_on_new_session(self, tmp_path):
        """Parent is set when creating a new session."""
        sessions_file = tmp_path / "sessions.toml"

        session = resolve_session(sessions_file, "wren", task="child task", parent_id="parent-123")

        assert session.parent_id == "parent-123"

    def test_preserves_session_identity(self, tmp_path):
        """Transitioning a session preserves its id."""
        sessions_file = tmp_path / "sessions.toml"
        original = create_session(sessions_file, "task", "wren", status="staged")

        session = resolve_session(sessions_file, "wren")

        assert session.id == original.id


class TestUpdateSession:
    """Tests for update_session()."""

    def test_updates_status(self, tmp_path):
        """Updates a session's status."""
        sessions_file = tmp_path / "sessions.toml"
        session = create_session(sessions_file, "Task", "wren", status="staged")

        updated = update_session(
            sessions_file, session.id,
            lambda s: setattr(s, "status", "started"),
        )

        assert updated.status == "started"
        # Verify persisted
        reloaded = get_session(sessions_file, session.id)
        assert reloaded is not None
        assert reloaded.status == "started"

    def test_rotates_claude_session_id(self, tmp_path):
        """Setting a new claude_session_id pushes the old one to history."""
        sessions_file = tmp_path / "sessions.toml"
        session = create_session(sessions_file, "Task", "wren")

        # Set initial claude_session_id
        update_session(
            sessions_file, session.id,
            lambda s: setattr(s, "claude_session_id", "claude-1"),
        )

        # Update to a new one — old should be archived
        updated = update_session(
            sessions_file, session.id,
            lambda s: setattr(s, "claude_session_id", "claude-2"),
        )

        assert updated.claude_session_id == "claude-2"
        assert updated.old_claude_session_ids == ["claude-1"]

    def test_no_rotation_when_claude_id_unchanged(self, tmp_path):
        """No rotation when claude_session_id doesn't change."""
        sessions_file = tmp_path / "sessions.toml"
        session = create_session(sessions_file, "Task", "wren")

        update_session(
            sessions_file, session.id,
            lambda s: setattr(s, "claude_session_id", "claude-1"),
        )
        # Update status only, not claude_session_id
        updated = update_session(
            sessions_file, session.id,
            lambda s: setattr(s, "status", "started"),
        )

        assert updated.claude_session_id == "claude-1"
        assert updated.old_claude_session_ids == []

    def test_no_rotation_when_claude_id_was_empty(self, tmp_path):
        """No rotation when there was no previous claude_session_id."""
        sessions_file = tmp_path / "sessions.toml"
        session = create_session(sessions_file, "Task", "wren")

        updated = update_session(
            sessions_file, session.id,
            lambda s: setattr(s, "claude_session_id", "claude-1"),
        )

        assert updated.claude_session_id == "claude-1"
        assert updated.old_claude_session_ids == []

    def test_raises_on_unknown_session(self, tmp_path):
        """Raises KeyError when session ID doesn't exist."""
        sessions_file = tmp_path / "sessions.toml"
        create_session(sessions_file, "Task", "wren")

        with pytest.raises(KeyError, match="Session not found"):
            update_session(
                sessions_file, "nonexistent-id",
                lambda s: setattr(s, "status", "started"),
            )

    def test_multiple_field_update(self, tmp_path):
        """Mutator can update multiple fields at once."""
        sessions_file = tmp_path / "sessions.toml"
        session = create_session(sessions_file, "Task", "wren", status="staged")

        def activate(s):
            s.status = "started"
            s.claude_session_id = "claude-abc"

        updated = update_session(sessions_file, session.id, activate)

        assert updated.status == "started"
        assert updated.claude_session_id == "claude-abc"


class TestGetCurrentSession:
    """Tests for get_current_session()."""

    def test_returns_session_from_env(self, tmp_path):
        """Finds session using MG_SESSION env var."""
        sessions_file = tmp_path / "sessions.toml"
        session = create_session(sessions_file, "Test task", "wren")

        with patch.dict("os.environ", {"MG_SESSION": session.id}):
            result = get_current_session(sessions_file)

        assert result.id == session.id

    def test_raises_when_env_not_set(self, tmp_path):
        """Raises CommandError when MG_SESSION is not set."""
        sessions_file = tmp_path / "sessions.toml"

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(CommandError, match="MG_SESSION is not set"):
                get_current_session(sessions_file)

    def test_raises_when_session_not_found(self, tmp_path):
        """Raises CommandError when session ID doesn't match."""
        sessions_file = tmp_path / "sessions.toml"

        with patch.dict("os.environ", {"MG_SESSION": "nonexistent-id"}):
            with pytest.raises(CommandError, match="Session not found"):
                get_current_session(sessions_file)


class TestAsFilename:
    """Tests for Session.as_filename()."""

    def test_simple_task(self):
        """Normal task becomes lowercase hyphenated."""
        s = _session("id", task="Add Session.as_filename() method")
        assert s.as_filename() == "add-session-as-filename-method"

    def test_special_characters_replaced(self):
        """Colons, parens, slashes, and quotes become hyphens."""
        s = _session("id", task='Research: notify "all" /instances/')
        assert s.as_filename() == "research-notify-all-instances"

    def test_consecutive_specials_collapsed(self):
        """Runs of special characters collapse to a single hyphen."""
        s = _session("id", task="fix --- the ::: bug")
        assert s.as_filename() == "fix-the-bug"

    def test_leading_trailing_stripped(self):
        """Leading and trailing non-alphanumeric chars are stripped."""
        s = _session("id", task="...hello world!!!")
        assert s.as_filename() == "hello-world"

    def test_numbers_preserved(self):
        """Digits are alphanumeric and kept as-is."""
        s = _session("id", task="Fix bug #42 in v2")
        assert s.as_filename() == "fix-bug-42-in-v2"

    def test_empty_task(self):
        """Empty task returns empty string."""
        s = _session("id", task="")
        assert s.as_filename() == ""

    def test_all_special_characters(self):
        """Task with only special characters returns empty string."""
        s = _session("id", task="!@#$%^&*()")
        assert s.as_filename() == ""

    def test_short_task_no_hash(self):
        """Tasks within the length limit don't get a hash appended."""
        s = _session("id", task="Short task")
        result = s.as_filename()
        assert result == "short-task"

    def test_exactly_at_limit_no_hash(self):
        """Task sanitizing to exactly the limit gets no hash."""
        task = "a" * 50
        s = _session("id", task=task)
        assert s.as_filename() == "a" * 50

    def test_one_over_limit_gets_hash(self):
        """Task sanitizing to limit+1 triggers truncation with hash."""
        task = "a" * 51
        s = _session("id", task=task)
        result = s.as_filename()
        assert len(result) <= 50
        assert re.search(r"-[a-f0-9]{4}$", result)

    def test_long_task_truncated_with_hash(self):
        """Long tasks are truncated and get a hash suffix."""
        s = _session("id", task="Research: notify running Claude instances of external events")
        result = s.as_filename()
        assert len(result) <= 50
        assert re.search(r"-[a-f0-9]{4}$", result)
        assert result.startswith("research-notify-running-claude")

    def test_truncation_prefers_word_boundary(self):
        """Truncation breaks at a hyphen rather than mid-word."""
        s = _session("id", task="Research: notify running Claude instances of external events")
        result = s.as_filename()
        # The base (before the hash) should end on "of" — a clean word
        # boundary — rather than cutting mid-word into "external"
        base = result[: result.rfind("-")]
        assert base.endswith("-of") or base.endswith("of")

    def test_deterministic(self):
        """Same task always produces the same filename."""
        s1 = _session("id1", task="Research: notify running Claude instances of external events")
        s2 = _session("id2", task="Research: notify running Claude instances of external events")
        assert s1.as_filename() == s2.as_filename()

    def test_different_long_tasks_differ(self):
        """Different long tasks produce different filenames via hash."""
        s1 = _session("id", task="This is a very long task description that will definitely need truncation abc")
        s2 = _session("id", task="This is a very long task description that will definitely need truncation xyz")
        assert s1.as_filename() != s2.as_filename()

    def test_cross_platform_safe(self):
        """Result contains no characters problematic on any OS."""
        s = _session("id", task='File: "test/path" <value> pipe|char back\\slash')
        result = s.as_filename()
        unsafe = set('<>:"/\\|?*') | {chr(c) for c in range(32)}
        assert not any(c in unsafe for c in result)
