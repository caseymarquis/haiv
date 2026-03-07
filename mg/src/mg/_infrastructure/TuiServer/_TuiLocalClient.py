"""TUI local client.

In-process client used by the Textual UI to access TUI state. Provides
the same read/write interface as TuiClient, but communicates with the
server via its message queue instead of IPC.

This exists to enforce separation — Textual code should never access the
server's mutable model directly. TuiLocalClient only holds a reference
to the server's submit callable, not the server itself.

Calls are synchronous. The server's model thread operations are pure
in-memory (microseconds), so blocking on future.result() is safe and
doesn't stall Textual's event loop. If the model thread ever gains slow
operations, callers can upgrade to asyncio.wrap_future at that point.

Usage (inside a Textual widget):
    state = self.app.tui_client.read()
    self.app.tui_client.write(lambda m: setattr(m.hud, 'summary', 'Working'))
"""

from __future__ import annotations

import concurrent.futures
from typing import Callable

from ._freeze import freeze_model
from ._TuiIpc import ReadRequest, Request, WriteRequest
from haiv.helpers.tui.TuiModel import TuiModel


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
        future, returns a deep-frozen snapshot. Never raises.
        """
        future = self._submit(ReadRequest())
        model = future.result()
        return freeze_model(model)

    def write(self, mutator: Callable[[TuiModel], None]) -> None:
        """Apply a mutation to the TUI state.

        Reads a mutable copy from the server, applies the mutator,
        then sends the modified model back for version-checked merge.

        Raises:
            ConcurrencyError: Version mismatch — another writer got there first.
        """
        # Read mutable copy
        future = self._submit(ReadRequest())
        model = future.result()

        # Apply mutator to the mutable copy
        mutator(model)

        # Write back for version-checked merge
        future = self._submit(WriteRequest(model=model))
        future.result()  # raises ConcurrencyError on version mismatch
