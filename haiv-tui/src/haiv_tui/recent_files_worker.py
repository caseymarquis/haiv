"""Background worker that gathers recent files across worktrees.

Runs on its own thread. Watches the worktrees directory for changes and
re-gathers on edits. Only does work when the file watcher signals a change.

TODO: Subscribe to active mind via a publish mechanism instead of polling.
      The TUI should publish derived state for external consumers.
"""

from __future__ import annotations

import threading
from pathlib import Path

from haiv._infrastructure.TuiServer import TuiLocalClient
from haiv.helpers.tui.recent_files import gather_recent_files
from haiv.helpers.utils.file_watcher import FileWatcher
from haiv_tui.command_filters import is_claude_hook_stop


class RecentFilesWorker:
    """Background thread that keeps recent files up to date.

    Lifecycle: create → start() → stop(). Not reusable after stop.
    """

    def __init__(self, *, client: TuiLocalClient, worktrees_dir: Path) -> None:
        self._client = client
        self._worktrees_dir = worktrees_dir
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._watcher: FileWatcher | None = None
        self._gather_requested = threading.Event()

    def start(self) -> RecentFilesWorker:
        self._thread = threading.Thread(target=self._run, daemon=True, name="recent-files")
        self._thread.start()

        if self._worktrees_dir.is_dir():
            def _on_change(paths: list[Path]) -> None:
                self._gather_requested.set()

            self._watcher = (
                FileWatcher(_on_change, debounce_seconds=1.0)
                .watch_directory(self._worktrees_dir)
                .start()
            )

        return self

    def request_gather(self) -> None:
        """Request a re-gather from an external trigger."""
        self._gather_requested.set()

    def register_with(self, dispatcher) -> None:
        """Listen for Stop hook events to trigger a refresh."""
        def _on_command(command_type, payload) -> None:
            if is_claude_hook_stop(command_type, payload):
                self.request_gather()

        dispatcher.add_listener(_on_command)

    def stop(self) -> None:
        self._stop.set()
        self._gather_requested.set()  # unblock wait
        if self._watcher is not None:
            self._watcher.stop()
            self._watcher = None
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _run(self) -> None:
        # Initial gather
        self._gather_and_push()

        while not self._stop.is_set():
            self._gather_requested.wait()
            self._gather_requested.clear()
            if self._stop.is_set():
                break
            self._gather_and_push()

    def _gather_and_push(self) -> None:
        try:
            recent = gather_recent_files(self._worktrees_dir)
            self._client.write_raw(recent_files=recent)
        except Exception:
            pass
