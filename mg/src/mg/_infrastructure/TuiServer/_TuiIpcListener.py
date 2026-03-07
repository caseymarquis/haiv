"""TUI IPC listener.

Accepts connections from remote clients (haiv commands) and submits their
requests to the server's message queue. Isolated from the model — only
holds a reference to the submit callable.

This enforces the same safety boundary as TuiLocalClient: neither can
touch the model directly.
"""

from __future__ import annotations

import concurrent.futures
import threading
from multiprocessing.connection import Client, Listener
from typing import Callable

from ._TuiIpc import (
    ConcurrencyError,
    ErrorResponse,
    OkResponse,
    Request,
    Response,
)


class TuiIpcListener:
    """IPC accept loop, isolated from the model.

    Only has access to a submit callable — cannot touch the model
    directly. This enforces the same safety boundary as TuiLocalClient.
    """

    def __init__(
        self,
        listener: Listener,
        submit: Callable[[Request], concurrent.futures.Future],
        stop_event: threading.Event,
    ) -> None:
        self._listener = listener
        self._submit = submit
        self._stop_event = stop_event
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the accept thread."""
        self._thread = threading.Thread(
            target=self._accept_loop, daemon=True, name="tui-ipc",
        )
        self._thread.start()

    def close(self) -> None:
        """Shut down the accept loop and clean up.

        Makes a dummy connection to unblock accept() so the thread
        exits promptly, then closes the underlying listener.
        """
        # Dummy connection unblocks accept() immediately so the thread
        # can see the stop flag and exit without waiting for a timeout.
        try:
            dummy = Client(self._listener.address)
            dummy.close()
        except OSError:
            pass
        try:
            self._listener.close()
        except OSError:
            pass
        if self._thread:
            self._thread.join(timeout=2)

    def _accept_loop(self) -> None:
        """Accept connections, read requests, submit via the queue.

        Each connection is one request/response, then closed.
        """
        while not self._stop_event.is_set():
            try:
                conn = self._listener.accept()
            except OSError:
                break  # Listener was closed (shutdown)

            # After accepting, re-check the stop flag to handle the
            # dummy connection from close() — just drop it and exit.
            if self._stop_event.is_set():
                try:
                    conn.close()
                except Exception:
                    pass
                break

            try:
                request: Request = conn.recv()
                future = self._submit(request)

                try:
                    result = future.result(timeout=5)
                    response: Response = OkResponse(result=result)
                except ConcurrencyError as e:
                    response = ErrorResponse(kind="concurrency", message=str(e))
                except Exception as e:
                    response = ErrorResponse(kind="internal", message=str(e))

                conn.send(response)
            except Exception:
                pass  # Connection error during recv/send, move on
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
