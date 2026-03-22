"""Tests for TuiModel and related utilities."""

import dataclasses

import pytest

from haiv._infrastructure.TuiServer import freeze_model, pipe_address
from haiv.helpers.tui.TuiModel import SessionsRaw, SessionEntry, TuiModel


class TestTuiModelStructure:
    """TuiModel section fields are all optional (None = not provided)."""

    def test_default_sections_are_present(self):
        """TuiModel() creates all sections with defaults."""
        model = TuiModel()
        assert model.sessions is not None
        assert model.git is not None
        assert model.active_mind is not None

    def test_none_sections_for_write(self):
        """Sections can be None to indicate 'not provided' on write."""
        model = TuiModel(sessions=None, git=None, active_mind=None)
        assert model.sessions is None
        assert model.git is None
        assert model.active_mind is None


class TestTuiModelFreeze:
    """freeze_model() produces a deep-frozen snapshot."""

    def test_frozen_sections_reject_assignment(self):
        """Fields on frozen sections can't be modified."""
        model = TuiModel()
        frozen = freeze_model(model)
        assert frozen.sessions is not None
        with pytest.raises(AttributeError):
            frozen.sessions.entries = []

    def test_frozen_preserves_values(self):
        """Frozen copy has the same field values as the original."""
        entry = SessionEntry(mind="wren", task="test task")
        model = TuiModel(sessions=SessionsRaw(entries=[entry]))
        frozen = freeze_model(model)
        assert frozen.sessions is not None
        assert len(frozen.sessions.entries) == 1
        assert frozen.sessions.entries[0].mind == "wren"
        assert frozen.sessions.entries[0].task == "test task"

    def test_frozen_is_independent_copy(self):
        """Mutating the original after freeze doesn't affect the snapshot."""
        sessions = SessionsRaw(entries=[SessionEntry(mind="wren")])
        model = TuiModel(sessions=sessions)
        frozen = freeze_model(model)
        sessions.entries.clear()
        assert frozen.sessions is not None
        assert len(frozen.sessions.entries) == 1

    def test_frozen_skips_none_sections(self):
        """None sections pass through freeze unchanged."""
        model = TuiModel(sessions=None, git=None, active_mind=None)
        frozen = freeze_model(model)
        assert frozen.sessions is None
        assert frozen.git is None


class TestSessionEntry:
    """SessionEntry raw data fields."""

    def test_defaults(self):
        """SessionEntry has sensible defaults."""
        entry = SessionEntry()
        assert entry.mind == ""
        assert entry.branch == ""
        assert entry.status == "started"


class TestPipeAddress:
    """pipe_address() returns the correct IPC path per platform."""

    def test_unix_address(self, monkeypatch):
        """Unix returns a socket path in /tmp."""
        monkeypatch.setattr("haiv._infrastructure.TuiServer._TuiIpc.platform.system", lambda: "Linux")
        assert pipe_address("myproject") == "/tmp/haiv-myproject.sock"

    def test_windows_address(self, monkeypatch):
        """Windows returns a named pipe path."""
        monkeypatch.setattr("haiv._infrastructure.TuiServer._TuiIpc.platform.system", lambda: "Windows")
        assert pipe_address("myproject") == r"\\.\pipe\haiv-myproject"
