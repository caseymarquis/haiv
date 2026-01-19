"""Tests for mg.helpers.sessions module."""

import pytest
from datetime import datetime, timezone

from mg.helpers.sessions import (
    Session,
    load_sessions,
    save_session,
    get_session,
    get_most_recent_session_for_mind,
)


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
