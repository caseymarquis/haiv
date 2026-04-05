"""TUI IPC client.

Used by haiv commands to read and write_raw TUI state. Communicates with
the running TUI server over a Unix domain socket (or Windows named pipe)
via multiprocessing.connection.

Each method opens a short-lived connection — no persistent sessions.

Usage:
    client = TuiClient(project="my-project")
    state = client.read()
    client.write_raw(sessions=SessionsRaw(entries=[...]))
"""

from __future__ import annotations

from multiprocessing.connection import Client

from haiv._infrastructure.TuiServer import (
    CommandRequest,
    ErrorResponse,
    OkResponse,
    ReadRequest,
    Response,
    TuiCommand,
    WriteRequest,
    freeze_model,
    pipe_address,
)
from haiv.helpers.tui.TuiModel import ActiveMindRaw, ClaudeHookEventsRaw, GitRaw, RecentCommitsRaw, RecentFilesRaw, SessionsRaw, TuiModel

__all__ = ["TuiClient"]


class TuiClient:
    """Remote IPC client for reading and writing TUI state.

    Used by haiv commands running in separate processes. Each call opens a
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

    def write_raw(
        self,
        *,
        sessions: SessionsRaw | None = None,
        git: GitRaw | None = None,
        active_mind: ActiveMindRaw | None = None,
        recent_files: RecentFilesRaw | None = None,
        recent_commits: RecentCommitsRaw | None = None,
        claude_hook_events: ClaudeHookEventsRaw | None = None,
    ) -> None:
        """Push raw data into the TUI model.

        Only the sections you provide are replaced on the server.
        Sections you omit are left untouched.

        Raises:
            ConnectionError: Cannot reach the TUI server.
        """
        model = TuiModel(
            sessions=sessions, git=git, active_mind=active_mind,
            recent_files=recent_files, recent_commits=recent_commits,
            claude_hook_events=claude_hook_events,
        )

        write_response: Response = self._request(WriteRequest(model=model))

        if isinstance(write_response, OkResponse):
            return
        if isinstance(write_response, ErrorResponse):
            raise ConnectionError(f"Server error: {write_response.message}")

    def send_command(self, command: TuiCommand) -> None:
        """Send a UI control command to the TUI.

        Raises:
            ConnectionError: Cannot reach the TUI server.
        """
        response: Response = self._request(CommandRequest(command=command))

        if isinstance(response, OkResponse):
            return
        if isinstance(response, ErrorResponse):
            raise ConnectionError(f"Server error: {response.message}")

    def _request(self, request: ReadRequest | WriteRequest | CommandRequest) -> Response:
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
