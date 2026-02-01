"""TUI IPC server.

Runs inside the TUI process. Owns the authoritative TuiModel and serves
state to both remote clients (mg commands via IPC) and the local Textual
UI (via TuiLocalClient).

Thread safety:
    All model mutation happens on a single thread (the model thread).
    All other access is via deep copies sent through a thread-safe queue
    and resolved via futures. No locks are needed on the model itself
    because it is only ever touched by one thread. Callers receive
    independent copies — either mutable (for write-back) or frozen
    (for display). This is safe because the copies are fully independent
    objects with no shared mutable state.

Threading architecture (two threads, neither managed by Textual):

    IPC listener (TuiIpcListener, separate file) — blocks on
    Listener.accept(), reads incoming messages, submits them via
    submit(). Has no access to the model; it only holds a reference
    to the submit callable.

    Model thread — owns the authoritative TuiModel. Drains the message
    queue, processes reads and writes, resolves futures.

    Textual's main thread uses TuiLocalClient, which also only has
    access to submit(). Same boundary as the IPC listener.

    Model thread operations are pure in-memory — microseconds. Callers
    can safely block on futures without wrapping for async. If the model
    thread ever gains slow operations, callers can upgrade to
    asyncio.wrap_future at that point.

Startup (stale socket recovery):
    1. Try to bind the listener socket.
    2. If bind fails, try to connect to the existing socket.
    3. If connect succeeds — another instance is live, refuse to start.
    4. If connect refused — stale socket from a crash. Unlink, retry bind.
    (Windows named pipes are kernel objects cleaned up automatically,
    but this flow is harmless on both platforms.)

Shutdown:
    Close the listener to unblock accept(), set a stop flag, join both
    threads. Outstanding operations may raise — wrapped in try/except
    so the app exits cleanly.
"""

from __future__ import annotations

import concurrent.futures
import copy
import dataclasses
import os
import queue
import random
import threading
from multiprocessing.connection import Client, Listener

from ._TuiIpc import (
    ConcurrencyError,
    ReadRequest,
    Request,
    WriteRequest,
    pipe_address,
)
from ._TuiIpcListener import TuiIpcListener
from mg.helpers.tui.TuiModel import TuiModel


class TuiServer:
    """Server-side handler for TUI state.

    Owns the authoritative TuiModel. Runs the model thread and
    coordinates the IPC listener. All external access (both IPC and
    local) goes through submit(), ensuring the model is only ever
    touched by the model thread.
    """

    def __init__(self, project: str, model: TuiModel | None = None) -> None:
        self._address = pipe_address(project)
        # Double-underscore for name mangling — discourages accidental
        # access from outside TuiServer.
        self.__model = model or TuiModel()
        self._queue: queue.Queue[tuple[Request, concurrent.futures.Future]] = queue.Queue()
        self._stop_event = threading.Event()
        self._ipc_listener: TuiIpcListener | None = None
        self.__model_thread: threading.Thread | None = None

    def start(self) -> None:
        """Bind the IPC socket and start both threads.

        Performs stale socket recovery if needed:
        bind → fail → connect → refused → unlink → rebind.

        Raises:
            RuntimeError: If another TUI server is already running.
        """
        listener = self._bind()
        self._stop_event.clear()

        # IPC listener gets only the submit callable — no model access.
        self._ipc_listener = TuiIpcListener(
            listener=listener,
            submit=self.submit,
            stop_event=self._stop_event,
        )

        self.__model_thread = threading.Thread(
            target=self.__model_loop, daemon=True, name="tui-model",
        )
        self.__model_thread.start()
        self._ipc_listener.start()

    def stop(self) -> None:
        """Shut down both threads and close the IPC socket.

        Sets the stop flag, closes the IPC listener (which unblocks
        accept via a dummy connection), and joins the model thread.
        Cleans up the socket file on Unix.
        """
        self._stop_event.set()
        if self._ipc_listener:
            self._ipc_listener.close()
        if self.__model_thread:
            self.__model_thread.join(timeout=2)
        try:
            os.unlink(self._address)
        except (OSError, FileNotFoundError):
            pass

    def submit(self, request: Request) -> concurrent.futures.Future:
        """Submit a request to the model thread's message queue.

        Used by TuiIpcListener and TuiLocalClient. Returns a
        concurrent.futures.Future that resolves once the model thread
        processes the request.

        Model thread operations are pure in-memory, so callers can
        safely call future.result() directly (blocking). No async
        wrapping needed unless the model thread gains slow operations
        in the future.
        """
        future: concurrent.futures.Future = concurrent.futures.Future()
        self._queue.put((request, future))
        return future

    # -- Internal: binding with stale socket recovery --

    def _bind(self) -> Listener:
        """Bind the IPC socket with stale socket recovery.

        1. Try to bind — if it works, done.
        2. Bind failed — try to connect to the existing socket.
        3. Connect succeeds — another instance is live, refuse to start.
        4. Connect refused — stale socket, unlink the file, retry bind.
        """
        try:
            return Listener(self._address)
        except OSError:
            try:
                conn = Client(self._address)
                conn.close()
                raise RuntimeError("Another TUI server is already running")
            except ConnectionRefusedError:
                os.unlink(self._address)
                return Listener(self._address)

    # -- Internal: model thread --
    # This is the ONLY code that touches self.__model. All other access
    # is via copies returned through futures.

    def __model_loop(self) -> None:
        """Model thread main loop.

        Blocks on queue.get(timeout=short) to avoid CPU burn while idle.
        On timeout, checks the stop flag and loops. When a message arrives,
        processes it (read or write) and resolves the caller's future.

        Both IPC and local requests are handled through the same path.
        Runs until the stop flag is set.
        """
        while not self._stop_event.is_set():
            try:
                request, future = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                if isinstance(request, ReadRequest):
                    # Return a mutable deep copy. The caller freezes it
                    # for display or mutates it for a write-back.
                    result = copy.deepcopy(self.__model)
                    future.set_result(result)
                elif isinstance(request, WriteRequest):
                    self._apply_write(request.model)
                    future.set_result(None)
            except Exception as e:
                future.set_exception(e)

    def _apply_write(self, incoming: TuiModel) -> None:
        """Apply a client write to the authoritative model.

        Per section: if incoming version matches, apply non-None fields
        and rotate version. If mismatch, raise ConcurrencyError.
        """
        for f in dataclasses.fields(TuiModel):
            inc_section = getattr(incoming, f.name)
            cur_section = getattr(self.__model, f.name)

            if inc_section._version != cur_section._version:
                raise ConcurrencyError(
                    f"Version mismatch on section '{f.name}': "
                    f"expected {cur_section._version}, got {inc_section._version}"
                )

            # Apply non-None fields (skip _version)
            for sf in dataclasses.fields(inc_section):
                if sf.name == "_version":
                    continue
                value = getattr(inc_section, sf.name)
                if value is not None:
                    setattr(cur_section, sf.name, value)

            # Rotate version to a new random value
            cur_section._version = random.randint(1, 2**63)
