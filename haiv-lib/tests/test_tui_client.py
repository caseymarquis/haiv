"""Tests for TuiClient (remote IPC) and TuiLocalClient (in-process).

Both clients share the same read/write_raw interface. These tests verify
behavior through a running TuiServer — they're integration tests that
exercise the full request path.
"""

import pytest

# All tests in this module share a TuiServer socket, so they must run
# on the same xdist worker to avoid address conflicts.
pytestmark = pytest.mark.xdist_group("tui_server")

from haiv._infrastructure.TuiServer import TuiCommand, TuiCommandType, TuiLocalClient, TuiServer
from haiv.helpers.tui.TuiClient import TuiClient
from haiv.helpers.tui.TuiModel import SessionsRaw, SessionEntry, TuiModel


@pytest.fixture
def server(tmp_path):
    """Start a TuiServer for testing."""
    project = f"test-{tmp_path.name}"
    srv = TuiServer(project)
    srv.start()
    yield srv
    srv.stop()


@pytest.fixture
def remote_client(server, tmp_path):
    """Create a TuiClient connected to the test server."""
    project = f"test-{tmp_path.name}"
    return TuiClient(project)


@pytest.fixture
def local_client(server):
    """Create a TuiLocalClient connected to the test server."""
    return TuiLocalClient(server.submit)


class TestRemoteClientRead:
    """TuiClient.read() over IPC."""

    def test_read_returns_frozen_model(self, remote_client):
        """read() returns a TuiModel with frozen sections."""
        model = remote_client.read()
        assert isinstance(model, TuiModel)
        with pytest.raises(AttributeError):
            model.sessions.entries = []

    def test_read_reflects_current_state(self, remote_client):
        """read() reflects write_raw that has already been applied."""
        remote_client.write_raw(sessions=SessionsRaw(entries=[SessionEntry(mind="wren")]))
        model = remote_client.read()
        assert len(model.sessions.entries) == 1
        assert model.sessions.entries[0].mind == "wren"


class TestRemoteClientWriteRaw:
    """TuiClient.write_raw() over IPC."""

    def test_write_raw_applies_section(self, remote_client):
        """write_raw() replaces the provided section."""
        remote_client.write_raw(sessions=SessionsRaw(entries=[SessionEntry(mind="wren")]))
        model = remote_client.read()
        assert model.sessions.entries[0].mind == "wren"

    def test_write_raw_independent_sections(self, remote_client):
        """write_raw() only touches provided sections."""
        remote_client.write_raw(sessions=SessionsRaw(entries=[SessionEntry(mind="wren")]))
        remote_client.write_raw(git=None)  # no-op for git
        model = remote_client.read()
        assert len(model.sessions.entries) == 1


class TestRemoteClientConnectionError:
    """TuiClient behavior when the server is unreachable."""

    def test_read_raises_on_no_server(self, tmp_path):
        """read() raises ConnectionError when no server is running."""
        client = TuiClient(f"nonexistent-{tmp_path.name}")
        with pytest.raises(ConnectionError):
            client.read()

    def test_write_raw_raises_on_no_server(self, tmp_path):
        """write_raw() raises ConnectionError when no server is running."""
        client = TuiClient(f"nonexistent-{tmp_path.name}")
        with pytest.raises(ConnectionError):
            client.write_raw(sessions=SessionsRaw(entries=[]))


class TestLocalClientRead:
    """TuiLocalClient.read() via in-process queue."""

    def test_read_returns_frozen_model(self, local_client):
        """read() returns a TuiModel with frozen sections."""
        model = local_client.read()
        assert isinstance(model, TuiModel)
        with pytest.raises(AttributeError):
            model.sessions.entries = []

    def test_read_reflects_current_state(self, local_client):
        """read() reflects write_raw that has already been applied."""
        local_client.write_raw(sessions=SessionsRaw(entries=[SessionEntry(mind="wren")]))
        model = local_client.read()
        assert model.sessions.entries[0].mind == "wren"


class TestLocalClientWriteRaw:
    """TuiLocalClient.write_raw() via in-process queue."""

    def test_write_raw_applies_section(self, local_client):
        """write_raw() replaces the provided section."""
        local_client.write_raw(sessions=SessionsRaw(entries=[SessionEntry(mind="wren")]))
        model = local_client.read()
        assert model.sessions.entries[0].mind == "wren"

    def test_write_raw_independent_sections(self, local_client):
        """write_raw() only touches provided sections."""
        local_client.write_raw(sessions=SessionsRaw(entries=[SessionEntry(mind="wren")]))
        local_client.write_raw(git=None)
        model = local_client.read()
        assert len(model.sessions.entries) == 1


class TestLocalClientSendCommand:
    """TuiLocalClient.send_command() via in-process queue."""

    def test_send_command_buffers_on_server(self, local_client, server):
        """send_command() enqueues a command that drain_commands() returns."""
        cmd = TuiCommand(type=TuiCommandType.RESTART, payload=None)
        local_client.send_command(cmd)

        commands = server.drain_commands()
        assert len(commands) == 1
        assert commands[0].type == TuiCommandType.RESTART

    def test_send_command_does_not_dirty_model(self, local_client, server):
        """send_command() does not mark any model sections dirty."""
        cmd = TuiCommand(type=TuiCommandType.BOUNCE, payload=None)
        local_client.send_command(cmd)

        dirty = server.drain_dirty()
        assert len(dirty) == 0


class TestRemoteClientSendCommand:
    """TuiClient.send_command() over IPC."""

    def test_send_command_buffers_on_server(self, remote_client, server):
        """send_command() over IPC enqueues a command."""
        cmd = TuiCommand(type=TuiCommandType.RESTART, payload=None)
        remote_client.send_command(cmd)

        commands = server.drain_commands()
        assert len(commands) == 1
        assert commands[0].type == TuiCommandType.RESTART
