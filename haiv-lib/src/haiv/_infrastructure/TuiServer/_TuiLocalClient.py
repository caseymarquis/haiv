"""TUI local client.

In-process client used by the Textual UI to access TUI state. Provides
the same read/write_raw interface as TuiClient, but communicates with
the server via its message queue instead of IPC.

This exists to enforce separation — Textual code should never access the
server's mutable model directly. TuiLocalClient only holds a reference
to the server's submit callable, not the server itself.

Calls are synchronous. The server's model thread operations are pure
in-memory (microseconds), so blocking on future.result() is safe and
doesn't stall Textual's event loop.

Usage (inside a Textual widget):
    state = self.app.tui_client.read()
    self.app.tui_client.write_raw(sessions=SessionsRaw(entries=[...]))
"""

from __future__ import annotations

import concurrent.futures
from typing import Callable

from ._freeze import freeze_model
from ._TuiIpc import ReadRequest, Request, WriteRequest
from haiv.helpers.tui.TuiModel import ActiveMindRaw, GitRaw, SessionsRaw, TuiModel


class TuiLocalClient:
    """In-process client for the Textual UI to access TUI state.

    Only holds a reference to the server's submit callable — cannot
    touch the model directly. Same safety boundary as TuiIpcListener.
    """

    def __init__(self, submit: Callable[[Request], concurrent.futures.Future]) -> None:
        self._submit = submit

    def read(self) -> TuiModel:
        """Read the current TUI state.

        Submits a read request to the server's queue, blocks on the
        future, returns a deep-frozen snapshot.
        """
        future = self._submit(ReadRequest())
        model = future.result()
        return freeze_model(model)

    def write_raw(
        self,
        *,
        sessions: SessionsRaw | None = None,
        git: GitRaw | None = None,
        active_mind: ActiveMindRaw | None = None,
    ) -> None:
        """Push raw data into the TUI model.

        Only the sections you provide are replaced on the server.
        Sections you omit are left untouched.
        """
        model = TuiModel(sessions=sessions, git=git, active_mind=active_mind)
        future = self._submit(WriteRequest(model=model))
        future.result()
