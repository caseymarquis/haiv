"""Tests for TuiServer."""

import socket

import pytest

from mg._infrastructure.TuiServer import (
    ConcurrencyError,
    ReadRequest,
    TuiServer,
    WriteRequest,
    pipe_address,
)
from mg.helpers.tui.TuiModel import HudSection, TuiModel


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
        assert not srv._TuiServer__model_thread.is_alive()


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
        model1.hud.role = "changed"
        assert model2.hud.role is None

    def test_write_applies_non_none_fields(self, server):
        """Writing a section with non-None fields updates the model."""
        # Read, mutate, write
        future = server.submit(ReadRequest())
        model = future.result(timeout=1)
        model.hud.role = "COO"
        future = server.submit(WriteRequest(model=model))
        future.result(timeout=1)

        # Verify
        future = server.submit(ReadRequest())
        updated = future.result(timeout=1)
        assert updated.hud.role == "COO"

    def test_write_ignores_none_fields(self, server):
        """None fields in a write are not applied (partial update)."""
        # Set role first
        future = server.submit(ReadRequest())
        model = future.result(timeout=1)
        model.hud.role = "COO"
        future = server.submit(WriteRequest(model=model))
        future.result(timeout=1)

        # Write only summary, leave role as-is on the copy
        future = server.submit(ReadRequest())
        model = future.result(timeout=1)
        model.hud.summary = "Working"
        future = server.submit(WriteRequest(model=model))
        future.result(timeout=1)

        # Both should be present
        future = server.submit(ReadRequest())
        updated = future.result(timeout=1)
        assert updated.hud.role == "COO"
        assert updated.hud.summary == "Working"

    def test_write_rotates_version(self, server):
        """A successful write changes the section's version."""
        future = server.submit(ReadRequest())
        model = future.result(timeout=1)
        original_version = model.hud._version

        model.hud.role = "COO"
        future = server.submit(WriteRequest(model=model))
        future.result(timeout=1)

        future = server.submit(ReadRequest())
        updated = future.result(timeout=1)
        assert updated.hud._version != original_version

    def test_write_with_stale_version_raises(self, server):
        """Writing with a mismatched version raises ConcurrencyError."""
        # Do a write to advance the version
        future = server.submit(ReadRequest())
        model = future.result(timeout=1)
        model.hud.role = "COO"
        future = server.submit(WriteRequest(model=model))
        future.result(timeout=1)

        # Create a model with version 0 (stale)
        stale_model = TuiModel(hud=HudSection(role="CTO", _version=0))
        future = server.submit(WriteRequest(model=stale_model))
        with pytest.raises(ConcurrencyError):
            future.result(timeout=1)


