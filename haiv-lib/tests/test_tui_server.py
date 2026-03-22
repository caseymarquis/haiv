"""Tests for TuiServer."""

import socket
import sys
import threading
from typing import cast

import pytest

from haiv._infrastructure.TuiServer import (
    ReadRequest,
    TuiServer,
    WriteRequest,
    pipe_address,
)
from haiv.helpers.tui.TuiModel import SessionsRaw, SessionEntry, TuiModel


@pytest.fixture
def server(tmp_path):
    """Create a TuiServer with a unique socket in tmp_path.

    Uses tmp_path to avoid collisions with real sockets or other tests.
    """
    project = f"test-{tmp_path.name}"
    srv = TuiServer(project)
    srv.start()
    yield srv
    srv.stop()


class TestServerLifecycle:
    """Start, stop, and single-instance enforcement."""

    def test_start_and_stop(self, tmp_path):
        """Server starts and stops without error."""
        project = f"test-{tmp_path.name}"
        srv = TuiServer(project)
        srv.start()
        srv.stop()

    def test_second_instance_refused(self, server, tmp_path):
        """Starting a second server for the same project raises."""
        project = f"test-{tmp_path.name}"
        second = TuiServer(project)
        with pytest.raises(RuntimeError):
            second.start()

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix sockets not available on Windows; named pipes don't leave stale files")
    def test_stale_socket_recovery(self, tmp_path):
        """If a stale socket file exists, server recovers and starts."""
        project = f"test-{tmp_path.name}"
        addr = pipe_address(project)

        # Create a real stale socket: bind then close without unlinking.
        s = socket.socket(socket.AF_UNIX)
        s.bind(addr)
        s.close()

        # Server should detect stale socket, unlink, and bind successfully.
        srv = TuiServer(project)
        srv.start()
        srv.stop()


class TestServerShutdown:
    """Clean shutdown behavior."""

    def test_stop_joins_threads(self, tmp_path):
        """After stop(), neither thread is alive."""
        project = f"test-{tmp_path.name}"
        srv = TuiServer(project)
        srv.start()
        srv.stop()
        thread = cast(threading.Thread, getattr(srv, "_TuiServer__model_thread"))
        assert not thread.is_alive()


class TestServerReadWrite:
    """Read and write operations via submit()."""

    def test_read_returns_model(self, server):
        """A read request returns a TuiModel."""
        future = server.submit(ReadRequest())
        model = future.result(timeout=1)
        assert isinstance(model, TuiModel)

    def test_read_returns_independent_copy(self, server):
        """Each read returns a separate mutable copy."""
        future1 = server.submit(ReadRequest())
        model1 = future1.result(timeout=1)
        future2 = server.submit(ReadRequest())
        model2 = future2.result(timeout=1)
        model1.sessions.entries.append(SessionEntry(mind="wren"))
        assert len(model2.sessions.entries) == 0

    def test_write_replaces_provided_section(self, server):
        """Writing a section replaces it on the model."""
        entry = SessionEntry(mind="wren", task="test")
        model = TuiModel(sessions=SessionsRaw(entries=[entry]))
        future = server.submit(WriteRequest(model=model))
        future.result(timeout=1)

        future = server.submit(ReadRequest())
        updated = future.result(timeout=1)
        assert len(updated.sessions.entries) == 1
        assert updated.sessions.entries[0].mind == "wren"

    def test_write_skips_none_sections(self, server):
        """None sections are left untouched."""
        # Write sessions
        entry = SessionEntry(mind="wren", task="test")
        model = TuiModel(sessions=SessionsRaw(entries=[entry]), git=None)
        future = server.submit(WriteRequest(model=model))
        future.result(timeout=1)

        # Write only git (sessions=None), sessions should survive
        model2 = TuiModel(sessions=None, git=None, active_mind=None)
        future = server.submit(WriteRequest(model=model2))
        future.result(timeout=1)

        future = server.submit(ReadRequest())
        updated = future.result(timeout=1)
        assert len(updated.sessions.entries) == 1
        assert updated.sessions.entries[0].mind == "wren"

    def test_write_marks_dirty(self, server):
        """Writing a section marks it dirty."""
        entry = SessionEntry(mind="wren")
        model = TuiModel(sessions=SessionsRaw(entries=[entry]))
        future = server.submit(WriteRequest(model=model))
        future.result(timeout=1)

        dirty = server.drain_dirty()
        assert "sessions" in dirty

    def test_drain_dirty_clears(self, server):
        """drain_dirty returns and clears the dirty set."""
        entry = SessionEntry(mind="wren")
        model = TuiModel(sessions=SessionsRaw(entries=[entry]))
        future = server.submit(WriteRequest(model=model))
        future.result(timeout=1)

        dirty1 = server.drain_dirty()
        dirty2 = server.drain_dirty()
        assert "sessions" in dirty1
        assert len(dirty2) == 0


