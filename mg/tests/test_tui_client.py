"""Tests for TuiClient (remote IPC) and TuiLocalClient (in-process).

Both clients share the same read/write interface. These tests verify
behavior through a running TuiServer — they're integration tests that
exercise the full request path.
"""

import pytest

# All tests in this module share a TuiServer socket, so they must run
# on the same xdist worker to avoid address conflicts.
pytestmark = pytest.mark.xdist_group("tui_server")

from haiv._infrastructure.TuiServer import TuiLocalClient, TuiServer
from haiv.helpers.tui.TuiClient import TuiClient
from haiv.helpers.tui.TuiClient import ConcurrencyError
from haiv.helpers.tui.TuiModel import HudSection, TuiModel


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
            model.hud.role = "COO"

    def test_read_reflects_current_state(self, remote_client):
        """read() reflects writes that have already been applied."""
        remote_client.write(lambda m: setattr(m.hud, 'role', 'COO'))
        model = remote_client.read()
        assert model.hud.role == "COO"


class TestRemoteClientWrite:
    """TuiClient.write() over IPC."""

    def test_write_applies_mutation(self, remote_client):
        """write() applies the mutator's changes."""
        remote_client.write(lambda m: setattr(m.hud, 'role', 'COO'))
        model = remote_client.read()
        assert model.hud.role == "COO"

    def test_write_partial_update(self, remote_client):
        """write() only touches fields the mutator sets."""
        remote_client.write(lambda m: setattr(m.hud, 'role', 'COO'))
        remote_client.write(lambda m: setattr(m.hud, 'summary', 'Working'))
        model = remote_client.read()
        assert model.hud.role == "COO"
        assert model.hud.summary == "Working"


class TestRemoteClientConnectionError:
    """TuiClient behavior when the server is unreachable."""

    def test_read_raises_on_no_server(self, tmp_path):
        """read() raises ConnectionError when no server is running."""
        client = TuiClient(f"nonexistent-{tmp_path.name}")
        with pytest.raises(ConnectionError):
            client.read()

    def test_write_raises_on_no_server(self, tmp_path):
        """write() raises ConnectionError when no server is running."""
        client = TuiClient(f"nonexistent-{tmp_path.name}")
        with pytest.raises(ConnectionError):
            client.write(lambda m: setattr(m.hud, 'role', 'COO'))


class TestLocalClientRead:
    """TuiLocalClient.read() via in-process queue."""

    def test_read_returns_frozen_model(self, local_client):
        """read() returns a TuiModel with frozen sections."""
        model = local_client.read()
        assert isinstance(model, TuiModel)
        with pytest.raises(AttributeError):
            model.hud.role = "COO"

    def test_read_reflects_current_state(self, local_client):
        """read() reflects writes that have already been applied."""
        local_client.write(lambda m: setattr(m.hud, 'role', 'COO'))
        model = local_client.read()
        assert model.hud.role == "COO"


class TestLocalClientWrite:
    """TuiLocalClient.write() via in-process queue."""

    def test_write_applies_mutation(self, local_client):
        """write() applies the mutator's changes."""
        local_client.write(lambda m: setattr(m.hud, 'role', 'COO'))
        model = local_client.read()
        assert model.hud.role == "COO"

    def test_write_partial_update(self, local_client):
        """write() only touches fields the mutator sets."""
        local_client.write(lambda m: setattr(m.hud, 'role', 'COO'))
        local_client.write(lambda m: setattr(m.hud, 'summary', 'Working'))
        model = local_client.read()
        assert model.hud.role == "COO"
        assert model.hud.summary == "Working"
