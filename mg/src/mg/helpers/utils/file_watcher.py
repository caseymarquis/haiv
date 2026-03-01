"""File system watcher with built-in debounced batch delivery.

Wraps watchdog and MessageHandler to detect file/directory changes and
deliver them as batched Path lists to a callback after a quiet period.

IMPORTANT: The callback runs on a SEPARATE THREAD. See MessageHandler
docs for naming conventions that make this obvious at the call site.

Usage:

    def _refresh_on_worker_thread(paths: list[Path]) -> None:
        client.write(...)  # TuiLocalClient is thread-safe

    watcher = FileWatcher(_refresh_on_worker_thread, debounce_seconds=1.0)
    watcher.watch_file(sessions_file)
    watcher.watch_directory(minds_dir)
    watcher.start()

    # ... later ...
    watcher.stop()
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from mg.helpers.utils.message_handler import MessageHandler


class FileWatcher:
    """Watches files and directories, delivering changed paths in debounced batches.

    IMPORTANT: ``handler`` runs on a separate thread. See module docstring.

    Args:
        handler: Called with a list of changed Paths after the debounce
            window expires. Runs on a worker thread.
        debounce_seconds: Quiet time after the last change before delivering
            the batch. Defaults to 0.5 seconds.
        tick_seconds: How often the worker checks for pending changes.
            Defaults to 0.1 seconds.
        on_error: Called if the handler raises. Receives the exception.
    """

    def __init__(
        self,
        handler: Callable[[list[Path]], None],
        *,
        debounce_seconds: float = 0.5,
        tick_seconds: float = 0.1,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self._mh = MessageHandler(
            handler,
            debounce_seconds=debounce_seconds,
            tick_seconds=tick_seconds,
            on_error=on_error,
        )
        self._observer = Observer()
        self._watches: list[tuple[str, bool, set[str] | None]] = []

    def watch_file(self, path: Path) -> None:
        """Watch a single file for changes.

        Internally watches the parent directory and filters to only the
        target file, since watchdog operates on directories.
        """
        resolved = path.resolve()
        self._watches.append((str(resolved.parent), False, {str(resolved)}))

    def watch_directory(self, path: Path) -> None:
        """Watch a directory recursively for changes."""
        self._watches.append((str(path.resolve()), True, None))

    def start(self) -> None:
        """Start watching for file system changes."""
        for watch_path, recursive, file_filter in self._watches:
            bridge = _BridgeHandler(self._mh, file_filter)
            self._observer.schedule(bridge, watch_path, recursive=recursive)
        self._mh.start()
        self._observer.start()

    def stop(self) -> None:
        """Stop watching and flush any pending changes."""
        self._observer.stop()
        self._observer.join()
        self._mh.stop()


class _BridgeHandler(FileSystemEventHandler):
    """Bridges watchdog events to MessageHandler.queue()."""

    def __init__(
        self, mh: MessageHandler[Path], file_filter: set[str] | None,
    ) -> None:
        self._mh = mh
        self._file_filter = file_filter

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        src = event.src_path
        if self._file_filter is not None and src not in self._file_filter:
            return
        self._mh.queue(Path(src))
