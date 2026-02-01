"""TUI IPC client.

Used by mg commands to read and write TUI state. Communicates with the
running TUI server over a Unix domain socket (or Windows named pipe)
via multiprocessing.connection.

Each method opens a short-lived connection — no persistent sessions.

Usage:
    client = TuiClient(project="my-project")
    state = client.read()          # frozen snapshot, never throws*
    client.write(lambda m: setattr(m.hud, 'role', 'COO'))  # mutator pattern

* read() only raises on connection failure.
  write() raises ConcurrencyError on version mismatch.
"""

from __future__ import annotations

from multiprocessing.connection import Client
from typing import Callable

from mg._infrastructure.TuiServer import (
    ConcurrencyError,
    ErrorResponse,
    OkResponse,
    ReadRequest,
    Response,
    WriteRequest,
    freeze_model,
    pipe_address,
)
from mg.helpers.tui.TuiModel import TuiModel

# Re-export so callers can import ConcurrencyError from TuiClient
# without reaching into infrastructure.
__all__ = ["TuiClient", "ConcurrencyError"]


class TuiClient:
    """Remote IPC client for reading and writing TUI state.

    Used by mg commands running in separate processes. Each call opens a
    connection to the TUI server, sends a request, and reads the response.
    """

    def __init__(self, project: str) -> None:
        self._address = pipe_address(project)

    def read(self) -> TuiModel:
        """Read the current TUI state.

        Returns a deep-frozen snapshot. Never raises except on connection
        failure (ConnectionError).
        """
        response: Response = self._request(ReadRequest())

        if isinstance(response, OkResponse) and response.result is not None:
            return freeze_model(response.result)
        raise ConnectionError(f"Server error: {response}")

    def write(self, mutator: Callable[[TuiModel], None]) -> None:
        """Apply a mutation to the TUI state.

        Internally performs a read-modify-write cycle:
        1. Sends a read request to the server, receives mutable model.
        2. Calls mutator(model) — the caller modifies sections in place.
        3. Sends the modified model back with the original version(s).
        4. Server validates versions and applies or rejects.

        Raises:
            ConcurrencyError: Version mismatch — another writer got there first.
            ConnectionError: Cannot reach the TUI server.
        """
        # Read mutable copy
        read_response: Response = self._request(ReadRequest())
        if not isinstance(read_response, OkResponse) or read_response.result is None:
            raise ConnectionError(f"Server error: {read_response}")
        model = read_response.result

        # Apply mutator to the mutable copy
        mutator(model)

        # Send modified model back for version-checked merge
        write_response: Response = self._request(WriteRequest(model=model))

        if isinstance(write_response, OkResponse):
            return
        if isinstance(write_response, ErrorResponse):
            if write_response.kind == "concurrency":
                raise ConcurrencyError(write_response.message)
            raise ConnectionError(f"Server error: {write_response.message}")

    def _request(self, request: ReadRequest | WriteRequest) -> Response:
        """Send a request and return the response.

        Opens a short-lived connection for each request/response cycle.
        Wraps all OS-level errors as ConnectionError.
        """
        conn = self._connect()
        try:
            conn.send(request)
            return conn.recv()
        finally:
            conn.close()

    def _connect(self):
        """Open a connection to the TUI server.

        Wraps all OS-level errors as ConnectionError so callers have a
        single exception type for "can't reach the server."
        """
        try:
            return Client(self._address)
        except OSError as e:
            raise ConnectionError(f"Cannot connect to TUI server: {e}") from e
