"""Tests for MessageHandler — debounced batch processing on a worker thread."""

from __future__ import annotations

import threading
import time

import pytest

from mg.helpers.utils.message_handler import MessageHandler

# Fast tick for tests — don't wait 500ms per cycle.
_TICK = 0.02


class TestMessageHandler:
    """Core behavior: queue messages, receive batches after debounce."""

    def test_delivers_batch_after_debounce(self):
        """Messages queued in quick succession are delivered as one batch."""
        received: list[list[str]] = []
        event = threading.Event()

        def handler(batch: list[str]) -> None:
            received.append(batch)
            event.set()

        mh = MessageHandler(handler, debounce_seconds=0.1, tick_seconds=_TICK)
        mh.start()
        try:
            mh.queue("a")
            mh.queue("b")
            mh.queue("c")
            event.wait(timeout=2.0)
            assert received == [["a", "b", "c"]]
        finally:
            mh.stop()

    def test_separate_batches_after_quiet_period(self):
        """Messages separated by more than the debounce window arrive as separate batches."""
        received: list[list[str]] = []
        first_done = threading.Event()
        second_done = threading.Event()

        def handler(batch: list[str]) -> None:
            received.append(batch)
            if len(received) == 1:
                first_done.set()
            elif len(received) >= 2:
                second_done.set()

        mh = MessageHandler(handler, debounce_seconds=0.05, tick_seconds=_TICK)
        mh.start()
        try:
            mh.queue("first")
            first_done.wait(timeout=2.0)
            mh.queue("second")
            second_done.wait(timeout=2.0)
            assert received == [["first"], ["second"]]
        finally:
            mh.stop()

    def test_no_delivery_when_queue_empty(self):
        """Handler is never called if nothing is queued."""
        received: list[list[str]] = []

        def handler(batch: list[str]) -> None:
            received.append(batch)

        # Debounce + a few ticks is enough to confirm nothing fires.
        mh = MessageHandler(handler, debounce_seconds=0.02, tick_seconds=_TICK)
        mh.start()
        try:
            time.sleep(0.08)
            assert received == []
        finally:
            mh.stop()

    def test_stop_flushes_pending(self):
        """stop() delivers any pending messages before shutting down."""
        received: list[list[int]] = []

        def handler(batch: list[int]) -> None:
            received.append(batch)

        mh = MessageHandler(handler, debounce_seconds=10.0, tick_seconds=_TICK)
        mh.start()
        mh.queue(1)
        mh.queue(2)
        mh.stop()  # Should flush without waiting for debounce
        assert received == [[1, 2]]


class TestErrorHandling:
    """Handler errors are caught and routed, never crash the worker."""

    def test_handler_error_calls_on_error(self):
        """When handler raises, on_error receives the exception."""
        errors: list[Exception] = []
        event = threading.Event()

        def bad_handler(batch: list[str]) -> None:
            raise ValueError("boom")

        def on_error(e: Exception) -> None:
            errors.append(e)
            event.set()

        mh = MessageHandler(bad_handler, debounce_seconds=0.05, tick_seconds=_TICK, on_error=on_error)
        mh.start()
        try:
            mh.queue("x")
            event.wait(timeout=2.0)
            assert len(errors) == 1
            assert str(errors[0]) == "boom"
        finally:
            mh.stop()

    def test_handler_error_without_on_error_is_swallowed(self):
        """When handler raises and no on_error is set, worker continues."""
        received: list[list[str]] = []
        first_called = threading.Event()
        second_done = threading.Event()

        def flaky_handler(batch: list[str]) -> None:
            if not first_called.is_set():
                first_called.set()
                raise ValueError("first call fails")
            received.append(batch)
            second_done.set()

        mh = MessageHandler(flaky_handler, debounce_seconds=0.05, tick_seconds=_TICK)
        mh.start()
        try:
            mh.queue("fails")
            first_called.wait(timeout=2.0)
            mh.queue("succeeds")
            second_done.wait(timeout=2.0)
            assert received == [["succeeds"]]
        finally:
            mh.stop()

    def test_on_error_exception_is_swallowed(self):
        """If on_error itself raises, the worker still continues."""
        received: list[list[str]] = []
        first_called = threading.Event()
        second_done = threading.Event()

        def bad_handler(batch: list[str]) -> None:
            if not first_called.is_set():
                first_called.set()
                raise ValueError("handler boom")
            received.append(batch)
            second_done.set()

        def bad_on_error(e: Exception) -> None:
            raise RuntimeError("on_error boom")

        mh = MessageHandler(bad_handler, debounce_seconds=0.05, tick_seconds=_TICK, on_error=bad_on_error)
        mh.start()
        try:
            mh.queue("fails")
            first_called.wait(timeout=2.0)
            mh.queue("succeeds")
            second_done.wait(timeout=2.0)
            assert received == [["succeeds"]]
        finally:
            mh.stop()


class TestThreadSafety:
    """queue() is safe to call from multiple threads concurrently."""

    def test_concurrent_producers(self):
        """Messages from multiple threads all arrive in a single batch."""
        received: list[list[int]] = []
        event = threading.Event()

        def handler(batch: list[int]) -> None:
            received.append(batch)
            event.set()

        mh = MessageHandler(handler, debounce_seconds=0.15, tick_seconds=_TICK)
        mh.start()
        try:
            barrier = threading.Barrier(5)

            def produce(value: int) -> None:
                barrier.wait()
                mh.queue(value)

            threads = [threading.Thread(target=produce, args=(i,)) for i in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            event.wait(timeout=2.0)
            assert len(received) == 1
            assert sorted(received[0]) == [0, 1, 2, 3, 4]
        finally:
            mh.stop()


class TestLifecycle:
    """Start/stop behavior."""

    def test_stop_is_idempotent(self):
        """Calling stop() twice does not raise."""
        mh = MessageHandler(lambda batch: None, debounce_seconds=0.05, tick_seconds=_TICK)
        mh.start()
        mh.stop()
        mh.stop()  # Should not raise

    def test_queue_before_start_raises(self):
        """Queuing before start() is an error."""
        mh = MessageHandler(lambda batch: None)
        with pytest.raises(RuntimeError):
            mh.queue("x")
