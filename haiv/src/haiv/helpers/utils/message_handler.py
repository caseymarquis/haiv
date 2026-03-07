"""Debounced batch message handler.

Collects messages from any thread and delivers them in batches to a handler
running on a dedicated worker thread. Delivery is debounced — the handler
is only called after a quiet period with no new messages.

IMPORTANT: The handler callable runs on a SEPARATE THREAD. Name your
handler to make this obvious at the call site:

    def _refresh_sessions_on_worker_thread(events: list[FileEvent]) -> None:
        client.write(...)   # TuiLocalClient is thread-safe

    watcher = MessageHandler(_refresh_sessions_on_worker_thread)
    watcher.start()
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from types import TracebackType
from typing import Generic, TypeVar

TMessage = TypeVar("TMessage")


class MessageHandler(Generic[TMessage]):
    """Collects messages and processes them in batches on a dedicated thread.

    IMPORTANT: ``handler`` runs on a separate thread. Name your handler to
    make this obvious at the call site — see module docstring for examples.

    Args:
        handler: Called with a list of all pending messages once the debounce
            window expires. Runs on the worker thread.
        debounce_seconds: Quiet time required after the last queue() call
            before the batch is delivered. Defaults to 1 second.
        tick_seconds: How often the worker thread checks for pending messages.
            Defaults to 0.5 seconds.
        on_error: Called if the handler raises. Receives the exception.
            Defaults to None (errors are silently swallowed).
    """

    def __init__(
        self,
        handler: Callable[[list[TMessage]], None],
        *,
        debounce_seconds: float = 1.0,
        tick_seconds: float = 0.5,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self._handler = handler
        self._debounce_seconds = debounce_seconds
        self._tick_seconds = tick_seconds
        self._on_error = on_error

        self._lock = threading.Lock()
        self._pending: list[TMessage] = []
        self._last_queue_time: float = 0.0

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> MessageHandler[TMessage]:
        """Launch the worker thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        """Signal shutdown, flush pending messages, and join the thread."""
        if self._thread is None:
            return

        self._stop_event.set()
        self._thread.join()
        self._thread = None

        # Flush anything left in the queue
        self._flush()

    def __enter__(self) -> MessageHandler[TMessage]:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop()

    def queue(self, message: TMessage) -> None:
        """Add a message to the pending queue. Thread-safe.

        Raises:
            RuntimeError: If start() has not been called.
        """
        if self._thread is None:
            raise RuntimeError("MessageHandler is not running — call start() first")

        with self._lock:
            self._pending.append(message)
            self._last_queue_time = time.monotonic()

    def _run(self) -> None:
        """Worker loop: wait for quiet period, then deliver batch."""
        while not self._stop_event.is_set():
            self._stop_event.wait(self._tick_seconds)
            self._maybe_flush()

    def _maybe_flush(self) -> None:
        """Flush if there are pending messages and the debounce window has passed."""
        with self._lock:
            if not self._pending:
                return
            elapsed = time.monotonic() - self._last_queue_time
            if elapsed < self._debounce_seconds:
                return

        self._flush()

    def _flush(self) -> None:
        """Drain pending messages and deliver to handler."""
        with self._lock:
            if not self._pending:
                return
            batch = self._pending[:]
            self._pending.clear()

        try:
            self._handler(batch)
        except Exception as e:
            if self._on_error is not None:
                try:
                    self._on_error(e)
                except Exception:
                    pass
